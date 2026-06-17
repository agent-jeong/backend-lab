---
title:  @Async와 ThreadLocal 함정
description: ThreadLocal 기반 Spring 상태 관리가 비동기와 스레드 풀에서 깨지는 원인과 대응
---

#  @Async와 ThreadLocal 함정

## 한 줄 정의

Spring의 트랜잭션, SecurityContext, MDC는 모두 ThreadLocal 기반이므로, @Async나 CompletableFuture로 스레드가 바뀌면 전파되지 않고, 스레드 풀에서 재사용되면 이전 값이 남는다.

## 실무에서 왜 문제 되는가

- `@Async` 메서드에서 DB 저장이 커밋되지 않거나 별도 트랜잭션으로 동작하는 이유를 모른다.
- 비동기 작업에서 `SecurityContextHolder.getContext()`가 null이 되는 이유를 모른다.
- 로그에 traceId가 비동기 구간에서 사라진다 (MDC).
- 스레드 풀에서 이전 요청의 사용자 정보가 다음 요청에 노출되는 보안 사고가 난다.
- 면접에서 "@Async에서 트랜잭션이 동작하는가?"는 단골 꼬리 질문이다.

## ThreadLocal 동작 원리

ThreadLocal은 각 스레드가 독립적으로 값을 저장하는 저장소다. 같은 변수명이지만 스레드마다 다른 값을 가진다.

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

**핵심**: 이 모든 것이 "현재 스레드"에 바인딩된다. 스레드가 바뀌면 전부 끊긴다.

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
        logRepository.save(new NotificationLog(request)); // 별도 트랜잭션 필요
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

**원인**: `@Async`는 별도 스레드에서 실행되므로 호출자의 ThreadLocal에 접근할 수 없다.

### 대응 전략

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
| SecurityContext 전파 설정 | `MODE_INHERITABLETHREADLOCAL` | 인증 정보 전파 |
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
                MDC.clear(); // 반드시 정리
            }
        };
    }
}
```

## 스레드 풀 + ThreadLocal 누수

스레드 풀은 스레드를 **재사용**한다. ThreadLocal을 정리하지 않으면 이전 요청의 값이 다음 요청에 남는다.

```
요청 A (userId=100) → Thread-1에 ThreadLocal 저장 → 응답 → Thread-1 반환

요청 B (인증 안 됨) → Thread-1 재할당 → ThreadLocal에 userId=100이 남아있음 ❌
```

### 누수가 발생하는 패턴

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

### 올바른 패턴

```java
// ✅ 안전: afterCompletion에서 반드시 정리
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, ...) {
        UserContext.set(extractUserId(request));
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                 Object handler, Exception ex) {
        UserContext.remove(); // 반드시 정리
    }
}
```

### 정리 위치

| 방식 | 정리 위치 | 비고 |
|---|---|---|
| Filter | `finally` 블록에서 `remove()` | doFilter 감싸기 |
| Interceptor | `afterCompletion()`에서 `remove()` | 예외 시에도 호출됨 |
| TaskDecorator | 비동기 작업의 `finally`에서 `clear()` | 위 예제 참고 |
| try-with-resources 패턴 | `AutoCloseable` 구현 | 범위가 명확한 경우 |

## 자주 나는 실수

- `@Async` 메서드가 호출자의 트랜잭션에 참여한다고 가정한다.
- `@Async` 메서드에서 `SecurityContextHolder`로 인증 정보를 꺼내려 한다.
- ThreadLocal에 값을 저장하고 `remove()`를 호출하지 않아서 스레드 풀에서 누수된다.
- `CompletableFuture.supplyAsync()`에서 MDC traceId가 사라지는 이유를 모른다.
- `InheritableThreadLocal`을 쓰면 해결된다고 생각하지만, 스레드 풀에서는 스레드 생성 시점에만 상속되므로 재사용 시에는 전파되지 않는다.

## 핵심 요약

Spring의 트랜잭션, SecurityContext, MDC는 모두 ThreadLocal에 바인딩됩니다.
`@Async`나 `CompletableFuture`로 스레드가 바뀌면 이 값들이 전파되지 않습니다.

비동기 메서드에서 DB 작업이 필요하면 자체 `@Transactional`을 선언해야 합니다.
traceId나 인증 정보가 필요하면 파라미터로 전달하거나 TaskDecorator로 복사합니다.

스레드 풀에서 ThreadLocal을 정리하지 않으면 이전 요청의 값이 다음 요청에 남는 보안/정합성 문제가 발생합니다.
`afterCompletion()` 또는 `finally`에서 반드시 `remove()`를 호출해야 합니다.

## 꼬리 질문

> [!question]- @Async에서 트랜잭션이 동작하는가?
> 호출자의 트랜잭션에는 참여하지 않습니다. 별도 스레드이므로 ThreadLocal에 바인딩된 Connection이 없습니다. 비동기 메서드 자체에 `@Transactional`을 선언하면 독립 트랜잭션으로 동작합니다.

> [!question]- InheritableThreadLocal로 해결되지 않는 이유는?
> `InheritableThreadLocal`은 자식 스레드 **생성 시점**에만 부모 값을 복사합니다. 스레드 풀은 스레드를 재사용하므로 생성이 아닌 재할당 시에는 값이 복사되지 않습니다.

> [!question]- ThreadLocal 누수가 보안 사고로 이어지는 경우는?
> Interceptor에서 인증된 사용자 ID를 ThreadLocal에 저장하고 정리하지 않으면, 같은 스레드에 할당된 다음 요청(인증 안 된 요청)에서 이전 사용자의 ID로 동작할 수 있습니다.

> [!question]- CompletableFuture에서 MDC traceId를 유지하려면?
> TaskDecorator 패턴으로 작업 실행 전 호출 스레드의 MDC를 캡처하고, 비동기 스레드에서 설정한 뒤, finally에서 정리합니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[transaction-integration]]
- [[transactional-pitfalls]]
- [[aop]]
- [[01-core/java/java-concurrency-basics|java-concurrency-basics]]
- [[01-core/os/process-and-thread|process-and-thread]]