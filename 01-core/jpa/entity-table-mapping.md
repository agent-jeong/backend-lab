---
title: "엔티티-테이블 매핑 기본"
description: Entity를 만들 때 지킬 조건과, id 전략과 enum 매핑에서 나중에 후회하는 선택
tags: [concept, jpa]
---

# 엔티티-테이블 매핑 기본

Entity는 JPA가 관리하는 객체다. DB 테이블 하나와 1:1로 짝지어지고, 영속성 컨텍스트가 관리한다.

매핑은 어노테이션 몇 줄이지만, 데이터가 쌓인 뒤에는 되돌리기 어렵다. id 생성 전략을 무엇으로 잡느냐에 따라 batch insert를 쓸 수 있는지가 갈리고, enum을 어떻게 저장하느냐에 따라 이미 쌓인 주문 상태 값이 엉뚱한 뜻으로 읽힐 수 있다.

## 기본 매핑

```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserStatus status;

    @Column(updatable = false)
    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;

    protected User() {
    }

    // 생성 메서드, getter 등
}
```

Entity가 되려면 아래 네 가지를 갖춰야 한다.

| 조건 | 이유 |
|---|---|
| `@Entity` 어노테이션 | JPA가 관리할 대상으로 등록한다 |
| `@Id` 필드 | 영속성 컨텍스트가 이 값으로 Entity를 구분한다 |
| 기본 생성자 (protected 이상) | JPA가 리플렉션으로 객체를 만든다 |
| final class가 아닐 것 | 프록시를 만들려면 상속할 수 있어야 한다 |

## @Id 생성 전략

| 전략 | 동작 | 실무에서 |
|---|---|---|
| `IDENTITY` | DB의 auto_increment를 쓴다 | MySQL에서 주로 쓴다. insert해야 id를 알 수 있어서 batch insert가 안 된다 |
| `SEQUENCE` | DB 시퀀스를 쓴다 | PostgreSQL/Oracle에서 주로 쓴다. `allocationSize`로 시퀀스 호출 횟수를 줄인다 |
| `TABLE` | 별도 테이블로 시퀀스를 흉내 낸다 | 느려서 실무에서는 거의 안 쓴다 |
| `AUTO` | DB 방언을 보고 알아서 고른다 | 무엇이 골라질지 짐작하기 어려우니 직접 정하는 게 안전하다 |

MySQL에서는 보통 `IDENTITY`를 쓴다. 다만 `IDENTITY`는 insert할 때 DB에서 id를 받아와야 해서 JDBC batch insert가 안 된다.

## @Column 설정

```java
@Column(nullable = false, length = 100)  // NOT NULL, VARCHAR(100)
private String name;

@Column(unique = true)                    // UNIQUE 제약조건
private String email;

@Column(updatable = false)                // UPDATE 시 제외
private LocalDateTime createdAt;

@Column(insertable = false, updatable = false)  // 읽기 전용
private LocalDateTime dbCreatedAt;
```

`@Column`을 빼면 필드명이 그대로 컬럼명이 된다. Spring Boot는 기본으로 camelCase를 snake_case로 바꾼다(`userName` → `user_name`).

## Enum 매핑

```java
// 위험: 순서 기반 저장
@Enumerated(EnumType.ORDINAL)
private UserStatus status; // 0, 1, 2...

// 안전: 이름 기반 저장
@Enumerated(EnumType.STRING)
private UserStatus status; // "ACTIVE", "INACTIVE"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 이미 저장된 숫자가 다른 상수를 가리키게 된다. 그래서 늘 `STRING`을 쓴다. `@Enumerated`만 붙이고 값을 안 주면 기본값이 `ORDINAL`이라는 것도 기억해 둔다.

## 날짜/시간 매핑

Java 8+ `LocalDateTime`, `LocalDate`는 어노테이션을 따로 붙이지 않아도 매핑된다.

```java
private LocalDateTime createdAt;
private LocalDate birthDate;
```

생성 시간과 수정 시간은 `@CreatedDate`, `@LastModifiedDate`를 붙이면 알아서 채워진다. Configuration 클래스에 `@EnableJpaAuditing`을 붙여야 동작한다.

```java
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public abstract class BaseEntity {

    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    private LocalDateTime updatedAt;
}
```

```java
@Configuration
@EnableJpaAuditing
public class JpaConfig { }
```

## 자주 깨지는 곳

- 기본 생성자를 만들지 않으면, JPA가 객체를 만들지 못해 `InstantiationException`이 난다.
- `@Enumerated`를 값 없이 붙이면 `ORDINAL`로 저장되고, enum 순서를 바꾸는 순간 기존 데이터가 다른 상태로 읽힌다.
- Entity를 API 응답으로 그대로 내보내면, 순환 참조, 민감 정보 노출, lazy loading 문제가 생긴다. DTO로 바꿔서 내보낸다.
- `@Column(nullable = false)`를 붙였다고 DB에 NOT NULL이 걸렸다고 믿으면 틀린다. 이 설정은 DDL 자동 생성을 쓸 때만 스키마에 들어가고, 안 쓰면 DB에는 제약이 없다. 그렇다고 아무 효과가 없는 건 아니다. Hibernate는 Bean Validation이 없으면 INSERT 전에 null을 검사해 `PropertyValueException`을 던진다(`hibernate.check_nullability`).
- `@Column` 설정을 빠뜨리면, DDL 자동 생성 때 생각과 다른 스키마가 만들어진다.
- `@GeneratedValue` 전략을 따져 보지 않고 기본값을 쓰면, batch insert가 느려질 수 있다.
- `@Id` 타입을 primitive(`long`)로 쓰면, null이 될 수 없어서 아직 저장 안 된 Entity를 구분하지 못한다.

## 한 번에 설명하기

> Entity는 `@Entity`, `@Id`, 기본 생성자가 있어야 하고, 테이블 하나와 1:1로 짝지어집니다.
>
> id 전략은 MySQL에서 `IDENTITY`를 주로 씁니다. insert할 때 id를 받아와야 해서 batch insert가 안 된다는 걸 알고 씁니다.
>
> enum은 순서가 바뀌어도 괜찮게 `@Enumerated(STRING)`으로 저장하고, Entity는 API 응답으로 그대로 내보내지 않고 DTO로 바꿉니다.

## 꼬리 질문

> [!question]- Entity에 기본 생성자가 필요한 이유는?
> JPA가 리플렉션으로 객체를 만들기 때문에 인자 없는 생성자가 있어야 합니다. `protected`로 두면 바깥 코드가 함부로 부르는 것도 막을 수 있습니다.

> [!question]- `IDENTITY` 전략에서 batch insert가 안 되는 이유는?
> `IDENTITY`는 DB가 만든 id를 insert한 뒤에 받아와야 영속성 컨텍스트에 넣을 수 있습니다. 그래서 한 건씩 insert할 수밖에 없고, JDBC batch로 묶이지 않습니다.

> [!question]- `@Id` 타입을 `long`이 아닌 `Long`으로 써야 하는 이유는?
> primitive `long`은 기본값이 0이라, 아직 저장 안 된 건지 id가 0인 건지 구분이 안 됩니다. `Long`은 null을 쓸 수 있어서, null이면 아직 저장 전이라고 알 수 있습니다.

> [!question]- `@Column`을 생략하면 어떻게 되는가?
> 필드명이 그대로 컬럼명이 됩니다. Spring Boot를 쓰면 기본으로 camelCase가 snake_case로 바뀝니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Entity에 기본 생성자가 필요한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="JPA 구현체가 리플렉션과 프록시로 Entity를 만들어야 하기 때문이다." aria-pressed="false">A. JPA가 리플렉션/프록시로 Entity를 생성할 수 있어야 하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="기본 생성자는 JSON 직렬화만을 위한 것이 아니다." aria-pressed="false">B. Jackson 직렬화만을 위해 필요하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="기본 생성자가 모든 검증을 자동으로 수행하지 않는다." aria-pressed="false">C. 필드 검증을 자동 실행하기 위해서다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Enum을 ORDINAL로 저장하면 enum 순서 변경 시 기존 데이터의 의미가 바뀔 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="운영 데이터의 의미 안정성을 위해 보통 EnumType.STRING을 우선 고려한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="ORDINAL은 저장 공간은 작을 수 있지만 순서 변경에 취약하다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Id 타입을 primitive long보다 Long으로 쓰는 것이 일반적인 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Long은 null로 아직 영속화되지 않은 신규 Entity 상태를 표현할 수 있다." aria-pressed="false">A. 저장 전 식별자 미할당 상태를 null로 표현할 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Long이 항상 long보다 빠른 것은 아니다." aria-pressed="false">B. wrapper 타입이 항상 성능이 더 좋기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Long을 쓴다고 동시성 문제가 자동으로 해결되지는 않는다." aria-pressed="false">C. 동시성 제어를 자동으로 제공하기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Domain Model](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#domain-model)
- [Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[why-jpa]]
- [[persistence-context]]
- [[association-mapping]]