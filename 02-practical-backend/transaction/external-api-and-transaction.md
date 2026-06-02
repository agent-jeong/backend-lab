---
title: 외부 API와 트랜잭션
description: 외부 시스템 호출과 DB 트랜잭션을 함께 다룰 때의 실패 대응 기준
---

# 외부 API와 트랜잭션

## 한 줄 정의

외부 API는 DB 트랜잭션으로 rollback할 수 없는 부작용이므로, DB 변경과 같은 방식으로 묶지 않고 실패와 재시도를 별도로 설계해야 한다.

## 실무에서 왜 문제 되는가

- DB는 rollback됐지만 외부 결제는 승인되는 불일치가 생길 수 있다.
- 외부 API 지연 때문에 DB 커넥션과 락을 오래 점유할 수 있다.
- 외부 API 성공 후 애플리케이션이 장애 나면 DB 상태가 갱신되지 않을 수 있다.
- 재시도 시 외부 요청이 중복 처리될 수 있다.

## 동작 원리

1. 애플리케이션이 DB 상태를 변경한다.
2. 외부 API를 호출한다.
3. DB commit, 외부 API 성공, 애플리케이션 장애가 서로 다른 순서로 발생할 수 있다.
4. DB 트랜잭션 rollback은 외부 시스템에 이미 전달된 요청을 되돌리지 못한다.
5. 따라서 상태 모델, 멱등키, 재시도, 보상 처리로 최종 정합성을 맞춘다.

## 실무 판단 기준

| 상황 | 전략 | 이유 |
|---|---|---|
| 결제 승인 요청 | 주문 pending 저장 후 외부 호출 | 승인 전후 상태를 명확히 남긴다 |
| 알림 발송 | commit 이후 비동기 발송 | 알림 실패가 핵심 거래 rollback을 만들지 않게 한다 |
| 중복 요청 위험 | idempotency key 사용 | 재시도해도 한 번만 처리되게 한다 |
| 외부 성공 후 DB 실패 | 보상 또는 상태 복구 작업 | 외부 부작용은 rollback되지 않는다 |
| 호출 지연 가능 | 짧은 timeout과 circuit breaker | DB 자원 점유와 장애 전파를 줄인다 |

## 자주 나는 실수

- `@Transactional` 안에서 결제, 배송, 알림 API를 호출한다.
- 외부 API 성공 응답을 받은 뒤 DB commit이 반드시 성공한다고 가정한다.
- timeout이 발생했을 때 실패인지 성공인지 확인하지 않는다.
- 재시도에 멱등키를 사용하지 않아 중복 결제나 중복 발송이 생긴다.
- 외부 API 호출 결과를 상태로 남기지 않아 복구 작업이 어렵다.

## 확인 방법

- 테스트: 외부 API 성공 후 DB commit 실패, 외부 timeout, 애플리케이션 재시작 상황을 시뮬레이션한다.
- 로그: 외부 요청 id, idempotency key, 응답 코드, 상태 전이를 남긴다.
- 메트릭: 외부 API latency, timeout, retry count, compensation count를 본다.
- 운영 도구: pending 상태가 오래 남은 데이터를 조회할 수 있어야 한다.

## 장점과 한계

| 접근 | 장점 | 한계 |
|---|---|---|
| 트랜잭션 안에서 외부 호출 | 코드 흐름이 단순해 보인다 | 락 점유와 불일치 위험이 크다 |
| commit 후 외부 호출 | DB 정합성을 먼저 확정한다 | 외부 호출 실패 시 후속 처리가 필요하다 |
| 이벤트 기반 비동기 | 장애 전파를 줄이고 재시도 가능하다 | 최종 정합성 모델과 운영 모니터링이 필요하다 |
| 보상 처리 | 이미 발생한 부작용을 되돌릴 수 있다 | 완전한 rollback과 다르며 업무 규칙이 복잡하다 |

## 짧은 예제

```java
public void requestPayment(Long orderId) {
    Order order = orderService.markPaymentPending(orderId);

    PaymentResult result = paymentClient.approve(
        order.getPaymentKey(),
        order.getAmount()
    );

    orderService.completePayment(orderId, result.approvalId());
}

@Transactional
public Order markPaymentPending(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.markPaymentPending();
    return order;
}
```

외부 결제 호출을 긴 DB 트랜잭션 안에 넣지 않고, 상태를 먼저 `PAYMENT_PENDING`으로 남긴다. 이후 성공/실패 결과를 별도 트랜잭션에서 반영하고, 중간 장애는 pending 상태를 기준으로 재조회하거나 보상한다.

## 핵심 요약

외부 API 호출은 DB 트랜잭션으로 rollback할 수 없다.

따라서 DB 변경과 외부 부작용을 하나의 원자적 작업처럼 생각하면 위험하다.

트랜잭션 안에서 외부 API를 호출하면 락과 커넥션 점유 시간이 길어지고 장애 전파가 커진다.

실무에서는 상태를 먼저 남기고, 외부 호출은 짧은 timeout과 멱등키로 처리한다.

외부 성공 후 내부 실패 같은 불일치는 보상, 재시도, 운영 복구 플로우로 다룬다.

## 꼬리 질문

- 결제 API를 트랜잭션 안에서 호출하면 어떤 문제가 생기는가?
- 외부 API timeout은 항상 실패인가?
- 외부 API 성공 후 DB 반영이 실패하면 어떻게 복구할 것인가?
- idempotency key는 왜 필요한가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[compensation-and-outbox]]
- [[timeout]]
