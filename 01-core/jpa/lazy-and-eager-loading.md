---
title: "지연 로딩과 즉시 로딩의 차이"
description: JPA 지연 로딩과 즉시 로딩의 실무 선택 기준
---

# 지연 로딩과 즉시 로딩의 차이

## 한 줄 정의

지연 로딩(LAZY)은 연관 Entity를 실제 사용할 때 조회하고, 즉시 로딩(EAGER)은 Entity를 조회할 때 연관 Entity를 함께 조회한다.

## 실무에서 왜 중요한가

로딩 전략을 잘못 선택하면 다음 문제가 생긴다.

- EAGER로 설정해서 사용하지 않는 연관 Entity까지 매번 JOIN한다.
- LAZY로 설정했는데 트랜잭션 밖에서 접근해서 `LazyInitializationException`이 발생한다.
- 반복문 안에서 지연 로딩이 실행되면서 N+1 문제가 발생한다.
- 프록시 객체의 동작을 모르고 `instanceof`나 `==` 비교에서 예상과 다른 결과가 나온다.

## 즉시 로딩 (EAGER)

```java
@ManyToOne(fetch = FetchType.EAGER)
@JoinColumn(name = "user_id")
private User user;
```

Entity를 조회하면 연관된 User도 함께 조회된다.

```sql
SELECT o.*, u.* FROM orders o LEFT JOIN users u ON o.user_id = u.id WHERE o.id = ?
```

문제점: 해당 API에서 User 정보가 필요 없어도 항상 JOIN이 실행된다.

## 지연 로딩 (LAZY)

```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "user_id")
private User user;
```

Entity를 조회할 때 연관 Entity 자리에 프록시 객체가 들어간다. 실제로 `order.getUser().getName()`처럼 접근할 때 SELECT가 실행된다.

```sql
-- Order 조회 시
SELECT o.* FROM orders o WHERE o.id = ?

-- user.getName() 호출 시
SELECT u.* FROM users u WHERE u.id = ?
```

## 프록시 동작

지연 로딩은 프록시를 통해 구현된다.

```java
Order order = orderRepository.findById(1L).orElseThrow();
User user = order.getUser(); // 프록시 객체 (아직 SELECT 안 함)
String name = user.getName(); // 이 시점에 SELECT 실행
```

프록시는 실제 Entity를 상속한 가짜 객체다.

| 특성 | 동작 |
|---|---|
| `getId()` | 이미 가지고 있으므로 쿼리 없음 |
| `getName()` 등 다른 필드 | 첫 접근 시 SELECT 실행 |
| `getClass()` | 프록시 클래스 반환 (`User$HibernateProxy`) |
| `instanceof User` | true (상속이므로) |

## LazyInitializationException

트랜잭션(영속성 컨텍스트) 밖에서 지연 로딩을 시도하면 발생한다.

```java
// Controller에서 직접 Entity를 반환하는 경우
public User getUser(Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return user;
    // JSON 직렬화 시 user.getOrders()에 접근 → 트랜잭션 종료 후라 예외 발생
}
```

해결 방법:

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

## 실무 원칙

| 원칙 | 이유 |
|---|---|
| 모든 연관관계를 LAZY로 설정 | 불필요한 JOIN 방지 |
| 필요한 데이터만 fetch join으로 조회 | 사용하는 데이터만 로딩 |
| Entity를 API 응답으로 직접 반환하지 않음 | LazyInitializationException 방지 |
| `@Transactional(readOnly = true)` 사용 | 읽기 전용 트랜잭션으로 성능 최적화 |

## 자주 나는 실수

- `@ManyToOne`의 기본 fetch가 EAGER인 것을 모르고 방치한다.
- 트랜잭션 밖에서 지연 로딩을 시도해서 예외가 발생한다.
- `open-in-view`를 true로 두고 Controller에서 지연 로딩에 의존한다.
- 반복문 안에서 지연 로딩이 호출되어 N+1 문제가 발생한다.
- 프록시 객체의 `getClass()`가 실제 클래스와 다른 것을 모르고 비교한다.

## 핵심 요약

실무에서는 모든 연관관계를 LAZY로 설정하고, 필요한 데이터만 fetch join으로 조회하는 것이 원칙입니다.

EAGER는 사용하지 않는 데이터까지 항상 JOIN하므로 성능 문제를 일으킵니다.
LAZY는 실제 접근 시점에 프록시를 통해 쿼리를 실행하지만, 트랜잭션 밖에서 접근하면 `LazyInitializationException`이 발생합니다.

Entity를 API 응답으로 직접 반환하지 않고, 서비스 계층에서 DTO로 변환하면 이 문제를 근본적으로 방지할 수 있습니다.

## 꼬리 질문

> [!question]- `open-in-view`란 무엇이고 왜 false로 설정하는가?
> 영속성 컨텍스트를 Controller까지 열어두는 설정입니다. View에서 지연 로딩이 가능하지만, DB 커넥션을 오래 점유해서 커넥션 풀 고갈 위험이 있습니다.

> [!question]- 프록시 객체와 실제 Entity를 어떻게 구분하는가?
> `Hibernate.isInitialized(entity)`로 초기화 여부를 확인할 수 있습니다. `getClass()`는 프록시 클래스를 반환하므로 타입 비교에는 `instanceof`를 사용해야 합니다.

> [!question]- `@Transactional(readOnly = true)`의 효과는?
> 영속성 컨텍스트의 변경 감지를 생략해서 flush 비용을 줄입니다. DB에 따라 읽기 전용 트랜잭션으로 최적화될 수 있습니다.

> [!question]- 지연 로딩과 N+1의 관계는?
> 지연 로딩 자체는 문제가 아닙니다. 반복문 안에서 N개의 Entity가 각각 지연 로딩을 실행하면 N+1 쿼리가 발생하는 것이 문제입니다. fetch join으로 해결합니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[n-plus-one-and-fetch-join]]
- [[association-mapping]]
- [[01-core/spring/transaction-integration|transaction-integration]]