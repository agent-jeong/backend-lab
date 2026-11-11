---
title: 결제와 주문 멱등성
description: 주문 생성과 결제 승인 요청이 반복돼도 결제가 한 번만 남게 하는 방법
tags: [concept, idempotency]
---

# 결제와 주문 멱등성

같은 주문 생성이나 결제 승인 요청이 여러 번 와도, 주문, 결제, 재고, 이벤트가 한 번 처리한 것처럼 남게 만드는 일이다.

결제에서는 중복이 곧 돈 문제다. 사용자는 버튼을 여러 번 누르고, 결제 승인이 timeout 나면 같은 결제를 다시 시도한다. 외부 결제는 성공했는데 우리 DB에 반영하기 전에 장애가 나기도 한다. 주문 완료 이벤트나 포인트 적립 메시지도 두 번 처리될 수 있다. 그 결과가 이중 결제, 재고 이중 차감, 쿠폰 중복 사용이다. 그래서 목표는 중복 요청이 아예 안 오게 하는 게 아니라, 와도 결과가 하나로 남게 하는 것이다.

## 동작

1. 주문 생성 요청에 idempotency key나 주문 요청 key를 붙인다.
2. 주문은 `CREATED`, `PAYMENT_PENDING`, `PAID`, `CANCELED` 같은 상태로 관리한다.
3. 결제 승인을 요청할 때 외부 결제 시스템에도 같은 멱등키를 넘긴다.
4. timeout이 나면 결제 상태를 조회해서 결과를 확인한다.
5. 주문 완료 뒤 이벤트 발행과 소비는 outbox와 소비자 멱등성으로 처리한다.

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
        Order order = orderRepository.findById(orderId).orElseThrow();
        if (!order.isPaid()) {
            throw new InvalidOrderStateException(orderId, order.getStatus());
        }
    }
    return orderRepository.findPaymentResponse(orderId);
}
```

바뀐 행 수가 0이면 왜 0인지 나눠 본다. 이미 `PAID`라면 같은 결제 완료 요청이 다시 온 것이니 기존 결과를 돌려준다. `CANCELED`처럼 다른 상태라면 결제는 승인됐는데 주문은 취소된 어긋난 상태다. 이때는 성공으로 응답하지 말고 망취소하거나 운영자가 확인할 건으로 넘긴다.

`paymentClient.approve`가 timeout으로 끝나도 주문을 실패로 바꾸지 않는다. `PAYMENT_PENDING`으로 둔 채, 같은 `paymentKey`로 결제 상태를 조회해서 결과를 확정한다.

## 단계별로 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 주문 생성 중복 | request key unique | 같은 주문 의도를 하나로 수렴시킨다 |
| 결제 승인 중복 | payment key unique | 같은 결제를 여러 번 승인하지 않는다 |
| 결제 timeout | 외부 상태 조회 | 결과 불명 상태를 실패로 단정하지 않는다 |
| 재고 차감 | 조건부 update 또는 예약 상태 | 음수 재고와 중복 차감을 막는다 |
| 주문 완료 이벤트 | outbox + 소비자 멱등성 | 이벤트 유실과 중복 소비를 함께 다룬다 |

이렇게 조합하려면 상태 모델과 복구 흐름이 갖춰져 있어야 하고, 외부 결제사의 상태 조회 API에 기대는 경우가 많다. 이벤트로 도는 후속 처리는 바로 맞춰지지 않으니, 반영이 조금 늦는 것을 받아들여야 한다.

## 자주 깨지는 곳

- 결제 timeout 뒤 새 payment key로 승인을 다시 요청하면, 첫 요청이 사실 성공했을 때 이중 결제가 된다.
- 결제 API 호출을 긴 DB 트랜잭션 안에서 하면, 결제사가 느린 만큼 락과 커넥션을 쥔다.
- 주문 상태 없이 boolean 값 하나로 흐름을 표현하면, 결제 중인지 결과를 모르는 건지 구분할 수 없다.
- 결제는 성공했는데 DB 반영이 실패한 건을 복구할 상태를 남기지 않으면, 돈은 나갔는데 주문은 미결제로 남는다.
- 주문 완료 이벤트 소비자가 중복 적립을 막지 않으면, 이벤트가 두 번 올 때 포인트가 두 번 쌓인다.

## 운영에서 볼 것

- 같은 주문 생성 key로 여러 번 요청해도 주문이 하나만 생기는지 테스트한다.
- 결제 승인 timeout 뒤 상태 조회와 재시도 흐름을 테스트한다.
- 주문 완료 이벤트를 두 번 소비해도 포인트나 쿠폰이 한 번만 반영되는지 테스트한다.
- order id, payment key, idempotency key, 상태 전이, 외부 요청 id를 로그로 남긴다.
- 중복 결제 시도 수, pending 결제가 머문 시간, 보상 처리 횟수를 본다.

## 한 번에 설명하기

> 결제와 주문에서는 주문 생성, 결제 승인, 재고 차감, 이벤트 발행, 메시지 소비가 각각 중복될 수 있습니다. 저는 주문 상태 전이, payment key unique, idempotency key, outbox, 소비자 멱등성을 함께 씁니다.
>
> 결제 timeout은 실패가 아니라 결과를 모르는 상태라서, 같은 payment key로 결제사에 상태를 조회해 확정합니다.
>
> 중복 요청을 아예 없앨 수는 없으니, 와도 결과가 하나로 남게 만드는 걸 목표로 둡니다.

## 꼬리 질문

- 결제 timeout 뒤 새 payment key로 다시 시도하면 어떤 문제가 생기나?
- 주문 상태 모델이 멱등성에 왜 중요한가?
- 주문 완료 이벤트가 두 번 소비되면 어떻게 막나?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 송금 승인 중복 방지

## 참고

2026년 11월에 확인한 공식 문서다.

- [Stripe API: Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[message-consumer-idempotency]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
