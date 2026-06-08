---
title: Transaction
description: 데이터 정합성과 트랜잭션 경계 학습 인덱스
comments: false
---

# Transaction

## 운영 방식

- 이 문서는 Transaction 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/transaction/` 아래 개념별 문서로 나눈다.
- 학습한 내용은 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 정합성, 격리 수준, 락, 실패 복구, 면접 답변을 중심으로 작성한다.

## 학습 산출물

- 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-transaction|트랜잭션이 필요한 이유]]
2. [[acid-and-isolation|ACID와 격리 수준]]
3. [[transaction-boundary|트랜잭션 경계 설정]]
4. [[spring-transaction|Spring 트랜잭션]]
5. [[lock-and-deadlock|락과 데드락]]
6. [[external-api-and-transaction|외부 API와 트랜잭션]]
7. [[compensation-and-outbox|보상 트랜잭션과 Outbox]]

## 핵심 질문

- Transaction 영역에서 실무적으로 중요한 문제는 무엇인가?
- 트랜잭션은 어떤 정합성 문제를 해결하고 어떤 비용을 만드는가?
- 트랜잭션 범위는 어디서 시작하고 어디서 끝내야 하는가?
- 격리 수준을 높이면 항상 안전해지는가?
- 락 경합과 데드락은 어떤 증상으로 드러나는가?
- Spring `@Transactional`은 언제 적용되지 않을 수 있는가?
- 외부 API 호출을 DB 트랜잭션 안에 넣으면 어떤 문제가 생기는가?
- 커밋 이후 후속 작업이 실패하면 어떻게 복구할 것인가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- 트랜잭션은 데이터 정합성을 지키지만 범위가 커지면 락 경합과 장애 전파를 만든다.
- DB 작업과 외부 API 호출을 같은 사고방식으로 묶지 않는다.
- 면접에서는 ACID 암기보다 정합성 요구사항에 맞는 경계 설정을 설명한다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[01-core/database/database|database]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[04-interview/interview-questions|interview-questions]]
