---
title: Validation And Exception Handling
description: Spring의 입력 검증과 예외 처리 전략
---

# Validation And Exception Handling

## 한 줄 정의

Validation은 외부 입력을 시스템 경계에서 검증하는 것이고, 예외 처리는 발생한 예외를 적절한 계층에서 일관된 응답으로 변환하는 것이다.

## 실무에서 왜 중요한가

검증과 예외 처리를 체계적으로 하지 않으면 다음 문제가 생긴다.

- 잘못된 입력이 Service 계층까지 도달해서 예상치 못한 에러가 발생한다.
- API마다 에러 응답 형식이 달라서 클라이언트가 일관된 처리를 할 수 없다.
- 예외를 삼켜서(catch 후 무시) 원인 추적이 불가능하다.
- 모든 메서드에 try-catch를 넣어서 코드가 복잡해진다.
- 검증 에러와 시스템 에러를 구분하지 않는다.

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

### 주요 검증 어노테이션

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

`@Valid`를 중첩 객체 필드에 붙여야 내부 필드도 검증된다.

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

생성과 수정 시 다른 필드를 검증해야 할 때 사용한다. `@Validated`에 그룹을 지정한다.

## 예외 처리 전략

### 계층별 역할

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

모든 API가 동일한 에러 응답 구조를 사용해야 클라이언트가 일관되게 처리할 수 있다.

## 자주 나는 실수

- `@Valid`를 빠뜨려서 검증이 실행되지 않는다.
- 중첩 객체에 `@Valid`를 붙이지 않아서 내부 필드가 검증되지 않는다.
- 예외를 catch하고 로그만 남긴 뒤 무시한다 (예외 삼키기).
- API마다 에러 응답 형식이 달라서 클라이언트가 파싱할 수 없다.
- 비즈니스 예외와 시스템 예외를 구분하지 않고 모두 500으로 응답한다.
- `@ExceptionHandler`의 우선순위(구체적인 예외가 먼저)를 모른다.

## 핵심 요약

입력 검증은 `@Valid`와 Bean Validation으로 Controller 계층에서 처리합니다.
중첩 객체에도 `@Valid`를 붙여야 내부 필드가 검증됩니다.

예외 처리는 `@RestControllerAdvice`에서 글로벌하게 처리하고, 일관된 에러 응답 형식을 사용합니다.
비즈니스 예외는 커스텀 예외와 ErrorCode로 구분하고, 예상치 못한 예외는 로그를 남기고 500으로 응답합니다.

## 꼬리 질문

> [!question]- `@Valid`와 `@Validated`의 차이는?
> `@Valid`는 Java 표준(JSR-303)이고, `@Validated`는 Spring 어노테이션입니다. `@Validated`는 그룹별 검증을 지원합니다. Controller 파라미터에서 그룹이 필요 없으면 둘 다 사용 가능합니다.

> [!question]- 검증 로직을 Service에 넣어야 하는 경우는?
> Bean Validation은 단일 필드의 형식 검증에 적합합니다. "주문 수량이 재고보다 많은지" 같은 비즈니스 규칙 검증은 Service에서 처리해야 합니다. DB 조회가 필요한 검증은 Controller에서 할 수 없습니다.

> [!question]- `@ExceptionHandler`의 우선순위는?
> 구체적인 예외 타입이 우선입니다. `IllegalArgumentException`과 `Exception` 핸들러가 모두 있으면, `IllegalArgumentException`이 발생했을 때 더 구체적인 핸들러가 실행됩니다.

> [!question]- checked 예외와 unchecked 예외 중 어떤 것을 사용하는가?
> Spring에서는 unchecked 예외(RuntimeException)를 주로 사용합니다. checked 예외는 호출부에서 반드시 처리해야 해서 코드가 복잡해지고, `@Transactional`의 기본 롤백 대상도 unchecked 예외입니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[spring-mvc-request-flow]]
- [[transaction-integration]]
- [[01-core/java/exception-handling|exception-handling]]