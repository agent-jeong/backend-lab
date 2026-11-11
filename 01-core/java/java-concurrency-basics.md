---
title: "Java 동시성 기초"
description: 스레드를 직접 만들지 않고 ExecutorService, Future, CompletableFuture로 동시 작업을 돌리는 기준
tags: [concept, java]
---

# Java 동시성 기초 (스레드, synchronized, volatile)

Java에서 여러 작업을 동시에 돌리는 방법은 `Thread`, `ExecutorService`, `Future`, `CompletableFuture`가 있다. 각각 작업을 어떻게 띄우고 결과를 어떻게 받는지가 다르니 알고 골라야 한다. thread pool은 빠르게 하려고 쓰기 전에, 동시에 도는 작업 수를 묶어 두어 서버가 무너지지 않게 하려고 쓴다.

백엔드 서버는 요청 처리, 외부 API 호출, 배치, 메시지 소비를 한꺼번에 한다. 여기서 흔히 터지는 일은 이렇다. 요청마다 `Thread`를 만들어 OS 스레드와 메모리를 낭비한다. pool 크기를 근거 없이 키워서 DB connection pool이나 외부 API 호출 한도를 더 빨리 바닥낸다. `Future.get()`을 바로 불러서 비동기로 띄운 작업을 결국 기다리고 앉아 있는다. `CompletableFuture`에 executor를 안 넘겨서 공용 pool을 붐비게 한다. timeout, 취소, 예외 처리 없이 비동기 작업을 띄워 놓고 내버려 둔다.

## Thread를 직접 만들지 않는 이유

`Thread`를 직접 만들면 띄우기는 쉽지만, 운영 중에 몇 개가 돌고 있는지 보거나 줄일 방법이 없다.

```java
Thread thread = new Thread(() -> sendEmail(orderId));
thread.start();
```

서버에서는 thread pool을 쓴다. 스레드를 매번 만들지 않아도 되고, 동시에 도는 작업 수에 상한이 생기고, queue와 reject policy, shutdown을 직접 정할 수 있고, active thread와 queue size를 메트릭으로 볼 수 있다.

## ExecutorService

`ExecutorService`를 쓰면 작업을 넘기는 코드와 스레드를 관리하는 코드가 나뉜다. 호출하는 쪽은 작업만 넘기면 된다.

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

queue에 제한이 없으면 작업이 계속 쌓이기만 해서 장애를 늦게 알아차린다. pool이 너무 크면 DB 커넥션 같은 다른 자원이 먼저 바닥난다.

## Future와 CompletableFuture

`Future`로 비동기 작업의 결과를 받을 수는 있지만, 여러 작업을 엮거나 예외를 처리하기가 불편하다.

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

`supplyAsync()`에 executor를 넘기지 않으면 common pool에서 돈다. 서버 애플리케이션에서는 외부 API 호출용처럼 작업 성격에 맞는 executor를 따로 만들어 넘긴다.

## 작업별로 어떻게 돌리나

| 상황 | 권장 |
|---|---|
| 짧은 CPU 작업 | 현재 스레드 또는 작은 pool |
| 외부 API 병렬 호출 | 별도 I/O executor + timeout |
| 배치 병렬 처리 | 제한된 pool + chunk 단위 |
| 요청 흐름의 부가 작업 | 비동기로 돌리되 실패 보상 기준을 정해 둔다 |
| 공유 상태 수정 | 동기화, lock, atomic, 불변 구조 검토 |

pool 크기는 CPU 수, I/O를 기다리는 시간, DB connection pool 크기, 외부 API 호출 한도를 함께 보고 정한다.

## 자주 깨지는 곳

- 요청마다 Thread를 만들면, 스레드 수에 상한이 없어서 요청이 몰릴 때 메모리부터 무너진다.
- pool 크기만 키우면 빨라질 거라고 믿고 DB connection pool보다 훨씬 크게 잡으면, 커넥션을 기다리는 스레드만 늘어난다.
- timeout 없이 `Future.get()`을 부르면, 작업이 안 끝날 때 끝없이 기다린다.
- `CompletableFuture`의 예외를 처리하지 않으면, 실패가 아무 흔적 없이 사라진다.
- executor를 shutdown하지 않으면, 테스트나 배치가 끝나지 않는다.

## 운영에서 볼 것

- 로그에 thread name, 걸린 시간, timeout이 났는지를 남긴다.
- 메트릭으로 active thread, queue size, rejected task, task duration을 본다.
- timeout, 예외, 취소가 났을 때 결과가 생각한 대로 처리되는지 테스트한다.
- 스레드 덤프에서 blocked나 waiting 상태인 작업이 쌓이는지 본다.

## 한 번에 설명하기

> 동시 작업은 Thread를 직접 만들지 않고, ExecutorService로 동시에 도는 수와 queue를 정해 두고 돌립니다. thread pool은 빠르게 하려고 쓰기보다 동시에 도는 작업 수를 묶어서 서버를 지키려고 씁니다. 그래서 크기는 CPU, I/O 대기 시간, DB connection pool, 외부 API 한도를 같이 보고 정합니다.
>
> Future.get()에는 꼭 timeout을 주고, CompletableFuture에는 executor와 예외 처리를 직접 넣습니다.
>
> 여러 스레드가 같은 값을 건드리는 문제는 작업을 어떻게 띄우느냐와는 다른 문제라서, Java Memory Model까지 같이 봅니다.

## 꼬리 질문

> [!question]- Thread를 직접 만들지 않고 ExecutorService를 쓰는 이유는?
> 스레드를 매번 만드는 비용이 줄고, 동시에 몇 개를 돌릴지, queue와 reject policy, shutdown을 직접 정할 수 있어서입니다.

> [!question]- thread pool 크기를 무작정 키우면 왜 위험한가?
> CPU context switching이 늘고, 메모리를 더 쓰고, DB 커넥션을 기다리는 스레드가 쌓이고, 외부 API에도 부하가 더 갑니다. 그러다 서비스 전체 장애로 번질 수 있습니다.

> [!question]- `CompletableFuture.supplyAsync()`에 executor를 안 넘기면 어떻게 되나?
> common pool에서 돕니다. 서버에서는 다른 작업과 그 pool을 나눠 쓰게 돼서, 언제 느려질지 예측하기 어려워집니다.

> [!question]- `Future.get()`을 쓸 때 조심할 점은?
> timeout 없이 부르면 작업이 끝날 때까지 끝없이 기다릴 수 있습니다. 그래서 `get(timeout, unit)`을 쓰고, 예외도 처리합니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: java.util.concurrent](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)

## 관련 문서

- [[java]]
- [[java-memory-model]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/connection-pool-and-timeout|connection-pool-and-timeout]]
