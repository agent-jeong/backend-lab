---
title: 멱등성
description: 같은 요청이 여러 번 와도 한 번만 처리되게 만드는 방법을 다룬 글 모음
tags: [idempotency]
comments: false
---

# 멱등성

중복 요청과 재시도, 멱등키, 메시지 소비, 결제와 주문의 멱등성을 다룬다. 같은 요청이 여러 번 와도 결과가 바뀌지 않게 하는 방법을 주로 이야기한다.

## 읽는 순서

1. [[why-idempotency|멱등성이 필요한 이유]]
2. [[duplicate-request-and-retry|중복 요청과 재시도]]
3. [[idempotency-key|Idempotency Key]]
4. [[state-transition-and-unique-constraint|상태 전이와 Unique 제약]]
5. [[message-consumer-idempotency|메시지 소비 멱등성]]
6. [[payment-order-idempotency|결제와 주문 멱등성]]

## 먼저 답해 볼 질문

- 멱등성과 단순히 중복을 걸러 내는 것은 무엇이 다른가?
- timeout 뒤 재시도할 때 왜 "결과를 모르는 상태"를 따져야 하나?
- idempotency key는 어디서 만들고 얼마나 보관하나?
- unique constraint와 상태 전이는 멱등성에서 무엇을 막나?
- 메시지는 왜 두 번 소비될 수 있고, 소비자는 어떻게 막아야 하나?
- 결제와 주문에서 중복 요청을 어떻게 안전하게 처리하나?

## 실무에서 보는 것

- 멱등성은 같은 요청이 여러 번 와도 한 번 처리한 것과 같은 결과가 남게 하는 설계다. 네트워크 재시도, 중복 클릭, 메시지 재처리에서 필요하다.
- timeout은 실패가 아니라 "결과 모름"이다. 실패로 단정하고 새 요청을 만들면 두 번 처리된다.
- 락은 동시에 들어온 요청을 줄 세울 뿐, 이미 처리된 요청을 알아보지 못한다. 10초 뒤에 온 재시도는 락으로 막을 수 없다.
- 마지막에 막아 주는 건 DB다. idempotency key 저장소가 있어도 업무 테이블에 unique 제약과 조건부 update를 같이 둔다.
- 설명할 때는 API에서 받는 키, DB 제약, 상태 전이를 하나의 흐름으로 이어서 말한다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 멱등키 없는 외부 승인을 한 번만 보내기
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 같은 웹훅이 두 번 와도 한 번만 처리
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 두 번 돌아도 한 번만 지급하는 배치

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[02-practical-backend/transaction/compensation-and-outbox|compensation-and-outbox]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
