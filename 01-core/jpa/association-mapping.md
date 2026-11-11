---
title: "연관관계 매핑 전략"
description: 연관관계를 단방향 LAZY로 시작하는 이유와, 양방향과 Cascade에서 실수하는 곳
tags: [concept, jpa]
---

# 연관관계 매핑 전략

연관관계 매핑은 `order.getUser()` 같은 객체 참조와 `orders.user_id` 같은 외래 키를 JPA가 서로 바꿀 수 있게 알려 주는 설정이다.

사고는 매핑 문법보다 기본값과 주인 규칙에서 난다. `@ManyToOne`은 기본이 즉시 로딩이라 주문을 조회할 때마다 회원까지 따라온다. 양방향에서 주인이 아닌 쪽만 바꾸면 외래 키가 저장되지 않는다. 그래서 단방향 `@ManyToOne(LAZY)`로 시작하고, 필요할 때만 늘린다.

## 연관관계 종류

| 관계 | 어노테이션 | 실무에서 |
|---|---|---|
| 다대일 | `@ManyToOne` | 가장 많이 쓴다 |
| 일대다 | `@OneToMany` | 양방향으로 만들 때 쓴다 |
| 일대일 | `@OneToOne` | 조심해서 쓴다 (지연 로딩이 안 될 때가 있다) |
| 다대다 | `@ManyToMany` | 거의 안 쓴다 |

## 다대일 (ManyToOne)

외래 키를 가진 쪽이 연관관계의 주인이다. 실무에서 가장 많이 쓰는 관계다.

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

`@ManyToOne`의 기본 fetch 전략은 `EAGER`다. 늘 `LAZY`로 바꿔 둔다.

## 양방향 매핑과 연관관계 주인

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

- 외래 키가 있는 테이블(`Order`)의 `@ManyToOne` 쪽이 주인이다.
- `mappedBy`가 있는 쪽은 읽기만 하고 외래 키는 건드리지 않는다.
- 그래서 주인이 아닌 쪽에서 값을 바꿔도 DB에는 안 들어간다.

```java
// 잘못된 예: 주인이 아닌 쪽에서만 설정
user.getOrders().add(order);
// → DB에 외래 키 반영되지 않음

// 올바른 예: 주인 쪽에서 설정
order.setUser(user);
// → DB에 외래 키 반영됨
```

주인 쪽만 설정하면 DB는 맞지만, 같은 영속성 컨텍스트 안의 `user.getOrders()`에는 아직 안 보인다. 그래서 양쪽을 한 번에 설정하는 메서드를 따로 둔다.

```java
public void assignUser(User user) {
    this.user = user;
    user.getOrders().add(this);
}
```

## 단방향으로 시작한다

| 기준 | 단방향 | 양방향 |
|---|---|---|
| 복잡도 | 낮다 | 높다 (순환 참조가 생기기 쉽다) |
| 외래 키 관리 | 누가 관리하는지 분명하다 | 주인 규칙을 알아야 한다 |
| 반대 방향으로 찾기 | 쿼리를 따로 써야 한다 | `user.getOrders()`로 된다 |

단방향으로 시작하고, 반대 방향으로 따라가야 할 일이 꼭 생겼을 때만 양방향을 더한다.

## @OneToOne의 지연 로딩 제약

`@OneToOne`에서 외래 키가 없는 쪽(주인이 아닌 쪽)은 LAZY로 설정해도 즉시 로딩될 수 있다.

```java
@Entity
public class User {

    @OneToOne(mappedBy = "user", fetch = FetchType.LAZY)
    private UserProfile profile;
    // → LAZY로 설정해도 실제로는 EAGER로 동작할 수 있음
}
```

프록시를 만들려면 먼저 연관 Entity가 있는지 없는지를 알아야 한다. 외래 키가 없는 쪽은 그걸 알 방법이 없어서 Hibernate가 추가 쿼리로 바로 조회해 버린다. JPA 스펙에서 LAZY는 힌트일 뿐이라 이건 구현체의 동작이다. Hibernate에서 이쪽까지 지연 로딩하려면 bytecode enhancement를 켜야 하고, 그게 없으면 지연 로딩은 외래 키를 가진 쪽에서만 제대로 된다.

## @ManyToMany 대신 중간 Entity

중간 테이블에는 거의 언제나 생성일, 상태 같은 컬럼이 나중에 붙는다. `@ManyToMany`로는 이런 컬럼을 넣을 수 없으니 중간 Entity를 직접 만든다.

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

## Cascade

```java
@OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
private List<OrderItem> items = new ArrayList<>();
```

| 옵션 | 뜻 | 조심할 점 |
|---|---|---|
| `CascadeType.PERSIST` | 부모를 저장하면 자식도 저장 | 생명주기가 같을 때만 |
| `CascadeType.REMOVE` | 부모를 지우면 자식도 삭제 | 다른 곳에서 그 자식을 쓰고 있으면 위험 |
| `CascadeType.ALL` | 모든 작업을 자식에게도 | 생명주기가 완전히 같을 때만 |
| `orphanRemoval = true` | 부모 컬렉션에서 빼면 자식 삭제 | 실수로 빼도 데이터가 지워진다 |

Cascade는 주문 항목처럼 자식이 부모 없이는 존재할 수 없을 때만 쓴다.

## 자주 깨지는 곳

- `@ManyToOne`을 기본값 `EAGER`로 두면, 조회할 때마다 필요 없는 JOIN이 붙는다.
- 양방향에서 주인이 아닌 쪽만 설정하면, 외래 키가 저장되지 않는다. 반대로 주인만 설정하면 영속성 컨텍스트 안에서 양쪽 값이 어긋난다.
- 단방향으로 충분한데 양방향을 붙이면, 복잡해지기만 하고 순환 참조가 생긴다.
- 생명주기가 다른 Entity에 `CascadeType.ALL`을 걸면, 부모를 지울 때 다른 곳에서 쓰던 자식까지 지워진다.
- `@OneToOne` 주인이 아닌 쪽에 LAZY를 걸고 안심하면, bytecode enhancement가 없는 Hibernate에서는 실제로 즉시 로딩된다.
- `@ManyToMany`를 쓰면, 나중에 중간 테이블에 컬럼을 추가할 수 없다.

## 한 번에 설명하기

> 연관관계는 `@ManyToOne`을 가장 많이 쓰는데, 기본이 EAGER라서 늘 `LAZY`로 바꿔 둡니다.
>
> 양방향에서는 외래 키를 가진 쪽이 주인이고 반대쪽은 읽기만 합니다. 그래서 저는 단방향으로 시작하고, 반대 방향으로 따라갈 일이 꼭 생기면 그때 양방향을 더합니다.
>
> `@OneToOne`은 Hibernate에서 bytecode enhancement 없이는 주인이 아닌 쪽에서 지연 로딩이 안 되고, `@ManyToMany`는 중간 Entity로 풉니다. Cascade는 생명주기가 완전히 같을 때만 겁니다.

## 꼬리 질문

> [!question]- 연관관계의 주인이란 무엇인가?
> 외래 키를 실제로 관리하는 쪽입니다. `mappedBy`가 없는 쪽이 주인이고, 외래 키 값은 주인 쪽 필드를 바꿀 때만 바뀝니다.

> [!question]- `@ManyToOne`의 기본 fetch 전략이 EAGER인 이유는?
> JPA 스펙이 그렇게 정했습니다. `*ToOne` 관계는 기본이 EAGER고, `*ToMany` 관계는 기본이 LAZY입니다. 그래도 실무에서는 필요 없는 조회를 막고 조회 시점을 직접 정하려고 모든 연관관계를 LAZY로 둡니다.

> [!question]- `@OneToOne`에서 지연 로딩이 안 되는 경우는?
> 외래 키가 없는 쪽, 즉 mappedBy가 있는 쪽에서는 Hibernate가 지연 로딩을 못 합니다. 프록시를 넣을지 null을 넣을지 정하려면 연관 Entity가 있는지 알아야 하는데, 외래 키가 없으니 조회해 보기 전엔 알 수 없어서입니다. 이쪽까지 지연 로딩하려면 bytecode enhancement를 켭니다.

> [!question]- Cascade를 잘못 사용하면 어떤 문제가 생기는가?
> `CascadeType.REMOVE`가 걸린 부모를 지우면 자식도 같이 지워집니다. 그 자식을 다른 곳에서도 쓰고 있었다면, 남은 쪽이 사라진 데이터를 가리키게 됩니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>연관관계의 주인을 정해야 하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="외래 키를 관리하는 쪽이 변경의 기준이 되며, 주인이 아닌 쪽만 수정하면 DB 반영이 안 될 수 있다." aria-pressed="false">A. 외래 키 변경을 어느 쪽 변경으로 반영할지 결정하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="주인은 객체 생성 순서가 아니라 외래 키 관리 기준이다." aria-pressed="false">B. 먼저 생성된 Entity를 뜻한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="주인이 된다고 항상 cascade가 자동 적용되는 것은 아니다." aria-pressed="false">C. 주인은 모든 하위 Entity를 자동 삭제한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>@ManyToMany는 실무에서 보통 중간 Entity로 풀어 @OneToMany/@ManyToOne으로 모델링하는 편이 안전하다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="중간 테이블에 생성일, 상태, 정렬 순서 같은 속성이 생기기 쉽고 제어도 명확해진다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@ManyToMany는 단순해 보이지만 중간 테이블에 컬럼을 더하거나 다루기가 어렵다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Cascade를 쓸지 정하는 기준은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="부모와 자식의 생명주기가 정말 같은지 확인해야 한다. 공유 참조 Entity에 cascade remove를 걸면 위험하다." aria-pressed="false">A. 생명주기가 같은 aggregate 내부인지 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="cascade는 성능 최적화 옵션이 아니라 영속성 전이 옵션이다." aria-pressed="false">B. 조회 성능을 높이기 위해 모든 연관관계에 켠다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="cascade가 외래 키 제약을 자동 설계하지 않는다." aria-pressed="false">C. DB 스키마 설계를 자동 완성하기 위해 사용한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Associations](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#associations)
- [Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[entity-table-mapping]]
- [[lazy-and-eager-loading]]
- [[n-plus-one-and-fetch-join]]