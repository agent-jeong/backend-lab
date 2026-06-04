---
title: Kotlin Coroutine 기본
description: Kotlin coroutine의 기본 개념과 Spring 백엔드에서의 실무 주의점
---

# Kotlin Coroutine 기본

## 한 줄 정의

Coroutine은 스레드를 직접 점유하지 않고 중단과 재개가 가능한 비동기 작업을 순차 코드처럼 표현하게 해주는 Kotlin의 동시성 추상화다.

## 실무에서 왜 중요한가

Coroutine은 비동기 I/O 코드를 읽기 쉽게 만들 수 있지만, 잘못 쓰면 오히려 장애 원인이 된다.

- coroutine을 thread와 같은 것으로 오해한다.
- blocking JDBC, blocking HTTP client를 coroutine 안에서 그대로 호출한다.
- dispatcher를 구분하지 않아 CPU 작업과 I/O 작업이 섞인다.
- structured concurrency 없이 `GlobalScope`를 사용해 작업 생명주기를 잃는다.
- timeout, cancellation, exception propagation을 고려하지 않는다.

## 기본 개념

`suspend` 함수는 중단 가능한 함수다.

```kotlin
suspend fun findOrder(orderId: Long): OrderResponse {
    val order = orderClient.getOrder(orderId)
    val payment = paymentClient.getPayment(order.paymentId)
    return OrderResponse.of(order, payment)
}
```

`suspend`는 새 스레드를 만든다는 뜻이 아니다. 중단 지점에서 스레드를 반납하고 나중에 재개될 수 있다는 뜻이다.

## Dispatcher

Dispatcher는 coroutine이 어떤 스레드 풀에서 실행될지 결정한다.

| Dispatcher | 용도 |
|---|---|
| `Dispatchers.Default` | CPU 작업 |
| `Dispatchers.IO` | blocking I/O 작업 |
| custom dispatcher | 외부 API, 제한된 병렬성 |

blocking API를 호출해야 한다면 별도 dispatcher나 `Dispatchers.IO`를 명확히 사용한다.

```kotlin
suspend fun loadUser(id: Long): User = withContext(Dispatchers.IO) {
    blockingUserRepository.findById(id)
}
```

하지만 Spring MVC + JDBC/JPA 기반에서는 전체 요청 처리 모델이 blocking이므로 coroutine 도입 효과가 제한적일 수 있다.

## Structured Concurrency

coroutine은 부모 scope 안에서 자식 작업의 생명주기를 관리하는 것이 중요하다.

```kotlin
suspend fun loadOrderView(orderId: Long): OrderView = coroutineScope {
    val order = async { orderClient.getOrder(orderId) }
    val payment = async { paymentClient.getPayment(orderId) }

    OrderView.of(order.await(), payment.await())
}
```

`GlobalScope`는 작업 생명주기가 요청이나 서비스 scope와 분리되므로 일반 서버 코드에서 피하는 것이 좋다.

## Timeout과 Cancellation

외부 호출에는 timeout이 필요하다.

```kotlin
val result = withTimeout(1_000) {
    paymentClient.pay(request)
}
```

cancellation은 협력적으로 동작한다. blocking 호출은 취소 신호를 즉시 따르지 않을 수 있다.

## 자주 나는 실수

- coroutine을 쓰면 blocking 코드도 자동으로 non-blocking이 된다고 생각한다.
- `GlobalScope.launch`로 요청과 무관한 작업을 만든다.
- `async`를 사용하고 `await`를 빠뜨린다.
- dispatcher 없이 CPU 작업과 I/O 작업을 섞는다.
- timeout과 cancellation 전파를 테스트하지 않는다.

## 실무 판단 기준

| 상황 | 판단 |
|---|---|
| Spring MVC + JPA | coroutine 효과 제한적, blocking 모델 이해 우선 |
| WebFlux + non-blocking client | coroutine 장점이 커질 수 있음 |
| 외부 API 병렬 호출 | `coroutineScope` + `async` + timeout |
| fire-and-forget 작업 | queue/event 기반 우선 검토 |
| blocking API 호출 | `Dispatchers.IO` 또는 별도 dispatcher |

## 확인 방법

- coroutine 안에서 blocking API를 호출하는지 확인한다.
- dispatcher별 thread 사용량과 queue 지표를 본다.
- timeout, cancellation, exception propagation 테스트를 작성한다.
- `GlobalScope` 사용 여부를 코드 리뷰에서 확인한다.

## 핵심 요약

Coroutine은 thread가 아니라 중단과 재개가 가능한 비동기 작업 추상화다.

`suspend` 함수는 새 스레드를 만든다는 의미가 아니며, non-blocking API와 함께 쓸 때 효과가 크다.

blocking JDBC/JPA나 blocking HTTP client를 그대로 호출하면 coroutine만으로 성능이 좋아지지 않는다.

서버 코드에서는 `GlobalScope`를 피하고 structured concurrency로 작업 생명주기를 관리해야 한다.

실무에서는 dispatcher, timeout, cancellation, exception propagation을 함께 설계해야 안전하다.

## 꼬리 질문

> [!question]- Coroutine과 Thread의 차이는 무엇인가?
> Thread는 OS 실행 단위이고, coroutine은 Kotlin 런타임이 관리하는 중단 가능한 작업 단위입니다. Coroutine은 실행될 때 결국 어떤 thread 위에서 동작합니다.

> [!question]- `suspend`는 무슨 의미인가?
> 함수가 중단되고 나중에 재개될 수 있다는 의미입니다. `suspend` 자체가 새 스레드를 만들거나 blocking 코드를 non-blocking으로 바꾸지는 않습니다.

> [!question]- `GlobalScope`를 서버 코드에서 피하는 이유는?
> 요청이나 서비스 생명주기와 분리되어 취소, 예외 전파, 종료 관리가 어려워지기 때문입니다.

## 관련 문서

- [[kotlin]]
- [[kotlin-java-interop]]
- [[01-core/java/java-concurrency-basics|java-concurrency-basics]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/connection-pool-and-timeout|connection-pool-and-timeout]]
