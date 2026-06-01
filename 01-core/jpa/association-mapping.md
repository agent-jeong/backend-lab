---
title: Association Mapping
description: JPA 연관관계 매핑의 실무 설계와 주의점
---

# Association Mapping

## 한 줄 정의

연관관계 매핑은 객체의 참조와 테이블의 외래 키를 JPA가 자동으로 변환할 수 있도록 설정하는 것이다.

## 실무에서 왜 중요한가

연관관계 매핑을 잘못하면 다음 문제가 생긴다.

- 양방향 매핑에서 연관관계 주인을 잘못 설정해서 외래 키가 업데이트되지 않는다.
- 양방향 참조를 모두 설정하지 않아서 영속성 컨텍스트에서 불일치가 생긴다.
- 무분별한 양방향 매핑으로 순환 참조가 발생한다.
- `CascadeType.ALL`을 무분별하게 사용해서 의도하지 않은 삭제가 일어난다.
- 연관관계를 모두 즉시 로딩으로 설정해서 불필요한 JOIN이 발생한다.

## 연관관계 종류

| 관계 | 어노테이션 | 실무 빈도 |
|---|---|---|
| 다대일 | `@ManyToOne` | 가장 많이 사용 |
| 일대다 | `@OneToMany` | 양방향 시 사용 |
| 일대일 | `@OneToOne` | 주의 필요 (지연 로딩 제약) |
| 다대다 | `@ManyToMany` | 실무에서 거의 사용하지 않음 |

## 다대일 (ManyToOne) - 기본

외래 키를 가진 쪽이 연관관계의 주인이다. 실무에서 가장 많이 쓰는 매핑이다.

```java
@Entity
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
}
```

`@ManyToOne`의 기본 fetch 전략은 `EAGER`다. 반드시 `LAZY`로 설정해야 한다.

## 양방향 매핑

```java
@Entity
public class User {

    @OneToMany(mappedBy = "user")
    private List<Order> orders = new ArrayList<>();
}

@Entity
public class Order {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
}
```

### 연관관계 주인

- `mappedBy`가 있는 쪽은 읽기 전용이다. 외래 키를 관리하지 않는다.
- 외래 키가 있는 테이블(`Order`)의 `@ManyToOne` 쪽이 주인이다.
- 주인이 아닌 쪽에서 값을 변경해도 DB에 반영되지 않는다.

```java
// 잘못된 예: 주인이 아닌 쪽에서만 설정
user.getOrders().add(order);
// → DB에 외래 키 반영되지 않음

// 올바른 예: 주인 쪽에서 설정
order.setUser(user);
// → DB에 외래 키 반영됨
```

양방향에서는 양쪽 모두 설정하는 편의 메서드를 만드는 것이 안전하다.

```java
public void assignUser(User user) {
    this.user = user;
    user.getOrders().add(this);
}
```

## 양방향 vs 단방향

| 기준 | 단방향 | 양방향 |
|---|---|---|
| 복잡도 | 낮음 | 높음 (순환 참조 위험) |
| 외래 키 관리 | 명확 | 주인 개념 이해 필요 |
| 역방향 탐색 | 별도 쿼리 필요 | `user.getOrders()` 가능 |

**원칙**: 단방향으로 시작하고, 역방향 탐색이 꼭 필요할 때만 양방향을 추가한다.

## @OneToOne 주의점

`@OneToOne`에서 외래 키가 없는 쪽(주인이 아닌 쪽)은 LAZY로 설정해도 즉시 로딩으로 동작할 수 있다.

```java
@Entity
public class User {

    @OneToOne(mappedBy = "user", fetch = FetchType.LAZY)
    private UserProfile profile;
    // → LAZY로 설정해도 실제로는 EAGER로 동작할 수 있음
}
```

JPA는 프록시 생성 시 해당 연관 Entity가 존재하는지 알 수 없어서 즉시 로딩으로 대체한다. 외래 키를 가진 쪽에서만 지연 로딩이 정상 동작한다.

## @ManyToMany를 쓰지 않는 이유

중간 테이블에 추가 컬럼(생성일, 상태 등)이 필요한 경우가 대부분이므로, 중간 Entity를 직접 만드는 것이 안전하다.

```java
// 대신 중간 Entity를 만든다
@Entity
public class UserRole {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "role_id")
    private Role role;

    private LocalDateTime assignedAt;
}
```

## Cascade 주의점

```java
@OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItem> items = new ArrayList<>();
```

| 옵션 | 의미 | 주의점 |
|---|---|---|
| `CascadeType.PERSIST` | 부모 저장 시 자식도 저장 | 생명주기가 같을 때만 |
| `CascadeType.REMOVE` | 부모 삭제 시 자식도 삭제 | 다른 곳에서 참조하면 위험 |
| `CascadeType.ALL` | 모든 작업 전파 | 생명주기가 완전히 같을 때만 |
| `orphanRemoval = true` | 부모 컬렉션에서 제거하면 자식 삭제 | 실수로 제거 시 데이터 삭제됨 |

**원칙**: 자식 Entity가 부모 없이 존재할 수 없을 때만 Cascade를 사용한다.

## 자주 나는 실수

- `@ManyToOne`의 기본 fetch가 `EAGER`인 것을 모르고 사용한다.
- 양방향에서 주인이 아닌 쪽만 값을 설정한다.
- 단방향으로 충분한데 양방향을 무조건 추가한다.
- `CascadeType.ALL`을 생명주기가 다른 Entity에 사용한다.
- `@OneToOne`에서 주인이 아닌 쪽의 지연 로딩이 안 되는 것을 모른다.
- `@ManyToMany`를 사용해서 중간 테이블 컬럼 추가가 불가능해진다.

## 핵심 요약

연관관계 매핑에서 가장 많이 쓰는 것은 `@ManyToOne`이며, 반드시 `fetch = FetchType.LAZY`로 설정해야 합니다.

양방향 매핑에서는 외래 키를 가진 쪽이 연관관계의 주인이고, 주인이 아닌 쪽은 읽기 전용입니다.
단방향으로 시작하고 꼭 필요할 때만 양방향을 추가하는 것이 원칙입니다.

`@OneToOne`은 주인이 아닌 쪽에서 지연 로딩이 안 되는 제약이 있고, `@ManyToMany`는 중간 Entity를 직접 만드는 것이 안전합니다.
Cascade는 생명주기가 완전히 같을 때만 사용해야 합니다.

## 꼬리 질문

> [!question]- 연관관계의 주인이란 무엇인가?
> 외래 키를 실제로 관리하는 쪽입니다. `mappedBy`가 없는 쪽이 주인이며, 주인만이 외래 키 값을 변경할 수 있습니다.

> [!question]- `@ManyToOne`의 기본 fetch 전략이 EAGER인 이유는?
> JPA 스펙에서 `*ToOne` 관계는 기본 EAGER, `*ToMany` 관계는 기본 LAZY입니다. 하지만 실무에서는 N+1 방지를 위해 모든 연관관계를 LAZY로 설정하는 것이 원칙입니다.

> [!question]- `@OneToOne`에서 지연 로딩이 안 되는 경우는?
> 외래 키가 없는 쪽(mappedBy가 있는 쪽)에서 지연 로딩이 동작하지 않습니다. JPA가 프록시를 만들려면 값의 존재 여부를 알아야 하는데, 외래 키가 없으면 알 수 없기 때문입니다.

> [!question]- Cascade를 잘못 사용하면 어떤 문제가 생기는가?
> `CascadeType.REMOVE`가 걸린 부모를 삭제하면 자식도 함께 삭제됩니다. 다른 곳에서 참조하는 자식이면 데이터 정합성이 깨집니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[entity-table-mapping]]
- [[lazy-and-eager-loading]]
- [[n-plus-one-and-fetch-join]]