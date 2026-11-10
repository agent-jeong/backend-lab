---
title: 외부 API와 트랜잭션
description: 외부 시스템 호출과 DB 트랜잭션을 함께 다룰 때의 실패 대응 기준
---

# 외부 API와 트랜잭션

외부 API 호출은 DB 트랜잭션으로 rollback할 수 없는 부작용이다. 그래서 DB 변경과 한 덩어리로 묶지 않고, 실패와 재시도를 따로 설계한다.

둘을 하나의 원자적 작업처럼 다루면 DB는 rollback됐는데 외부 결제는 승인되는 불일치가 생긴다. 외부 API가 느리면 그동안 DB 커넥션과 락을 쥐고 있게 되고, 외부 호출이 성공한 뒤 애플리케이션이 죽으면 DB 상태가 갱신되지 않는다. 재시도하면 외부 요청이 중복 처리된다.

## 동작

1. 애플리케이션이 DB 상태를 바꾼다.
2. 외부 API를 호출한다.
3. DB commit, 외부 API 성공, 애플리케이션 장애는 서로 다른 순서로 일어날 수 있다.
4. DB rollback은 외부 시스템에 이미 전달된 요청을 되돌리지 못한다.
5. 그래서 상태 모델, 멱등키, 재시도, 보상 처리로 최종 정합성을 맞춘다.

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

외부 결제 호출을 긴 DB 트랜잭션 안에 넣지 않고, 상태를 먼저 `PAYMENT_PENDING`으로 남긴다. 성공/실패 결과는 별도 트랜잭션에서 반영하고, 중간 장애는 pending 상태를 기준으로 재조회하거나 보상한다.

## 상황별 전략

| 상황 | 전략 | 이유 |
|---|---|---|
| 결제 승인 요청 | 주문 pending 저장 후 외부 호출 | 승인 전후 상태를 남긴다 |
| 알림 발송 | commit 이후 비동기 발송 | 알림 실패가 핵심 거래 rollback을 만들지 않게 한다 |
| 중복 요청 위험 | idempotency key 사용 | 재시도해도 한 번만 처리되게 한다 |
| 외부 성공 후 DB 실패 | 보상 또는 상태 복구 작업 | 외부 부작용은 rollback되지 않는다 |
| 호출 지연 가능 | 짧은 timeout과 circuit breaker | DB 자원 점유와 장애 전파를 줄인다 |
| timeout 발생 | 결과 조회 또는 상태 확인 | timeout은 실패가 아니라 결과 불명 상태일 수 있다 |

| 접근 | 장점 | 한계 |
|---|---|---|
| 트랜잭션 안에서 외부 호출 | 코드 흐름이 단순해 보인다 | 락 점유와 불일치 위험이 크다 |
| commit 후 외부 호출 | DB 정합성을 먼저 확정한다 | 외부 호출 실패 시 후속 처리가 필요하다 |
| 이벤트 기반 비동기 | 장애 전파를 줄이고 재시도할 수 있다 | 최종 정합성 모델과 운영 모니터링이 필요하다 |
| 보상 처리 | 이미 일어난 부작용을 되돌린다 | 완전한 rollback과 다르고 업무 규칙이 복잡하다 |

## 자주 깨지는 곳

- **`@Transactional` 안에서 결제, 배송, 알림 API를 호출한다.** 락과 커넥션 점유 시간이 길어지고 외부 장애가 그대로 번진다.
- **외부 API가 성공했으니 DB commit도 성공한다고 가정한다.**
- **timeout이 났을 때 실패인지 성공인지 확인하지 않는다.**
- **재시도에 멱등키를 쓰지 않는다.** 중복 결제나 중복 발송이 생긴다.
- **외부 호출 결과를 상태로 남기지 않는다.** 복구 작업의 출발점이 없다.

## 운영에서 볼 것

- 외부 API 성공 후 DB commit 실패, 외부 timeout, 애플리케이션 재시작을 테스트로 시뮬레이션한다.
- 외부 요청 id, idempotency key, 응답 코드, 상태 전이를 로그로 남긴다.
- 외부 API latency, timeout, retry count, compensation count를 본다.
- pending 상태로 오래 남은 데이터를 조회할 수 있게 해 둔다.

## 면접에서 말하기

> 외부 API 호출은 DB 트랜잭션으로 rollback할 수 없어서, 트랜잭션 안에서 호출하면 락과 커넥션 점유가 길어지고 불일치가 생깁니다. 저는 상태를 먼저 pending으로 남기고, 외부 호출은 트랜잭션 밖에서 짧은 timeout과 멱등키로 처리합니다. 외부는 성공했는데 내부 반영이 실패한 경우는 pending 상태를 기준으로 재조회, 보상, 운영 복구 흐름으로 맞춥니다.

## 꼬리 질문

- 결제 API를 트랜잭션 안에서 호출하면 어떤 문제가 생기는가?
- 외부 API timeout은 항상 실패인가?
- 외부 API 성공 후 DB 반영이 실패하면 어떻게 복구할 것인가?
- idempotency key는 왜 필요한가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 취소할 수 없는 외부 승인 앞뒤의 트랜잭션 경계

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[compensation-and-outbox]]
- [[timeout]]
