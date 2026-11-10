---
title: 요청 검증과 예외 처리
description: Spring의 입력 검증과 예외 처리 전략
---

# 요청 검증과 예외 처리

Validation은 외부 입력을 시스템 경계에서 걸러 내는 일이고, 예외 처리는 이미 난 예외를 맞는 계층에서 일관된 응답으로 바꾸는 일이다.

둘 다 빠지면 증상이 비슷하다. 잘못된 입력이 Service까지 들어와 엉뚱한 곳에서 터지고, API마다 에러 응답 모양이 달라 클라이언트가 처리를 통일하지 못한다. 반대로 메서드마다 try-catch를 넣으면 코드만 복잡해지고, catch 후 무시한 예외는 원인 추적을 끊는다. 검증 에러와 시스템 에러를 구분하는 것부터 시작한다.

## Bean Validation

### 기본 사용

```java
public class OrderRequest {

    @NotBlank(message = "상품명은 필수입니다")
    private String productName;

    @Min(value = 1, message = "수량은 1 이상이어야 합니다")
    private int quantity;

    @NotNull(message = "배송 주소는 필수입니다")
    private Address address;
}
```

```java
@RestController
public class OrderController {

    @PostMapping("/api/orders")
    public ResponseEntity<OrderResponse> createOrder(@Valid @RequestBody OrderRequest request) {
        // @Valid가 있으면 Bean Validation 자동 실행
        // 검증 실패 시 MethodArgumentNotValidException 발생
        return ResponseEntity.ok(orderService.createOrder(request));
    }
}
```

### 자주 쓰는 어노테이션

| 어노테이션 | 용도 |
|---|---|
| `@NotNull` | null 불가 |
| `@NotBlank` | null, 빈 문자열, 공백 불가 (String 전용) |
| `@NotEmpty` | null, 빈 값 불가 (String, Collection) |
| `@Size(min, max)` | 길이/크기 범위 |
| `@Min`, `@Max` | 숫자 최소/최대 |
| `@Email` | 이메일 형식 |
| `@Pattern(regexp)` | 정규식 패턴 |

### 중첩 객체 검증

```java
public class OrderRequest {

    @Valid // 중첩 객체도 검증하려면 @Valid 필요
    @NotNull
    private Address address;
}
```

중첩 객체 필드에 `@Valid`가 없으면 그 안의 필드는 검증되지 않는다.

### 그룹별 검증

```java
public class UserRequest {

    @NotBlank(groups = Create.class)
    private String name;

    @NotBlank(groups = Update.class)
    private String nickname;

    public interface Create {}
    public interface Update {}
}
```

```java
@PostMapping
public ResponseEntity<?> create(@Validated(Create.class) @RequestBody UserRequest request) { }
```

생성과 수정에서 검증할 필드가 다를 때 쓴다. 그룹은 `@Validated`에 지정한다.

## 예외 처리

### 계층별로 무엇을 던지나

```
Controller    → 입력 검증 예외, 요청 형식 오류
Service       → 비즈니스 규칙 위반 (잔액 부족, 중복 주문 등)
Repository    → 데이터 접근 예외
Global        → @RestControllerAdvice에서 일관된 응답 변환
```

### 커스텀 비즈니스 예외

```java
public class BusinessException extends RuntimeException {

    private final ErrorCode errorCode;

    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}

public enum ErrorCode {

    ORDER_NOT_FOUND("주문을 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    INSUFFICIENT_BALANCE("잔액이 부족합니다", HttpStatus.BAD_REQUEST),
    DUPLICATE_ORDER("중복 주문입니다", HttpStatus.CONFLICT);

    private final String message;
    private final HttpStatus status;

    // constructor, getters
}
```

### 글로벌 예외 핸들러

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    // Bean Validation 실패
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));

        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", message));
    }

    // 비즈니스 예외
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusiness(BusinessException e) {
        ErrorCode code = e.getErrorCode();
        return ResponseEntity.status(code.getStatus())
            .body(new ErrorResponse(code.name(), code.getMessage()));
    }

    // 예상치 못한 예외
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity.internalServerError()
            .body(new ErrorResponse("INTERNAL_ERROR", "서버 오류가 발생했습니다."));
    }
}
```

### 일관된 에러 응답 형식

```java
public record ErrorResponse(String code, String message) { }
```

```json
{
    "code": "ORDER_NOT_FOUND",
    "message": "주문을 찾을 수 없습니다"
}
```

모든 API가 같은 에러 응답 구조를 써야 클라이언트가 한 가지 방식으로 처리할 수 있다.

## 자주 깨지는 곳

- **`@Valid`를 빠뜨린다.** 검증 어노테이션이 있어도 실행되지 않는다.
- **중첩 객체에 `@Valid`를 붙이지 않는다.** 내부 필드가 검증되지 않는다.
- **예외를 catch하고 로그만 남긴다.** 예외가 삼켜져 호출자는 실패를 모른다.
- **API마다 에러 응답 형식이 다르다.** 클라이언트가 파싱할 수 없다.
- **비즈니스 예외와 시스템 예외를 구분하지 않는다.** 잔액 부족도 500으로 나간다.
- **`@ExceptionHandler` 우선순위를 모른다.** 구체적인 예외 타입 핸들러가 먼저 선택된다.

## 면접에서 말하기

> 입력 검증은 Controller 계층에서 `@Valid`와 Bean Validation으로 하고, 중첩 객체에도 `@Valid`를 붙입니다. 재고 확인처럼 DB가 필요한 비즈니스 규칙은 Service에서 검증합니다. 예외는 `@RestControllerAdvice` 한곳에서 일관된 형식으로 바꿉니다. 비즈니스 예외는 커스텀 예외와 ErrorCode로 상태 코드를 나누고, 예상하지 못한 예외는 로그를 남긴 뒤 500으로 응답합니다.

## 꼬리 질문

> [!question]- `@Valid`와 `@Validated`의 차이는?
> `@Valid`는 Java 표준(JSR-303)이고, `@Validated`는 Spring 어노테이션입니다. `@Validated`는 그룹별 검증을 지원합니다. Controller 파라미터에서 그룹이 필요 없으면 어느 쪽을 써도 됩니다.

> [!question]- 검증 로직을 Service에 넣어야 하는 경우는?
> Bean Validation은 필드 하나의 형식 검증용입니다. "주문 수량이 재고보다 많은지" 같은 비즈니스 규칙은 Service에서 검증합니다. DB 조회가 필요한 검증은 Controller에서 할 수 없습니다.

> [!question]- `@ExceptionHandler`의 우선순위는?
> 구체적인 예외 타입이 우선입니다. `IllegalArgumentException`과 `Exception` 핸들러가 모두 있으면, `IllegalArgumentException`이 발생했을 때 더 구체적인 핸들러가 실행됩니다.

> [!question]- checked 예외와 unchecked 예외 중 어떤 것을 사용하는가?
> Spring에서는 주로 unchecked 예외(RuntimeException)를 씁니다. checked 예외는 호출부가 꼭 처리해야 해서 코드가 복잡해지고, `@Transactional`의 기본 롤백 대상도 unchecked 예외입니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Valid와 @Validated의 차이로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="@Validated는 Spring의 검증 애노테이션으로 validation group 지정 등 Spring 기능과 함께 쓰인다." aria-pressed="false">A. @Validated는 validation group 같은 Spring 검증 기능에 유용하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@Valid도 요청 DTO 검증에 사용할 수 있다." aria-pressed="false">B. @Valid는 DTO 검증에 사용할 수 없다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 예외를 제거하는 문법은 아니다." aria-pressed="false">C. @Validated를 쓰면 예외 처리가 필요 없어졌다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>모든 검증 로직은 DTO 애노테이션으로만 처리해야 하고 Service에서는 절대 검증하면 안 된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="형식 검증은 DTO에서, DB 조회나 도메인 상태가 필요한 비즈니스 검증은 Service/Domain에서 처리하는 것이 자연스럽다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="검증 위치는 단순 입력 형식인지 비즈니스 규칙인지에 따라 나뉜다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>글로벌 예외 핸들러를 설계할 때 정할 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="예외 종류를 HTTP 상태 코드와 일관된 에러 응답으로 변환하고, 민감 정보는 응답에 노출하지 않는다." aria-pressed="false">A. 예외를 일관된 상태 코드/응답으로 변환하고 민감 정보 노출을 막는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 예외를 200으로 응답하면 클라이언트와 모니터링이 실패를 인식하기 어렵다." aria-pressed="false">B. 모든 예외를 HTTP 200으로 반환한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="스택트레이스를 응답으로 노출하면 보안 위험이 있다." aria-pressed="false">C. 운영에서도 stack trace 전체를 사용자에게 반환한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[spring-mvc-request-flow]]
- [[transaction-integration]]
- [[01-core/java/exception-handling|exception-handling]]