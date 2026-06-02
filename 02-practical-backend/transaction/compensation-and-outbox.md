---
title: 보상 트랜잭션과 Outbox
description: 분산 환경에서 최종 정합성을 맞추는 보상 처리와 outbox 패턴
---

# 보상 트랜잭션과 Outbox

## 한 줄 정의

보상 트랜잭션은 이미 완료된 작업을 업무적으로 되돌리는 후속 작업이고, Outbox는 DB 변경과 이벤트 발행 의도를 같은 트랜잭션에 저장해 메시지 유실을 줄이는 패턴이다.

## 실무에서 왜 문제 되는가

- 여러 서비스나 외부 시스템을 하나의 DB 트랜잭션으로 묶을 수 없다.
- 이벤트 발행 전에 장애가 나면 DB는 변경됐지만 후속 처리가 실행되지 않을 수 있다.
- 이벤트를 먼저 발행하고 DB commit이 실패하면 존재하지 않는 상태를 다른 서비스가 처리할 수 있다.
- 보상 처리가 없으면 pending, paid, canceled 같은 상태가 장기간 꼬일 수 있다.

## 동작 원리

1. 핵심 DB 변경과 outbox 이벤트 레코드를 같은 트랜잭션으로 저장한다.
2. 트랜잭션이 commit되면 outbox 레코드도 함께 확정된다.
3. 별도 publisher가 outbox를 읽어 메시지 브로커나 외부 시스템에 발행한다.
4. 발행 성공 시 outbox 상태를 published로 바꾼다.
5. 후속 처리 실패나 외부 불일치는 보상 트랜잭션으로 상태를 되돌리거나 정정한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| DB 변경 후 반드시 이벤트 발행 | Outbox | DB 변경과 발행 의도를 함께 commit한다 |
| 외부 작업을 되돌릴 수 있음 | 보상 트랜잭션 | 이미 발생한 부작용을 업무적으로 취소한다 |
| 외부 작업을 되돌릴 수 없음 | 정정 상태와 수동 복구 | 완전한 rollback이 불가능하다 |
| 후속 처리가 느림 | 비동기 이벤트 | 사용자 응답과 후속 처리를 분리한다 |
| 중복 이벤트 가능 | 소비자 멱등성 | outbox 재시도는 중복 발행될 수 있다 |

## 자주 나는 실수

- Outbox를 쓰면 exactly once가 보장된다고 생각한다.
- 이벤트 소비자가 멱등하지 않은데 publisher 재시도를 켠다.
- 메시지 발행은 성공했지만 outbox 상태를 `published`로 바꾸기 전에 장애가 나면 같은 이벤트가 다시 발행될 수 있다는 점을 놓친다.
- 보상 트랜잭션을 기술적 rollback과 동일하게 생각한다.
- outbox 테이블 적체, 발행 실패, 재시도 횟수를 모니터링하지 않는다.
- 보상 실패 시 운영자가 어떤 상태를 봐야 하는지 정의하지 않는다.

## 확인 방법

- 테스트: DB commit 후 publisher 장애, 메시지 브로커 장애, 중복 발행을 재현한다.
- 로그: outbox id, aggregate id, event type, publish status를 남긴다.
- 메트릭: outbox pending count, publish failure count, retry age를 본다.
- 운영 쿼리: 오래된 pending 이벤트와 보상 실패 건을 조회할 수 있어야 한다.

## 장점과 한계

| 방식 | 장점 | 한계 |
|---|---|---|
| 보상 트랜잭션 | 분산 작업 실패를 업무적으로 복구한다 | 원래 작업을 완전히 없던 일로 만들지는 못한다 |
| Outbox | DB 변경과 이벤트 발행 의도 유실을 줄인다 | 중복 발행 가능성이 있어 소비자 멱등성이 필요하다 |
| 비동기 이벤트 | 장애 전파와 응답 지연을 줄인다 | 최종 정합성 지연을 허용해야 한다 |

## 짧은 예제

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

주문 완료와 이벤트 발행 의도를 같은 트랜잭션에 저장한다. 이후 별도 publisher가 outbox를 읽어 메시지를 발행한다. publisher가 중간에 죽어도 outbox 레코드가 남아 있으므로 재시도할 수 있다.

## 핵심 요약

보상 트랜잭션은 이미 끝난 작업을 업무적으로 되돌리는 후속 작업이다.

Outbox는 DB 변경과 이벤트 발행 의도를 같은 트랜잭션에 저장해 이벤트 유실을 줄인다.

Outbox는 exactly once를 보장하지 않으므로 소비자는 중복 이벤트를 처리할 수 있어야 한다.

예를 들어 메시지 발행은 성공했지만 outbox 상태 변경 전에 publisher가 장애 나면, 복구 후 같은 outbox 레코드를 다시 발행할 수 있다.

분산 환경에서는 강한 원자성보다 상태 전이, 재시도, 보상, 모니터링을 조합해 최종 정합성을 맞춘다.

운영에서는 오래된 pending 이벤트와 보상 실패 건을 볼 수 있어야 한다.

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
