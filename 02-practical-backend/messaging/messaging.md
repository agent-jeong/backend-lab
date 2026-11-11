---
title: 메시징
description: 메시지 큐와 Kafka로 서비스 사이 작업을 나눌 때 생기는 중복과 순서와 유실을 다룬 글 모음
tags: [messaging]
comments: false
---

# 메시징

메시지 큐를 쓰는 이유와 대가, Kafka의 파티션과 소비자 그룹, offset 커밋, producer 설정을 다룬다. 후속 작업을 메시지로 떼어 내면 장애가 덜 번지지만, 그 대신 생기는 중복과 순서 문제와 유실을 어디서 막을지를 주로 이야기한다.

## 읽는 순서

1. [[message-queue-basics|메시지 큐를 쓰는 이유와 대가]]
2. [[kafka-core-concepts|Kafka 핵심 동작]]

## 먼저 답해 볼 질문

- 어떤 후속 작업을 메시지로 빼고, 어떤 작업은 동기 호출로 남기나?
- at-least-once에서 소비자는 왜 같은 메시지를 두 번 받나?
- 메시지 순서는 어디까지 지켜지고, 같은 주문의 이벤트는 어떻게 순서대로 처리하나?
- DB 저장과 메시지 발행 중 하나만 일어나면 어떻게 되나?
- Kafka에서 offset을 언제 커밋하느냐에 따라 무엇이 달라지나?
- `acks=all`만으로 메시지를 잃지 않을 수 있나?

## 실무에서 보는 것

- 메시지는 잃지 않는 쪽(at-least-once)을 고르고, 중복은 소비자가 event id와 업무 키로 막는다.
- 순서는 파티션이나 큐 하나 안에서만 지켜진다. 순서가 필요한 이벤트는 같은 키로 보내고, 소비자도 오래된 이벤트를 버릴 수 있게 만든다.
- DB 변경과 이벤트 발행은 Outbox로 같은 트랜잭션에 남긴다.
- 운영에서는 consumer lag, 재시도 횟수, DLQ 건수를 본다.
- 설명할 때는 브로커 이름보다, 메시지가 두 번 오거나 빠지거나 순서가 바뀌는 순간을 어디서 막았는지부터 말한다.

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 같은 웹훅을 다시 보내는 외부 시스템을 at-least-once 송신자로 보고 중복을 거른 사례

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/message-consumer-idempotency|message-consumer-idempotency]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[02-practical-backend/observability/observability|observability]]
- [[04-design-cases/interview-questions|technical-questions]]
