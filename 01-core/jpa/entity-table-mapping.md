---
title: "엔티티-테이블 매핑 기본"
description: JPA Entity와 테이블 매핑의 실무 규칙과 주의점
---

# 엔티티-테이블 매핑 기본

Entity는 JPA가 관리하는 객체다. 데이터베이스 테이블과 1:1로 매핑되고, 영속성 컨텍스트가 관리한다.

매핑은 몇 줄짜리 어노테이션이지만 잘못 잡으면 나중에 되돌리기 어렵다. id 생성 전략은 batch insert 가능 여부를, enum 저장 방식은 기존 데이터의 의미를 결정한다.

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
| `@Entity` 어노테이션 | JPA 관리 대상으로 등록 |
| `@Id` 필드 | 영속성 컨텍스트에서 식별자로 사용 |
| 기본 생성자 (protected 이상) | JPA가 리플렉션으로 객체를 생성 |
| final class가 아닐 것 | 프록시 생성을 위해 상속 가능해야 함 |

## @Id 생성 전략

| 전략 | 동작 | 실무 포인트 |
|---|---|---|
| `IDENTITY` | DB의 auto_increment 사용 | MySQL에서 주로 사용, insert 후 id를 알 수 있어 batch insert 불가 |
| `SEQUENCE` | DB 시퀀스 사용 | PostgreSQL/Oracle에서 주로 사용, `allocationSize`로 성능 조절 |
| `TABLE` | 별도 테이블로 시퀀스 흉내 | 성능이 나빠서 실무에서 거의 사용하지 않음 |
| `AUTO` | DB 방언에 따라 자동 선택 | 예측이 어려워 명시적 전략이 안전 |

MySQL에서는 `IDENTITY`가 일반적이다. 다만 `IDENTITY`는 insert 시점에 DB에서 id를 받아와야 해서 JDBC batch insert가 동작하지 않는다.

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

`@Column`을 생략하면 필드명이 그대로 컬럼명이 된다. Spring Boot의 기본 네이밍 전략은 camelCase를 snake_case로 바꾼다(`userName` → `user_name`).

## Enum 매핑

```java
// 위험: 순서 기반 저장
@Enumerated(EnumType.ORDINAL)
private UserStatus status; // 0, 1, 2...

// 안전: 이름 기반 저장
@Enumerated(EnumType.STRING)
private UserStatus status; // "ACTIVE", "INACTIVE"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 기존 데이터와 매핑이 깨진다. 항상 `STRING`을 쓴다. `@Enumerated`를 붙이기만 하고 값을 안 주면 기본값이 `ORDINAL`이라는 점도 기억한다.

## 날짜/시간 매핑

Java 8+ `LocalDateTime`, `LocalDate`는 별도 어노테이션 없이 매핑된다.

```java
private LocalDateTime createdAt;
private LocalDate birthDate;
```

생성/수정 시간은 `@CreatedDate`, `@LastModifiedDate`로 자동 관리한다. Configuration 클래스에 `@EnableJpaAuditing`을 붙여야 동작한다.

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

- **기본 생성자를 만들지 않는다.** JPA가 객체를 만들지 못해 `InstantiationException`이 난다.
- **`@Enumerated` 기본값이 `ORDINAL`인 걸 모른다.** enum 순서를 바꾸는 순간 기존 데이터의 의미가 바뀐다.
- **Entity를 API 응답으로 그대로 반환한다.** 순환 참조, 민감 정보 노출, lazy loading 문제가 생긴다. DTO로 바꿔서 내보낸다.
- **`@Column(nullable = false)`를 DB 제약조건과 혼동한다.** 이 설정은 DDL 자동 생성 때만 스키마에 반영된다. DDL 자동 생성을 쓰지 않으면 DB에는 제약이 없다. 그렇다고 효과가 전혀 없는 것도 아니다. Hibernate는 Bean Validation이 없으면 INSERT 전에 null을 검사해 `PropertyValueException`을 던진다(`hibernate.check_nullability`).
- **`@Column` 설정을 빠뜨린다.** DDL 자동 생성 시 의도와 다른 스키마가 만들어진다.
- **`@GeneratedValue` 전략을 이해하지 않고 기본값을 쓴다.** 잘못 고르면 batch insert 성능이 나빠진다.
- **`@Id` 타입을 primitive(`long`)로 쓴다.** null 체크가 안 돼 저장 전 상태를 구분하지 못한다.

## 면접에서 말하기

> Entity는 `@Entity`, `@Id`, 기본 생성자가 있어야 하고 테이블과 1:1로 매핑됩니다. id 전략은 MySQL에서 `IDENTITY`를 주로 쓰는데, insert 시점에 id를 받아와야 해서 batch insert가 안 된다는 제약을 알고 씁니다. enum은 순서 변경에 안전하도록 `@Enumerated(STRING)`으로 저장하고, Entity는 API 응답으로 직접 내보내지 않고 DTO로 바꿉니다.

## 꼬리 질문

> [!question]- Entity에 기본 생성자가 필요한 이유는?
> JPA는 리플렉션으로 객체를 생성하기 때문에 인자 없는 생성자가 필요합니다. `protected`로 선언하면 외부에서 직접 호출하는 것을 방지할 수 있습니다.

> [!question]- `IDENTITY` 전략에서 batch insert가 안 되는 이유는?
> `IDENTITY`는 insert 후 DB에서 생성된 id를 받아와야 영속성 컨텍스트에 저장할 수 있습니다. 이 때문에 한 건씩 insert해야 하고 JDBC batch가 동작하지 않습니다.

> [!question]- `@Id` 타입을 `long`이 아닌 `Long`으로 써야 하는 이유는?
> primitive `long`은 기본값이 0이라 저장 전 상태와 구분이 안 됩니다. `Long`은 null이 가능해서 아직 저장되지 않은 Entity를 식별할 수 있습니다.

> [!question]- `@Column`을 생략하면 어떻게 되는가?
> JPA가 필드명을 그대로 컬럼명으로 사용합니다. Spring Boot의 기본 네이밍 전략은 camelCase를 snake_case로 변환합니다.

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

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[why-jpa]]
- [[persistence-context]]
- [[association-mapping]]