---
title: 보상 트랜잭션과 Outbox
description: 여러 서비스에 걸친 작업을 보상 처리와 outbox로 결국 맞추는 방법
tags: [concept, transaction]
---

# 보상 트랜잭션과 Outbox

보상 트랜잭션은 이미 끝난 작업을 업무적으로 되돌리는 후속 작업이다. 결제를 취소하거나 차감한 포인트를 다시 넣어 주는 식이다. Outbox는 DB 변경과 "이 이벤트를 보내야 한다"는 기록을 같은 트랜잭션에 저장해서 메시지가 사라지지 않게 하는 패턴이다.

여러 서비스나 외부 시스템에 걸친 작업은 DB 트랜잭션 하나로 묶을 수 없다. 주문을 완료로 바꾸고 이벤트를 보내기 전에 서버가 죽으면, DB는 바뀌었는데 배송 쪽은 아무것도 모른다. 반대로 이벤트를 먼저 보냈는데 commit이 실패하면, 다른 서비스는 있지도 않은 주문을 처리한다. 이런 어긋남을 되돌릴 방법이 없으면 pending, paid, canceled 같은 상태가 꼬인 채 오래 남는다.

## 동작

1. 주문 상태 변경 같은 DB 변경과 outbox 이벤트 레코드를 같은 트랜잭션으로 저장한다.
2. 트랜잭션이 commit되면 outbox 레코드도 함께 확정된다.
3. 따로 도는 publisher가 outbox를 읽어 메시지 브로커나 외부 시스템에 보낸다.
4. 보내는 데 성공하면 outbox 상태를 published로 바꾼다.
5. 후속 처리가 실패하거나 외부 시스템과 어긋나면 보상 트랜잭션으로 상태를 되돌리거나 고친다.

```java
@Transactional
public void completeOrder(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.complete();

    outboxRepository.save(OutboxEvent.of(
        "Order",
        order.getId(),
        "OrderCompleted",
        Map.of("orderId", order.getId())
    ));
}
```

주문 완료와 "이벤트를 보내야 한다"는 기록을 같은 트랜잭션에 저장하고, 실제 발행은 publisher가 따로 한다. publisher가 중간에 죽어도 outbox 레코드가 남아 있으니 다시 보내면 된다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| DB 변경 후 이벤트를 꼭 발행해야 함 | Outbox | DB 변경과 발행 의도를 함께 commit한다 |
| 외부 작업을 되돌릴 수 있음 | 보상 트랜잭션 | 이미 일어난 부작용을 업무적으로 취소한다 |
| 외부 작업을 되돌릴 수 없음 | 정정 상태와 수동 복구 | 완전한 rollback이 불가능하다 |
| 후속 처리가 느림 | 비동기 이벤트 | 사용자 응답과 후속 처리를 분리한다 |
| 중복 이벤트 가능 | 소비자 멱등성 | outbox 재시도는 중복 발행될 수 있다 |

각 방식에는 치르는 값이 있다. 보상 트랜잭션은 실패를 업무적으로 수습하지만, 원래 작업을 없던 일로 만들지는 못한다. Outbox는 보내야 할 이벤트를 잃지 않게 해 주지만 같은 이벤트가 두 번 갈 수 있어서 소비자가 멱등해야 한다. 비동기 이벤트는 한쪽 장애가 다른 쪽으로 번지는 것과 응답 지연을 줄이지만, 데이터가 맞춰지기까지 시간이 걸리는 것을 받아들여야 한다.

## 자주 깨지는 곳

- Outbox를 쓰면 정확히 한 번(exactly once) 전달된다고 생각하면, 중복 이벤트를 대비하지 않게 된다. Outbox는 유실은 막지만 중복은 막지 못한다.
- 메시지를 보낸 뒤 `published`로 바꾸기 전에 서버가 죽으면, 같은 이벤트가 다시 발행된다.
- 소비자가 멱등하지 않은데 publisher 재시도를 켜면, 같은 이벤트가 두 번 처리된다.
- 보상 트랜잭션을 rollback과 같은 것으로 보면, 보상 자체가 실패할 경우를 설계하지 않는다. 보상은 되돌리는 새 작업이다.
- outbox에 쌓인 건수, 발행 실패, 재시도 횟수를 모니터링하지 않으면, 이벤트가 밀려도 한참 뒤에야 안다.
- 보상이 실패했을 때 운영자가 어떤 상태를 보고 처리할지 정해 두지 않으면, 실패 건이 그대로 묻힌다.

## 운영에서 볼 것

- DB commit 뒤 publisher 장애, 메시지 브로커 장애, 중복 발행을 테스트로 재현한다.
- outbox id, aggregate id, event type, 발행 상태를 로그로 남긴다.
- 발행 대기 건수(outbox pending count), 발행 실패 건수, 가장 오래 기다린 이벤트의 나이를 본다.
- 오래된 pending 이벤트와 보상 실패 건을 조회하는 운영 쿼리를 미리 준비해 둔다.

## 한 번에 설명하기

> Outbox는 DB 변경과 "이벤트를 보내야 한다"는 기록을 같은 트랜잭션에 넣어서 이벤트가 사라지지 않게 하는 패턴입니다. 다만 같은 이벤트가 두 번 갈 수는 있어서 소비자를 멱등하게 만듭니다.
>
> 보상 트랜잭션은 rollback이 아니라, 이미 끝난 일을 업무적으로 되돌리는 새 작업입니다.
>
> 여러 서비스에 걸친 작업은 상태 전이, 재시도, 보상을 함께 쓰고, 오래 남은 pending과 보상 실패 건을 지켜보면서 결국 데이터가 맞춰지게 합니다.

## 꼬리 질문

- Outbox 패턴은 어떤 문제를 막는가?
- Outbox를 써도 중복 이벤트가 생기는 이유는?
- 보상 트랜잭션과 rollback은 어떻게 다른가?
- 이벤트는 보냈는데 소비자 처리가 실패하면 어떻게 하나?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 원문을 먼저 저장하고 커밋 뒤에 처리

## 참고

2026년 11월에 확인한 공식 문서다.

- [microservices.io: Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [microservices.io: Saga](https://microservices.io/patterns/data/saga.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[external-api-and-transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/observability/observability|observability]]
- [[message-queue-basics]]
