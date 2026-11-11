---
title: 메시지 소비 멱등성
description: 같은 메시지가 두 번 와도 한 번만 반영되게 소비자를 만드는 방법
tags: [concept, idempotency]
---

# 메시지 소비 멱등성

같은 메시지를 여러 번 받아도, 소비자 쪽 DB와 외부에 나간 결과가 한 번 처리한 것과 같게 남도록 만드는 일이다.

많은 메시지 시스템은 장애가 나도 메시지를 잃지 않으려고 최소 한 번 전달(at-least-once)을 쓴다. 소비자가 처리를 끝내고 ack를 보내기 전에 죽으면 같은 메시지를 다시 받는다. outbox publisher가 같은 이벤트를 두 번 보내도 다시 온다. 소비자가 멱등하지 않으면 포인트가 두 번 쌓이고, 쿠폰이 두 장 나가고, 알림이 두 번 간다. 그래서 소비자는 처음부터 같은 메시지가 여러 번 온다고 보고 만든다.

## 동작

1. 메시지마다 event id나 업무 키(business key)를 둔다.
2. 소비자는 처리 이력 테이블에 event id를 unique로 저장한다.
3. 처음 보는 메시지만 업무를 처리한다.
4. 이미 처리한 메시지는 ack만 하고 끝낸다.
5. 처리 이력 저장과 업무 변경은 같은 트랜잭션으로 묶는다.

```java
@Transactional
public void handle(OrderCompletedEvent event) {
    if (!processedEventRepository.tryInsert(event.eventId())) {
        return;
    }

    rewardService.grant(event.userId(), event.orderId());
}
```

`tryInsert`는 `event_id`에 걸린 unique 제약을 이용해 처음 받은 이벤트만 처리 이력으로 저장한다. 처리 이력 저장과 업무 변경은 같은 트랜잭션으로 묶는다. `rewardService.grant` 쪽도 `user_id`, `order_id` 같은 업무 키로 중복을 막아 두는 편이 안전하다.

## 상황별 대응

| 상황 | 선택 | 이유 |
|---|---|---|
| 이벤트 중복 전달 가능 | processed_event unique | 같은 이벤트를 한 번만 반영한다 |
| 업무적으로 중복 금지 | business key unique | event id가 달라도 중복 결과를 막는다 |
| 처리 후 ack 전 장애 | 재수신 허용 + 멱등 소비 | 메시지 유실보다 중복 방어가 낫다 |
| 외부 API 호출 포함 | 별도 멱등키 또는 outbox | 소비자 재처리로 외부 부작용이 중복될 수 있다 |
| 실패 반복 | DLQ와 재처리 정책 | 무한 재시도를 막고 운영자가 확인한다 |

이렇게 해 두면 중복 전달이나 outbox 중복 발행이 와도 결과가 한 번만 남고, 메시지를 잃었을 때보다 복구가 훨씬 쉽다. 대신 처리 이력을 저장할 곳이 있어야 하고, event id와 업무 키를 무엇으로 잡느냐에 따라 막을 수 있는 범위가 달라진다.

## 자주 깨지는 곳

- 메시지가 정확히 한 번만 온다고 가정하면 중복 처리를 대비하지 않게 된다. Kafka의 exactly-once(트랜잭션 프로듀서 + `read_committed`)도 Kafka 안에서 읽고 쓰는 범위만 보장하고, 소비자가 DB에 쓰거나 외부 API를 부르는 일까지 한 번으로 만들어 주지는 않는다.
- event id만 믿고 업무 테이블의 중복 방어를 빼면, event id가 다른 같은 업무 이벤트가 왔을 때 두 번 반영된다.
- 처리 이력 저장과 업무 변경을 다른 트랜잭션으로 처리하면, 한쪽만 남는다.
- ack를 먼저 보내고 DB 처리를 나중에 하면, 처리 중에 죽었을 때 메시지가 사라진다.
- 외부 API 호출을 소비자 멱등성만으로 막으려 하면, 소비자가 다시 돌 때 외부 호출도 다시 나간다. 외부 호출에는 따로 멱등키가 필요할 수 있다.
- DLQ에 들어간 메시지를 언제 어떻게 다시 처리할지 정하지 않으면, 실패한 메시지가 그대로 쌓인다.

## 운영에서 볼 것

- 같은 메시지를 여러 번 소비해도 최종 행 수와 금액이 변하지 않는지 테스트한다.
- 처리는 성공했는데 ack 전에 장애가 난 상황을 재현한다.
- event id, aggregate id, 소비자 이름, 중복 여부를 로그로 남긴다.
- 중복 이벤트 수, 소비자 재시도 횟수, DLQ 건수를 본다.

## 한 번에 설명하기

> 최소 한 번 전달(at-least-once)에서는 소비자가 같은 메시지를 여러 번 받는다고 보고 만들어야 합니다.
>
> 저는 처리 이력 테이블에 event id를 unique로 저장하고, 그 저장과 업무 변경을 같은 트랜잭션으로 묶습니다.
>
> event id만으로 부족할 때가 있어서 업무 결과 쪽에도 업무 키로 unique를 겁니다. 외부 API를 부르는 경우에는 그 호출에도 따로 멱등키를 붙입니다.

## 꼬리 질문

- 최소 한 번 전달에서 소비자 멱등성이 필요한 이유는?
- 처리는 끝났는데 ack 전에 장애가 나면 어떻게 되나?
- event id unique와 business key unique는 무엇이 다른가?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 중복 수신을 조건부 UPDATE로 거르기

## 참고

2026년 11월에 확인한 공식 문서다.

- [Apache Kafka: Message Delivery Semantics](https://kafka.apache.org/documentation/#semantics)
- [microservices.io: Idempotent Consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/observability/observability|observability]]
- [[message-queue-basics]]
- [[kafka-core-concepts]]
