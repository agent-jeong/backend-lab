---
title: N Plus One And Fetch Join
description: JPA N+1 문제의 원인과 fetch join 기반 해결 전략
---

# N Plus One And Fetch Join

## 한 줄 정의

N+1 문제는 1번의 쿼리로 N건의 데이터를 가져온 뒤, 각 건의 연관 데이터를 조회하기 위해 N번의 추가 쿼리가 발생하는 현상이다.

## 실무에서 왜 중요한가

N+1은 JPA를 사용하는 실무에서 가장 자주 발생하는 성능 문제다.

- 목록 API 응답 시간이 데이터가 늘수록 비례해서 느려진다.
- 단순 목록 조회인데 수십~수백 개의 SELECT가 실행된다.
- 개발 환경에서는 데이터가 적어서 문제를 모르고, 운영에서 터진다.
- DB 커넥션 점유 시간이 길어져 커넥션 풀이 고갈된다.

## N+1이 발생하는 과정

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

주문이 100건이면 101번의 쿼리가 실행된다.

## 해결 방법 1: Fetch Join

```java
@Query("SELECT o FROM Order o JOIN FETCH o.user")
List<Order> findAllWithUser();
```

```sql
SELECT o.*, u.* FROM orders o INNER JOIN users u ON o.user_id = u.id
```

한 번의 쿼리로 Order와 User를 함께 가져온다.

### 컬렉션 fetch join

`@OneToMany` 관계에서 fetch join하면 데이터가 중복될 수 있다.

```java
@Query("SELECT DISTINCT u FROM User u JOIN FETCH u.orders")
List<User> findAllWithOrders();
```

`DISTINCT`를 사용해서 중복을 제거한다. Hibernate 6에서는 JPQL에 `DISTINCT`를 쓰면 SQL에는 DISTINCT를 넣지 않고 애플리케이션 레벨에서 중복 Entity를 제거한다. Hibernate 5에서는 SQL에도 DISTINCT가 포함된다.

### 컬렉션 fetch join과 페이징

**컬렉션 fetch join과 페이징은 함께 사용할 수 없다.**

```java
// 위험: 메모리에서 페이징 처리 (모든 데이터를 먼저 가져옴)
@Query("SELECT u FROM User u JOIN FETCH u.orders")
Page<User> findAllWithOrders(Pageable pageable);
```

Hibernate가 경고 로그를 남기며 전체 데이터를 메모리에 올린 후 페이징한다.

해결 방법: `@BatchSize`를 사용한다.

## 해결 방법 2: @BatchSize

```java
@Entity
public class User {

    @BatchSize(size = 100)
    @OneToMany(mappedBy = "user")
    private List<Order> orders = new ArrayList<>();
}
```

또는 전역 설정:

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

N번의 쿼리가 `ceil(N / batchSize)`번으로 줄어든다. 컬렉션 fetch join과 달리 페이징과 함께 사용할 수 있어서, 실무에서는 `default_batch_fetch_size`를 전역 설정하고 페이징이 필요한 곳에서 활용하는 것이 일반적이다.

## 해결 방법 3: EntityGraph

```java
@EntityGraph(attributePaths = {"user"})
List<Order> findAll();
```

JPQL 없이 fetch join과 같은 효과를 낸다. 간단한 경우에 유용하지만, 복잡한 조건에서는 JPQL fetch join이 더 명확하다.

## 해결 방법 비교

| 방법 | 장점 | 단점 |
|---|---|---|
| Fetch Join | 한 번의 쿼리로 해결 | 컬렉션 페이징 불가, 다중 컬렉션 fetch 불가 |
| `@BatchSize` | 페이징 가능, 설정 간단 | 쿼리가 여러 번 나갈 수 있음 |
| `@EntityGraph` | 어노테이션만으로 간단히 적용 | 복잡한 조건에서 한계 |
| DTO 직접 조회 | 필요한 컬럼만 조회, 성능 최적화 | 코드가 복잡해짐 |

## 자주 나는 실수

- N+1이 발생하는지 확인하지 않고 코드를 작성한다.
- 컬렉션 fetch join과 페이징을 함께 사용한다.
- 여러 컬렉션을 동시에 fetch join해서 `MultipleBagFetchException`이 발생한다.
- `@BatchSize`를 설정하지 않고 모든 곳에 fetch join을 사용한다.
- 개발 환경에서 데이터가 적어 N+1을 발견하지 못한다.
- `spring.jpa.show-sql=true`만 보고 실제 쿼리 수를 파악하지 못한다.

## 핵심 요약

N+1은 목록 조회 시 각 건의 연관 데이터를 개별 쿼리로 조회해서 쿼리 수가 N+1이 되는 문제입니다.

가장 기본적인 해결 방법은 fetch join으로 한 번의 쿼리에 연관 데이터를 함께 가져오는 것입니다.
단, 컬렉션 fetch join은 페이징과 함께 사용할 수 없습니다.

페이징이 필요하면 `@BatchSize`(또는 `default_batch_fetch_size`)를 설정해서 IN 절로 묶어 조회합니다.
실무에서는 `default_batch_fetch_size`를 전역으로 설정하고, 성능이 중요한 곳에서 fetch join을 추가로 적용하는 조합이 일반적입니다.

## 꼬리 질문

> [!question]- EAGER로 설정하면 N+1이 해결되는가?
> 아닙니다. EAGER는 연관 Entity를 즉시 로딩할 뿐, `findAll()` 같은 JPQL에서는 여전히 N+1이 발생합니다.

> [!question]- `MultipleBagFetchException`이 발생하는 이유는?
> 두 개 이상의 `List` 타입 컬렉션을 동시에 fetch join하면 카테시안 곱이 발생합니다. 하나를 `Set`으로 바꾸거나 `@BatchSize`로 해결합니다.

> [!question]- `default_batch_fetch_size`의 적정 값은?
> 일반적으로 100~1000 사이로 설정합니다. DB의 IN 절 제한과 메모리 사용량을 고려해서 정합니다.

> [!question]- N+1을 어떻게 발견하는가?
> `spring.jpa.properties.hibernate.format_sql=true`와 로그 레벨 설정으로 실행되는 SQL을 확인합니다. 목록 API에서 쿼리 수가 데이터 건수에 비례하면 N+1을 의심합니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[lazy-and-eager-loading]]
- [[association-mapping]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/database/pagination-and-bulk-query|pagination-and-bulk-query]]