---
title: Exception Handling
description: Java 예외 처리 전략과 실무에서의 설계 판단
---

# Exception Handling

## 한 줄 정의

예외 처리는 프로그램 실행 중 발생하는 비정상 상황을 코드 흐름으로 제어하는 메커니즘이다.

## 실무에서 왜 중요한가

예외 처리는 문법 수준에서 끝나는 주제가 아니다. 실무에서는 다음 문제를 자주 마주한다.

- catch 블록에서 예외를 삼켜서 장애 원인을 찾지 못한다.
- checked exception을 무의미하게 throws로 전파해서 호출부가 복잡해진다.
- 커스텀 예외를 만들었지만 HTTP 상태 코드와 매핑이 뒤섞인다.
- 트랜잭션 경계에서 예외 종류에 따라 롤백 여부가 달라지는 것을 모르고 버그가 생긴다.
- 외부 API 호출 실패를 어디서 잡고 어디까지 전파할지 기준이 없다.

## Checked vs Unchecked 실무 판단

Java는 checked exception과 unchecked exception을 구분한다.

| 구분 | 상위 클래스 | 컴파일러 강제 | 실무에서의 의미 |
|---|---|---|---|
| Checked | `Exception` | O | 호출자가 반드시 처리해야 하는 복구 가능한 상황 |
| Unchecked | `RuntimeException` | X | 프로그래밍 오류이거나 호출자가 처리할 수 없는 상황 |

실무에서는 대부분의 비즈니스 예외를 unchecked로 만드는 경향이 강하다.

이유는 다음과 같다.

- checked exception은 모든 호출 계층에 throws 선언을 강제해서 코드가 장황해진다.
- Spring의 `@Transactional`은 기본적으로 unchecked exception에서만 롤백한다.
- 실제로 catch해서 복구할 수 있는 상황은 많지 않다.

단, 외부 시스템 연동이나 파일 I/O처럼 호출자가 실패를 인지하고 대응해야 하는 경우에는 checked exception이 적절할 수 있다.

## 커스텀 예외 설계

실무에서 예외 클래스를 설계할 때 자주 사용하는 패턴이다.

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
```

```java
public enum ErrorCode {

    USER_NOT_FOUND("사용자를 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    DUPLICATE_EMAIL("이미 사용 중인 이메일입니다", HttpStatus.CONFLICT),
    INSUFFICIENT_BALANCE("잔액이 부족합니다", HttpStatus.BAD_REQUEST);

    private final String message;
    private final HttpStatus httpStatus;

    ErrorCode(String message, HttpStatus httpStatus) {
        this.message = message;
        this.httpStatus = httpStatus;
    }

    // getter 생략
}
```

이렇게 하면 예외 발생 시 HTTP 상태 코드와 메시지를 일관되게 관리할 수 있다.

## 예외를 삼키면 안 되는 이유

```java
// 장애 원인을 숨기는 코드
try {
    externalApi.call();
} catch (Exception e) {
    // 아무것도 하지 않음
}
```

이 코드는 외부 API가 실패해도 아무 로그가 남지 않아 장애 원인 추적이 불가능하다.

최소한 로그를 남기거나, 의미 있는 예외로 변환해서 상위로 전파해야 한다.

```java
try {
    externalApi.call();
} catch (ExternalApiException e) {
    log.error("외부 API 호출 실패: {}", e.getMessage(), e);
    throw new BusinessException(ErrorCode.EXTERNAL_SERVICE_ERROR);
}
```

## Spring @Transactional과 예외의 관계

| 예외 종류 | 기본 롤백 여부 |
|---|---|
| Unchecked (`RuntimeException`) | 롤백 |
| Checked (`Exception`) | 커밋 |
| `Error` | 롤백 |

checked exception에서도 롤백이 필요하면 `@Transactional(rollbackFor = Exception.class)`를 명시해야 한다.

이 규칙을 모르면 checked exception이 발생했는데 데이터가 커밋되는 버그가 생긴다.

## 자주 나는 실수

- catch 블록에서 예외를 삼키고 아무 처리도 하지 않는다.
- `Exception`이나 `Throwable`로 모든 예외를 한꺼번에 잡는다.
- 예외 메시지에 민감 정보(비밀번호, 토큰)를 포함한다.
- `e.printStackTrace()`를 프로덕션 코드에서 사용한다.
- 예외를 변환할 때 원본 예외를 cause로 넘기지 않아서 stack trace가 끊긴다.
- `@Transactional` 메서드 안에서 checked exception을 던졌는데 롤백이 안 되는 것을 모른다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| 비즈니스 규칙 위반 | 커스텀 unchecked exception + ErrorCode |
| 외부 API 실패 | catch 후 로그 + 의미 있는 예외로 변환 |
| 입력값 검증 실패 | `@Valid` + `MethodArgumentNotValidException` 활용 |
| 복구 불가능한 시스템 오류 | 잡지 말고 전파, 글로벌 핸들러에서 처리 |
| 트랜잭션 롤백이 필요한 checked exception | `rollbackFor` 명시 |

## 핵심 요약

Java 예외는 checked와 unchecked로 나뉘는데, 실무에서는 대부분의 비즈니스 예외를 unchecked로 만듭니다.
checked exception은 모든 호출 계층에 throws를 강제해서 코드가 장황해지고, Spring의 `@Transactional`이 기본적으로 unchecked에서만 롤백하기 때문입니다.

커스텀 예외를 설계할 때는 ErrorCode enum과 함께 사용해서 HTTP 상태 코드와 메시지를 일관되게 관리합니다.

가장 주의할 점은 예외를 삼키지 않는 것과, 예외 변환 시 원본 cause를 반드시 포함하는 것입니다.
트랜잭션 경계에서는 checked exception이 기본적으로 롤백을 유발하지 않으므로 `rollbackFor`를 명시해야 하는 상황을 인지하고 있어야 합니다.

## 꼬리 질문

> [!question]- checked exception과 unchecked exception의 차이는 무엇인가?
> checked는 `Exception`을 상속하며 컴파일러가 처리를 강제합니다. unchecked는 `RuntimeException`을 상속하며 처리를 강제하지 않습니다.

> [!question]- 실무에서 checked exception보다 unchecked exception을 선호하는 이유는?
> checked는 모든 호출 계층에 throws를 강제해서 코드가 장황해지고, 실제로 catch해서 복구할 수 있는 상황이 많지 않기 때문입니다.

> [!question]- Spring `@Transactional`에서 checked exception이 발생하면 어떻게 되는가?
> 기본적으로 롤백하지 않고 커밋합니다. 롤백이 필요하면 `@Transactional(rollbackFor = Exception.class)`를 명시해야 합니다.

> [!question]- 예외를 변환할 때 cause를 넘기지 않으면 어떤 문제가 생기는가?
> 원본 예외의 stack trace가 유실되어 실제 장애 발생 지점을 추적할 수 없게 됩니다. `new BusinessException(errorCode, e)`처럼 cause를 포함해야 합니다.

> [!question]- 글로벌 예외 핸들러(`@ControllerAdvice`)는 어떤 역할을 하는가?
> 컨트롤러에서 발생한 예외를 한 곳에서 잡아 일관된 에러 응답(HTTP 상태 코드, 메시지)으로 변환합니다. 각 컨트롤러에서 try-catch를 반복하지 않아도 됩니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[02-practical-backend/transaction/transaction|transaction]]