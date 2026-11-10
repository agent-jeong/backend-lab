---
title: "@Transactional 동작 원리와 롤백"
description: Spring의 트랜잭션 관리와 @Transactional 동작 원리
tags: [concept, spring]
---

# @Transactional 동작 원리와 롤백

Spring은 `@Transactional`을 AOP로 처리한다. 프록시가 메서드 앞뒤에서 트랜잭션을 시작하고, 커밋하거나 롤백한다.

어노테이션을 붙였다고 끝이 아니다. checked 예외는 기본으로 롤백되지 않고, 같은 클래스 안에서 부른 메서드에는 트랜잭션이 걸리지 않고, 전파 설정을 잘못 잡으면 의도하지 않은 커밋이나 롤백이 생긴다. 여기서는 롤백 규칙과 전파를 중심으로 본다.

> [!tip] 함께 읽기
> - [[transactional-pitfalls]]: `@Transactional`이 적용되지 않을 때 원인을 찾는 체크리스트
> - [[spring-transaction]]: 트랜잭션 주제 안에서 본 짧은 요약

## 동작

```
외부 호출 → 프록시 → 트랜잭션 시작 → 실제 메서드 실행 → 커밋 or 롤백
```

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        paymentService.pay(request.getPaymentInfo());
        // 예외 발생 시 전체 롤백
    }
}
```

프록시가 메서드 시작 전에 트랜잭션을 열고, 정상으로 끝나면 커밋, 예외가 나면 롤백한다.

## 어떤 예외에 롤백하나

```java
// 기본: unchecked 예외(RuntimeException)만 롤백
@Transactional
public void process() {
    throw new RuntimeException(); // 롤백 O
}

@Transactional
public void process() throws IOException {
    throw new IOException(); // 롤백 X (checked 예외)
}

// checked 예외도 롤백하려면 명시
@Transactional(rollbackFor = Exception.class)
public void process() throws IOException {
    throw new IOException(); // 롤백 O
}
```

| 예외 타입 | 기본 롤백 | 변경 방법 |
|---|---|---|
| RuntimeException (unchecked) | O | `noRollbackFor`로 제외 가능 |
| Exception (checked) | X | `rollbackFor`로 롤백 대상 추가 |
| Error | O | - |

## 전파 (Propagation)

```java
@Transactional(propagation = Propagation.REQUIRED)
public void outerMethod() {
    innerService.innerMethod();
}
```

| 전파 옵션 | 동작 | 실무 사용 |
|---|---|---|
| `REQUIRED` (기본값) | 기존 트랜잭션이 있으면 참여, 없으면 새로 생성 | 대부분 |
| `REQUIRES_NEW` | 항상 새 트랜잭션 생성, 기존 트랜잭션 일시 중지 | 독립 로깅, 알림 |
| `SUPPORTS` | 기존 트랜잭션이 있으면 참여, 없으면 트랜잭션 없이 실행 | 드물게 사용 |
| `NOT_SUPPORTED` | 트랜잭션 없이 실행, 기존 트랜잭션 일시 중지 | 드물게 사용 |

### REQUIRES_NEW: 트랜잭션은 나뉘어도 예외는 올라온다

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        try {
            notificationService.sendNotification(request);
        } catch (RuntimeException e) {
            log.warn("알림 저장 실패, 주문은 유지", e); // catch하지 않으면 주문도 롤백된다
        }
    }
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification(OrderRequest request) {
        // 별도 트랜잭션 → 여기서 롤백돼도 주문 트랜잭션은 롤백되지 않는다
    }
}
```

REQUIRES_NEW는 트랜잭션을 나눌 뿐 **예외를 막아 주지 않는다.** 내부에서 던진 예외가 외부 메서드로 올라오면 외부 트랜잭션도 롤백된다. "알림이 실패해도 주문은 유지"하려면 호출부에서 예외를 잡아야 한다.

REQUIRES_NEW를 쓰기 전에 두 가지를 더 본다.

- 외부 트랜잭션이 커넥션을 쥔 채로 내부가 커넥션을 하나 더 가져간다. 동시 요청이 몰리면 커넥션 풀이 바닥나서 서로를 기다리는 교착이 생길 수 있다.
- 외부가 나중에 롤백돼도 내부는 이미 커밋됐다. "주문은 롤백됐는데 알림 기록은 남는" 상태를 허용해도 되는지 먼저 정한다.

### REQUIRED 안에서 예외를 잡았는데 UnexpectedRollbackException이 나는 경우

```java
@Transactional
public void createOrder() {
    orderRepository.save(order);
    try {
        pointService.earn(userId); // REQUIRED, 내부에서 RuntimeException
    } catch (RuntimeException e) {
        log.warn("포인트 적립 실패", e);
    }
} // 커밋 시점에 UnexpectedRollbackException
```

`pointService.earn()`은 같은 트랜잭션에 참여한다. 예외가 프록시를 지나가는 순간 트랜잭션 전체가 rollback-only로 표시되고, 바깥에서 예외를 잡아도 이 표시는 되돌릴 수 없다. 포인트 실패와 무관하게 주문을 살리려면 `earn()`을 REQUIRES_NEW로 분리하거나, `earn()` 안에서 예외를 던지지 않도록 바꾼다.

## readOnly 트랜잭션

```java
@Transactional(readOnly = true)
public List<OrderResponse> getOrders() {
    return orderRepository.findAll().stream()
        .map(OrderResponse::from)
        .toList();
}
```

JPA가 변경 감지(dirty checking)를 건너뛰어 스냅샷 비교 비용이 줄어든다. DB에 따라 읽기 전용 쿼리 최적화가 추가로 적용될 수 있다. 조회 전용 메서드에는 습관처럼 붙인다.

## @Transactional이 동작하지 않는 경우

프록시를 거치지 않는 호출에는 걸리지 않는다. 내부 호출, private 메서드, final 클래스가 대표적이다. 실패 케이스 6가지와 진단 순서는 [[transactional-pitfalls]]에 정리했다.

## 자주 깨지는 곳

- **checked 예외에 `rollbackFor`를 주지 않는다.** 예외가 나도 커밋된다.
- **REQUIRED 내부 예외를 바깥에서 잡고 안심한다.** 트랜잭션이 이미 rollback-only라 커밋 시점에 `UnexpectedRollbackException`이 난다.
- **REQUIRES_NEW면 내부 실패가 바깥에 영향이 없다고 믿는다.** 예외가 올라오면 바깥도 롤백된다.
- **조회 메서드에 `readOnly = true`를 붙이지 않는다.** 쓸데없는 변경 감지 비용을 낸다.
- **트랜잭션 범위를 너무 넓게 잡는다.** DB 커넥션을 오래 쥐고 있게 된다.

## 한 번에 설명하기

> `@Transactional`은 프록시가 메서드 앞뒤에서 트랜잭션을 열고 닫는 구조입니다. 기본 롤백 대상은 RuntimeException과 Error이고, checked 예외는 `rollbackFor`로 추가합니다. 전파에서 실수가 많은 곳은 두 군데입니다. REQUIRED로 참여한 내부 메서드가 예외를 던지면 바깥에서 잡아도 rollback-only가 되어 `UnexpectedRollbackException`이 나고, REQUIRES_NEW는 트랜잭션만 나눌 뿐 예외 전파는 막지 않아서 호출부에서 잡아야 합니다.

## 꼬리 질문

> [!question]- checked 예외에서 롤백되지 않는 이유는?
> Spring의 기본 롤백 정책이 unchecked 예외(RuntimeException)와 Error만 대상이기 때문입니다. checked 예외는 호출자가 복구할 수 있다는 가정으로 롤백하지 않습니다. `rollbackFor`로 바꿀 수 있습니다.

> [!question]- `REQUIRED`와 `REQUIRES_NEW`의 차이는?
> `REQUIRED`는 기존 트랜잭션에 참여하고, `REQUIRES_NEW`는 항상 새 트랜잭션을 생성합니다. `REQUIRES_NEW`는 외부 트랜잭션이 롤백되어도 내부 트랜잭션이 독립적으로 커밋됩니다. 다만 내부 예외가 외부로 전파되면 외부도 롤백되므로 호출부에서 잡아야 하고, 커넥션을 하나 더 쓴다는 점도 따져야 합니다.

> [!question]- `readOnly = true`의 효과는?
> JPA 영속성 컨텍스트에서 변경 감지(dirty checking)를 생략해서 스냅샷 비교 비용이 줄어듭니다. DB에 따라 읽기 전용 최적화가 추가로 적용될 수 있습니다.

> [!question]- 트랜잭션 범위를 어떻게 설정해야 하는가?
> 꼭 필요한 범위만 묶습니다. 외부 API 호출이나 파일 I/O는 트랜잭션 밖으로 빼고, DB 작업만 안에 둡니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring @Transactional의 기본 롤백 규칙으로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="기본적으로 RuntimeException과 Error에서 롤백되고 checked exception은 rollbackFor 설정이 필요하다." aria-pressed="false">A. RuntimeException/Error는 롤백, checked exception은 기본 커밋</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 Exception이 기본 롤백 대상은 아니다." aria-pressed="false">B. 모든 Exception은 기본으로 롤백된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="롤백 여부는 예외 종류와 설정에 따라 달라진다." aria-pressed="false">C. 예외가 발생해도 항상 커밋된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>REQUIRES_NEW는 기존 트랜잭션에 참여하지 않고 별도 트랜잭션을 시작한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="기존 트랜잭션을 보류하고 독립 트랜잭션을 만들기 때문에 감사 로그나 outbox 등에서 신중히 사용한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="REQUIRES_NEW는 REQUIRED와 다르게 독립 트랜잭션 경계를 만든다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>readOnly = true의 실무 의미로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="JPA flush 최적화나 DB read-only 힌트 등으로 쓰일 수 있지만 쓰기 방지 보안 장치로만 믿으면 안 된다." aria-pressed="false">A. 읽기 최적화 힌트로 보고 쓰기 방지 장치로 과신하지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="readOnly가 모든 DB 쓰기를 물리적으로 항상 차단한다고 단정할 수 없다." aria-pressed="false">B. 어떤 환경에서도 INSERT/UPDATE가 100% 불가능해진다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="readOnly가 트랜잭션을 제거하는 것은 아니다." aria-pressed="false">C. 트랜잭션이 아예 생성되지 않는다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Spring Framework: Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html)
- [Spring Framework: Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)
- [Spring Framework: Rolling Back a Declarative Transaction](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[transactional-pitfalls]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/transaction-and-isolation|transaction-and-isolation]]
- [[01-core/jpa/transaction-and-flush|transaction-and-flush]]