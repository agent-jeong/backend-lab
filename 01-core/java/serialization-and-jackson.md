---
title: 직렬화와 Jackson 동작 원리
description: Jackson이 객체와 JSON을 어떤 규칙으로 바꾸는지와, 날짜·enum·Entity 응답에서 자주 막히는 곳
tags: [concept, java]
---

# 직렬화와 Jackson 동작 원리

직렬화(Serialization)는 객체를 네트워크로 보내거나 저장할 수 있는 형태로 바꾸는 일이다. 반대로 그 형태를 다시 객체로 만드는 일이 역직렬화다. 백엔드 실무에서는 대부분 Jackson으로 객체와 JSON을 오가는 일을 말한다.

Spring Boot API 서버는 요청과 응답이 거의 다 JSON이다. Jackson이 알아서 바꿔 주지만, 어떤 규칙으로 바꾸는지 모르면 이런 일을 겪는다.

- 응답에서 필드가 빠지거나 null로 나온다.
- 날짜가 숫자 timestamp나 예상과 다른 포맷으로 나온다.
- JPA Entity를 그대로 반환해 순환 참조로 `StackOverflowError`가 난다.
- 요청 JSON과 Java 필드명이 달라 값이 안 들어온다.
- enum 대소문자가 안 맞아 역직렬화가 실패한다.

> [!note] 기준 버전
> 이 글의 클래스 이름과 기본값은 Spring Boot 3.x(Jackson 2) 기준이다. Spring Boot 4부터는 Jackson 3이 기본이다. 패키지가 `com.fasterxml.jackson`에서 `tools.jackson`으로 바뀌고, 자동 설정 빈은 `ObjectMapper` 대신 `JsonMapper`, 컨버터는 `JacksonJsonHttpMessageConverter`다. Jackson 2 지원(`spring-boot-jackson2` 모듈)은 이전을 돕는 용도로만 남아 있고 deprecated다. 동작 원리와 어노테이션 사용법은 같지만 일부 기본값이 달라졌으므로, 이전할 때 날짜·enum 직렬화 결과를 테스트로 확인한다. Jackson 2 시절 기본값에 가깝게 맞추려면 `spring.jackson.use-jackson2-defaults=true`를 쓴다.

## Jackson은 어떻게 동작하나

`@RestController`가 반환한 객체는 `HttpMessageConverter`가 JSON으로 바꾼다. 기본으로 쓰이는 구현체가 Jackson의 `MappingJackson2HttpMessageConverter`다.

### 직렬화 (객체 → JSON)

기본적으로 public getter가 있는 필드만 JSON에 넣는다.

```java
public class UserResponse {
    private Long id;
    private String name;

    public Long getId() { return id; }        // → "id"
    public String getName() { return name; }  // → "name"
}
```

getter가 없으면 그 필드는 JSON에서 빠진다. 에러도 나지 않는다.

### 역직렬화 (JSON → 객체)

기본적으로 기본 생성자로 객체를 만든 뒤 setter로 값을 채우거나, `@JsonCreator`가 붙은 생성자로 만든다.

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

기본 생성자가 없으면 Jackson은 생성자 파라미터 이름을 알아야 객체를 만들 수 있다. Spring Boot는 `ParameterNamesModule`을 등록하지만, 파라미터 이름이 class 파일에 남도록 `-parameters`로 컴파일하지 않았다면 역직렬화가 실패한다. 확실히 하려면 생성자에 `@JsonCreator`를 붙인다. record는 Jackson이 canonical constructor를 알아서 찾아 쓴다.

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

### 날짜와 시간 포맷

`ObjectMapper`를 직접 만들고 `JavaTimeModule`만 등록하면 `LocalDateTime`이 배열(`[2024, 1, 15, 10, 30]`)로 나간다. Spring Boot가 만들어 주는 `ObjectMapper`는 `WRITE_DATES_AS_TIMESTAMPS`를 이미 꺼 두어서 기본이 ISO-8601 문자열이다. 그러니 배열로 나온다면, 누군가 `ObjectMapper`를 직접 만들어 Boot 설정을 덮어쓴 경우가 많다.

```java
// 문제: 직접 만든 ObjectMapper에서는 배열로 나온다
private LocalDateTime createdAt;
// → [2024, 1, 15, 10, 30] (초가 0이면 초 자리를 생략한다)

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

JPA Entity를 그대로 응답으로 반환하면, 양방향 연관관계를 따라 Team에서 Member로, Member에서 다시 Team으로 끝없이 돈다.

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

Entity를 반환하지 말고 DTO로 바꿔서 내보낸다.

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

`@JsonIgnore`나 `@JsonManagedReference`/`@JsonBackReference`로도 막을 수는 있다. 하지만 Entity를 API 응답으로 직접 내보내지 않아야 이런 문제가 아예 생기지 않는다.

### enum 역직렬화

```java
public enum OrderStatus {
    PENDING, APPROVED, REJECTED
}

// 요청: {"status": "pending"} → 기본적으로 실패 (대소문자 불일치)
```

해결 1은 대소문자를 무시하는 전역 설정이다.

```yaml
spring:
  jackson:
    mapper:
      accept-case-insensitive-enums: true
```

해결 2는 `@JsonValue`와 `@JsonCreator`로 JSON 값을 직접 정하는 방법이다.

```java
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

Java 16부터 나온 record는 Jackson 2.12부터 따로 설정 없이 역직렬화된다. canonical constructor를 알아서 찾아 쓴다.

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

Entity나 내부 객체를 그대로 반환하면 내보낼 생각이 없던 필드까지 나간다.

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

연동하는 외부 API가 snake_case를 쓰면 전역 설정으로 바꾼다.

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

- Entity를 그대로 응답으로 반환하면, 순환 참조와 민감 정보 노출이 한꺼번에 생긴다.
- `ObjectMapper`를 직접 만들어 Boot 기본 설정을 덮어쓰면, `LocalDateTime`이 배열로 나가 프론트엔드가 기대하는 포맷과 어긋난다.
- 기본 생성자도 `@JsonCreator`도 없는데 파라미터 이름까지 남지 않으면, 역직렬화가 실패하는데 원인을 찾기 어렵다.
- getter가 없으면, 직렬화할 때 그 필드가 아무 말 없이 빠진다.
- enum 대소문자가 맞지 않으면, `HttpMessageNotReadableException`이 난다.
- `@JsonIgnore`를 getter에만 붙이면 직렬화만 막힐 거라고 생각하면 틀린다. Jackson은 그 property 전체를 무시해서 역직렬화에서도 빠진다. 한 방향만 막으려면 `@JsonProperty(access = ...)`를 쓴다.
- 외부 API의 snake_case를 필드마다 손으로 매핑하면, 하나라도 빠뜨린 필드는 null로 들어온다.

## 한 번에 설명하기

> Spring Boot에서 요청과 응답을 JSON으로 바꾸는 일은 Jackson이 합니다. 직렬화는 getter를 보고, 역직렬화는 기본 생성자와 setter 또는 `@JsonCreator`를 보고 동작합니다.
>
> 제가 가장 먼저 지키는 건 Entity를 API 응답으로 직접 반환하지 않는 것입니다. 순환 참조로 StackOverflowError가 나거나, 민감 정보가 나가거나, lazy loading 문제가 생기기 때문에 record DTO로 바꿔서 내보냅니다.
>
> 그 밖에 날짜 포맷과 enum 대소문자는 설정으로 맞춰 두고, `ObjectMapper`를 직접 만들어 Boot 기본 설정을 덮어쓰지 않습니다.

## 꼬리 질문

> [!question]- Jackson은 직렬화와 역직렬화를 각각 무엇을 보고 하나?
> 직렬화는 public getter가 있는 필드를 JSON에 넣습니다. 역직렬화는 기본 생성자로 만든 뒤 setter로 채우거나, `@JsonCreator`가 붙은 생성자로 객체를 만듭니다.

> [!question]- Entity를 API 응답으로 직접 반환하면 어떤 문제가 생기나?
> 양방향 연관관계가 서로를 계속 따라가서 `StackOverflowError`가 날 수 있습니다. 민감 정보가 나갈 수 있고, lazy loading 때문에 쿼리가 더 나가거나 예외가 날 수도 있습니다.

> [!question]- `@JsonIgnore`를 getter에만 붙이면 어떻게 되나?
> getter에만 붙여도 Jackson은 그 property 전체를 무시해서, 직렬화와 역직렬화 양쪽에서 다 빠집니다. setter 같은 다른 접근자에 `@JsonProperty`를 붙이면 그쪽은 다시 살아납니다. 한 방향만 막으려면 `@JsonProperty(access = WRITE_ONLY)`나 `READ_ONLY`를 씁니다.

> [!question]- `LocalDateTime`은 기본으로 어떤 모양으로 나가나?
> Jackson만 쓰면 `WRITE_DATES_AS_TIMESTAMPS`가 켜져 있어서 배열(`[2024, 1, 15, 10, 30]`)로 나갑니다. Spring Boot가 자동으로 만들어 주는 `ObjectMapper`는 이 옵션을 꺼 둬서 ISO-8601 문자열로 나갑니다.

> [!question]- record는 어떻게 역직렬화되나?
> Jackson 2.12부터 record의 canonical constructor를 알아서 찾아 씁니다. JSON 필드명이 다르면 생성자 파라미터에 `@JsonProperty`를 붙여 줘야 합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

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
    <p class="quiz-question"><span class="quiz-label">객관식</span>LocalDateTime을 직렬화할 때 먼저 정할 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="타임존이 없는 타입이므로 API 경계에서는 포맷과 시간대 의미를 명확히 정해야 한다." aria-pressed="false">A. 포맷과 시간대 의미를 API 스펙으로 명확히 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="LocalDateTime 자체에는 timezone 정보가 없다." aria-pressed="false">B. 항상 UTC 정보가 포함되어 안전하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="프론트엔드가 알아서 해석하게 두면 환경별 오류가 생길 수 있다." aria-pressed="false">C. 문자열이면 어떤 포맷이든 상관없다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Boot: JSON](https://docs.spring.io/spring-boot/reference/features/json.html)
- [Jackson Databind](https://github.com/FasterXML/jackson-databind)

## 관련 문서

- [[01-core/java/java|java]]
- [[class-interface-enum-record]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[spring-boot-auto-configuration]]