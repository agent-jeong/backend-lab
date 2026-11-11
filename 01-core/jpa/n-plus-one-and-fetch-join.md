---
title: "N+1 문제와 Fetch Join 해결"
description: 목록 API에서 쿼리가 건수만큼 늘어나는 이유와, fetch join과 BatchSize 중 무엇을 쓰는지
tags: [concept, jpa]
---

# N+1 문제와 Fetch Join 해결

N+1 문제는 쿼리 한 번으로 N건을 가져온 뒤, 건마다 연관 데이터를 읽느라 쿼리가 N번 더 나가는 현상이다.

JPA를 쓰면 가장 자주 만나는 성능 문제다. 개발 환경은 데이터가 적어서 티가 안 나다가, 운영에서 주문 목록 API가 주문 수만큼 느려지고 커넥션을 오래 쥐어서 풀까지 바닥낸다. 그래서 목록 API를 보면 쿼리 수가 건수만큼 늘어나는지부터 본다.

## 어떻게 생기나

```java
@Entity
public class Order {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
}
```

```java
@Transactional(readOnly = true)
public List<OrderResponse> getOrders() {
    List<Order> orders = orderRepository.findAll(); // 1번 쿼리

    return orders.stream()
        .map(order -> new OrderResponse(
            order.getId(),
            order.getUser().getName() // 주문마다 User SELECT → N번 쿼리
        ))
        .toList();
}
```

```sql
-- 1번: 주문 목록 조회
SELECT * FROM orders;

-- N번: 각 주문의 사용자 조회
SELECT * FROM users WHERE id = 1;
SELECT * FROM users WHERE id = 2;
SELECT * FROM users WHERE id = 3;
...
```

주문이 100건이면 쿼리가 101번 나간다.

## 해결 1: Fetch Join

```java
@Query("SELECT o FROM Order o JOIN FETCH o.user")
List<Order> findAllWithUser();
```

```sql
SELECT o.*, u.* FROM orders o INNER JOIN users u ON o.user_id = u.id
```

쿼리 한 번으로 Order와 User를 같이 가져온다.

### 컬렉션 fetch join

`@OneToMany` 쪽을 fetch join하면 SQL 결과에서 자식 수만큼 부모 행이 중복된다.

```java
@Query("SELECT DISTINCT u FROM User u JOIN FETCH u.orders")
List<User> findAllWithOrders();
```

Hibernate 6부터는 `DISTINCT` 없이도 중복된 부모 Entity를 알아서 걸러 낸다. `DISTINCT`를 쓰면 SQL에도 그대로 들어간다. Hibernate 5에서는 `DISTINCT`를 써야 중복 부모가 걸러졌다.

### 컬렉션 fetch join과 페이징

컬렉션 fetch join과 페이징은 함께 쓸 수 없다.

```java
// 위험: 메모리에서 페이징 처리 (모든 데이터를 먼저 가져옴)
@Query("SELECT u FROM User u JOIN FETCH u.orders")
Page<User> findAllWithOrders(Pageable pageable);
```

Hibernate는 경고 로그 한 줄만 남기고, 전체 데이터를 메모리에 올린 다음 거기서 페이징한다. 이럴 때는 `@BatchSize`를 쓴다.

## 해결 2: @BatchSize

```java
@Entity
public class User {

    @BatchSize(size = 100)
    @OneToMany(mappedBy = "user")
    private List<Order> orders = new ArrayList<>();
}
```

전역으로 걸 수도 있다.

```yaml
spring:
  jpa:
    properties:
      hibernate:
        default_batch_fetch_size: 100
```

```sql
-- BatchSize 적용: IN 절로 묶어서 조회
SELECT * FROM orders WHERE user_id IN (1, 2, 3, ... , 100);
```

N번 나가던 쿼리가 `ceil(N / batchSize)`번으로 준다. 컬렉션 fetch join과 달리 페이징과 같이 쓸 수 있어서, 실무에서는 보통 `default_batch_fetch_size`를 전역으로 걸어 두고 페이징하는 곳에서 덕을 본다.

## 해결 3: EntityGraph

```java
@EntityGraph(attributePaths = {"user"})
List<Order> findAll();
```

JPQL을 쓰지 않고도 fetch join처럼 가져온다. 간단할 때는 편하지만, 조건이 복잡하면 JPQL fetch join으로 쓰는 편이 읽기 쉽다.

## 무엇을 고르나

| 방법 | 장점 | 단점 |
|---|---|---|
| Fetch Join | 쿼리 한 번으로 끝난다 | 컬렉션은 페이징 불가, `List` 컬렉션 둘 이상은 동시에 fetch 불가 |
| `@BatchSize` | 페이징과 같이 쓸 수 있고, 설정이 간단하다 | 쿼리가 몇 번 더 나갈 수 있다 |
| `@EntityGraph` | 어노테이션 하나로 끝난다 | 조건이 복잡하면 표현하기 어렵다 |
| DTO 직접 조회 | 필요한 컬럼만 가져와서 가장 가볍다 | 코드가 복잡해진다 |

보통은 `default_batch_fetch_size`를 전역으로 두고, 응답 속도가 특히 중요한 곳에만 fetch join을 더한다.

## 자주 깨지는 곳

- 쿼리 수를 세 보지 않고 코드를 쓰면, 개발 환경은 데이터가 적어서 N+1이 안 보인다.
- 컬렉션 fetch join에 페이징을 붙이면, 전체 데이터가 메모리에 올라간다.
- `List` 타입 컬렉션 둘 이상을 동시에 fetch join하면, `MultipleBagFetchException`이 난다. 하나를 `Set`으로 바꾸면 예외는 사라지지만, 컬렉션 둘을 같이 fetch join하면 DB에서 행이 곱으로 불어나는 건 그대로다. 그래서 하나만 fetch join하고 나머지는 `@BatchSize`로 읽는다.
- `@BatchSize` 없이 모든 곳을 fetch join으로 막으면, 페이징이 필요한 곳에서 막힌다.
- `spring.jpa.show-sql=true` 로그만 보고 있으면, 로그가 흘러가 버려서 실제 쿼리 수를 세지 못한다.

## 한 번에 설명하기

> N+1은 목록을 조회한 뒤 건마다 연관 데이터를 따로 쿼리해서, 쿼리가 N+1번 나가는 문제입니다. 저는 목록 API에서 쿼리 수가 건수만큼 늘어나는지를 보고 찾습니다.
>
> 기본 해결은 fetch join으로 연관 데이터를 한 번에 가져오는 건데, 컬렉션 fetch join은 페이징과 같이 쓸 수 없습니다.
>
> 그래서 `default_batch_fetch_size`를 전역으로 걸어 IN 절로 묶어 두고, 응답 속도가 특히 중요한 곳에만 fetch join을 더합니다.

## 꼬리 질문

> [!question]- EAGER로 설정하면 N+1이 해결되는가?
> 아닙니다. EAGER는 연관 Entity를 바로 불러올 뿐이라, `findAll()` 같은 JPQL에서는 주문 목록을 먼저 가져온 뒤 회원을 건마다 따로 조회해서 여전히 N+1이 납니다.

> [!question]- `MultipleBagFetchException`이 발생하는 이유는?
> Hibernate가 `List` 타입 컬렉션(bag) 두 개 이상을 동시에 fetch join하는 걸 막아서입니다. 하나를 `Set`으로 바꾸면 예외는 사라지지만 카테시안 곱으로 행이 불어나는 건 그대로라, 보통은 하나만 fetch join하고 나머지는 `@BatchSize`로 불러옵니다.

> [!question]- `default_batch_fetch_size`의 적정 값은?
> 보통 100~1000 사이로 둡니다. DB가 IN 절에 받아 주는 개수 제한과 메모리 사용량을 보고 정합니다.

> [!question]- N+1을 어떻게 발견하는가?
> `logging.level.org.hibernate.SQL=debug`로 실제로 나가는 SQL을 찍고, `spring.jpa.properties.hibernate.format_sql=true`로 보기 좋게 정리해서 봅니다. 목록 API에서 쿼리 수가 데이터 건수만큼 늘어나면 N+1을 의심합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>N+1 문제를 발견하는 가장 현실적인 방법은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="SQL 로그, p6spy, datasource-proxy, APM 등으로 실제 쿼리 수와 패턴을 확인한다." aria-pressed="false">A. 실제 발생 SQL과 쿼리 수를 관찰한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="코드 라인 수만으로 N+1 여부를 확정할 수 없다." aria-pressed="false">B. Repository 메서드 이름 길이를 본다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Entity 개수만으로 쿼리 발생 패턴을 알 수는 없다." aria-pressed="false">C. Entity 클래스 파일 개수만 센다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>컬렉션 fetch join에 pagination을 그대로 적용하면 메모리 페이징이나 데이터 중복 문제가 생길 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="to-many fetch join은 row가 늘어나므로 페이징과 함께 쓸 때 특히 주의해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="fetch join과 pagination 조합은 항상 안전하지 않다. 조회 구조를 분리할 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>MultipleBagFetchException이 발생하는 대표 원인은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Hibernate에서 둘 이상의 bag 컬렉션을 동시에 fetch join하면 row 조합을 안전하게 매핑하기 어렵기 때문이다." aria-pressed="false">A. 여러 bag 컬렉션을 동시에 fetch join했기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="단일 ManyToOne 조회 자체가 원인은 아니다." aria-pressed="false">B. ManyToOne 하나를 LAZY로 둬서 발생한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="컬럼명이 길어서 발생하는 예외가 아니다." aria-pressed="false">C. DB 컬럼명이 너무 길어서 발생한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Fetching](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#fetching)
- [Spring Data JPA: Entity Graphs](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[lazy-and-eager-loading]]
- [[association-mapping]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/database/pagination-and-bulk-query|pagination-and-bulk-query]]