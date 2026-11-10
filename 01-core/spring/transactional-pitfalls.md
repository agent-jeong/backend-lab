---
title: "@Transactional 동작 실패 케이스"
description: "@Transactional 미적용 원인을 빠르게 진단하는 체크리스트"
---

# @Transactional 동작 실패 케이스

`@Transactional`은 AOP 프록시로 동작한다. 그래서 호출이 프록시를 우회하거나 프록시가 아예 만들어지지 않으면 트랜잭션도 걸리지 않는다.

이 실패는 컴파일 에러 없이 런타임에만 드러나서 코드 리뷰로 걸러내기 어렵다. 어노테이션이 붙어 있으니 원인 후보에서 빠지고, 테스트에서는 되는데 운영에서 데이터가 어긋나는 식으로 나타난다. 아래 여섯 가지를 순서대로 확인한다.

## 원인 여섯 가지

### 1. 같은 클래스 내부 호출 (Self-Invocation)

```java
@Service
public class OrderService {

    public void process() {
        this.createOrder(); // ❌ 프록시를 거치지 않음
    }

    @Transactional
    public void createOrder() {
        // 트랜잭션 미적용
    }
}
```

`this`는 프록시가 아니라 실제 객체를 가리킨다. 메서드를 별도 클래스로 떼어 내는 게 정석이다. `ApplicationContext`에서 빈을 다시 꺼내 호출하는 방법도 있지만 권하지 않는다.

### 2. private (및 버전에 따라 non-public) 메서드

```java
@Transactional
private void internalProcess() { // ❌ CGLIB이 오버라이드 불가
    // 트랜잭션 미적용
}
```

CGLIB 프록시는 상속 기반이라 `private`을 오버라이드하지 못한다. 그 밖의 non-public 메서드는 버전과 프록시 방식에 따라 다르다.

| 버전 | CGLIB(클래스 기반) 프록시 | JDK(인터페이스 기반) 프록시 |
|---|---|---|
| Spring 5.x (Boot 2) | `public`만 적용 | `public`만 |
| Spring 6.0+ (Boot 3) | `protected`, package-private도 적용 | `public`만 |

버전과 상관없이 안전한 건 `public`이다. 어느 경우든 외부 빈에서 프록시를 거쳐 호출해야 한다.

### 3. final 클래스 또는 메서드

```java
@Service
public final class OrderService { // ❌ CGLIB이 상속 불가
    @Transactional
    public void createOrder() { }
}
```

CGLIB은 클래스를 상속해 프록시를 만드므로 `final`이면 만들 수 없다.

### 4. checked 예외에서 롤백 안 됨

```java
@Transactional
public void process() throws IOException {
    throw new IOException(); // ❌ 기본 설정에서 롤백되지 않음
}
```

Spring 기본 정책은 `RuntimeException`과 `Error`만 롤백한다. checked 예외도 롤백하려면 `@Transactional(rollbackFor = Exception.class)`를 명시한다.

### 5. try-catch로 예외를 삼킴

```java
@Transactional
public void process() {
    try {
        riskyOperation();
    } catch (RuntimeException e) {
        log.error("에러 발생", e); // ❌ 예외가 프록시까지 전파되지 않음
    }
}
```

프록시는 메서드 밖으로 예외가 나와야 롤백을 결정한다. 안에서 catch하면 프록시는 정상 완료로 보고 커밋한다. catch한 뒤 `throw`로 다시 던지거나, `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`를 호출한다.

### 6. REQUIRES_NEW를 내부 호출로 사용

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder() {
        this.saveLog(); // ❌ 내부 호출 → REQUIRES_NEW 무시
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLog() { }
}
```

내부 호출이라 프록시를 거치지 않고, 전파 설정도 함께 무시된다. `saveLog()`를 별도 빈으로 뺀다.

## 진단 순서

```
@Transactional이 안 먹힌다
  ├─ 호출 경로가 외부(다른 빈)에서 오는가?
  │   └─ 아니오 → 내부 호출 문제 (self-invocation)
  ├─ 메서드가 public인가? (Spring 6+ CGLIB은 protected/package-private도 허용)
  │   └─ 아니오 → private/final 문제
  ├─ 예외가 프록시까지 전파되는가?
  │   └─ 아니오 → try-catch로 삼키는 문제
  ├─ 예외가 RuntimeException인가?
  │   └─ 아니오 → checked 예외 롤백 정책 문제
  └─ 클래스가 Spring 빈으로 등록되어 있는가?
      └─ 아니오 → 프록시 자체가 생성되지 않음
```

## 자주 깨지는 곳

- **리팩터링으로 메서드를 한 클래스에 합친다.** 다른 빈 호출이 내부 호출로 바뀌어 트랜잭션이 사라진다.
- **어노테이션이 붙어 있으니 동작한다고 가정한다.** 위 여섯 가지 중 하나에 걸리면 조용히 빠진다.
- **catch로 예외를 삼킨다.** 테스트에서는 멀쩡해 보이고 운영에서 데이터가 어긋난다.
- **Kotlin에서 all-open 플러그인을 빠뜨린다.** Kotlin 클래스와 메서드는 기본이 `final`이다. `kotlin-spring`(all-open) 플러그인이 `@Service`, `@Transactional` 등이 붙은 클래스를 `open`으로 바꿔 주므로, 플러그인이 빠지면 프록시가 만들어지지 않는다.

## 면접에서 말하기

> `@Transactional`이 안 걸리는 원인은 대부분 호출이 프록시를 우회하는 구조입니다. 가장 흔한 건 같은 클래스 내부 호출이고, 메서드를 별도 빈으로 떼어 내서 해결합니다. 그다음이 checked 예외가 기본으로 롤백되지 않는 것과, try-catch로 예외를 삼켜 커밋되는 경우입니다. 저는 의심되면 트랜잭션 DEBUG 로그로 시작과 커밋이 실제로 찍히는지부터 봅니다.

## 꼬리 질문

> [!question]- 내부 호출 문제를 어떻게 발견할 수 있는가?
> 통합 테스트에서 예외가 난 뒤 DB에 데이터가 남아 있으면 의심합니다. 트랜잭션 로그(`logging.level.org.springframework.transaction=DEBUG`)로 트랜잭션 시작과 커밋 여부를 확인할 수도 있습니다.

> [!question]- `@Transactional`을 테스트에서 검증하는 방법은?
> 예외를 강제로 낸 뒤 DB 상태를 확인합니다. `TransactionSynchronizationManager.isActualTransactionActive()`로 트랜잭션 활성 여부를 직접 검증해도 됩니다.

## 점검 퀴즈

아래 문항은 개념을 실제로 설명할 수 있는지 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Transactional이 적용되지 않는 대표적인 내부 호출 문제는 무엇인가?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="같은 클래스의 메서드를 this로 호출하면 프록시를 거치지 않아 트랜잭션 advice가 실행되지 않을 수 있다." aria-pressed="false">A. 같은 클래스 내부에서 this로 호출해 프록시를 우회하는 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="메서드 이름 길이와 프록시 적용은 직접 관련이 없다." aria-pressed="false">B. 메서드 이름이 너무 짧은 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="파라미터 개수 자체가 트랜잭션 적용 실패 원인은 아니다." aria-pressed="false">C. 파라미터가 두 개 이상인 경우</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>private 메서드에 @Transactional을 붙이면 외부 프록시 호출 대상이 아니므로 기대대로 동작하지 않을 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Spring AOP는 프록시를 통한 public 메서드 호출 경계에서 주로 동작한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="private 메서드는 프록시가 외부에서 호출할 수 있는 진입점이 아니다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Transactional 동작 여부를 테스트에서 확인하는 방법으로 가장 적절한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="실제 프록시를 통한 호출 경로와 롤백/커밋 결과를 검증해야 한다. 단순히 어노테이션 존재만 보면 부족하다." aria-pressed="false">A. 프록시 호출 경로와 DB 반영/롤백 결과를 함께 검증한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="어노테이션이 붙었다고 항상 적용되는 것은 아니다." aria-pressed="false">B. 리플렉션으로 어노테이션 존재만 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="로그가 없다고 트랜잭션이 없는 것은 아니며 결과 검증이 필요하다." aria-pressed="false">C. 콘솔 로그가 조용하면 정상으로 본다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[aop]]
- [[transaction-integration]]
- [[02-practical-backend/transaction/spring-transaction|spring-transaction]]