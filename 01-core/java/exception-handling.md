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

`try-catch`는 오류를 없애는 문법이 아니다. 실패가 발생했을 때 복구할지, 기본값을 사용할지, 재시도할지, 기록한 뒤 계속할지, 상위 계층으로 전달할지를 결정하는 구조다.

예외를 잡는 목적은 프로그램을 무조건 계속 실행하는 것이 아니라, 현재 계층이 책임질 수 있는 방식으로 실패를 안전하게 처리하는 데 있다. 복구할 수 없다면 억지로 잡지 말고 상위로 전파해야 한다.

## 한눈에 보는 판단 기준

| 상황 | 권장 처리 |
|---|---|
| 비즈니스 규칙 위반 | 커스텀 unchecked exception + ErrorCode |
| 입력값 검증 실패 | `@Valid`와 글로벌 예외 핸들러에서 응답 변환 |
| 외부 API 실패 | 의미 있는 예외로 변환하고 처리 경계에서 로깅 |
| 복구할 수 없는 시스템 오류 | 억지로 잡지 말고 상위로 전파 |
| 트랜잭션 롤백이 필요한 checked exception | `rollbackFor` 명시 |

## try-catch를 사용하는 기준

`try-catch`는 현재 계층에서 실패에 대한 구체적인 조치를 할 수 있을 때 사용한다.

- 외부 API, 결제, 이메일·SMS, 외부 SDK 호출 실패를 도메인 의미가 있는 예외로 변환한다.
- 파일 읽기·쓰기나 JSON 파싱 실패에 대체 값 또는 명확한 중단 기준을 적용한다.
- 선택적인 부가 기능의 실패를 기록하고 핵심 흐름은 계속 진행한다.
- 배치나 메시지 처리에서 한 건의 실패를 격리하고 다음 건을 처리한다.
- 자원을 직접 다룰 때 정리 작업을 보장한다. 가능하면 `try-with-resources`를 사용한다.

DB 접근처럼 프레임워크가 이미 예외를 변환해 주는 영역은 모든 호출을 습관적으로 감싸지 않는다. 중복 키를 비즈니스 예외로 바꾸는 등 현재 계층에서 의미 있는 처리가 가능할 때만 잡는다.

다음 상황은 보통 `try-catch`보다 정상적인 제어 흐름으로 처리한다.

- 입력값과 비즈니스 조건 검사는 `if`, Bean Validation 등으로 명시한다.
- 단순 계산이나 일반적인 변수 접근을 예외로 제어하지 않는다.
- `NullPointerException` 같은 프로그래밍 오류를 잡아 정상 상태처럼 위장하지 않는다.

예외를 정상적인 분기 수단으로 남용하면 실제 장애와 예상 가능한 조건을 구분하기 어렵고, 흐름을 이해하는 비용도 커진다.

## 실패 중요도에 따른 처리 패턴

### 핵심 기능의 실패

주문 저장이나 결제 승인처럼 요청의 목적을 달성할 수 없는 실패는 상위로 전파한다. 외부 시스템 예외는 현재 서비스가 이해할 수 있는 예외로 변환하되, 원본 예외를 `cause`로 보존한다.

```java
try {
    paymentClient.approve(command);
} catch (PaymentClientException e) {
    throw new PaymentProcessingException("Payment approval failed", e);
}
```

### 선택적인 부가 기능의 실패

알림 발송처럼 핵심 결과와 분리할 수 있는 작업은 실패를 기록한 뒤 핵심 흐름을 계속할 수 있다. 단, 실패한 작업을 잃어도 되는지 먼저 결정해야 한다. 유실이 허용되지 않으면 단순히 로그만 남기지 말고 이벤트나 재처리 큐를 사용한다.

```java
try {
    notificationSender.sendOrderCompleted(orderId);
} catch (NotificationException e) {
    log.warn("Order notification failed. orderId={}", orderId, e);
}
```

### 기본값으로 복구

기본값은 해당 값이 없어도 결과의 정확성과 안전성이 훼손되지 않을 때만 사용한다. 외부 API 실패를 무조건 `null`로 바꾸면 실패와 실제 데이터 부재를 구분하기 어려우므로 피한다.

```java
try {
    return recommendationClient.getRecommendations(userId);
} catch (RecommendationException e) {
    log.warn("Recommendation lookup failed. userId={}", userId, e);
    return List.of();
}
```

기본값이 결과를 왜곡할 수 있다면 복구하지 말고 예외를 전파한다.

### 재시도

재시도는 타임아웃이나 일시적인 네트워크 실패처럼 다시 시도하면 성공할 가능성이 있는 경우에만 적용한다. 잘못된 요청, 인증 실패, 비즈니스 규칙 위반에는 재시도하지 않는다. 중복 요청이 발생해도 안전하도록 멱등성을 확보하고, 재시도 횟수와 대기 시간을 제한해야 한다.

직접 `try-catch`와 반복문을 조합하기보다 Spring Retry나 Resilience4j 같은 검증된 도구를 우선 고려한다.

## InterruptedException 처리

`InterruptedException`은 단순한 작업 실패가 아니라 스레드에 중단을 요청하는 신호다. 예외를 잡고 계속 실행하면 취소나 애플리케이션 종료가 지연될 수 있다.

현재 계층에서 예외를 그대로 전파할 수 없다면 인터럽트 상태를 복원한 뒤 의미 있는 예외로 변환한다.

```java
try {
    return blockingQueue.take();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new TaskExecutionException("Task interrupted", e);
}
```

`InterruptedException`을 빈 `catch` 블록으로 삼키거나, 인터럽트 상태를 복원하지 않은 채 일반 실패처럼 처리하지 않는다.

## Checked vs Unchecked

| 구분 | 상위 클래스 | 컴파일러 강제 | 실무 의미 |
|---|---|---|---|
| Checked | `Exception` 중 `RuntimeException`을 제외한 타입 | O | 호출자가 복구하거나 반드시 처리해야 하는 실패 |
| Unchecked | `RuntimeException`, `Error` | X | 비즈니스 규칙 위반, 프로그래밍 오류, 복구 어려운 시스템 실패 |

Spring 백엔드에서는 대부분의 비즈니스 예외를 unchecked로 만든다.

이유는 간단하다.

- 모든 호출 계층에 `throws`를 강제하지 않는다.
- 실제로 중간 계층에서 복구할 수 있는 경우가 많지 않다.
- `@Transactional`은 기본적으로 `RuntimeException`과 `Error`에서 롤백한다.

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

현재 계층에서 복구할 수 없다면 상위 계층이 이해할 수 있는 예외로 변환한다.

```java
try {
    externalApi.call();
} catch (ExternalApiException e) {
    throw new BusinessException(ErrorCode.EXTERNAL_SERVICE_ERROR, e);
}
```

예외를 변환할 때는 원본 예외를 `cause`로 넘긴다. 그래야 실제 실패 지점의 stack trace가 보존된다.

같은 예외를 여러 계층에서 반복해서 로깅하면 하나의 실패가 여러 장애처럼 보일 수 있다. 예외를 처리하고 흐름을 계속하는 지점이나 글로벌 예외 핸들러 같은 최종 경계에서 한 번 로깅하는 것을 기본으로 한다. 비즈니스 규칙 위반처럼 예상 가능한 예외는 필요에 따라 낮은 로그 레벨을 사용하거나 로깅하지 않을 수 있다.

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

`@Transactional` 메서드 내부에서 예외를 잡고 정상 반환하면 Spring 프록시가 예외를 확인하지 못해 트랜잭션이 롤백되지 않을 수 있다. 롤백이 필요한 실패는 다시 던지는 것이 기본이다.

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

예외를 외부로 던질 수 없지만 반드시 롤백해야 하는 특별한 경우에는 rollback-only로 표시할 수 있다.

```java
catch (DataAccessException e) {
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    return;
}
```

rollback-only는 호출자에게 실패가 전달되지 않으므로 제한적으로 사용한다. 가능하면 예외를 다시 던져 실패와 롤백을 함께 전달한다. 자세한 함정은 [[transactional-pitfalls]]에서 다룬다.

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

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>외부 API 호출 실패를 현재 계층에서 복구할 수 없다. 가장 적절한 처리는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="실패를 null로 바꾸면 호출자가 실제 데이터 부재와 장애를 구분하기 어렵다." aria-pressed="false">A. null을 반환하고 호출자가 알아서 처리하게 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="현재 서비스가 이해할 수 있는 예외로 변환하되 원본 예외를 cause로 보존하는 것이 적절하다." aria-pressed="false">B. 의미 있는 예외로 변환하고 원본 예외를 cause로 포함해 상위로 전파한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 실패를 잡아 성공처럼 처리하면 장애 원인을 숨기고 잘못된 후속 처리를 만들 수 있다." aria-pressed="false">C. Exception으로 모두 잡고 정상 응답을 반환한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>비즈니스 조건 검사는 try-catch보다 if문이나 Bean Validation으로 명시하는 것이 보통 더 적절하다.</p>
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
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="try-catch 여부가 아니라 트랜잭션 프록시 밖으로 어떤 예외가 전파되는지가 중요하다." aria-pressed="false">C. try-catch를 사용한 경우에만 롤백된다.</button>
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
