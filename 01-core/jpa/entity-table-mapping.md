---
title: "엔티티-테이블 매핑 기본"
description: JPA Entity와 테이블 매핑의 실무 규칙과 주의점
---

# 엔티티-테이블 매핑 기본

## 한 줄 정의

Entity는 JPA가 관리하는 객체로, 데이터베이스 테이블과 1:1로 매핑되어 영속성 컨텍스트의 관리 대상이 된다.

## 실무에서 왜 중요한가

Entity 매핑이 잘못되면 다음 문제가 생긴다.

- 기본 생성자가 없어서 JPA가 객체를 생성하지 못한다.
- `@Column` 설정이 누락되어 DDL 자동 생성 시 의도와 다른 스키마가 만들어진다.
- `@Id` 생성 전략을 잘못 선택해서 배치 insert 성능이 나빠진다.
- `@Enumerated(ORDINAL)`을 써서 enum 순서 변경 시 데이터가 깨진다.
- Entity를 API 응답으로 직접 반환해서 순환 참조, 민감 정보 노출 문제가 생긴다.

## 기본 매핑 규칙

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

### Entity 필수 조건

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

MySQL 환경에서는 `IDENTITY`가 일반적이다. 단, `IDENTITY`는 insert 시점에 DB에서 id를 받아와야 하므로 JDBC batch insert가 동작하지 않는다.

## @Column 실무 설정

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

`@Column`을 생략하면 JPA가 필드명을 그대로 컬럼명으로 사용한다. Spring Boot의 기본 네이밍 전략은 camelCase를 snake_case로 변환한다 (`userName` → `user_name`).

## Enum 매핑

```java
// 위험: 순서 기반 저장
@Enumerated(EnumType.ORDINAL)
private UserStatus status; // 0, 1, 2...

// 안전: 이름 기반 저장
@Enumerated(EnumType.STRING)
private UserStatus status; // "ACTIVE", "INACTIVE"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 기존 데이터와 매핑이 깨진다. 반드시 `STRING`을 사용해야 한다.

## 날짜/시간 매핑

Java 8+ `LocalDateTime`, `LocalDate`는 별도 어노테이션 없이 매핑된다.

```java
private LocalDateTime createdAt;
private LocalDate birthDate;
```

`@CreatedDate`, `@LastModifiedDate`를 사용하면 자동으로 생성/수정 시간을 관리할 수 있다. 단, Configuration 클래스에 `@EnableJpaAuditing`을 추가해야 동작한다.

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

## 자주 나는 실수

- 기본 생성자를 만들지 않아서 `InstantiationException`이 발생한다.
- `@Enumerated`의 기본값이 `ORDINAL`인 것을 모르고 사용한다.
- Entity를 API 응답으로 직접 반환한다.
- `@Column(nullable = false)`를 DB 제약조건으로 착각하고, DDL 자동 생성을 안 쓰면 아무 효과 없다고 생각한다.
- `@GeneratedValue` 전략을 이해하지 않고 기본값을 사용한다.
- `@Id` 타입을 primitive(`long`)로 써서 null 체크가 안 된다.

## 핵심 요약

JPA Entity는 `@Entity`, `@Id`, 기본 생성자가 필수이며, 테이블과 1:1로 매핑됩니다.

`@Id` 생성 전략은 MySQL에서는 `IDENTITY`가 일반적이지만, batch insert가 안 되는 제약이 있습니다.
enum은 반드시 `@Enumerated(STRING)`을 사용해야 순서 변경에 안전합니다.

Entity를 API 응답으로 직접 반환하면 순환 참조, 민감 정보 노출, lazy loading 문제가 생기므로 DTO로 변환해야 합니다.

## 꼬리 질문

> [!question]- Entity에 기본 생성자가 필요한 이유는?
> JPA는 리플렉션으로 객체를 생성하기 때문에 인자 없는 생성자가 필요합니다. `protected`로 선언하면 외부에서 직접 호출하는 것을 방지할 수 있습니다.

> [!question]- `IDENTITY` 전략에서 batch insert가 안 되는 이유는?
> `IDENTITY`는 insert 후 DB에서 생성된 id를 받아와야 영속성 컨텍스트에 저장할 수 있습니다. 이 때문에 한 건씩 insert해야 하고 JDBC batch가 동작하지 않습니다.

> [!question]- `@Id` 타입을 `long`이 아닌 `Long`으로 써야 하는 이유는?
> primitive `long`은 기본값이 0이라 저장 전 상태와 구분이 안 됩니다. `Long`은 null이 가능해서 아직 저장되지 않은 Entity를 식별할 수 있습니다.

> [!question]- `@Column`을 생략하면 어떻게 되는가?
> JPA가 필드명을 그대로 컬럼명으로 사용합니다. Spring Boot의 기본 네이밍 전략은 camelCase를 snake_case로 변환합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Entity에 기본 생성자가 필요한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="JPA 구현체가 리플렉션과 프록시 생성을 통해 Entity를 생성할 수 있어야 하기 때문이다." aria-pressed="false">A. JPA가 리플렉션/프록시로 Entity를 생성할 수 있어야 하기 때문이다.</button>
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