---
title: 결제와 주문 멱등성
description: 주문 생성과 결제 승인에서 중복 요청을 안전하게 처리하는 실무 예시
---

# 결제와 주문 멱등성

같은 주문 생성이나 결제 승인 요청이 반복돼도 주문, 결제, 재고, 이벤트가 한 번 처리한 결과로 남게 만드는 설계다.

결제는 중복이 곧 돈 문제가 되는 곳이다. 사용자는 버튼을 여러 번 누르고, 결제 승인 timeout 뒤 같은 결제를 다시 시도하고, 외부 결제는 성공했는데 내부 DB 반영 전에 장애가 난다. 주문 완료 이벤트나 포인트 적립 메시지도 중복 처리된다. 그 결과가 이중 결제, 중복 재고 차감, 중복 쿠폰 사용이다. 목표는 "중복 요청을 막는다"가 아니라 "중복 요청이 와도 같은 결과로 수렴한다"이다.

## 동작

1. 주문 생성 요청에 idempotency key 또는 주문 요청 key를 둔다.
2. 주문은 `CREATED`, `PAYMENT_PENDING`, `PAID`, `CANCELED` 같은 상태로 관리한다.
3. 결제 승인 요청 때 외부 결제 시스템에도 같은 멱등키를 넘긴다.
4. timeout이 나면 결제 상태 조회로 결과를 확인한다.
5. 주문 완료 후 이벤트 발행과 소비는 outbox와 소비자 멱등성으로 처리한다.

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

update count가 0이면 이유를 나눠 본다. 이미 `PAID`라면 같은 결제 완료 요청이 다시 온 것이니 기존 결과를 반환한다. `CANCELED`처럼 다른 상태라면 결제는 승인됐는데 주문은 취소된 불일치다. 성공으로 응답하지 말고 망취소나 운영 확인 대상으로 넘긴다.

`paymentClient.approve`가 timeout으로 끝나도 주문을 실패로 바꾸지 않는다. `PAYMENT_PENDING`으로 둔 채 같은 `paymentKey`로 결제 상태를 조회해 결과를 확정한다.

## 단계별로 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 주문 생성 중복 | request key unique | 같은 주문 의도를 하나로 수렴시킨다 |
| 결제 승인 중복 | payment key unique | 같은 결제를 여러 번 승인하지 않는다 |
| 결제 timeout | 외부 상태 조회 | 결과 불명 상태를 실패로 단정하지 않는다 |
| 재고 차감 | 조건부 update 또는 예약 상태 | 음수 재고와 중복 차감을 막는다 |
| 주문 완료 이벤트 | outbox + 소비자 멱등성 | 이벤트 유실과 중복 소비를 함께 다룬다 |

이 조합은 상태 모델과 복구 흐름이 있어야 돌아가고, 외부 결제 상태 조회 API에 기댈 때가 많다. 이벤트 기반 후속 처리는 최종 정합성이므로 반영 지연을 받아들여야 한다.

## 자주 깨지는 곳

- **결제 timeout 뒤 새 payment key로 다시 승인 요청을 보낸다.** 첫 요청이 성공했다면 이중 결제다.
- **결제 API 호출을 긴 DB 트랜잭션 안에서 실행한다.**
- **주문 상태 없이 boolean flag만으로 흐름을 표현한다.** 결제 중인지, 결과를 모르는지 구분할 수 없다.
- **결제 성공 후 DB 반영 실패를 복구할 상태를 남기지 않는다.**
- **주문 완료 이벤트 소비자가 중복 적립을 막지 않는다.**

## 운영에서 볼 것

- 같은 주문 생성 key로 여러 번 요청해 주문이 하나만 생기는지 테스트한다.
- 결제 승인 timeout 뒤 상태 조회와 재시도 흐름을 테스트한다.
- 주문 완료 이벤트를 중복 소비해도 포인트나 쿠폰이 한 번만 반영되는지 테스트한다.
- order id, payment key, idempotency key, 상태 전이, external request id를 로그로 남긴다.
- duplicate payment attempt, pending payment age, compensation count를 본다.

## 면접에서 말하기

> 결제와 주문은 주문 생성, 결제 승인, 재고 차감, 이벤트 발행, 메시지 소비가 각각 중복될 수 있는 영역입니다. 저는 주문 상태 전이, payment key unique, idempotency key, outbox, 소비자 멱등성을 같이 씁니다. 결제 timeout은 실패가 아니라 결과 불명이라서 같은 payment key로 외부 상태를 조회해 확정합니다. 목표는 중복을 막는 게 아니라 중복이 와도 같은 결과로 수렴하게 하는 것입니다.

## 꼬리 질문

- 결제 timeout 후 새 payment key로 재시도하면 어떤 문제가 생기는가?
- 주문 상태 모델이 멱등성에 왜 중요한가?
- 주문 완료 이벤트가 중복 소비되면 어떻게 막을 수 있는가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 송금 승인 중복 방지

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[message-consumer-idempotency]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
