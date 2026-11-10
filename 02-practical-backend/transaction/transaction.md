---
title: 트랜잭션
description: 데이터 정합성과 트랜잭션 경계 학습 인덱스
tags: [transaction]
comments: false
---

# 트랜잭션

ACID와 격리 수준, 트랜잭션 경계, Spring 트랜잭션, 락과 데드락, 외부 API, 보상과 Outbox를 다룬다. 정합성과 락 경합 사이에서 경계를 어디에 둘지가 중심이다.

## 읽는 순서

1. [[why-transaction|트랜잭션이 필요한 이유]]
2. [[acid-and-isolation|ACID와 격리 수준]]
3. [[transaction-boundary|트랜잭션 경계 설정]]
4. [[spring-transaction|Spring 트랜잭션]]
5. [[lock-and-deadlock|락과 데드락]]
6. [[external-api-and-transaction|외부 API와 트랜잭션]]
7. [[compensation-and-outbox|보상 트랜잭션과 Outbox]]

## 핵심 질문

- 트랜잭션은 어떤 정합성 문제를 해결하고 어떤 비용을 만드는가?
- 트랜잭션 범위는 어디서 시작하고 어디서 끝내야 하는가?
- 격리 수준을 높이면 항상 안전해지는가?
- 락 경합과 데드락은 어떤 증상으로 드러나는가?
- Spring `@Transactional`은 언제 적용되지 않을 수 있는가?
- 외부 API 호출을 DB 트랜잭션 안에 넣으면 어떤 문제가 생기는가?
- 커밋 이후 후속 작업이 실패하면 어떻게 복구할 것인가?

## 실무에서 보는 것

- 트랜잭션은 데이터 정합성을 지키지만 범위가 커지면 락 경합과 장애 전파를 만든다.
- DB 작업과 외부 API 호출을 같은 사고방식으로 묶지 않는다.
- 설명할 때는 ACID 암기보다 정합성 요구사항에 맞는 경계 설정을 먼저 말한다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 외부 호출 전에 전송 기록을 먼저 커밋한 경계
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 커밋 후 비동기, `REQUIRES_NEW`로 나눈 경계
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 여러 서버에서 겹친 스케줄러의 데드락

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[01-core/database/database|database]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[04-design-cases/interview-questions|technical-questions]]
