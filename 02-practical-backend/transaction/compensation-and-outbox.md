---
title: 보상 트랜잭션과 Outbox
description: 분산 환경에서 최종 정합성을 맞추는 보상 처리와 outbox 패턴
---

# 보상 트랜잭션과 Outbox

보상 트랜잭션은 이미 끝난 작업을 업무적으로 되돌리는 후속 작업이다. Outbox는 DB 변경과 "이벤트를 보내야 한다"는 기록을 같은 트랜잭션에 저장해 메시지 유실을 막는 패턴이다.

여러 서비스나 외부 시스템은 하나의 DB 트랜잭션으로 묶을 수 없다. 이벤트 발행 전에 죽으면 DB는 바뀌었는데 후속 처리가 안 돌고, 이벤트를 먼저 보냈는데 commit이 실패하면 존재하지 않는 상태를 다른 서비스가 처리한다. 보상 처리가 없으면 pending, paid, canceled 같은 상태가 오래 꼬인 채 남는다.

## 동작

1. 핵심 DB 변경과 outbox 이벤트 레코드를 같은 트랜잭션으로 저장한다.
2. 트랜잭션이 commit되면 outbox 레코드도 함께 확정된다.
3. 별도 publisher가 outbox를 읽어 메시지 브로커나 외부 시스템에 발행한다.
4. 발행에 성공하면 outbox 상태를 published로 바꾼다.
5. 후속 처리 실패나 외부 불일치는 보상 트랜잭션으로 상태를 되돌리거나 정정한다.

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

주문 완료와 이벤트 발행 의도를 같은 트랜잭션에 저장하고, 별도 publisher가 outbox를 읽어 발행한다. publisher가 중간에 죽어도 outbox 레코드가 남아 있어서 다시 시도할 수 있다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| DB 변경 후 이벤트를 꼭 발행해야 함 | Outbox | DB 변경과 발행 의도를 함께 commit한다 |
| 외부 작업을 되돌릴 수 있음 | 보상 트랜잭션 | 이미 일어난 부작용을 업무적으로 취소한다 |
| 외부 작업을 되돌릴 수 없음 | 정정 상태와 수동 복구 | 완전한 rollback이 불가능하다 |
| 후속 처리가 느림 | 비동기 이벤트 | 사용자 응답과 후속 처리를 분리한다 |
| 중복 이벤트 가능 | 소비자 멱등성 | outbox 재시도는 중복 발행될 수 있다 |

각 방식의 대가도 분명하다. 보상 트랜잭션은 실패를 업무적으로 복구하지만 원래 작업을 없던 일로 만들지는 못한다. Outbox는 발행 의도 유실을 줄이지만 중복 발행이 가능해서 소비자 멱등성이 필요하다. 비동기 이벤트는 장애 전파와 응답 지연을 줄이지만 최종 정합성 지연을 받아들여야 한다.

## 자주 깨지는 곳

- **Outbox를 쓰면 exactly once가 보장된다고 생각한다.** 유실은 막지만 중복은 막지 못한다.
- **메시지 발행 후 `published`로 바꾸기 전의 장애를 놓친다.** 그 사이에 죽으면 같은 이벤트가 다시 발행된다.
- **소비자가 멱등하지 않은데 publisher 재시도를 켠다.**
- **보상 트랜잭션을 기술적 rollback과 같다고 생각한다.** 보상은 되돌리는 새 작업이다.
- **outbox 적체, 발행 실패, 재시도 횟수를 모니터링하지 않는다.**
- **보상이 실패했을 때 운영자가 볼 상태를 정의하지 않는다.**

## 운영에서 볼 것

- DB commit 후 publisher 장애, 메시지 브로커 장애, 중복 발행을 테스트로 재현한다.
- outbox id, aggregate id, event type, publish status를 로그로 남긴다.
- outbox pending count, publish failure count, retry age를 본다.
- 오래된 pending 이벤트와 보상 실패 건을 조회하는 운영 쿼리를 준비해 둔다.

## 면접에서 말하기

> Outbox는 DB 변경과 이벤트를 보내야 한다는 기록을 같은 트랜잭션에 넣어서 이벤트 유실을 막는 패턴입니다. 중복 발행까지 막지는 못하기 때문에 소비자는 멱등하게 만듭니다. 보상 트랜잭션은 rollback이 아니라 업무적으로 되돌리는 새 작업이고, 저는 분산 환경에서는 상태 전이, 재시도, 보상, 그리고 오래된 pending과 보상 실패 건 모니터링을 조합해 최종 정합성을 맞춥니다.

## 꼬리 질문

- Outbox 패턴은 어떤 문제를 해결하는가?
- Outbox를 사용해도 중복 이벤트가 발생할 수 있는 이유는 무엇인가?
- 보상 트랜잭션과 rollback은 어떻게 다른가?
- 이벤트 발행 후 소비자 처리가 실패하면 어떻게 해야 하는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[external-api-and-transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/observability/observability|observability]]
