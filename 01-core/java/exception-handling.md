---
title: 예외 처리 전략과 실무 기준
description: 예외를 어디서 잡고, 무엇으로 바꾸고, 언제 위로 던질지 정하는 백엔드 실무 기준
tags: [concept, java]
---

# 예외 처리 전략과 실무 기준

예외는 코드가 정상 흐름으로 더 갈 수 없을 때 실행을 멈추고, 그 실패를 위로 알리거나 그 자리에서 수습하게 해 주는 장치다. `try-catch`는 오류를 없애는 문법이 아니다. 실패했을 때 복구할지, 기본값을 쓸지, 다시 해 볼지, 기록만 하고 넘어갈지, 위로 넘길지를 정하는 자리다.

이 기준이 없으면 장애 원인을 찾기 어렵고, API 에러 응답 모양이 제각각이 되고, 실패했는데 트랜잭션이 커밋된다. 외부 API, DB, 메시지 처리, 파일 I/O처럼 실패가 잦은 곳일수록 기준이 필요하다. 예를 들어 결제 승인이 실패했는데 그 예외를 잡고 넘어가면, 주문은 "결제 완료"로 저장된다. 예외를 잡는 건 프로그램을 어떻게든 계속 돌리려는 게 아니라, 지금 계층이 책임질 수 있는 방식으로 실패를 처리하려는 것이다. 여기서 복구할 수 없으면 잡지 말고 위로 넘긴다.

## 상황별로 어떻게 처리하나

| 상황 | 처리 |
|---|---|
| 비즈니스 규칙 위반 | 커스텀 unchecked exception + ErrorCode |
| 입력값 검증 실패 | `@Valid`와 글로벌 예외 핸들러에서 응답 변환 |
| 외부 API 실패 | 의미 있는 예외로 변환하고 처리 경계에서 로깅 |
| 복구할 수 없는 시스템 오류 | 잡지 말고 위로 전파 |
| 트랜잭션 롤백이 필요한 checked exception | `rollbackFor` 명시 |

## try-catch는 언제 쓰나

지금 계층에서 그 실패를 두고 구체적으로 할 일이 있을 때만 쓴다.

- 외부 API, 결제, 이메일·SMS, 외부 SDK 호출이 실패하면 우리 서비스가 이해하는 예외로 바꾼다.
- 파일 읽기·쓰기나 JSON 파싱이 실패하면 대체 값을 쓰거나, 어디서 멈출지 정해 둔 대로 멈춘다.
- 있으면 좋은 부가 기능이 실패하면 기록만 하고 주 흐름은 계속 간다.
- 배치나 메시지 처리에서 한 건이 실패하면 그 건만 빼고 다음 건으로 넘어간다.
- 자원을 직접 다룰 때는 실패해도 정리 작업이 돌게 한다. 되도록 `try-with-resources`를 쓴다.

DB 접근처럼 프레임워크가 이미 예외를 바꿔 주는 곳은 호출마다 습관처럼 감싸지 않는다. 중복 키 예외를 "이미 가입된 이메일" 같은 비즈니스 예외로 바꾸는 것처럼, 이 계층에서 할 일이 있을 때만 잡는다.

반대로 아래는 `try-catch` 말고 평범한 제어 흐름으로 처리한다.

- 입력값과 비즈니스 조건은 `if`, Bean Validation 등으로 직접 검사한다.
- 단순 계산이나 일반 변수 접근을 예외로 제어하지 않는다.
- `NullPointerException` 같은 프로그래밍 오류를 잡아서 아무 일 없던 척하지 않는다.

예외를 분기 수단으로 쓰면 진짜 장애와 미리 알 수 있던 조건이 섞여 구분이 안 되고, 코드를 읽기도 힘들어진다.

## 실패가 얼마나 중요한지에 따라 다르게 처리한다

### 주 기능이 실패하면 위로 넘긴다

주문 저장이나 결제 승인처럼 요청한 일 자체를 못 하게 되는 실패는 위로 넘긴다. 외부 시스템의 예외는 우리 서비스가 이해하는 예외로 바꾸되, 원래 예외를 `cause`로 남긴다.

```java
try {
    paymentClient.approve(command);
} catch (PaymentClientException e) {
    throw new PaymentProcessingException("Payment approval failed", e);
}
```

### 부가 기능이 실패하면 기록하고 계속한다

주문 완료 알림처럼 주문 결과와 떼어 낼 수 있는 작업은, 실패를 기록하고 주문 흐름을 이어 간다. 다만 그 작업을 잃어도 되는지 먼저 정한다. 잃으면 안 되는 작업이면 로그만 남기지 말고 이벤트나 재처리 큐를 쓴다.

```java
try {
    notificationSender.sendOrderCompleted(orderId);
} catch (NotificationException e) {
    log.warn("Order notification failed. orderId={}", orderId, e);
}
```

### 기본값으로 복구한다

기본값은 그 값이 없어도 결과가 틀리거나 위험해지지 않을 때만 쓴다. 외부 API 실패를 무조건 `null`로 바꾸면, 호출이 실패한 건지 정말 데이터가 없는 건지 구분할 수 없다.

```java
try {
    return recommendationClient.getRecommendations(userId);
} catch (RecommendationException e) {
    log.warn("Recommendation lookup failed. userId={}", userId, e);
    return List.of();
}
```

추천 목록은 비어 있어도 화면이 깨지지 않지만, 기본값 때문에 결과가 틀어진다면 복구하지 말고 위로 넘긴다.

### 다시 시도한다

재시도는 타임아웃이나 잠깐의 네트워크 실패처럼 다시 하면 될 수도 있을 때만 한다. 잘못된 요청, 인증 실패, 비즈니스 규칙 위반은 다시 해도 같으니 재시도하지 않는다. 같은 요청이 두 번 가도 문제가 없게 멱등하게 만들고, 횟수와 대기 시간에 상한을 둔다.

`try-catch`와 반복문을 직접 엮기보다 Spring Retry나 Resilience4j처럼 이미 검증된 도구를 먼저 쓴다.

## InterruptedException

`InterruptedException`은 작업이 실패했다는 뜻이 아니라, 스레드에 "멈춰 달라"고 보낸 신호다. 잡고 그냥 계속 실행하면 취소나 애플리케이션 종료가 늦어진다.

그대로 던질 수 없는 계층이라면 인터럽트 상태를 되살린 뒤 다른 예외로 바꿔 던진다.

```java
try {
    return blockingQueue.take();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new TaskExecutionException("Task interrupted", e);
}
```

빈 `catch`로 삼키거나, 인터럽트 상태를 되살리지 않고 보통 실패처럼 처리하지 않는다.

## Checked와 Unchecked

| 구분 | 상위 클래스 | 컴파일러 강제 | 실무 의미 |
|---|---|---|---|
| Checked | `Exception` 중 `RuntimeException`을 제외한 타입 | O | 호출자가 복구하거나 꼭 처리해야 하는 실패 |
| Unchecked | `RuntimeException`, `Error` | X | 비즈니스 규칙 위반, 프로그래밍 오류, 복구가 어려운 시스템 실패 |

Spring 백엔드에서는 비즈니스 예외를 대부분 unchecked로 만든다.

- 호출하는 모든 계층에 `throws`를 붙이지 않아도 된다.
- 중간 계층에서 실제로 복구하는 경우가 드물다.
- `@Transactional`은 기본적으로 `RuntimeException`과 `Error`에서 롤백한다.

checked exception이 나쁜 건 아니다. 파일 I/O, 외부 라이브러리, 일부 연동 실패처럼 호출자가 실패를 알고 대응해야 하는 경우에는 checked가 맞다.

## 커스텀 예외와 ErrorCode

API 서버는 어떤 예외가 어떤 HTTP 응답이 되는지 한 가지 규칙으로 정해 둬야 한다. 보통 `BusinessException`과 `ErrorCode`를 같이 둔다.

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

예외에는 "사용자를 못 찾았다" 같은 업무상 이유만 담고, HTTP 응답으로 바꾸는 일은 글로벌 예외 핸들러가 한다. 그래서 컨트롤러마다 에러 응답을 만들 필요가 없다.

## 예외를 삼키지 않는다

가장 위험한 코드는 실패를 숨기는 코드다.

```java
try {
    externalApi.call();
} catch (Exception e) {
    // 아무 처리도 하지 않음
}
```

장애 원인이 어디에도 남지 않고, 호출한 쪽은 성공한 줄 알고 다음 로직을 실행한다. 여기서 복구할 수 없으면 위 계층이 알아듣는 예외로 바꿔 던진다.

```java
try {
    externalApi.call();
} catch (ExternalApiException e) {
    throw new BusinessException(ErrorCode.EXTERNAL_SERVICE_ERROR, e);
}
```

바꿀 때는 원래 예외를 `cause`로 넘긴다. 그래야 실제로 실패한 지점의 stack trace가 남는다.

로그는 한 번만 남긴다. 같은 예외를 여러 계층에서 찍으면 실패 하나가 장애 여러 건처럼 보인다. 예외를 처리하고 흐름을 이어 가는 곳이나, 글로벌 예외 핸들러처럼 맨 바깥에서 한 번 남기는 게 기본이다. 비즈니스 규칙 위반처럼 미리 알 수 있는 예외는 로그 레벨을 낮추거나 아예 남기지 않아도 된다.

## 트랜잭션과 예외

Spring `@Transactional`은 기본적으로 이렇게 롤백한다.

| 예외 종류 | 기본 동작 |
|---|---|
| `RuntimeException` | 롤백 |
| `Error` | 롤백 |
| checked `Exception` | 커밋 |

checked exception에서도 롤백하려면 직접 적어 줘야 한다. 이걸 모르면 예외가 났는데 DB 변경이 커밋되는 버그가 생긴다.

```java
@Transactional(rollbackFor = IOException.class)
public void importOrders(Path path) throws IOException {
    // 파일 읽기 + DB 저장
}
```

`@Transactional` 메서드 안에서 예외를 잡고 정상으로 반환하면, Spring 프록시는 예외를 보지 못해서 롤백하지 않는다. 롤백해야 하는 실패는 다시 던지는 게 기본이다.

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

예외를 밖으로 던질 수 없는데 꼭 롤백해야 하는 드문 경우에는 rollback-only로 표시한다.

```java
catch (DataAccessException e) {
    TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    return;
}
```

rollback-only를 쓰면 호출한 쪽은 실패했다는 걸 모르니, 꼭 필요할 때만 쓴다. 되도록 예외를 다시 던져서 실패와 롤백을 함께 알린다. 다른 함정은 [[transactional-pitfalls]]에 있다.

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

- catch에서 예외를 삼키면, 원인이 사라지고 호출한 쪽은 성공한 줄 안다.
- `Exception`이나 `Throwable`로 전부 잡으면, 복구할 수 없는 오류까지 정상 흐름에 섞인다.
- 예외를 바꾸면서 `cause`를 빠뜨리면, 원래 실패한 지점의 stack trace가 없어진다.
- 운영 코드에서 `e.printStackTrace()`를 쓰면, 로그 체계 밖으로 찍혀서 나중에 찾을 수 없다.
- 예외 메시지에 토큰, 비밀번호, 개인정보를 넣으면, 로그와 응답으로 그대로 새어 나간다.
- checked exception은 기본으로 롤백되지 않는다는 걸 모르면, 실패했는데 DB 변경이 커밋된다.
- 모든 예외를 같은 HTTP 상태 코드로 응답하면, 클라이언트가 다시 보내야 할지 요청을 고쳐야 할지 알 수 없다.

## 한 번에 설명하기

> 저는 예외를 잡기 전에, 이 계층에서 복구하거나 다른 예외로 바꿀 이유가 있는지부터 봅니다. 없으면 잡지 않고 위로 넘깁니다.
>
> 비즈니스 예외는 unchecked로 만들고, ErrorCode와 글로벌 예외 핸들러로 HTTP 응답 모양을 한 가지로 맞춥니다. 잡은 예외는 숨기지 않고 다른 예외로 바꾸되, 원래 예외를 cause로 넘겨서 나중에 추적할 수 있게 합니다.
>
> 트랜잭션에서는 checked exception이 기본으로 커밋된다는 걸 염두에 두고, 롤백이 필요하면 rollbackFor를 적어 줍니다.

## 꼬리 질문

> [!question]- checked exception과 unchecked exception은 뭐가 다른가?
> checked exception은 잡거나 `throws`로 넘기지 않으면 컴파일이 안 됩니다. unchecked exception은 그런 강제가 없고, Spring 백엔드에서는 비즈니스 예외를 보통 이걸로 만듭니다.

> [!question]- 실무에서 비즈니스 예외를 왜 unchecked로 많이 만드나?
> 중간 계층에서 복구할 일이 별로 없고, 모든 계층에 `throws`를 붙이지 않아도 되고, Spring 트랜잭션이 기본으로 롤백하는 규칙과도 맞아서입니다.

> [!question]- 예외를 바꿀 때 cause를 왜 넘기나?
> 원래 stack trace가 남아 있어야 실제로 어디서 터졌는지 찾을 수 있어서입니다.

> [!question]- `@Transactional`에서 checked exception이 나면 기본적으로 어떻게 되나?
> 롤백하지 않고 커밋합니다. 롤백하려면 `rollbackFor`를 적어 줘야 합니다.

> [!question]- 글로벌 예외 핸들러는 무슨 일을 하나?
> 컨트롤러에서 올라온 예외를 한 곳에서 받아 HTTP 상태 코드와 에러 응답으로 바꿉니다. 그래서 API마다 에러 응답 모양이 달라지지 않습니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [JLS 21: Exceptions](https://docs.oracle.com/javase/specs/jls/se21/html/jls-11.html)
- [Spring Framework: Rolling Back a Declarative Transaction](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[02-practical-backend/transaction/transaction|transaction]]
