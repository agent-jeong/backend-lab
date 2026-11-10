---
title: Kotlin Coroutine 기본
description: Kotlin coroutine의 기본 개념과 Spring 백엔드에서의 실무 주의점
tags: [concept, kotlin]
---

# Kotlin Coroutine 기본

Coroutine은 중단했다가 다시 이어 갈 수 있는 비동기 작업을 순차 코드처럼 쓰게 해 주는 Kotlin의 동시성 추상화다. 대기하는 동안 스레드를 붙잡고 있지 않는다.

비동기 I/O 코드는 읽기 쉬워지지만, 잘못 쓰면 오히려 장애 원인이 된다. coroutine을 thread와 같은 것으로 보거나, blocking JDBC와 HTTP client를 그대로 부르거나, `GlobalScope`로 작업 생명주기를 놓치는 경우다. 도입 전에 "지금 호출하는 API가 non-blocking인가"부터 확인한다.

## 기본 개념

`suspend` 함수는 중간에 멈출 수 있는 함수다.

```kotlin
suspend fun findOrder(orderId: Long): OrderResponse {
    val order = orderClient.getOrder(orderId)
    val payment = paymentClient.getPayment(order.paymentId)
    return OrderResponse.of(order, payment)
}
```

`suspend`는 새 스레드를 만든다는 뜻이 아니다. 중단 지점에서 스레드를 내놓고, 나중에 다시 이어서 실행될 수 있다는 뜻이다.

## Dispatcher

Dispatcher는 coroutine을 어느 스레드 풀에서 돌릴지 정한다.

| Dispatcher | 용도 |
|---|---|
| `Dispatchers.Default` | CPU 작업 |
| `Dispatchers.IO` | blocking I/O 작업 |
| custom dispatcher | 외부 API, 제한된 병렬성 |

blocking API를 불러야 하면 `Dispatchers.IO`나 별도 dispatcher로 명시적으로 옮긴다.

```kotlin
suspend fun loadUser(id: Long): User = withContext(Dispatchers.IO) {
    blockingUserRepository.findById(id)
}
```

다만 Spring MVC + JDBC/JPA 기반이면 요청 처리 모델 전체가 blocking이라 coroutine을 들여도 얻는 게 적다.

## Structured Concurrency

자식 작업은 부모 scope 안에서 시작하고 끝나야 한다. 그래야 하나가 실패하거나 취소될 때 나머지도 같이 정리된다.

```kotlin
suspend fun loadOrderView(orderId: Long): OrderView = coroutineScope {
    val order = async { orderClient.getOrder(orderId) }
    val payment = async { paymentClient.getPayment(orderId) }

    OrderView.of(order.await(), payment.await())
}
```

`GlobalScope`는 작업 생명주기가 요청이나 서비스 scope와 떨어져 있어서 일반 서버 코드에서는 쓰지 않는다.

## Timeout과 Cancellation

외부 호출에는 timeout을 건다.

```kotlin
val result = withTimeout(1_000) {
    paymentClient.pay(request)
}
```

cancellation은 협력적으로 동작한다. 취소 신호를 확인하는 지점에서만 멈추므로, blocking 호출은 신호를 바로 따르지 않을 수 있다.

## 언제 쓰나

| 상황 | 판단 |
|---|---|
| Spring MVC + JPA | 효과가 적다. blocking 모델부터 이해한다 |
| WebFlux + non-blocking client | coroutine 장점이 커질 수 있다 |
| 외부 API 병렬 호출 | `coroutineScope` + `async` + timeout |
| fire-and-forget 작업 | queue/event 기반을 먼저 검토 |
| blocking API 호출 | `Dispatchers.IO` 또는 별도 dispatcher |

## 자주 깨지는 곳

- **coroutine이면 blocking 코드도 non-blocking이 된다고 믿는다.** blocking JDBC/JPA나 HTTP client는 그대로 스레드를 잡는다. 코드 리뷰에서 coroutine 안의 blocking 호출을 찾는다.
- **`GlobalScope.launch`로 요청과 무관한 작업을 만든다.** 취소, 예외 전파, 종료 관리가 끊긴다.
- **`async`를 쓰고 `await`를 빠뜨린다.** 결과와 예외를 받지 못한다.
- **dispatcher 없이 CPU 작업과 I/O 작업을 섞는다.** 한쪽이 다른 쪽 스레드를 잡아먹는다. dispatcher별 스레드 사용량과 queue 지표를 본다.
- **timeout과 cancellation 전파를 테스트하지 않는다.** 장애가 나야 취소가 안 먹는다는 걸 안다.

## 한 번에 설명하기

> Coroutine은 thread가 아니라 중단했다가 재개할 수 있는 비동기 작업 단위입니다. `suspend`는 새 스레드를 만들지 않고, non-blocking API와 함께 쓸 때 효과가 큽니다. blocking JDBC나 HTTP client를 그대로 부르면 coroutine만으로는 빨라지지 않아서, 그럴 땐 `Dispatchers.IO`로 옮깁니다. 서버 코드에서는 `GlobalScope`를 피하고 structured concurrency로 생명주기를 묶은 뒤, timeout과 cancellation, 예외 전파를 같이 설계합니다.

## 꼬리 질문

> [!question]- Coroutine과 Thread의 차이는 무엇인가?
> Thread는 OS 실행 단위이고, coroutine은 Kotlin 런타임이 관리하는 중단 가능한 작업 단위입니다. Coroutine도 실행될 때는 결국 어떤 thread 위에서 돕니다.

> [!question]- `suspend`는 무슨 의미인가?
> 함수가 중단됐다가 나중에 재개될 수 있다는 뜻입니다. `suspend` 자체가 새 스레드를 만들거나 blocking 코드를 non-blocking으로 바꾸지는 않습니다.

> [!question]- `GlobalScope`를 서버 코드에서 피하는 이유는?
> 요청이나 서비스 생명주기와 떨어져 있어서 취소, 예외 전파, 종료 관리가 어려워지기 때문입니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Coroutine과 Thread의 차이로 맞는 설명은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Coroutine은 Thread보다 가벼운 실행 단위이며, suspend 지점에서 스레드를 점유하지 않고 중단/재개될 수 있다." aria-pressed="false">A. Coroutine은 suspend 지점에서 중단·재개 가능한 가벼운 실행 단위다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Coroutine이 항상 새 OS 스레드를 만드는 것은 아니다." aria-pressed="false">B. Coroutine 하나는 항상 OS Thread 하나를 새로 만든다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Coroutine도 dispatcher와 thread pool 위에서 실행된다." aria-pressed="false">C. Coroutine은 스레드와 완전히 무관하게 CPU에서 실행된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>GlobalScope를 서버 코드에서 남용하면 요청 생명주기와 무관한 작업이 남아 장애 추적과 취소가 어려워질 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="구조화된 동시성을 깨면 부모 작업 취소, 예외 전파, 리소스 정리가 어려워진다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="GlobalScope는 생명주기 관리를 개발자가 직접 책임져야 하므로 서버 요청 처리에서는 신중해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>suspend 함수의 의미로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="호출 지점에서 중단될 수 있으며, 중단 중에는 스레드를 계속 점유하지 않을 수 있음을 표현한다." aria-pressed="false">A. 중단 가능 지점을 타입 수준에 드러낸다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="suspend가 붙었다고 항상 별도 스레드에서 실행되는 것은 아니다." aria-pressed="false">B. 항상 새 스레드에서 실행된다는 뜻이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="suspend는 예외를 없애는 문법이 아니다." aria-pressed="false">C. 함수 내부 예외가 모두 무시된다는 뜻이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Kotlin: Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)

## 관련 문서

- [[kotlin]]
- [[kotlin-java-interop]]
- [[01-core/java/java-concurrency-basics|java-concurrency-basics]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/connection-pool-and-timeout|connection-pool-and-timeout]]
