---
title: 예외 처리 전략과 실무 기준
description: Java 예외 처리 전략과 백엔드 실무 판단 기준
---

# 예외 처리 전략과 실무 기준

## 한 줄 정의

예외 처리는 정상 흐름으로 처리할 수 없는 상황을 중단하고, 의미 있는 방식으로 전파하거나 복구하는 메커니즘이다.

## 실무에서 왜 중요한가

백엔드에서 예외 처리는 단순한 `try-catch` 문법이 아니다.

예외 설계가 어긋나면 장애 원인을 찾기 어렵고, API 에러 응답이 일관되지 않으며, 트랜잭션이 의도와 다르게 커밋될 수 있다. 외부 API, DB, 메시지 처리, 파일 I/O처럼 실패 가능성이 큰 경계에서는 예외 처리 기준이 특히 중요하다.

## 한눈에 보는 판단 기준

| 상황 | 권장 처리 |
|---|---|
| 비즈니스 규칙 위반 | 커스텀 unchecked exception + ErrorCode |
| 입력값 검증 실패 | `@Valid`와 글로벌 예외 핸들러에서 응답 변환 |
| 외부 API 실패 | 로그를 남기고 의미 있는 예외로 변환 |
| 복구할 수 없는 시스템 오류 | 억지로 잡지 말고 상위로 전파 |
| 트랜잭션 롤백이 필요한 checked exception | `rollbackFor` 명시 |

## Checked vs Unchecked

| 구분 | 상위 클래스 | 컴파일러 강제 | 실무 의미 |
|---|---|---|---|
| Checked | `Exception` | O | 호출자가 복구하거나 반드시 처리해야 하는 실패 |
| Unchecked | `RuntimeException` | X | 비즈니스 규칙 위반, 프로그래밍 오류, 복구 어려운 실패 |

Spring 백엔드에서는 대부분의 비즈니스 예외를 unchecked로 만든다.

이유는 간단하다.

- 모든 호출 계층에 `throws`를 강제하지 않는다.
- 실제로 중간 계층에서 복구할 수 있는 경우가 많지 않다.
- `@Transactional`은 기본적으로 unchecked exception에서 롤백한다.

checked exception이 나쁜 것은 아니다. 파일 I/O, 외부 라이브러리, 일부 연동 실패처럼 호출자가 실패를 인지하고 명확히 대응해야 한다면 checked exception도 의미가 있다.

## 커스텀 예외와 ErrorCode

API 서버에서는 예외와 HTTP 응답을 일관되게 연결해야 한다. 보통 `BusinessException`과 `ErrorCode`를 함께 둔다.

```java
public class BusinessException extends RuntimeException {
    private final ErrorCode errorCode;

    public BusinessException(ErrorCode errorCode) {
        super(errorCode.message());
        this.errorCode = errorCode;
    }

    public BusinessException(ErrorCode errorCode, Throwable cause) {
        super(errorCode.message(), cause);
        this.errorCode = errorCode;
    }

    public ErrorCode errorCode() {
        return errorCode;
    }
}
```

```java
public enum ErrorCode {
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자를 찾을 수 없습니다."),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "이미 사용 중인 이메일입니다."),
    EXTERNAL_SERVICE_ERROR(HttpStatus.BAD_GATEWAY, "외부 서비스 호출에 실패했습니다.");

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }

    public HttpStatus status() {
        return status;
    }

    public String message() {
        return message;
    }
}
```

이 구조의 장점은 컨트롤러마다 에러 응답을 직접 만들지 않아도 된다는 점이다. 예외는 비즈니스 의미를 담고, 글로벌 예외 핸들러가 HTTP 응답으로 변환한다.

## 예외를 삼키지 않는다

가장 위험한 코드는 실패를 숨기는 코드다.

```java
try {
    externalApi.call();
} catch (Exception e) {
    // 아무 처리도 하지 않음
}
```

장애 원인도 남지 않고, 호출자는 성공한 것처럼 다음 로직을 실행한다.

최소한 로그를 남기고, 상위 계층이 이해할 수 있는 예외로 변환한다.

```java
try {
    externalApi.call();
} catch (ExternalApiException e) {
    log.error("External API call failed. provider={}, requestId={}", provider, requestId, e);
    throw new BusinessException(ErrorCode.EXTERNAL_SERVICE_ERROR, e);
}
```

예외를 변환할 때는 원본 예외를 `cause`로 넘긴다. 그래야 실제 실패 지점의 stack trace가 보존된다.

## 트랜잭션과 예외

Spring `@Transactional`의 기본 롤백 규칙은 반드시 알아야 한다.

| 예외 종류 | 기본 동작 |
|---|---|
| `RuntimeException` | 롤백 |
| `Error` | 롤백 |
| checked `Exception` | 커밋 |

checked exception에서도 롤백이 필요하면 명시해야 한다.

```java
@Transactional(rollbackFor = IOException.class)
public void importOrders(Path path) throws IOException {
    // 파일 읽기 + DB 저장
}
```

이 규칙을 모르면 예외가 발생했는데도 DB 변경이 커밋되는 버그가 생길 수 있다.

## 글로벌 예외 핸들러

Spring MVC에서는 `@ControllerAdvice`로 API 에러 응답을 한 곳에서 만든다.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException e) {
        ErrorCode errorCode = e.errorCode();

        return ResponseEntity
            .status(errorCode.status())
            .body(new ErrorResponse(errorCode.name(), errorCode.message()));
    }
}
```

컨트롤러는 정상 흐름에 집중하고, 예외 응답 포맷은 핸들러에서 일관되게 관리한다.

## 자주 나는 실수

- catch 블록에서 예외를 삼킨다.
- `Exception`이나 `Throwable`로 모든 예외를 무조건 잡는다.
- 예외를 변환하면서 원본 예외를 `cause`로 넘기지 않는다.
- 프로덕션 코드에서 `e.printStackTrace()`를 사용한다.
- 예외 메시지에 토큰, 비밀번호, 개인정보를 넣는다.
- `@Transactional`에서 checked exception이 기본 롤백되지 않는 것을 모른다.
- 모든 예외를 같은 HTTP 상태 코드로 응답한다.

## 핵심 요약

비즈니스 예외는 보통 unchecked exception으로 만들고, `ErrorCode`와 글로벌 예외 핸들러를 통해 HTTP 응답을 일관되게 만든다.

예외를 잡았다면 숨기지 말고 로그를 남기거나 의미 있는 예외로 변환한다. 변환할 때는 원본 예외를 `cause`로 포함해야 장애 추적이 가능하다.

트랜잭션에서는 unchecked exception은 기본 롤백되지만 checked exception은 기본 커밋된다. checked exception에서도 롤백이 필요하면 `rollbackFor`를 명시한다.

## 꼬리 질문

> [!question]- checked exception과 unchecked exception의 차이는?
> checked exception은 컴파일러가 처리나 전파를 강제합니다. unchecked exception은 강제하지 않으며, Spring 백엔드에서는 비즈니스 예외에 자주 사용합니다.

> [!question]- 실무에서 비즈니스 예외를 unchecked로 많이 만드는 이유는?
> 중간 계층에서 복구할 수 있는 경우가 적고, 모든 계층에 `throws`를 퍼뜨리지 않아도 되며, Spring 트랜잭션 기본 롤백 규칙과도 잘 맞기 때문입니다.

> [!question]- 예외를 변환할 때 cause를 넘겨야 하는 이유는?
> 원본 stack trace를 보존해야 실제 장애 발생 지점을 추적할 수 있기 때문입니다.

> [!question]- `@Transactional`에서 checked exception이 발생하면 기본적으로 어떻게 되는가?
> 기본적으로 롤백하지 않고 커밋됩니다. 롤백이 필요하면 `rollbackFor`를 명시해야 합니다.

> [!question]- 글로벌 예외 핸들러의 역할은?
> 컨트롤러에서 발생한 예외를 한 곳에서 HTTP 상태 코드와 에러 응답으로 변환해 API 응답 형식을 일관되게 만드는 것입니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[02-practical-backend/transaction/transaction|transaction]]
