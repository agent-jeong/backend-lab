---
title: AOP 동작 원리와 프록시 제약
description: Spring AOP가 프록시로 동작하는 방식과, 그래서 부가 기능이 빠지는 경우
tags: [concept, spring]
---

# AOP 동작 원리와 프록시 제약

AOP(Aspect-Oriented Programming)는 트랜잭션, 로깅, 권한 체크처럼 여러 메서드에 똑같이 붙는 코드를 비즈니스 로직 밖으로 빼내는 방법이다.

Spring AOP는 프록시로 동작한다. 그래서 `@Transactional`을 붙여도 내부 호출, `private` 메서드, `final` 메서드에서는 아무 경고 없이 빠진다. `final` 클래스는 CGLIB이 상속하지 못해 애플리케이션이 뜰 때 바로 실패한다. 주문 저장과 재고 차감을 한 트랜잭션으로 묶었다고 믿었는데, 실제로는 각자 따로 커밋되는 일이 이렇게 생긴다.

## 용어

| 용어 | 뜻 | 예시 |
|---|---|---|
| Aspect | 공통 코드를 한 덩어리로 묶은 것 | 트랜잭션 관리, 로깅 |
| Advice | 실행할 부가 기능 | `@Before`, `@After`, `@Around` |
| Pointcut | Advice를 적용할 대상 | `execution(* com.example.service.*.*(..))` |
| JoinPoint | Advice가 끼어들 수 있는 지점 | 메서드 실행 시점 |
| Proxy | 실제 객체 앞에 세워 두는 대리 객체 | CGLIB 프록시 |

## 동작

호출은 프록시를 먼저 거친다.

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

Spring은 `OrderService`를 감싼 프록시를 만든다. 외부에서 `createOrder()`를 부르면 프록시가 트랜잭션을 시작하고, 실제 메서드를 호출한 뒤, 커밋하거나 롤백한다.

### 프록시를 만드는 두 방식

| 방식 | 특징 |
|---|---|
| JDK 동적 프록시 | 인터페이스를 구현해 만든다. 인터페이스가 있는 클래스에만 쓸 수 있다 |
| CGLIB 프록시 | 클래스를 상속해 만든다. 인터페이스가 없어도 된다 |

Spring Boot는 `proxyTargetClass=true`가 기본값이라 인터페이스가 있든 없든 CGLIB 프록시를 쓴다.

### 프록시라서 생기는 제약

프록시를 거치지 않는 호출에는 AOP가 걸리지 않는다. 같은 클래스 안에서 자기 메서드를 부르는 경우, `private` 메서드, `final` 메서드가 그렇다. `final` 클래스는 프록시를 만들 수 없어서, 조용히 빠지는 대신 기동할 때 `Could not generate CGLIB subclass` 오류로 실패한다. 실패 사례와 확인하는 방법은 [[transactional-pitfalls|@Transactional 동작 실패 케이스]]에 모아 두었다.

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

`@Around`는 메서드 실행 앞뒤를 모두 감싸는 Advice다. 실제 메서드를 부를지 말지도 여기서 정한다.

## Advice 종류

| Advice | 실행 시점 | 용도 |
|---|---|---|
| `@Before` | 메서드 실행 전 | 권한 체크, 파라미터 검증 |
| `@After` | 메서드 실행 후 (성공/실패 무관) | 리소스 정리 |
| `@AfterReturning` | 정상 반환 후 | 결과 로깅 |
| `@AfterThrowing` | 예외 발생 후 | 에러 로깅, 알림 |
| `@Around` | 전후 모두 | 실행 시간 측정, 트랜잭션 |

## 자주 깨지는 곳

- `@Around`에서 `joinPoint.proceed()`를 빠뜨리면, 실제 메서드가 아예 실행되지 않는다.
- AOP가 늘 걸린다고 믿으면, 내부 호출, `private`, `final` 메서드처럼 프록시를 거치지 않는 곳에서 트랜잭션이나 로깅이 빠진 걸 모르고 지나간다.
- 이것저것 AOP로 빼면, 코드만 봐서는 무엇이 언제 실행되는지 알 수 없게 된다.

## 한 번에 설명하기

> Spring AOP는 프록시로 동작합니다. 외부에서 메서드를 부르면 프록시가 먼저 트랜잭션이나 로깅 같은 부가 기능을 실행하고, 그다음 실제 객체를 호출합니다.
>
> 그래서 프록시를 거치지 않는 내부 호출, `private` 메서드, `final` 메서드에는 걸리지 않습니다. `@Transactional`이 안 먹을 때 저는 이 세 가지부터 봅니다([[transactional-pitfalls]]).

## 꼬리 질문

> [!question]- JDK 동적 프록시와 CGLIB의 차이는?
> JDK 동적 프록시는 인터페이스를 구현해서 만들고, CGLIB은 클래스를 상속해서 만듭니다. Spring Boot는 기본으로 CGLIB을 씁니다. 인터페이스가 없어도 되지만, 상속이 안 되는 `final` 클래스는 프록시로 만들 수 없습니다.

> [!question]- AOP를 실무에서 직접 구현하는 경우는?
> 실행 시간 측정, API 요청과 응답 로깅, 권한 체크, 재시도(retry) 같은 데서 직접 만들어 씁니다. 다만 너무 많이 쓰면 코드만 봐서는 흐름을 따라가기 어려워서, 여러 곳에 정말 똑같이 붙는 것만 AOP로 뺍니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring AOP가 기본적으로 프록시 기반이라는 사실이 만드는 대표 제약은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="같은 클래스 내부 메서드 호출은 프록시를 거치지 않아 AOP advice가 적용되지 않을 수 있다." aria-pressed="false">A. self-invocation에서는 advice가 적용되지 않을 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="AOP가 SQL 실행을 자동으로 제거하지 않는다." aria-pressed="false">B. 모든 DB 호출이 자동으로 캐시된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="AOP는 런타임 프록시로 동작한다. 컴파일 에러와는 관계없다." aria-pressed="false">C. AOP를 쓰면 컴파일이 불가능하다.</button>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Aspect Oriented Programming](https://docs.spring.io/spring-framework/reference/core/aop.html)
- [Spring Framework: Proxying Mechanisms](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[spring-mvc-request-flow]]
- [[transaction-integration]]
- [[transactional-pitfalls]]