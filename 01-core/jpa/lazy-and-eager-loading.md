---
title: "지연 로딩과 즉시 로딩의 차이"
description: 연관 Entity를 언제 불러오는지, 왜 전부 LAZY로 두는지
tags: [concept, jpa]
---

# 지연 로딩과 즉시 로딩의 차이

지연 로딩(LAZY)은 연관 Entity를 실제로 쓰는 순간에 조회하고, 즉시 로딩(EAGER)은 Entity를 조회할 때 연관 Entity까지 한꺼번에 조회한다.

주문을 EAGER로 두면 회원 정보가 필요 없는 화면에서도 매번 회원 테이블을 JOIN한다. LAZY는 트랜잭션 밖에서 건드리면 예외가 나고, 반복문 안에서 건드리면 N+1을 만든다. 그래서 실무에서는 전부 LAZY로 두고, 필요한 데이터만 fetch join으로 가져온다.

## 즉시 로딩 (EAGER)

```java
@ManyToOne(fetch = FetchType.EAGER)
@JoinColumn(name = "user_id")
private User user;
```

Order를 조회하면 연결된 User도 같이 조회된다.

```sql
SELECT o.*, u.* FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.id = ?
```

그 API에서 User 정보가 필요 없어도 JOIN은 늘 실행된다.

## 지연 로딩 (LAZY)

```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "user_id")
private User user;
```

조회하면 연관 Entity 자리에 프록시 객체가 대신 들어간다. `order.getUser().getName()`처럼 실제로 값을 꺼낼 때 SELECT가 나간다.

```sql
-- Order 조회 시
SELECT o.* FROM orders o WHERE o.id = ?

-- user.getName() 호출 시
SELECT u.* FROM users u WHERE u.id = ?
```

## 프록시

지연 로딩은 프록시로 동작한다.

```java
Order order = orderRepository.findById(1L).orElseThrow();
User user = order.getUser(); // 프록시 객체 (아직 SELECT 안 함)
String name = user.getName(); // 이 시점에 SELECT 실행
```

프록시는 실제 Entity를 상속한 가짜 객체다. 그래서 `getClass()`나 `==`로 비교하면 생각과 다른 결과가 나온다.

| 호출 | 동작 |
|---|---|
| `getId()` | id는 이미 들고 있어서 쿼리가 안 나간다 |
| `getName()` 등 다른 필드 | 처음 꺼낼 때 SELECT가 나간다 |
| `getClass()` | 프록시 클래스가 나온다 (`User$HibernateProxy`) |
| `instanceof User` | true (상속했으니까) |

## LazyInitializationException

트랜잭션(영속성 컨텍스트)이 끝난 뒤에 지연 로딩을 하려고 하면 난다.

```java
// Controller에서 직접 Entity를 반환하는 경우
public User getUser(Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return user;
    // JSON 직렬화 시 user.getOrders()에 접근 → 트랜잭션 종료 후라 예외 발생
}
```

트랜잭션이 끝나기 전에 필요한 데이터를 다 꺼내 두면 된다. 방법은 두 가지다.

```java
// 1. 서비스 계층에서 DTO로 변환 (권장)
@Transactional(readOnly = true)
public UserResponse getUser(Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return UserResponse.from(user);
}

// 2. 필요한 연관 데이터를 fetch join으로 미리 로딩
@Query("SELECT u FROM User u JOIN FETCH u.orders WHERE u.id = :id")
Optional<User> findByIdWithOrders(@Param("id") Long id);
```

## 실무에서 지키는 것

| 지키는 것 | 이유 |
|---|---|
| 모든 연관관계를 LAZY로 둔다 | 필요 없는 JOIN을 막는다 |
| 필요한 데이터만 fetch join으로 조회한다 | 쓰는 데이터만 불러온다 |
| Entity를 API 응답으로 그대로 내보내지 않는다 | LazyInitializationException을 막는다 |
| 조회에는 `@Transactional(readOnly = true)`를 쓴다 | 읽기 전용 트랜잭션이라 변경 감지 같은 일을 덜 한다 |

## 자주 깨지는 곳

- `@ManyToOne` 기본값 EAGER를 그대로 두면, 안 쓰는 연관 Entity까지 매번 JOIN한다.
- 트랜잭션 밖에서 지연 로딩을 하면, `LazyInitializationException`이 난다.
- `open-in-view`를 true로 두고 Controller에서 지연 로딩에 기대면, DB 커넥션을 요청이 끝날 때까지 쥐고 있다.
- 반복문 안에서 지연 로딩을 부르면, N+1이 생긴다.
- 프록시의 `getClass()`로 타입을 비교하면, 프록시 클래스가 나와서 실제 클래스와 다르다고 판단한다.

## 한 번에 설명하기

> 실무에서는 모든 연관관계를 LAZY로 두고, 필요한 데이터만 fetch join으로 조회합니다.
>
> EAGER는 안 쓰는 데이터까지 늘 JOIN해서 느려집니다. LAZY는 프록시를 넣어 뒀다가 실제로 꺼낼 때 쿼리를 날리는데, 트랜잭션이 끝난 뒤에 꺼내면 `LazyInitializationException`이 납니다.
>
> 그래서 Entity를 API 응답으로 그대로 내보내지 않고, 서비스 계층 트랜잭션 안에서 DTO로 바꿔서 이 예외가 날 자리를 아예 없앱니다.

## 꼬리 질문

> [!question]- `open-in-view`란 무엇이고 왜 false로 설정하는가?
> 영속성 컨텍스트를 Controller와 View까지 열어 두는 설정입니다. View에서도 지연 로딩이 되긴 하지만, DB 커넥션을 오래 쥐고 있어서 트래픽이 몰리면 커넥션 풀이 바닥날 수 있습니다.

> [!question]- 프록시 객체와 실제 Entity를 어떻게 구분하는가?
> 실제 값을 불러왔는지는 `Hibernate.isInitialized(entity)`로 확인합니다. `getClass()`는 프록시 클래스를 돌려주니까, 타입을 비교할 때는 `instanceof`를 씁니다.

> [!question]- `@Transactional(readOnly = true)`의 효과는?
> 영속성 컨텍스트가 변경 감지를 건너뛰어서 flush에 드는 비용이 줄어듭니다. DB에 따라서는 읽기 전용 트랜잭션으로 더 가볍게 처리하기도 합니다.

> [!question]- 지연 로딩과 N+1의 관계는?
> 지연 로딩 자체는 문제가 아닙니다. 반복문 안에서 Entity N개가 각자 지연 로딩을 하면 쿼리가 N+1번 나가는 게 문제입니다. 이건 fetch join으로 풉니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>실무에서 연관관계 기본 전략을 LAZY로 두는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="필요하지 않은 연관 객체까지 즉시 조회하면 예측하기 어려운 쿼리와 성능 문제가 생길 수 있기 때문이다." aria-pressed="false">A. 필요한 시점에 명시적으로 조회 전략을 선택하기 위해서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="LAZY가 N+1을 자동으로 없애지는 않는다." aria-pressed="false">B. LAZY만 쓰면 N+1이 절대 발생하지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="LAZY는 트랜잭션을 제거하지 않는다." aria-pressed="false">C. 트랜잭션 없이도 모든 연관 객체를 안전하게 조회하게 해준다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>EAGER로 바꾸면 N+1 문제가 항상 해결된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="EAGER도 JPQL 조회 방식에 따라 추가 쿼리가 발생할 수 있고, 불필요한 조회까지 강제할 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="N+1은 fetch join, batch size, entity graph 등 조회 전략으로 해결해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>LazyInitializationException이 발생하는 대표 원인은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="영속성 컨텍스트가 닫힌 뒤 지연 로딩 프록시를 초기화하려고 하기 때문이다." aria-pressed="false">A. 트랜잭션/영속성 컨텍스트 밖에서 lazy 연관을 접근했기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="프록시 초기화 문제와 컴파일 여부는 다르다." aria-pressed="false">B. Entity 클래스가 컴파일되지 않았기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="기본 생성자만으로 해결되는 문제가 아니다." aria-pressed="false">C. DTO에 기본 생성자가 없기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Fetching](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#fetching)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[n-plus-one-and-fetch-join]]
- [[association-mapping]]
- [[01-core/spring/transaction-integration|transaction-integration]]