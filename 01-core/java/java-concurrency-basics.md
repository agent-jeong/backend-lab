---
title: "Java 동시성 기초"
description: Java 스레드, ExecutorService, Future, CompletableFuture의 실무 사용 기준
tags: [concept, java]
---

# Java 동시성 기초 (스레드, synchronized, volatile)

여러 작업을 동시에 돌리려면 `Thread`, `ExecutorService`, `Future`, `CompletableFuture` 같은 실행 모델을 알고 써야 한다. thread pool은 성능을 올리는 도구이기 전에 **동시에 도는 작업 수를 제한해 시스템을 지키는 장치**다.

백엔드 서버는 요청 처리, 외부 API 호출, 배치, 메시지 소비를 동시에 한다. 여기서 흔한 사고는 요청마다 `Thread`를 만들어 OS 스레드와 메모리를 낭비하는 것, pool 크기를 근거 없이 키워 DB connection pool이나 외부 API를 더 빨리 고갈시키는 것, `Future.get()`을 그냥 불러 비동기를 동기 대기로 바꾸는 것, `CompletableFuture`에 executor를 주지 않아 공용 pool에 부하를 주는 것, timeout·cancel·예외 처리 없이 비동기 작업을 방치하는 것이다.

## Thread를 직접 만들지 않는 이유

직접 `Thread`를 만들면 실행은 간단하지만 운영에서 제어할 손잡이가 없다.

```java
Thread thread = new Thread(() -> sendEmail(orderId));
thread.start();
```

서버에서는 thread pool을 쓴다. 스레드 생성 비용이 줄고, 동시에 도는 작업 수가 제한되고, queue·reject policy·shutdown을 관리할 수 있고, active thread와 queue size를 메트릭으로 볼 수 있다.

## ExecutorService

`ExecutorService`는 작업 제출과 스레드 관리를 분리한다.

```java
ExecutorService executor = Executors.newFixedThreadPool(10);

Future<OrderResult> future = executor.submit(() -> processOrder(orderId));

OrderResult result = future.get(500, TimeUnit.MILLISECONDS);
```

실무에서는 `Executors.newFixedThreadPool()`보다 queue 크기와 reject policy를 직접 정할 수 있는 `ThreadPoolExecutor`를 먼저 본다.

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

queue가 무제한이면 장애가 늦게 드러나고, pool이 과하게 크면 다른 자원이 먼저 고갈된다.

## Future와 CompletableFuture

`Future`는 비동기 결과를 표현하지만 조합과 예외 처리가 불편하다.

```java
Future<PaymentResult> future = executor.submit(() -> paymentClient.pay(request));
PaymentResult result = future.get(1, TimeUnit.SECONDS);
```

`CompletableFuture`는 작업을 엮고 예외를 처리하기가 더 쉽다.

```java
CompletableFuture<PaymentResult> paymentFuture =
    CompletableFuture.supplyAsync(() -> paymentClient.pay(request), executor)
        .orTimeout(1, TimeUnit.SECONDS)
        .exceptionally(ex -> PaymentResult.failed());
```

`supplyAsync()`에 executor를 주지 않으면 common pool에서 돈다. 서버 애플리케이션에서는 작업 성격에 맞는 executor를 명시한다.

## 작업별로 어떻게 돌리나

| 상황 | 권장 |
|---|---|
| 짧은 CPU 작업 | 현재 스레드 또는 작은 pool |
| 외부 API 병렬 호출 | 별도 I/O executor + timeout |
| 배치 병렬 처리 | 제한된 pool + chunk 단위 |
| 요청 흐름의 부가 작업 | 비동기로 돌리되 실패 보상 기준을 정해 둔다 |
| 공유 상태 수정 | 동기화, lock, atomic, 불변 구조 검토 |

pool 크기는 CPU, I/O 대기, DB connection pool, 외부 API 제한을 같이 보고 정한다.

## 자주 깨지는 곳

- **요청마다 Thread를 만든다.** 스레드 수에 상한이 없어 부하가 몰리면 메모리부터 무너진다.
- **pool 크기만 키우면 빨라진다고 믿는다.** DB connection pool보다 훨씬 큰 작업 pool은 대기만 늘린다.
- **timeout 없이 `Future.get()`을 부른다.** 작업이 안 끝나면 무기한 기다린다.
- **`CompletableFuture` 예외를 처리하지 않는다.** 실패가 조용히 사라진다.
- **executor를 shutdown하지 않는다.** 테스트나 배치가 끝나지 않는다.

## 운영에서 볼 것

- 로그에 thread name, 걸린 시간, timeout 여부를 남긴다.
- 메트릭으로 active thread, queue size, rejected task, task duration을 본다.
- timeout, 예외, cancel 상황에서 결과가 의도대로 처리되는지 테스트한다.
- 스레드 덤프에서 작업이 blocked, waiting 상태로 쌓이는지 본다.

## 면접에서 말하기

> 동시 작업은 Thread를 직접 만들지 않고 ExecutorService로 실행 수와 queue를 제어합니다. thread pool은 빠르게 하려는 도구라기보다 동시 실행 수를 제한해 시스템을 보호하는 장치라서, 크기는 CPU, I/O 대기, DB connection pool, 외부 API 제한을 같이 보고 정합니다. Future.get()은 timeout을 꼭 주고, CompletableFuture는 executor와 예외 처리를 명시합니다. 공유 상태 문제는 실행 모델과 별개라서 Java Memory Model까지 같이 봅니다.

## 꼬리 질문

> [!question]- Thread를 직접 만들기보다 ExecutorService를 사용하는 이유는?
> 스레드 생성 비용을 줄이고, 동시 실행 수, queue, reject policy, shutdown을 제어할 수 있기 때문입니다.

> [!question]- thread pool 크기를 무작정 키우면 왜 위험한가?
> CPU context switching, memory 사용량, DB connection 대기, 외부 API 부하가 증가해서 전체 장애로 번질 수 있습니다.

> [!question]- `CompletableFuture.supplyAsync()`에서 executor를 지정하지 않으면 어떻게 되는가?
> 기본적으로 common pool을 사용합니다. 서버 애플리케이션에서는 다른 작업과 pool을 공유해 예측하기 어려운 지연이 생길 수 있습니다.

> [!question]- `Future.get()`을 사용할 때 무엇을 주의해야 하는가?
> timeout 없이 호출하면 작업이 끝날 때까지 무기한 대기할 수 있으므로 `get(timeout, unit)`을 사용하고 예외 처리를 해야 합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Thread를 직접 생성하기보다 ExecutorService를 사용하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="스레드 생성 비용과 개수를 관리하고 작업 제출/종료 정책을 분리할 수 있다." aria-pressed="false">A. 스레드 생명주기와 풀 크기를 관리하기 쉽다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="ExecutorService도 잘못 쓰면 동시성 문제가 생긴다." aria-pressed="false">B. 모든 동시성 버그를 자동으로 제거한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="비동기 처리가 항상 단일 스레드라는 뜻은 아니다." aria-pressed="false">C. 모든 작업을 하나의 스레드에서만 실행한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>thread pool 크기를 무작정 키우면 처리량이 항상 증가한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="컨텍스트 스위칭, 메모리, DB 커넥션 같은 하위 자원 병목 때문에 오히려 나빠질 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="풀 크기는 CPU/IO 특성과 하위 리소스 한도를 함께 보고 정해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>CompletableFuture.supplyAsync()에서 executor를 지정하지 않을 때 주의점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="공용 ForkJoinPool을 사용하므로 blocking 작업이 섞이면 다른 비동기 작업에 영향을 줄 수 있다." aria-pressed="false">A. 공용 풀을 사용해 blocking 작업에서 문제가 될 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="별도 executor가 자동으로 무한 생성되는 것은 아니다." aria-pressed="false">B. 요청마다 전용 스레드 풀이 자동 생성된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="동기 실행만 하는 것이 아니라 비동기 실행된다." aria-pressed="false">C. 항상 호출한 스레드에서 동기 실행된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[java]]
- [[java-memory-model]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/connection-pool-and-timeout|connection-pool-and-timeout]]
