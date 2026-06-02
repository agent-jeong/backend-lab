---
title: 결제와 주문 멱등성
description: 주문 생성과 결제 승인에서 중복 요청을 안전하게 처리하는 실무 예시
---

# 결제와 주문 멱등성

## 한 줄 정의

결제와 주문 멱등성은 같은 주문 생성 또는 결제 승인 요청이 반복되어도 주문, 결제, 재고, 이벤트가 한 번 처리된 결과로 유지되게 만드는 설계다.

## 실무에서 왜 문제 되는가

- 사용자가 결제 버튼을 여러 번 누를 수 있다.
- 결제 승인 timeout 후 같은 결제를 다시 시도할 수 있다.
- 외부 결제는 성공했지만 내부 DB 반영 전에 장애가 날 수 있다.
- 주문 완료 이벤트나 포인트 적립 메시지가 중복 처리될 수 있다.
- 중복 처리되면 이중 결제, 중복 재고 차감, 중복 쿠폰 사용이 발생한다.

## 동작 원리

1. 주문 생성 요청에 idempotency key 또는 주문 요청 key를 둔다.
2. 주문은 `CREATED`, `PAYMENT_PENDING`, `PAID`, `CANCELED` 같은 상태로 관리한다.
3. 결제 승인 요청에는 외부 결제 시스템에도 같은 멱등키를 전달한다.
4. timeout이 발생하면 결제 상태 조회로 결과를 확인한다.
5. 주문 완료 후 이벤트 발행과 소비는 outbox와 소비자 멱등성으로 처리한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 주문 생성 중복 | request key unique | 같은 주문 의도를 하나로 수렴시킨다 |
| 결제 승인 중복 | payment key unique | 같은 결제를 여러 번 승인하지 않는다 |
| 결제 timeout | 외부 상태 조회 | 결과 불명 상태를 실패로 단정하지 않는다 |
| 재고 차감 | 조건부 update 또는 예약 상태 | 음수 재고와 중복 차감을 막는다 |
| 주문 완료 이벤트 | outbox + 소비자 멱등성 | 이벤트 유실과 중복 소비를 함께 다룬다 |

## 자주 나는 실수

- 결제 timeout 후 새 payment key로 다시 승인 요청을 보낸다.
- 결제 API 호출을 긴 DB 트랜잭션 안에서 실행한다.
- 주문 상태 없이 boolean flag만으로 흐름을 표현한다.
- 결제 성공 후 DB 반영 실패를 복구할 상태를 남기지 않는다.
- 주문 완료 이벤트 소비자가 중복 적립을 막지 않는다.

## 확인 방법

- 테스트: 같은 주문 생성 key로 여러 번 요청해 주문이 하나만 생성되는지 확인한다.
- 테스트: 결제 승인 timeout 후 상태 조회와 재시도 흐름을 검증한다.
- 테스트: 주문 완료 이벤트를 중복 소비해 포인트나 쿠폰이 한 번만 반영되는지 확인한다.
- 로그: order id, payment key, idempotency key, status transition, external request id를 남긴다.
- 메트릭: duplicate payment attempt, pending payment age, compensation count를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 이중 결제와 중복 주문을 줄인다 | 상태 모델과 복구 플로우가 필요하다 |
| timeout 이후 복구가 가능하다 | 외부 결제 상태 조회 API에 의존할 수 있다 |
| 이벤트 기반 후속 처리를 안전하게 만든다 | 최종 정합성 지연을 허용해야 한다 |

## 짧은 예제

```java
public PaymentResponse approvePayment(Long orderId, String paymentKey) {
    Order order = orderService.markPaymentPending(orderId, paymentKey);

    PaymentResult result = paymentClient.approve(
        paymentKey,
        order.getAmount()
    );

    return orderService.markPaid(orderId, result.approvalId());
}

@Transactional
public PaymentResponse markPaid(Long orderId, String approvalId) {
    int updated = orderRepository.markPaidIfPending(orderId, approvalId);
    if (updated == 0) {
        return orderRepository.findPaymentResponse(orderId);
    }
    return orderRepository.findPaymentResponse(orderId);
}
```

이미 `PAID` 상태라면 같은 결제 완료 요청은 새로 부작용을 만들지 않고 기존 결제 결과를 반환한다.

## 핵심 요약

결제와 주문은 멱등성이 가장 중요한 실무 영역이다.

주문 생성, 결제 승인, 재고 차감, 이벤트 발행, 메시지 소비가 각각 중복될 수 있다.

결제 timeout은 실패가 아니라 결과 불명 상태일 수 있으므로 외부 상태 조회가 필요하다.

주문 상태 전이, payment key unique, idempotency key, outbox, 소비자 멱등성을 함께 사용해야 한다.

면접에서는 "중복 요청을 막는다"보다 "중복 요청이 와도 같은 결과로 수렴하게 설계한다"고 설명하는 것이 좋다.

## 꼬리 질문

- 결제 timeout 후 새 payment key로 재시도하면 어떤 문제가 생기는가?
- 주문 상태 모델이 멱등성에 왜 중요한가?
- 주문 완료 이벤트가 중복 소비되면 어떻게 막을 수 있는가?

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[message-consumer-idempotency]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
