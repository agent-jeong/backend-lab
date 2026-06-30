---
title: AOP 동작 원리와 프록시 제약
description: Spring AOP의 동작 원리와 프록시 기반 제약
---

# AOP 동작 원리와 프록시 제약

## 한 줄 정의

AOP(Aspect-Oriented Programming)는 트랜잭션, 로깅, 보안 같은 공통 관심사를 비즈니스 로직에서 분리하는 프로그래밍 기법이다.

## 실무에서 왜 중요한가

AOP를 이해하지 못하면 다음 문제가 생긴다.

- `@Transactional`을 붙였는데 트랜잭션이 동작하지 않는 원인을 모른다.
- 같은 클래스 내부에서 메서드를 호출했는데 AOP가 적용되지 않는다.
- `private` 메서드에 `@Transactional`을 붙여도 동작하지 않는 이유를 모른다.
- 프록시 기반 AOP의 제약을 이해하지 못해서 런타임에 예상과 다른 동작이 발생한다.

## AOP 핵심 용어

| 용어 | 의미 | 예시 |
|---|---|---|
| Aspect | 공통 관심사를 모듈화한 것 | 트랜잭션 관리, 로깅 |
| Advice | 실행할 부가 기능 | `@Before`, `@After`, `@Around` |
| Pointcut | Advice를 적용할 대상 지정 | `execution(* com.example.service.*.*(..))` |
| JoinPoint | Advice가 적용될 수 있는 지점 | 메서드 실행 시점 |
| Proxy | AOP를 적용하기 위해 생성되는 대리 객체 | CGLIB 프록시 |

## Spring AOP의 동작 원리

Spring AOP는 **프록시 기반**으로 동작한다.

```
클라이언트 → 프록시 객체 → 부가 기능(Advice) 실행 → 실제 객체(Target) 메서드 실행
```

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        // 비즈니스 로직
    }
}
```

Spring이 `OrderService`의 프록시 객체를 생성한다. 외부에서 `createOrder()`를 호출하면 프록시가 트랜잭션을 시작하고, 실제 메서드를 호출한 뒤, 트랜잭션을 커밋하거나 롤백한다.

### 프록시 생성 방식

| 방식 | 특징 |
|---|---|
| JDK 동적 프록시 | 인터페이스 기반 프록시. 인터페이스를 구현한 클래스에만 적용 가능 |
| CGLIB 프록시 | 클래스 상속 기반 프록시. 인터페이스 없이도 적용 가능 |

Spring Boot는 `proxyTargetClass=true`가 기본값이므로, **인터페이스 유무와 관계없이 CGLIB 프록시를 사용**한다.

## 프록시 기반 AOP의 제약

프록시 기반이기 때문에 **내부 호출, private 메서드, final 클래스**에서는 AOP가 적용되지 않는다.

대표적인 실패 케이스와 진단 방법은 [[transactional-pitfalls|@Transactional 동작 실패 케이스]]에서 상세하게 다룬다.

## 커스텀 AOP 예시

```java
@Aspect
@Component
public class ExecutionTimeAspect {

    @Around("execution(* com.example.service.*.*(..))")
    public Object measureTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();

        Object result = joinPoint.proceed(); // 실제 메서드 실행

        long elapsed = System.currentTimeMillis() - start;
        log.info("{} executed in {}ms", joinPoint.getSignature(), elapsed);

        return result;
    }
}
```

`@Around`는 메서드 실행 전후 모두 제어할 수 있는 가장 강력한 Advice다.

## Advice 종류

| Advice | 실행 시점 | 용도 |
|---|---|---|
| `@Before` | 메서드 실행 전 | 권한 체크, 파라미터 검증 |
| `@After` | 메서드 실행 후 (성공/실패 무관) | 리소스 정리 |
| `@AfterReturning` | 정상 반환 후 | 결과 로깅 |
| `@AfterThrowing` | 예외 발생 후 | 에러 로깅, 알림 |
| `@Around` | 전후 모두 | 실행 시간 측정, 트랜잭션 |

## 자주 나는 실수

- `@Around`에서 `joinPoint.proceed()`를 호출하지 않아서 실제 메서드가 실행되지 않는다.
- AOP를 남용해서 코드 흐름을 추적하기 어렵게 만든다.
- 프록시 제약(내부 호출, private, final)을 모르고 AOP가 항상 동작한다고 가정한다.

## 핵심 요약

Spring AOP는 프록시 기반으로 동작합니다.
외부에서 메서드를 호출하면 프록시가 부가 기능(트랜잭션, 로깅 등)을 실행한 뒤 실제 객체의 메서드를 호출합니다.

프록시 기반이기 때문에 내부 호출, `private`, `final`에서는 AOP가 적용되지 않습니다.
구체적인 실패 케이스와 진단 방법은 [[transactional-pitfalls]]를 참고합니다.

## 꼬리 질문

> [!question]- JDK 동적 프록시와 CGLIB의 차이는?
> JDK 동적 프록시는 인터페이스 기반이고 CGLIB은 클래스 상속 기반입니다. Spring Boot는 기본적으로 CGLIB을 사용합니다. CGLIB은 인터페이스가 없어도 프록시를 만들 수 있지만 `final` 클래스에는 사용할 수 없습니다.

> [!question]- AOP를 실무에서 직접 구현하는 경우는?
> 실행 시간 측정, API 요청/응답 로깅, 권한 체크, 재시도(retry) 로직 등에서 직접 구현합니다. 단, 과도한 AOP는 코드 흐름을 추적하기 어렵게 만들므로 꼭 필요한 경우에만 사용합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring AOP가 기본적으로 프록시 기반이라는 사실이 만드는 대표 제약은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="같은 클래스 내부 메서드 호출은 프록시를 거치지 않아 AOP advice가 적용되지 않을 수 있다." aria-pressed="false">A. self-invocation에서는 advice가 적용되지 않을 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="AOP가 SQL 실행을 자동으로 제거하지 않는다." aria-pressed="false">B. 모든 DB 호출이 자동으로 캐시된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="AOP는 런타임 프록시를 통해 동작할 수 있으며 컴파일 에러가 핵심은 아니다." aria-pressed="false">C. AOP를 쓰면 컴파일이 불가능하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>JDK 동적 프록시는 인터페이스 기반이고, CGLIB은 클래스를 상속해 프록시를 만든다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="이 차이 때문에 인터페이스 유무, final 클래스/메서드 여부가 프록시 생성에 영향을 준다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="두 방식은 프록시 생성 방식이 다르다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>AOP를 직접 구현하기 적합한 실무 사례는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="여러 계층에 반복되는 로깅, 권한 체크, 감사 기록, 메트릭 수집 같은 횡단 관심사에 적합하다." aria-pressed="false">A. 여러 메서드에 공통으로 적용되는 횡단 관심사</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="핵심 비즈니스 규칙을 AOP로 숨기면 흐름 추적이 어려워진다." aria-pressed="false">B. 주문 상태 전이의 핵심 분기 로직 전체</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="단순 조건문을 모두 AOP로 바꾸는 것은 과한 추상화다." aria-pressed="false">C. 한 메서드 안에서만 쓰는 단순 if문</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[spring-mvc-request-flow]]
- [[transaction-integration]]
- [[transactional-pitfalls]]