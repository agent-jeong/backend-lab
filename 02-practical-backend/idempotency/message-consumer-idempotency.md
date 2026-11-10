---
title: 메시지 소비 멱등성
description: 중복 전달될 수 있는 메시지를 안전하게 처리하는 소비자 설계
tags: [concept, idempotency]
---

# 메시지 소비 멱등성

같은 메시지를 여러 번 받아도 소비자의 DB 상태와 외부 부작용이 한 번 처리한 결과로 수렴하게 만드는 설계다.

많은 메시지 시스템은 장애 복구를 위해 at-least-once 전달을 쓴다. 소비자가 처리한 뒤 ack 전에 죽으면 같은 메시지를 다시 받고, outbox publisher가 중복 발행해도 같은 이벤트가 다시 온다. 소비자가 멱등하지 않으면 포인트 적립, 쿠폰 발급, 알림 발송이 중복된다. 그래서 소비자는 같은 메시지가 여러 번 온다고 가정하고 만든다.

## 동작

1. 메시지마다 event id 또는 business key를 둔다.
2. 소비자는 처리 이력 테이블에 event id를 unique로 저장한다.
3. 처음 보는 메시지만 업무를 처리한다.
4. 이미 처리한 메시지는 ack하고 끝낸다.
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

`tryInsert`는 `event_id` unique 제약을 이용해 처음 소비한 이벤트만 처리 이력으로 저장한다. 처리 이력 저장과 업무 변경은 같은 트랜잭션으로 묶고, `rewardService.grant`도 `user_id`, `order_id` 같은 business key로 중복을 막아 두는 편이 안전하다.

## 상황별 대응

| 상황 | 선택 | 이유 |
|---|---|---|
| 이벤트 중복 전달 가능 | processed_event unique | 같은 이벤트를 한 번만 반영한다 |
| 업무적으로 중복 금지 | business key unique | event id가 달라도 중복 결과를 막는다 |
| 처리 후 ack 전 장애 | 재수신 허용 + 멱등 소비 | 메시지 유실보다 중복 방어가 낫다 |
| 외부 API 호출 포함 | 별도 멱등키 또는 outbox | 소비자 재처리로 외부 부작용이 중복될 수 있다 |
| 실패 반복 | DLQ와 재처리 정책 | 무한 재시도를 막고 운영자가 확인한다 |

이렇게 하면 중복 전달과 outbox 중복 발행을 흡수하고, 메시지를 잃는 것보다 복구가 쉽다. 대신 처리 이력 저장소가 필요하고, event id와 business key를 어떻게 잡느냐에 따라 효과가 갈린다.

## 자주 깨지는 곳

- **메시지가 정확히 한 번만 온다고 가정한다.** Kafka의 exactly-once(트랜잭션 프로듀서 + `read_committed`)도 Kafka 안에서 읽고 쓰는 범위만 보장하고, 소비자가 DB에 쓰거나 외부 API를 부르는 부작용까지 한 번으로 만들어 주지는 않는다.
- **event id만 믿고 업무 테이블의 중복 방어를 생략한다.** event id가 다른 같은 업무 이벤트가 오면 중복 반영된다.
- **처리 이력 저장과 업무 변경을 다른 트랜잭션으로 처리한다.** 한쪽만 남는다.
- **ack를 먼저 보내고 DB 처리를 나중에 한다.** 처리 중 죽으면 메시지가 사라진다.
- **외부 API 호출을 소비자 멱등성만으로 막으려 한다.** 외부 호출에는 별도 멱등키가 필요할 수 있다.
- **DLQ에 들어간 메시지의 재처리 기준을 정하지 않는다.**

## 운영에서 볼 것

- 같은 메시지를 여러 번 소비해 최종 row 수와 금액이 변하지 않는지 테스트한다.
- 처리 성공 후 ack 전에 장애가 난 상황을 재현한다.
- event id, aggregate id, consumer name, 중복 여부를 로그로 남긴다.
- duplicate event count, consumer retry count, DLQ count를 본다.

## 한 번에 설명하기

> at-least-once 전달에서는 소비자가 같은 메시지를 여러 번 받는다고 가정해야 합니다. 저는 처리 이력 테이블에 event id를 unique로 저장하고, 그 저장과 업무 변경을 같은 트랜잭션으로 묶습니다. event id만으로는 부족할 때가 있어서 업무 결과 쪽에도 business key unique를 두고, 외부 API를 부르면 그 호출에도 별도 멱등키를 씁니다.

## 꼬리 질문

- at-least-once 메시지 전달에서 소비자 멱등성이 필요한 이유는 무엇인가?
- 처리 후 ack 전에 장애가 나면 어떤 일이 생기는가?
- event id unique와 business key unique는 어떻게 다른가?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 중복 수신을 조건부 UPDATE로 거르기

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Apache Kafka: Message Delivery Semantics](https://kafka.apache.org/documentation/#semantics)
- [microservices.io: Idempotent Consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/observability/observability|observability]]
