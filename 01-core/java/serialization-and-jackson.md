---
title: Serialization And Jackson
description: Java 직렬화와 Jackson 기반 JSON 처리의 실무 주의점
---

# Serialization And Jackson

## 한 줄 정의

직렬화(Serialization)는 객체를 전송/저장 가능한 형태로 변환하는 과정이고, 실무에서는 대부분 Jackson을 통한 JSON 직렬화/역직렬화를 의미한다.

## 실무에서 왜 중요한가

Spring Boot 기반 API 서버에서 요청/응답은 거의 모두 JSON이다. Jackson이 자동으로 처리해주지만, 규칙을 모르면 다음 문제를 마주한다.

- API 응답에서 특정 필드가 누락되거나 null로 나온다.
- 날짜/시간 값이 timestamp 숫자나 예상과 다른 포맷으로 나온다.
- JPA Entity를 그대로 반환해서 순환 참조로 `StackOverflowError`가 발생한다.
- 요청 JSON의 필드명과 Java 필드명이 달라서 바인딩이 안 된다.
- enum 값이 대소문자 불일치로 역직렬화에 실패한다.
- record 기반 DTO에서 역직렬화가 안 되는 경우가 생긴다.

## Jackson 동작 원리

Spring Boot에서 `@RestController`의 반환 객체는 `HttpMessageConverter`를 통해 JSON으로 변환된다. 기본 구현체가 Jackson의 `MappingJackson2HttpMessageConverter`다.

### 직렬화 (객체 → JSON)

Jackson은 기본적으로 **public getter**를 기준으로 필드를 JSON에 포함한다.

```java
public class UserResponse {
    private Long id;
    private String name;

    public Long getId() { return id; }        // → "id"
    public String getName() { return name; }  // → "name"
}
```

getter가 없으면 해당 필드는 JSON에 포함되지 않는다.

### 역직렬화 (JSON → 객체)

기본적으로 **기본 생성자 + setter** 또는 **@JsonCreator** 를 통해 객체를 생성한다.

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

기본 생성자가 없으면 역직렬화에 실패한다. 단, record는 Jackson이 canonical constructor를 자동으로 인식한다.

## 자주 쓰는 어노테이션

| 어노테이션 | 용도 | 사용 예시 |
|---|---|---|
| `@JsonProperty` | JSON 필드명과 Java 필드명 매핑 | API 스펙의 snake_case를 camelCase로 |
| `@JsonIgnore` | 특정 필드를 직렬화/역직렬화에서 제외 | 비밀번호, 내부 상태 |
| `@JsonFormat` | 날짜/시간 포맷 지정 | `@JsonFormat(pattern = "yyyy-MM-dd")` |
| `@JsonInclude` | null이나 빈 값 제외 조건 | `@JsonInclude(NON_NULL)` |
| `@JsonCreator` | 역직렬화 시 사용할 생성자 지정 | 불변 객체 역직렬화 |
| `@JsonValue` | enum 직렬화 시 사용할 값 지정 | enum을 특정 문자열로 변환 |

## 실무에서 자주 겪는 문제

### 1. 날짜/시간 포맷

Jackson은 `LocalDateTime`을 기본적으로 배열(`[2024, 1, 15, 10, 30]`)로 직렬화한다.

```java
// 문제: 배열로 나온다
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
    date-format: "yyyy-MM-dd HH:mm:ss"
```

`write-dates-as-timestamps: false`를 설정하면 ISO-8601 형식(`2024-01-15T10:30:00`)으로 출력된다.

### 2. 순환 참조

JPA Entity를 그대로 API 응답으로 반환하면 양방향 연관관계에서 순환 참조가 발생한다.

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

해결 방법:

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

`@JsonIgnore`나 `@JsonManagedReference`/`@JsonBackReference`로도 해결할 수 있지만, **Entity를 API 응답으로 직접 노출하지 않는 것**이 근본적인 해결이다.

### 3. enum 역직렬화

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

### 4. record 역직렬화

Java 16+ record는 Jackson 2.12+에서 기본 지원된다. canonical constructor를 자동으로 인식한다.

```java
// 기본적으로 역직렬화가 동작한다
public record CreateUserRequest(String name, String email) {
}
```

단, JSON 필드명이 다른 경우 `@JsonProperty`를 생성자 파라미터에 붙여야 한다.

```java
public record CreateUserRequest(
    @JsonProperty("user_name") String name,
    @JsonProperty("user_email") String email
) {
}
```

### 5. 민감 정보 노출

Entity나 내부 객체를 그대로 반환하면 의도하지 않은 필드가 노출될 수 있다.

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

## snake_case ↔ camelCase 전략

외부 API가 snake_case를 사용하는 경우 전역 설정으로 변환할 수 있다.

```yaml
spring:
  jackson:
    property-naming-strategy: SNAKE_CASE
```

또는 특정 클래스에만 적용:

```java
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ExternalApiResponse(String userName, String emailAddress) {
}
// → {"user_name": "...", "email_address": "..."}
```

## 자주 나는 실수

- Entity를 그대로 API 응답으로 반환해서 순환 참조나 민감 정보 노출이 발생한다.
- `LocalDateTime`의 기본 직렬화가 배열인 것을 모르고 프론트엔드와 포맷이 안 맞는다.
- 기본 생성자가 없어서 역직렬화가 실패하는데 원인을 모른다.
- getter가 없어서 직렬화 시 필드가 누락되는데 원인을 모른다.
- enum 대소문자 불일치로 `HttpMessageNotReadableException`이 발생한다.
- `@JsonIgnore`를 getter에만 붙여서 역직렬화에서는 여전히 바인딩된다.
- 외부 API 연동 시 snake_case/camelCase 변환을 필드마다 수동으로 한다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| API 응답 | Entity 직접 반환 금지, DTO(record) 변환 |
| 날짜/시간 | 전역 설정으로 `write-dates-as-timestamps: false` |
| 외부 API 연동 | `@JsonNaming` 또는 `@JsonProperty`로 네이밍 매핑 |
| enum 요청 바인딩 | `accept-case-insensitive-enums: true` 또는 `@JsonCreator` |
| 민감 필드 | DTO 분리가 우선, 부득이하면 `@JsonIgnore` |
| 불변 요청 객체 | record 사용 (Jackson 2.12+) |

## 핵심 요약

Spring Boot에서 API 요청/응답의 JSON 변환은 Jackson이 담당합니다.
직렬화는 getter 기준, 역직렬화는 기본 생성자 + setter 또는 `@JsonCreator` 기준으로 동작합니다.

실무에서 가장 중요한 원칙은 Entity를 API 응답으로 직접 반환하지 않는 것입니다.
순환 참조로 인한 `StackOverflowError`, 민감 정보 노출, lazy loading 문제가 생길 수 있기 때문입니다.
record 기반 DTO로 변환하는 것이 안전합니다.

`LocalDateTime`은 기본적으로 배열로 직렬화되므로 `write-dates-as-timestamps: false` 설정이 필요하고, enum은 대소문자 불일치에 주의해야 합니다.

## 꼬리 질문

> [!question]- Jackson의 직렬화와 역직렬화 기준은 각각 무엇인가?
> 직렬화는 public getter 기준으로 필드를 JSON에 포함하고, 역직렬화는 기본 생성자 + setter 또는 `@JsonCreator`를 통해 객체를 생성합니다.

> [!question]- Entity를 API 응답으로 직접 반환하면 어떤 문제가 생기는가?
> 양방향 연관관계의 순환 참조로 `StackOverflowError`, 민감 정보 노출, lazy loading에 의한 추가 쿼리나 예외가 발생할 수 있습니다.

> [!question]- `@JsonIgnore`를 getter에만 붙이면 어떻게 되는가?
> 직렬화에서는 제외되지만 역직렬화에서는 여전히 바인딩됩니다. 양쪽 모두 제외하려면 필드에 붙이거나 `@JsonProperty(access = WRITE_ONLY)` 등을 사용합니다.

> [!question]- `LocalDateTime`의 기본 직렬화 형태는?
> 배열 형태(`[2024, 1, 15, 10, 30]`)로 직렬화됩니다. `write-dates-as-timestamps: false` 설정으로 ISO-8601 문자열로 변환할 수 있습니다.

> [!question]- record의 역직렬화가 동작하는 원리는?
> Jackson 2.12+에서 record의 canonical constructor를 자동 인식합니다. JSON 필드명이 다르면 생성자 파라미터에 `@JsonProperty`를 붙여야 합니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[class-interface-enum-record]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]