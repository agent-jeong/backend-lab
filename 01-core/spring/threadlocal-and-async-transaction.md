---
title: "@Async와 ThreadLocal 함정"
description: 트랜잭션, 인증 정보, traceId가 @Async와 스레드 풀에서 사라지거나 남는 이유와 대응
tags: [concept, spring]
---

# @Async와 ThreadLocal 함정

Spring의 트랜잭션, SecurityContext, MDC는 모두 ThreadLocal에 들어 있다. 그래서 `@Async`나 `CompletableFuture`로 스레드가 바뀌면 이 값들이 따라가지 않는다. 스레드 풀에서 스레드를 다시 쓰면 앞 요청의 값이 그대로 남아 있기도 한다.

증상은 제각각으로 보인다. `@Async` 메서드의 DB 저장이 호출자 트랜잭션과 따로 커밋돼서, 호출자가 롤백해도 남는다. `SecurityContextHolder.getContext()`가 비어 있고, 로그의 traceId가 비동기 구간에서 사라진다. `CompletableFuture.supplyAsync()` 안에서는 호출자의 DB 커넥션을 같이 쓰지 못해 커넥션을 하나씩 더 잡고, 커넥션 풀이 생각보다 빨리 바닥난다. 가장 위험한 건 앞 요청 사용자의 정보가 다음 요청에서 보이는 보안 사고다. 이 증상들은 모두 값이 지금 도는 스레드에 묶여 있어서 생긴다.

## ThreadLocal 동작

ThreadLocal은 스레드마다 값을 따로 두는 저장소다. 같은 변수를 읽어도 스레드마다 다른 값이 나온다.

```java
ThreadLocal<String> context = new ThreadLocal<>();

// Thread-1에서
context.set("user-A");
context.get(); // "user-A"

// Thread-2에서
context.get(); // null (Thread-1의 값과 무관)
```

```
Thread-1: ┌─ ThreadLocal ─┐
          │ userId = "A"  │
          └───────────────┘

Thread-2: ┌─ ThreadLocal ─┐
          │ userId = null │
          └───────────────┘
```

### Spring에서 ThreadLocal을 쓰는 곳

| 기능 | ThreadLocal 사용 | 저장하는 값 |
|---|---|---|
| `@Transactional` | `TransactionSynchronizationManager` | DB Connection, 트랜잭션 상태 |
| Spring Security | `SecurityContextHolder` | 인증 정보 (Authentication) |
| MDC (로깅) | `MDC.put()` | traceId, requestId |
| RequestContextHolder | `RequestContextHolder` | HttpServletRequest |

이 값들은 전부 지금 도는 스레드에 묶여 있어서, 스레드가 바뀌면 한꺼번에 끊긴다.

## @Async에서 트랜잭션이 동작하지 않는 이유

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        notificationService.sendAsync(request); // ❌ 다른 스레드
    }
}

@Service
public class NotificationService {

    @Async
    public void sendAsync(OrderRequest request) {
        // 이 메서드는 다른 스레드에서 실행됨
        // → 호출자의 트랜잭션에 참여 불가
        // → 호출자의 SecurityContext 접근 불가
        // → MDC의 traceId도 없음
        logRepository.save(new NotificationLog(request)); // 호출자 트랜잭션과 따로 커밋됨
    }
}
```

```
Thread-1 (요청 스레드)          Thread-2 (@Async 스레드)
┌─────────────────────┐       ┌─────────────────────┐
│ Transaction: active │       │ Transaction: none   │
│ SecurityContext: ✓  │       │ SecurityContext: ✗   │
│ MDC traceId: abc123 │  ──→  │ MDC traceId: null    │
└─────────────────────┘       └─────────────────────┘
```

`@Async` 메서드는 다른 스레드에서 돌기 때문에 호출한 쪽의 ThreadLocal을 볼 수 없다.

### 대응

```java
@Service
public class NotificationService {

    // 방법 1: 비동기 메서드에 자체 트랜잭션 선언
    @Async
    @Transactional
    public void sendAsync(OrderRequest request) {
        logRepository.save(new NotificationLog(request)); // 자체 트랜잭션
    }

    // 방법 2: 필요한 값을 파라미터로 전달
    @Async
    public void sendAsync(Long orderId, String traceId, String username) {
        MDC.put("traceId", traceId); // 수동 설정
        try {
            // 비동기 처리
        } finally {
            MDC.clear();
        }
    }
}
```

| 전략 | 방법 | 적용 대상 |
|---|---|---|
| 자체 `@Transactional` 선언 | 비동기 메서드에 독립 트랜잭션 | DB 작업이 필요한 경우 |
| 파라미터로 값 전달 | ThreadLocal 값을 인자로 넘김 | traceId, userId 등 |
| SecurityContext 전파 | `DelegatingSecurityContextAsyncTaskExecutor`로 executor를 감싼다 | 인증 정보 전파. `MODE_INHERITABLETHREADLOCAL`은 스레드 풀에서 깨지니 쓰지 않는다(아래 「자주 깨지는 곳」) |
| TaskDecorator | 실행 전 ThreadLocal 복사 | MDC, SecurityContext 일괄 전파 |

### TaskDecorator로 ThreadLocal 전파

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setTaskDecorator(new MdcTaskDecorator());
        executor.initialize();
        return executor;
    }
}

public class MdcTaskDecorator implements TaskDecorator {

    @Override
    public Runnable decorate(Runnable runnable) {
        // 호출 스레드의 MDC 값을 캡처
        Map<String, String> contextMap = MDC.getCopyOfContextMap();

        return () -> {
            try {
                if (contextMap != null) {
                    MDC.setContextMap(contextMap); // 비동기 스레드에 설정
                }
                runnable.run();
            } finally {
                MDC.clear(); // 정리하지 않으면 다음 작업에 값이 남는다
            }
        };
    }
}
```

## 스레드 풀에서 값이 새는 문제

스레드 풀은 스레드를 다시 쓴다. ThreadLocal을 비우지 않으면 앞 요청의 값이 다음 요청까지 그대로 남는다.

```
요청 A (userId=100) → Thread-1에 ThreadLocal 저장 → 응답 → Thread-1 반환

요청 B (인증 안 됨) → Thread-1 재할당 → ThreadLocal에 userId=100이 남아있음 ❌
```

### 새는 코드

```java
// ❌ 위험: 정리하지 않음
public class UserContext {
    private static final ThreadLocal<Long> currentUserId = new ThreadLocal<>();

    public static void set(Long userId) {
        currentUserId.set(userId);
    }

    public static Long get() {
        return currentUserId.get();
    }

    public static void clear() {
        currentUserId.remove();
    }
}

// Interceptor에서 set만 하고 remove를 안 함
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, ...) {
        UserContext.set(extractUserId(request));
        return true;
    }
    // afterCompletion에서 remove를 안 하면 누수
}
```

### 고친 코드

```java
// ✅ 안전: afterCompletion에서 정리 (preHandle이 true를 돌려줬다면 핸들러가 예외를 던져도 불린다)
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, ...) {
        UserContext.set(extractUserId(request));
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                 Object handler, Exception ex) {
        UserContext.clear(); // 요청이 끝나면 비운다
    }
}
```

### 어디서 비우나

| 방식 | 정리 위치 | 비고 |
|---|---|---|
| Filter | `finally` 블록에서 `remove()` | doFilter 감싸기 |
| Interceptor | `afterCompletion()`에서 `remove()` | `preHandle`이 true를 돌려준 뒤라면 예외가 나도 호출됨. `preHandle`에서 값을 넣고 예외가 나면 남으니 Filter의 `finally`가 더 확실하다 |
| TaskDecorator | 비동기 작업의 `finally`에서 `clear()` | 위 예제 참고 |
| try-with-resources 패턴 | `AutoCloseable` 구현 | 범위가 명확한 경우 |

## 자주 깨지는 곳

- `@Async` 메서드가 호출자의 트랜잭션에 함께 묶인다고 믿으면, 호출자가 롤백해도 비동기 쪽 작업은 따로 간다. 함께 묶이지 않는다. DB 작업이 필요하면 비동기 메서드에 따로 `@Transactional`을 단다.
- `@Async` 메서드에서 `SecurityContextHolder`로 인증 정보를 꺼내면, 비어 있다. 파라미터로 넘기거나 TaskDecorator로 복사한다.
- ThreadLocal에 넣고 `remove()`를 하지 않으면, 스레드 풀에서 다음 요청으로 값이 샌다. `afterCompletion()`이나 `finally`에서 비운다.
- `CompletableFuture.supplyAsync()`를 그냥 쓰면, 호출 스레드의 MDC가 복사되지 않아 traceId가 사라진다.
- `InheritableThreadLocal`이면 풀린다고 생각하면, 스레드 풀에서는 그대로 깨진다. 값은 스레드를 새로 만들 때만 넘어가고, 풀에서 스레드를 다시 쓸 때는 넘어가지 않는다.

## 한 번에 설명하기

> Spring의 트랜잭션, SecurityContext, MDC는 모두 ThreadLocal에 묶여 있어서, `@Async`나 `CompletableFuture`로 스레드가 바뀌면 따라가지 않습니다.
>
> 그래서 비동기 메서드에서 DB 작업이 필요하면 그 메서드에 따로 `@Transactional`을 달고, traceId나 인증 정보는 파라미터로 넘기거나 TaskDecorator로 복사합니다.
>
> 스레드 풀은 스레드를 다시 쓰기 때문에, ThreadLocal은 `afterCompletion()`이나 `finally`에서 꼭 `remove()`합니다. 안 그러면 앞 사용자의 정보가 다음 요청에 남습니다.

## 꼬리 질문

> [!question]- @Async에서 트랜잭션이 동작하는가?
> 호출한 쪽 트랜잭션에는 들어가지 않습니다. 다른 스레드라서 ThreadLocal에 묶인 Connection이 없거든요. 비동기 메서드에 직접 `@Transactional`을 달면, 그 메서드만의 독립 트랜잭션으로 돕니다.

> [!question]- InheritableThreadLocal로 해결되지 않는 이유는?
> `InheritableThreadLocal`은 자식 스레드를 **만들 때**만 부모 값을 복사합니다. 스레드 풀은 이미 만든 스레드를 다시 쓰기 때문에, 작업을 받을 때는 값이 복사되지 않습니다.

> [!question]- ThreadLocal 누수가 보안 사고로 이어지는 경우는?
> Interceptor에서 로그인한 사용자 ID를 ThreadLocal에 넣고 지우지 않았다고 해 보죠. 그 스레드가 다음에 인증 안 된 요청을 받으면, 그 요청이 앞 사용자의 ID로 처리될 수 있습니다.

> [!question]- CompletableFuture에서 MDC traceId를 유지하려면?
> TaskDecorator를 단 `ThreadPoolTaskExecutor`를 `supplyAsync(task, executor)`의 두 번째 인자로 넘깁니다. executor 없이 부르면 `ForkJoinPool.commonPool`에서 돌아서 TaskDecorator가 적용되지 않습니다. 데코레이터는 작업을 넘기기 전에 호출 스레드의 MDC를 복사해 두고, 비동기 스레드에서 그 값을 넣은 뒤 실행하고, finally에서 지웁니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Async 메서드에서 기존 요청 스레드의 트랜잭션이 그대로 이어지지 않는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Spring 트랜잭션 컨텍스트는 주로 ThreadLocal에 묶여 있고 @Async는 다른 스레드에서 실행되기 때문이다." aria-pressed="false">A. 트랜잭션 컨텍스트가 ThreadLocal 기반인데 다른 스레드에서 실행되기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@Async가 항상 같은 스레드에서 실행되는 것은 아니다." aria-pressed="false">B. @Async가 같은 스레드에서 동기 실행되기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문제는 final 여부가 아니라 스레드 경계다." aria-pressed="false">C. 메서드명이 async로 끝나지 않기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>스레드 풀 환경에서 ThreadLocal 값을 정리하지 않으면 다음 요청에 이전 요청의 값이 남을 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="스레드가 재사용되므로 finally에서 remove하거나 명확한 정리 전략을 둬야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="스레드 풀에서는 요청마다 스레드가 폐기되지 않을 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>CompletableFuture에서 MDC traceId를 유지하려면 필요한 접근은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="작업 제출 시점의 MDC를 캡처하고 실행 스레드에서 복원한 뒤 finally에서 정리하는 TaskDecorator류 전략이 필요하다." aria-pressed="false">A. MDC를 캡처·복원·정리하는 executor/task decorator를 사용한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="InheritableThreadLocal은 스레드 풀 재사용 문제를 안정적으로 해결하지 못한다." aria-pressed="false">B. InheritableThreadLocal만 쓰면 모든 스레드 풀 문제가 해결된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="static 필드는 요청 간 오염과 동시성 문제를 만들 수 있다." aria-pressed="false">C. traceId를 static 변수에 저장한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 커밋 후 전용 스레드풀에서 발급
- [[inherited-access-system-incidents|이어받은 시스템의 장애 추적]]: `parallelStream` 안에서 풀린 트랜잭션

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Task Execution and Scheduling](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)
- [Spring Framework: Transaction-bound Events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[transaction-integration]]
- [[transactional-pitfalls]]
- [[aop]]
- [[01-core/java/java-concurrency-basics|java-concurrency-basics]]
- [[01-core/os/process-and-thread|process-and-thread]]