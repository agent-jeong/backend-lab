---
title: 직렬화와 Jackson 동작 원리
description: Java 직렬화와 Jackson 기반 JSON 처리의 실무 주의점
---

# 직렬화와 Jackson 동작 원리

직렬화(Serialization)는 객체를 전송하거나 저장할 수 있는 형태로 바꾸는 일이다. 실무에서는 대부분 Jackson으로 하는 JSON 직렬화·역직렬화를 말한다.

Spring Boot API 서버의 요청과 응답은 거의 다 JSON이다. Jackson이 알아서 처리해 주지만 규칙을 모르면 이런 일을 겪는다. 응답에서 필드가 빠지거나 null로 나온다. 날짜가 숫자 timestamp나 예상과 다른 포맷으로 나온다. JPA Entity를 그대로 반환해 순환 참조로 `StackOverflowError`가 난다. 요청 JSON과 Java 필드명이 달라 바인딩이 안 된다. enum 대소문자가 안 맞아 역직렬화가 실패한다. record DTO가 역직렬화되지 않는다.

## Jackson은 어떻게 동작하나

`@RestController`의 반환 객체는 `HttpMessageConverter`가 JSON으로 바꾼다. 기본 구현체가 Jackson의 `MappingJackson2HttpMessageConverter`다.

### 직렬화 (객체 → JSON)

기본적으로 public getter를 기준으로 필드를 JSON에 넣는다.

```java
public class UserResponse {
    private Long id;
    private String name;

    public Long getId() { return id; }        // → "id"
    public String getName() { return name; }  // → "name"
}
```

getter가 없으면 그 필드는 JSON에 들어가지 않는다.

### 역직렬화 (JSON → 객체)

기본적으로 기본 생성자 + setter, 또는 `@JsonCreator`로 객체를 만든다.

```java
// 기본 생성자 + setter 방식
public class UserRequest {
    private String name;
    private String email;

    public UserRequest() {}

    public void setName(String name) { this.name = name; }
    public void setEmail(String email) { this.email = email; }
}
```

기본 생성자가 없으면 역직렬화가 실패한다. 단, record는 Jackson이 canonical constructor를 자동으로 인식한다.

## 자주 쓰는 어노테이션

| 어노테이션 | 용도 | 사용 예시 |
|---|---|---|
| `@JsonProperty` | JSON 필드명과 Java 필드명 매핑 | API 스펙의 snake_case를 camelCase로 |
| `@JsonIgnore` | 특정 필드를 직렬화/역직렬화에서 제외 | 비밀번호, 내부 상태 |
| `@JsonFormat` | 날짜/시간 포맷 지정 | `@JsonFormat(pattern = "yyyy-MM-dd")` |
| `@JsonInclude` | null이나 빈 값 제외 조건 | `@JsonInclude(NON_NULL)` |
| `@JsonCreator` | 역직렬화 시 사용할 생성자 지정 | 불변 객체 역직렬화 |
| `@JsonValue` | enum 직렬화 시 사용할 값 지정 | enum을 특정 문자열로 변환 |

## 실무에서 자주 부딪히는 문제

### 날짜·시간 포맷

`ObjectMapper`를 직접 만들어 `JavaTimeModule`만 등록하면 `LocalDateTime`은 배열(`[2024, 1, 15, 10, 30]`)로 나간다. Spring Boot가 만들어 주는 `ObjectMapper`는 `WRITE_DATES_AS_TIMESTAMPS`를 이미 꺼 두어서 기본이 ISO-8601 문자열이다. 배열로 나온다면 `ObjectMapper`를 직접 생성해 Boot 설정을 덮어쓴 경우가 많다.

```java
// 문제: 직접 만든 ObjectMapper에서는 배열로 나온다
private LocalDateTime createdAt;
// → [2024, 1, 15, 10, 30, 0]

// 해결 1: 필드 단위
@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
private LocalDateTime createdAt;
// → "2024-01-15 10:30:00"

// 해결 2: 전역 설정 (application.yml)
```

```yaml
# 전역 설정
spring:
  jackson:
    serialization:
      write-dates-as-timestamps: false
    date-format: "yyyy-MM-dd HH:mm:ss"  # java.util.Date에만 적용, java.time 타입에는 영향 없음
```

`write-dates-as-timestamps: false`면 ISO-8601 형식(`2024-01-15T10:30:00`)으로 나온다.

### 순환 참조

JPA Entity를 그대로 응답으로 반환하면 양방향 연관관계에서 순환 참조가 생긴다.

```java
@Entity
public class Team {
    @OneToMany(mappedBy = "team")
    private List<Member> members; // Member → Team → Member → ...
}

@Entity
public class Member {
    @ManyToOne
    private Team team;
}
```

Entity를 반환하지 말고 DTO로 바꾼다.

```java
// 가장 좋은 방법: Entity를 직접 반환하지 않고 DTO로 변환
public record TeamResponse(Long id, String name, List<String> memberNames) {

    public static TeamResponse from(Team team) {
        List<String> names = team.getMembers().stream()
            .map(Member::getName)
            .toList();
        return new TeamResponse(team.getId(), team.getName(), names);
    }
}
```

`@JsonIgnore`나 `@JsonManagedReference`/`@JsonBackReference`로도 막을 수는 있다. 하지만 근본 해결은 Entity를 API 응답으로 직접 내보내지 않는 것이다.

### enum 역직렬화

```java
public enum OrderStatus {
    PENDING, APPROVED, REJECTED
}

// 요청: {"status": "pending"} → 기본적으로 실패 (대소문자 불일치)
```

```java
// 해결 1: 대소문자 무시 설정
spring:
  jackson:
    mapper:
      accept-case-insensitive-enums: true

// 해결 2: @JsonValue + @JsonCreator로 커스텀 매핑
public enum OrderStatus {
    PENDING("pending"),
    APPROVED("approved"),
    REJECTED("rejected");

    private final String value;

    OrderStatus(String value) { this.value = value; }

    @JsonValue
    public String getValue() { return value; }

    @JsonCreator
    public static OrderStatus from(String value) {
        return Arrays.stream(values())
            .filter(s -> s.value.equals(value))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Unknown status: " + value));
    }
}
```

### record 역직렬화

Java 16+ record는 Jackson 2.12+에서 기본 지원된다. canonical constructor를 자동으로 인식한다.

```java
// 기본적으로 역직렬화가 동작한다
public record CreateUserRequest(String name, String email) {
}
```

JSON 필드명이 다르면 생성자 파라미터에 `@JsonProperty`를 붙인다.

```java
public record CreateUserRequest(
    @JsonProperty("user_name") String name,
    @JsonProperty("user_email") String email
) {
}
```

### 민감 정보 노출

Entity나 내부 객체를 그대로 반환하면 의도하지 않은 필드까지 나간다.

```java
// 위험: password, role 등이 그대로 노출
@GetMapping("/users/{id}")
public User getUser(@PathVariable Long id) {
    return userRepository.findById(id).orElseThrow();
}

// 안전: 필요한 필드만 포함된 DTO 반환
@GetMapping("/users/{id}")
public UserResponse getUser(@PathVariable Long id) {
    User user = userRepository.findById(id).orElseThrow();
    return UserResponse.from(user);
}
```

### snake_case와 camelCase

외부 API가 snake_case를 쓰면 전역 설정으로 바꾼다.

```yaml
spring:
  jackson:
    property-naming-strategy: SNAKE_CASE
```

특정 클래스에만 적용할 수도 있다.

```java
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ExternalApiResponse(String userName, String emailAddress) {
}
// → {"user_name": "...", "email_address": "..."}
```

## 상황별로 어떻게 하나

| 상황 | 권장 |
|---|---|
| API 응답 | Entity 직접 반환 금지, DTO(record) 변환 |
| 날짜/시간 | 전역 설정으로 `write-dates-as-timestamps: false` |
| 외부 API 연동 | `@JsonNaming` 또는 `@JsonProperty`로 네이밍 매핑 |
| enum 요청 바인딩 | `accept-case-insensitive-enums: true` 또는 `@JsonCreator` |
| 민감 필드 | DTO 분리가 우선, 부득이하면 `@JsonIgnore` |
| 불변 요청 객체 | record 사용 (Jackson 2.12+) |

## 자주 깨지는 곳

- **Entity를 그대로 응답으로 반환한다.** 순환 참조, 민감 정보 노출이 같이 온다.
- **`ObjectMapper`를 직접 생성해 Boot 기본 설정을 덮어쓴다.** `LocalDateTime`이 배열로 나가 프론트엔드와 포맷이 어긋난다.
- **기본 생성자가 없다.** 역직렬화가 실패하는데 원인을 찾기 어렵다.
- **getter가 없다.** 직렬화에서 필드가 조용히 빠진다.
- **enum 대소문자가 맞지 않는다.** `HttpMessageNotReadableException`이 난다.
- **`@JsonIgnore`가 한쪽 방향만 막는다고 생각한다.** getter에만 붙여도 Jackson은 property 전체를 무시해서 역직렬화에서도 빠진다. 한 방향만 막으려면 `@JsonProperty(access = ...)`를 쓴다.
- **외부 API의 snake_case를 필드마다 손으로 매핑한다.** 빠뜨린 필드가 null로 들어온다.

## 면접에서 말하기

> Spring Boot에서 요청과 응답의 JSON 변환은 Jackson이 맡고, 직렬화는 getter, 역직렬화는 기본 생성자와 setter 또는 `@JsonCreator`를 기준으로 동작합니다. 제가 가장 먼저 지키는 원칙은 Entity를 API 응답으로 직접 반환하지 않는 것입니다. 순환 참조로 StackOverflowError가 나거나 민감 정보가 노출되고 lazy loading 문제도 생기기 때문에 record DTO로 바꿔서 내보냅니다. 그 외에 날짜 포맷과 enum 대소문자 불일치를 설정으로 맞춰 두고, `ObjectMapper`를 직접 만들어 Boot 기본 설정을 덮어쓰지 않습니다.

## 꼬리 질문

> [!question]- Jackson의 직렬화와 역직렬화 기준은 각각 무엇인가?
> 직렬화는 public getter 기준으로 필드를 JSON에 포함하고, 역직렬화는 기본 생성자 + setter 또는 `@JsonCreator`를 통해 객체를 생성합니다.

> [!question]- Entity를 API 응답으로 직접 반환하면 어떤 문제가 생기는가?
> 양방향 연관관계의 순환 참조로 `StackOverflowError`, 민감 정보 노출, lazy loading에 의한 추가 쿼리나 예외가 발생할 수 있습니다.

> [!question]- `@JsonIgnore`를 getter에만 붙이면 어떻게 되는가?
> getter에만 붙여도 Jackson은 그 property 전체를 무시하므로 직렬화와 역직렬화 모두에서 빠집니다. 다른 접근자(setter 등)에 `@JsonProperty`를 명시하면 그쪽은 살아납니다. 한 방향만 막으려면 `@JsonProperty(access = WRITE_ONLY)`나 `READ_ONLY`를 씁니다.

> [!question]- `LocalDateTime`의 기본 직렬화 형태는?
> Jackson 단독으로는 `WRITE_DATES_AS_TIMESTAMPS`가 켜져 있어 배열(`[2024, 1, 15, 10, 30]`)로 나갑니다. Spring Boot의 자동 설정 `ObjectMapper`는 이 옵션을 꺼 두어 ISO-8601 문자열로 나갑니다.

> [!question]- record의 역직렬화가 동작하는 원리는?
> Jackson 2.12+에서 record의 canonical constructor를 자동 인식합니다. JSON 필드명이 다르면 생성자 파라미터에 `@JsonProperty`를 붙여야 합니다.

## 점검 퀴즈

아래 문항은 개념을 실제로 설명할 수 있는지 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Entity를 API 응답으로 직접 반환할 때 생길 수 있는 문제는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="지연 로딩, 순환 참조, 내부 필드 노출, API 스펙 변경 전파가 생길 수 있다." aria-pressed="false">A. Lazy loading, 순환 참조, 내부 구조 노출 문제가 생길 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Entity 반환이 항상 컴파일 에러를 만들지는 않는다." aria-pressed="false">B. Jackson이 Entity는 절대 직렬화하지 못한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DTO가 항상 더 느리다는 일반화는 맞지 않다." aria-pressed="false">C. DTO를 쓰면 무조건 성능이 나빠진다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>@JsonIgnore를 getter에만 붙이면 직렬화와 역직렬화 양쪽에 동일하게 적용된다고 단정할 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Jackson은 접근자, 필드, 생성자 등 설정에 따라 직렬화/역직렬화 경로가 달라질 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="읽기/쓰기 방향과 붙인 위치에 따라 결과가 달라질 수 있어 테스트가 필요하다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>LocalDateTime 직렬화에서 실무적으로 중요한 기준은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="타임존이 없는 타입이므로 API 경계에서는 포맷과 시간대 의미를 명확히 정해야 한다." aria-pressed="false">A. 포맷과 시간대 의미를 API 스펙으로 명확히 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="LocalDateTime 자체에는 timezone 정보가 없다." aria-pressed="false">B. 항상 UTC 정보가 포함되어 안전하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="프론트엔드가 알아서 해석하게 두면 환경별 오류가 생길 수 있다." aria-pressed="false">C. 문자열이면 어떤 포맷이든 상관없다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[class-interface-enum-record]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]