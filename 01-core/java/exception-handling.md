---
title: 예외 처리 전략과 실무 기준
description: Java 예외 처리 전략과 백엔드 실무 판단 기준
---

# 예외 처리 전략과 실무 기준

예외 처리는 정상 흐름으로 처리할 수 없는 상황에서 실행을 멈추고, 그 실패를 의미 있게 전파하거나 복구하는 장치다. `try-catch`는 오류를 없애는 문법이 아니라, 실패했을 때 복구할지·기본값을 쓸지·재시도할지·기록하고 계속할지·위로 넘길지를 정하는 자리다.

예외 설계가 어긋나면 장애 원인을 찾기 어렵고, API 에러 응답이 제각각이 되고, 트랜잭션이 의도와 다르게 커밋된다. 외부 API, DB, 메시지 처리, 파일 I/O처럼 실패가 잦은 경계일수록 기준이 필요하다. 예외를 잡는 목적은 프로그램을 계속 돌리는 게 아니라, 현재 계층이 책임질 수 있는 방식으로 실패를 처리하는 것이다. 복구할 수 없으면 잡지 말고 위로 넘긴다.

## 상황별로 어떻게 처리하나

| 상황 | 처리 |
|---|---|
| 비즈니스 규칙 위반 | 커스텀 unchecked exception + ErrorCode |
| 입력값 검증 실패 | `@Valid`와 글로벌 예외 핸들러에서 응답 변환 |
| 외부 API 실패 | 의미 있는 예외로 변환하고 처리 경계에서 로깅 |
| 복구할 수 없는 시스템 오류 | 잡지 말고 위로 전파 |
| 트랜잭션 롤백이 필요한 checked exception | `rollbackFor` 명시 |

## try-catch는 언제 쓰나

현재 계층에서 실패에 대해 구체적으로 할 일이 있을 때만 쓴다.

- 외부 API, 결제, 이메일·SMS, 외부 SDK 호출 실패를 도메인 의미가 있는 예외로 바꾼다.
- 파일 읽기·쓰기나 JSON 파싱 실패에 대체 값이나 명확한 중단 기준을 적용한다.
- 선택적인 부가 기능의 실패를 기록하고 핵심 흐름은 계속 간다.
- 배치나 메시지 처리에서 한 건의 실패를 격리하고 다음 건으로 넘어간다.
- 자원을 직접 다룰 때 정리 작업을 보장한다. 되도록 `try-with-resources`를 쓴다.

DB 접근처럼 프레임워크가 이미 예외를 변환해 주는 곳은 모든 호출을 습관적으로 감싸지 않는다. 중복 키를 비즈니스 예외로 바꾸는 것처럼 이 계층에서 의미 있는 처리가 있을 때만 잡는다.

반대로 아래는 `try-catch`가 아니라 정상 제어 흐름으로 처리한다.

- 입력값과 비즈니스 조건은 `if`, Bean Validation 등으로 명시적으로 검사한다.
- 단순 계산이나 일반 변수 접근을 예외로 제어하지 않는다.
- `NullPointerException` 같은 프로그래밍 오류를 잡아 정상인 척하지 않는다.

예외를 분기 수단으로 쓰면 실제 장애와 예상 가능한 조건이 섞여서 구분이 안 되고, 흐름을 읽는 비용도 커진다.

## 실패의 무게에 따라 다르게 처리한다

### 핵심 기능이 실패하면 전파한다

주문 저장이나 결제 승인처럼 요청의 목적 자체를 못 이루는 실패는 위로 넘긴다. 외부 시스템 예외는 현재 서비스가 이해하는 예외로 바꾸되, 원본 예외를 `cause`로 남긴다.

```java
try {
    paymentClient.approve(command);
} catch (PaymentClientException e) {
    throw new PaymentProcessingException("Payment approval failed", e);
}
```

### 부가 기능이 실패하면 기록하고 계속한다

알림 발송처럼 핵심 결과와 떼어 낼 수 있는 작업은 실패를 기록하고 핵심 흐름을 이어 간다. 다만 그 작업을 잃어도 되는지 먼저 정한다. 유실이 안 되면 로그만 남기지 말고 이벤트나 재처리 큐를 쓴다.

```java
try {
    notificationSender.sendOrderCompleted(orderId);
} catch (NotificationException e) {
    log.warn("Order notification failed. orderId={}", orderId, e);
}
```

### 기본값으로 복구한다

기본값은 그 값이 없어도 결과가 틀리거나 위험해지지 않을 때만 쓴다. 외부 API 실패를 무조건 `null`로 바꾸면 실패와 실제로 데이터가 없는 경우를 구분할 수 없다.

```java
try {
    return recommendationClient.getRecommendations(userId);
} catch (RecommendationException e) {
    log.warn("Recommendation lookup failed. userId={}", userId, e);
    return List.of();
}
```

기본값이 결과를 왜곡한다면 복구하지 말고 전파한다.

### 재시도한다

재시도는 타임아웃이나 일시적인 네트워크 실패처럼 다시 하면 성공할 가능성이 있을 때만 한다. 잘못된 요청, 인증 실패, 비즈니스 규칙 위반은 재시도하지 않는다. 같은 요청이 두 번 가도 안전하도록 멱등성을 갖추고, 횟수와 대기 시간에 상한을 둔다.

`try-catch`와 반복문을 직접 엮기보다 Spring Retry나 Resilience4j 같은 검증된 도구를 먼저 쓴다.

## InterruptedException

`InterruptedException`은 작업 실패가 아니라 스레드에 "멈춰 달라"는 신호다. 잡고 계속 실행하면 취소나 애플리케이션 종료가 늦어진다.

그대로 던질 수 없는 계층이라면 인터럽트 상태를 복원한 뒤 의미 있는 예외로 바꾼다.

```java
try {
    return blockingQueue.take();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new TaskExecutionException("Task interrupted", e);
}
```

빈 `catch`로 삼키거나, 인터럽트 상태를 복원하지 않은 채 일반 실패처럼 처리하지 않는다.

## Checked와 Unchecked

| 구분 | 상위 클래스 | 컴파일러 강제 | 실무 의미 |
|---|---|---|---|
| Checked | `Exception` 중 `RuntimeException`을 제외한 타입 | O | 호출자가 복구하거나 꼭 처리해야 하는 실패 |
| Unchecked | `RuntimeException`, `Error` | X | 비즈니스 규칙 위반, 프로그래밍 오류, 복구가 어려운 시스템 실패 |

Spring 백엔드에서는 비즈니스 예외를 대부분 unchecked로 만든다.

- 모든 호출 계층에 `throws`를 강제하지 않는다.
- 중간 계층에서 실제로 복구하는 경우가 많지 않다.
- `@Transactional`은 기본적으로 `RuntimeException`과 `Error`에서 롤백한다.

checked exception이 나쁜 건 아니다. 파일 I/O, 외부 라이브러리, 일부 연동 실패처럼 호출자가 실패를 알고 대응해야 하는 경우에는 checked가 맞다.

## 커스텀 예외와 ErrorCode

API 서버는 예외와 HTTP 응답을 일관되게 연결해야 한다. 보통 `BusinessException`과 `ErrorCode`를 같이 둔다.

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

예외는 비즈니스 의미를 담고, HTTP 응답 변환은 글로벌 예외 핸들러가 맡는다. 그래서 컨트롤러마다 에러 응답을 만들 필요가 없다.

## 예외를 삼키지 않는다

가장 위험한 코드는 실패를 숨기는 코드다.

```java
try {
    externalApi.call();
} catch (Exception e) {
    // 아무 처리도 하지 않음
}
```

장애 원인도 남지 않고, 호출자는 성공한 줄 알고 다음 로직을 실행한다. 복구할 수 없으면 상위 계층이 이해하는 예외로 바꿔 던진다.

```java
try {
    externalApi.call();
} catch (ExternalApiException e) {
    throw new BusinessException(ErrorCode.EXTERNAL_SERVICE_ERROR, e);
}
```

바꿀 때는 원본 예외를 `cause`로 넘긴다. 그래야 실제 실패 지점의 stack trace가 남는다.

로깅은 한 번만 한다. 같은 예외를 여러 계층에서 찍으면 실패 하나가 장애 여러 건처럼 보인다. 예외를 처리하고 흐름을 이어 가는 지점이나 글로벌 예외 핸들러 같은 최종 경계에서 한 번 남기는 게 기본이다. 비즈니스 규칙 위반처럼 예상 가능한 예외는 로그 레벨을 낮추거나 아예 남기지 않아도 된다.

## 트랜잭션과 예외

Spring `@Transactional`의 기본 롤백 규칙은 이렇다.

| 예외 종류 | 기본 동작 |
|---|---|
| `RuntimeException` | 롤백 |
| `Error` | 롤백 |
| checked `Exception` | 커밋 |

checked exception에서도 롤백하려면 명시한다. 모르면 예외가 났는데 DB 변경이 커밋되는 버그가 생긴다.

```java
@Transactional(rollbackFor = IOException.class)
public void importOrders(Path path) throws IOException {
    // 파일 읽기 + DB 저장
}
```

`@Transactional` 메서드 안에서 예외를 잡고 정상 반환하면, Spring 프록시는 예외를 보지 못해 롤백하지 않는다. 롤백이 필요한 실패는 다시 던지는 게 기본이다.

```java
@Transactional
public void processOrder() {
    try {
        orderRepository.save(order);
    } catch (DataAccessException e) {
        throw new OrderPersistenceException("Order save failed", e);
    }
}
```

예외를 밖으로 던질 수 없는데 꼭 롤백해야 하는 특별한 경우에는 rollback-only로 표시한다.

```java
catch (DataAccessException e) {
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    return;
}
```

rollback-only는 호출자에게 실패가 전달되지 않으므로 제한적으로만 쓴다. 되도록 예외를 다시 던져 실패와 롤백을 함께 전한다. 자세한 함정은 [[transactional-pitfalls]]에 있다.

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

컨트롤러는 정상 흐름만 다루고, 에러 응답 형식은 핸들러 한 곳에서 관리한다.

## 자주 깨지는 곳

- **catch에서 예외를 삼킨다.** 원인이 사라지고 호출자는 성공으로 착각한다.
- **`Exception`이나 `Throwable`로 전부 잡는다.** 복구할 수 없는 오류까지 정상 흐름에 섞인다.
- **변환하면서 `cause`를 빠뜨린다.** 원래 실패 지점의 stack trace가 없어진다.
- **프로덕션 코드에서 `e.printStackTrace()`를 쓴다.** 로그 체계 밖으로 출력돼 추적이 안 된다.
- **예외 메시지에 토큰, 비밀번호, 개인정보를 넣는다.** 로그와 응답으로 그대로 새어 나간다.
- **checked exception이 기본으로 롤백되지 않는다는 걸 모른다.** 실패했는데 DB 변경이 커밋된다.
- **모든 예외를 같은 HTTP 상태 코드로 응답한다.** 클라이언트가 재시도할지 고칠지 판단하지 못한다.

## 면접에서 말하기

> 저는 예외를 잡을 때 이 계층에서 복구하거나 의미를 바꿀 수 있는지를 먼저 봅니다. 비즈니스 예외는 unchecked로 만들고 ErrorCode와 글로벌 예외 핸들러로 HTTP 응답을 일관되게 맞춥니다. 잡은 예외는 숨기지 않고 의미 있는 예외로 바꾸되 원본을 cause로 넘겨 추적이 되게 합니다. 트랜잭션에서는 checked exception이 기본으로 커밋된다는 점을 알고, 롤백이 필요하면 rollbackFor를 명시합니다.

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

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>외부 API 호출 실패를 현재 계층에서 복구할 수 없다. 어떻게 처리하나?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="실패를 null로 바꾸면 호출자가 실제 데이터 부재와 장애를 구분하기 어렵다." aria-pressed="false">A. null을 반환하고 호출자가 알아서 처리하게 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="현재 서비스의 예외로 바꾸고, 원본 예외는 cause로 남긴다." aria-pressed="false">B. 의미 있는 예외로 변환하고 원본 예외를 cause로 포함해 상위로 전파한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 실패를 잡아 성공처럼 처리하면 장애 원인을 숨기고 잘못된 후속 처리를 만들 수 있다." aria-pressed="false">C. Exception으로 모두 잡고 정상 응답을 반환한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>비즈니스 조건 검사는 try-catch보다 if문이나 Bean Validation으로 드러내는 편이 읽기 쉽다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="예상 가능한 조건은 예외가 아니라 정상적인 제어 흐름으로 표현해야 장애와 분기 조건을 구분하기 쉽다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="예외를 일반 분기처럼 쓰면 흐름 이해 비용이 커지고 실제 장애와 조건 검사가 섞인다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Transactional 메서드에서 checked exception이 발생했을 때 Spring의 기본 동작은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring은 기본적으로 모든 Exception을 롤백하지 않는다. checked exception은 별도 설정이 필요하다." aria-pressed="false">A. 모든 Exception이므로 자동 롤백된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="기본 롤백 대상은 RuntimeException과 Error다. checked exception 롤백은 rollbackFor를 명시해야 한다." aria-pressed="false">B. 기본적으로 커밋되며, 롤백이 필요하면 rollbackFor를 명시한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="try-catch를 썼는지가 아니라, 트랜잭션 프록시 밖으로 어떤 예외가 나가는지가 롤백을 정한다." aria-pressed="false">C. try-catch를 사용한 경우에만 롤백된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>예외를 다른 예외로 변환할 때 원본 예외를 cause로 넘기지 않아도 메시지만 있으면 장애 추적에는 충분하다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="메시지만 남기면 실제 실패 지점의 stack trace가 끊긴다. 원본 예외를 cause로 보존해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="원본 stack trace를 보존해야 장애 발생 지점과 호출 경로를 추적할 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>InterruptedException을 catch한 뒤 현재 계층에서 그대로 throws 할 수 없다. 놓치기 쉬운 핵심 처리는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="인터럽트는 중단 요청 신호이므로 Thread.currentThread().interrupt()로 상태를 복원한 뒤 의미 있는 예외로 변환한다." aria-pressed="false">A. 인터럽트 상태를 복원하고 의미 있는 예외로 변환한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="빈 catch 블록은 중단 요청을 삼켜 애플리케이션 종료나 취소 처리를 지연시킬 수 있다." aria-pressed="false">B. 종료 중에도 안전하도록 catch 블록을 비워 둔다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="RuntimeException으로 바꾸더라도 인터럽트 상태를 복원하지 않으면 중단 신호가 사라질 수 있다." aria-pressed="false">C. RuntimeException으로만 감싸면 충분하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>같은 예외를 여러 계층에서 반복해서 로깅하면 장애 추적에 항상 도움이 된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="중복 로깅은 하나의 실패를 여러 장애처럼 보이게 할 수 있다. 보통 처리 경계나 글로벌 핸들러에서 한 번 남긴다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="예외를 처리하는 최종 경계에서 한 번 로깅하는 것이 기본이며, 예상 가능한 비즈니스 예외는 낮은 레벨을 쓴다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[02-practical-backend/transaction/transaction|transaction]]
