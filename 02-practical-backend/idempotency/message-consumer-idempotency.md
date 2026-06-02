---
title: 메시지 소비 멱등성
description: 중복 전달될 수 있는 메시지를 안전하게 처리하는 소비자 설계
---

# 메시지 소비 멱등성

## 한 줄 정의

메시지 소비 멱등성은 같은 메시지를 여러 번 받아도 소비자의 DB 상태와 외부 부작용이 한 번 처리된 결과로 수렴하게 만드는 설계다.

## 실무에서 왜 문제 되는가

- 많은 메시지 시스템은 장애 복구를 위해 at-least-once 전달을 사용한다.
- 소비자가 처리 후 ack 전에 장애 나면 같은 메시지를 다시 받을 수 있다.
- outbox publisher가 중복 발행하면 소비자는 같은 이벤트를 다시 처리할 수 있다.
- 소비자가 멱등하지 않으면 포인트 적립, 쿠폰 발급, 알림 발송이 중복된다.

## 동작 원리

1. 메시지마다 event id 또는 business key를 둔다.
2. 소비자는 처리 이력 테이블에 event id를 unique로 저장한다.
3. 처음 보는 메시지만 업무 처리를 수행한다.
4. 이미 처리된 메시지는 ack하고 종료한다.
5. 처리 이력 저장과 업무 변경은 같은 트랜잭션으로 묶는다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 이벤트 중복 전달 가능 | processed_event unique | 같은 이벤트를 한 번만 반영한다 |
| 업무적으로 중복 금지 | business key unique | event id가 달라도 중복 결과를 막는다 |
| 처리 후 ack 전 장애 | 재수신 허용 + 멱등 소비 | 메시지 유실보다 중복 방어가 낫다 |
| 외부 API 호출 포함 | 별도 멱등키 또는 outbox | 소비자 재처리로 외부 부작용이 중복될 수 있다 |
| 실패 반복 | DLQ와 재처리 정책 | 무한 재시도를 막고 운영자가 확인한다 |

## 자주 나는 실수

- 메시지가 정확히 한 번만 온다고 가정한다.
- event id만 믿고 업무 테이블의 중복 방어를 생략한다.
- 처리 이력 저장과 업무 변경을 다른 트랜잭션으로 처리한다.
- ack를 먼저 보내고 DB 처리를 나중에 한다.
- DLQ에 들어간 메시지의 재처리 기준을 정하지 않는다.

## 확인 방법

- 테스트: 같은 메시지를 여러 번 소비해 최종 row 수와 금액이 변하지 않는지 확인한다.
- 테스트: 처리 성공 후 ack 전에 장애가 난 상황을 재현한다.
- 로그: event id, aggregate id, consumer name, duplicate 여부를 남긴다.
- 메트릭: duplicate event count, consumer retry count, DLQ count를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 중복 전달에 안전해진다 | 처리 이력 저장소가 필요하다 |
| 메시지 유실보다 복구가 쉽다 | 외부 API 부작용은 별도 멱등 설계가 필요하다 |
| outbox 중복 발행을 흡수할 수 있다 | event id와 business key 설계가 중요하다 |

## 짧은 예제

```java
@Transactional
public void handle(OrderCompletedEvent event) {
    if (!processedEventRepository.tryInsert(event.eventId())) {
        return;
    }

    rewardService.grant(event.userId(), event.orderId());
}
```

`tryInsert`는 `event_id` unique 제약을 이용해 처음 소비한 이벤트만 처리 이력으로 저장하는 동작을 의미한다. 처리 이력 저장과 업무 변경은 같은 트랜잭션으로 묶어야 하며, `rewardService.grant`도 `user_id`, `order_id` 같은 business key 중복 방어를 갖는 것이 안전하다.

## 핵심 요약

메시지 소비자는 같은 메시지를 여러 번 받을 수 있다고 가정해야 한다.

처리 이력과 unique 제약으로 이미 처리한 이벤트를 식별한다.

처리 이력 저장과 업무 상태 변경은 같은 트랜잭션으로 묶어야 한다.

event id 중복 방어와 함께 업무 결과의 business key 중복 방어도 검토한다.

외부 API 호출이 포함되면 소비자 멱등성만으로 충분하지 않고 외부 호출 멱등키가 필요할 수 있다.

## 꼬리 질문

- at-least-once 메시지 전달에서 소비자 멱등성이 필요한 이유는 무엇인가?
- 처리 후 ack 전에 장애가 나면 어떤 일이 생기는가?
- event id unique와 business key unique는 어떻게 다른가?

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/observability/observability|observability]]
