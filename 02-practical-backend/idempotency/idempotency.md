---
title: Idempotency
description: 중복 요청과 재시도에 안전한 설계 학습 인덱스
comments: false
---

# Idempotency

## 운영 방식

- 이 문서는 Idempotency 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/idempotency/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 중복 요청, 재시도, 상태 전이, 유니크 제약, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-idempotency|멱등성이 필요한 이유]]
2. [[duplicate-request-and-retry|중복 요청과 재시도]]
3. [[idempotency-key|Idempotency Key]]
4. [[state-transition-and-unique-constraint|상태 전이와 Unique 제약]]
5. [[message-consumer-idempotency|메시지 소비 멱등성]]
6. [[payment-order-idempotency|결제와 주문 멱등성]]

## 핵심 질문

- Idempotency 영역에서 실무적으로 중요한 문제는 무엇인가?
- 멱등성과 단순 중복 제거는 무엇이 다른가?
- timeout 이후 재시도할 때 왜 결과 불명 상태를 고려해야 하는가?
- idempotency key는 어디에서 만들고 얼마나 보관해야 하는가?
- unique constraint와 상태 전이는 멱등성에서 어떤 역할을 하는가?
- 메시지는 왜 중복 소비될 수 있고 소비자는 어떻게 방어해야 하는가?
- 결제와 주문 처리에서 중복 요청을 어떻게 안전하게 처리할 수 있는가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- 멱등성은 같은 요청이 여러 번 와도 결과가 깨지지 않게 만드는 설계다.
- 네트워크 재시도, 사용자 중복 클릭, 메시지 재처리에서 필요하다.
- 면접에서는 API 레벨, DB 제약, 상태 전이를 함께 설명한다.

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|interview-questions]]
