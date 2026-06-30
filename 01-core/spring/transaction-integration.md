---
title: "@Transactional 동작 원리와 롤백"
description: Spring의 트랜잭션 관리와 @Transactional 동작 원리
---

# @Transactional 동작 원리와 롤백

## 한 줄 정의

Spring은 `@Transactional`을 통해 AOP 기반으로 트랜잭션을 관리하며, 프록시가 메서드 실행 전후에 트랜잭션 시작, 커밋, 롤백을 자동으로 처리한다.

## 실무에서 왜 중요한가

Spring 트랜잭션을 제대로 이해하지 못하면 다음 문제가 생긴다.

- `@Transactional`을 붙였는데 롤백이 되지 않는다.
- 같은 클래스 내부 호출에서 트랜잭션이 적용되지 않는다.
- checked 예외가 발생했는데 롤백되지 않는 이유를 모른다.
- 트랜잭션 전파 설정을 잘못해서 의도하지 않은 커밋이나 롤백이 발생한다.
- readOnly 트랜잭션의 의미와 효과를 모른다.

## @Transactional 동작 원리

`@Transactional`은 AOP 프록시 기반으로 동작한다.

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

프록시가 메서드 시작 전에 트랜잭션을 열고, 정상 완료 시 커밋, 예외 발생 시 롤백한다.

## 롤백 규칙

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

## 트랜잭션 전파 (Propagation)

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

### REQUIRES_NEW 활용

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        notificationService.sendNotification(request); // 알림 실패해도 주문은 유지
    }
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification(OrderRequest request) {
        // 별도 트랜잭션 → 실패해도 주문 트랜잭션에 영향 없음
    }
}
```

## readOnly 트랜잭션

```java
@Transactional(readOnly = true)
public List<OrderResponse> getOrders() {
    return orderRepository.findAll().stream()
        .map(OrderResponse::from)
        .toList();
}
```

- JPA에서 변경 감지(dirty checking)를 생략해서 성능이 향상된다.
- DB에 따라 읽기 전용 쿼리 최적화가 적용될 수 있다.
- 조회 전용 메서드에는 `readOnly = true`를 습관적으로 붙인다.

## @Transactional이 동작하지 않는 경우

`@Transactional`은 AOP 프록시 기반이므로 내부 호출, private 메서드, final 클래스 등에서 동작하지 않을 수 있다.

구체적인 실패 케이스 6가지와 진단 플로우는 [[transactional-pitfalls]]에서 다룬다.

## 자주 나는 실수

- checked 예외에서 롤백이 안 되는 것을 모르고 `rollbackFor`를 설정하지 않는다.
- `readOnly = true`를 조회 메서드에 붙이지 않는다.
- 트랜잭션 범위를 너무 넓게 잡아서 DB 커넥션 점유 시간이 길어진다.

## 핵심 요약

Spring의 `@Transactional`은 AOP 프록시 기반으로 동작합니다.
프록시가 메서드 실행 전에 트랜잭션을 시작하고, 정상 완료 시 커밋, 예외 발생 시 롤백합니다.

기본적으로 unchecked 예외(RuntimeException)만 롤백합니다.
checked 예외도 롤백하려면 `rollbackFor = Exception.class`를 설정해야 합니다.

프록시 제약으로 동작하지 않는 경우는 [[transactional-pitfalls]]를 참고합니다.
조회 전용 메서드에는 `readOnly = true`를 설정해서 변경 감지를 생략하는 것이 좋습니다.

## 꼬리 질문

> [!question]- checked 예외에서 롤백되지 않는 이유는?
> Spring의 기본 롤백 정책이 unchecked 예외(RuntimeException)와 Error만 대상이기 때문입니다. checked 예외는 호출자가 복구할 수 있다는 가정으로 롤백하지 않습니다. `rollbackFor`로 변경할 수 있습니다.

> [!question]- `REQUIRED`와 `REQUIRES_NEW`의 차이는?
> `REQUIRED`는 기존 트랜잭션에 참여하고, `REQUIRES_NEW`는 항상 새 트랜잭션을 생성합니다. `REQUIRES_NEW`는 외부 트랜잭션이 롤백되어도 내부 트랜잭션이 독립적으로 커밋됩니다. 알림, 로그 저장 등에 사용합니다.

> [!question]- `readOnly = true`의 효과는?
> JPA 영속성 컨텍스트에서 변경 감지(dirty checking)를 생략해서 스냅샷 비교 비용이 줄어듭니다. DB에 따라 읽기 전용 최적화가 추가로 적용될 수 있습니다.

> [!question]- 트랜잭션 범위를 어떻게 설정해야 하는가?
> 꼭 필요한 범위만 트랜잭션으로 묶어야 합니다. 외부 API 호출이나 파일 I/O는 트랜잭션 밖에서 처리하고, DB 작업만 트랜잭션 안에 포함시키는 것이 좋습니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

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
    <p class="quiz-question"><span class="quiz-label">객관식</span>readOnly = true의 실무적 의미로 가장 적절한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="JPA flush 최적화나 DB read-only 힌트 등으로 쓰일 수 있지만 쓰기 방지 보안 장치로만 믿으면 안 된다." aria-pressed="false">A. 읽기 최적화 힌트로 보고 쓰기 방지 장치로 과신하지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="readOnly가 모든 DB 쓰기를 물리적으로 항상 차단한다고 단정할 수 없다." aria-pressed="false">B. 어떤 환경에서도 INSERT/UPDATE가 100% 불가능해진다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="readOnly가 트랜잭션을 제거하는 것은 아니다." aria-pressed="false">C. 트랜잭션이 아예 생성되지 않는다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[transactional-pitfalls]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/transaction-and-isolation|transaction-and-isolation]]
- [[01-core/jpa/transaction-and-flush|transaction-and-flush]]