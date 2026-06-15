---
title: Java 동시성 기초
description: Java 스레드, ExecutorService, Future, CompletableFuture의 실무 사용 기준
---

# Java 동시성 기초 (스레드, synchronized, volatile)

## 한 줄 정의

Java 동시성 기본은 여러 작업을 동시에 실행하기 위해 `Thread`, `ExecutorService`, `Future`, `CompletableFuture` 같은 실행 모델을 이해하고 안전하게 사용하는 것이다.

## 실무에서 왜 중요한가

백엔드 서버는 요청 처리, 외부 API 호출, 배치, 메시지 소비처럼 여러 작업을 동시에 처리한다. 동시성 기본을 모르면 다음 문제가 생긴다.

- 요청마다 직접 `Thread`를 만들어 OS 스레드와 메모리를 과도하게 사용한다.
- thread pool 크기를 근거 없이 키워 DB connection pool이나 외부 API를 더 빨리 고갈시킨다.
- `Future.get()`을 무작정 호출해서 비동기 처리를 동기 대기로 만들어버린다.
- `CompletableFuture`에서 executor를 지정하지 않아 공용 pool에 부하를 준다.
- timeout, cancel, exception handling 없이 비동기 작업을 방치한다.

## Thread와 Runnable

직접 `Thread`를 만들면 작업 실행은 단순하지만 운영 제어가 어렵다.

```java
Thread thread = new Thread(() -> sendEmail(orderId));
thread.start();
```

실무 서버에서는 보통 직접 Thread를 만들기보다 thread pool을 사용한다.

이유는 다음과 같다.

- 스레드 생성 비용을 줄인다.
- 동시에 실행되는 작업 수를 제한한다.
- queue, reject policy, shutdown을 관리할 수 있다.
- 메트릭으로 active thread, queue size를 관찰할 수 있다.

## ExecutorService

`ExecutorService`는 작업 제출과 스레드 관리를 분리한다.

```java
ExecutorService executor = Executors.newFixedThreadPool(10);

Future<OrderResult> future = executor.submit(() -> processOrder(orderId));

OrderResult result = future.get(500, TimeUnit.MILLISECONDS);
```

실무에서는 `Executors.newFixedThreadPool()`을 바로 쓰기보다 queue 크기와 reject policy를 명시할 수 있는 `ThreadPoolExecutor`를 검토한다.

```java
ExecutorService executor = new ThreadPoolExecutor(
    10,
    10,
    0L,
    TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(100),
    new ThreadPoolExecutor.CallerRunsPolicy()
);
```

무제한 queue나 과도한 pool 크기는 장애를 늦게 드러내거나 다른 자원을 고갈시킬 수 있다.

## Future와 CompletableFuture

`Future`는 비동기 결과를 표현하지만 조합과 예외 처리가 불편하다.

```java
Future<PaymentResult> future = executor.submit(() -> paymentClient.pay(request));
PaymentResult result = future.get(1, TimeUnit.SECONDS);
```

`CompletableFuture`는 작업 조합과 예외 처리가 더 유연하다.

```java
CompletableFuture<PaymentResult> paymentFuture =
    CompletableFuture.supplyAsync(() -> paymentClient.pay(request), executor)
        .orTimeout(1, TimeUnit.SECONDS)
        .exceptionally(ex -> PaymentResult.failed());
```

다만 `supplyAsync()`에 executor를 지정하지 않으면 기본적으로 common pool을 사용한다. 서버 애플리케이션에서는 작업 성격에 맞는 executor를 명시하는 것이 안전하다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| 짧은 CPU 작업 | 현재 스레드 또는 작은 pool |
| 외부 API 병렬 호출 | 별도 I/O executor + timeout |
| 배치 병렬 처리 | 제한된 pool + chunk 단위 |
| 요청 흐름의 부가 작업 | 비동기 처리하되 실패 보상 기준 명확화 |
| 공유 상태 수정 | 동기화, lock, atomic, 불변 구조 검토 |

## 자주 나는 실수

- 요청마다 직접 Thread를 생성한다.
- pool 크기만 키우면 성능이 좋아진다고 생각한다.
- DB connection pool보다 훨씬 큰 작업 pool을 만들어 대기만 늘린다.
- timeout 없이 `Future.get()`을 호출한다.
- `CompletableFuture` 예외를 처리하지 않아 실패가 조용히 누락된다.
- executor shutdown을 하지 않아 테스트나 배치가 종료되지 않는다.

## 확인 방법

- 로그: thread name, elapsed time, timeout 여부를 확인한다.
- 메트릭: active thread, queue size, rejected task, task duration을 본다.
- 테스트: timeout, exception, cancel 상황에서 결과가 의도대로 처리되는지 확인한다.
- 스레드 덤프: 작업이 blocked, waiting 상태로 쌓이는지 확인한다.

## 핵심 요약

Java에서 동시 작업은 직접 `Thread`를 만들기보다 `ExecutorService`로 실행 수와 queue를 제어하는 것이 실무에 적합합니다.

Thread pool은 성능을 무조건 높이는 도구가 아니라 동시 실행 수를 제한해 시스템을 보호하는 장치입니다.

pool 크기는 CPU, I/O 대기, DB connection pool, 외부 API 제한을 함께 고려해야 합니다.

`Future.get()`은 timeout 없이 호출하면 무기한 대기가 될 수 있고, `CompletableFuture`는 executor와 예외 처리를 명시해야 안전합니다.

동시성 문제는 실행 모델뿐 아니라 공유 상태와 Java Memory Model까지 함께 이해해야 합니다.

## 꼬리 질문

> [!question]- Thread를 직접 만들기보다 ExecutorService를 사용하는 이유는?
> 스레드 생성 비용을 줄이고, 동시 실행 수, queue, reject policy, shutdown을 제어할 수 있기 때문입니다.

> [!question]- thread pool 크기를 무작정 키우면 왜 위험한가?
> CPU context switching, memory 사용량, DB connection 대기, 외부 API 부하가 증가해서 전체 장애로 번질 수 있습니다.

> [!question]- `CompletableFuture.supplyAsync()`에서 executor를 지정하지 않으면 어떻게 되는가?
> 기본적으로 common pool을 사용합니다. 서버 애플리케이션에서는 다른 작업과 pool을 공유해 예측하기 어려운 지연이 생길 수 있습니다.

> [!question]- `Future.get()`을 사용할 때 무엇을 주의해야 하는가?
> timeout 없이 호출하면 작업이 끝날 때까지 무기한 대기할 수 있으므로 `get(timeout, unit)`을 사용하고 예외 처리를 해야 합니다.

## 관련 문서

- [[java]]
- [[java-memory-model]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/connection-pool-and-timeout|connection-pool-and-timeout]]
