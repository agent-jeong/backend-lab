---
title: Idempotency
description: 중복 요청과 재시도에 안전한 설계 학습 인덱스
comments: false
---

# Idempotency

> 학습 인덱스다. 상세 내용은 `02-practical-backend/idempotency/` 아래 개념 문서에 둔다.
> 개념 문서는 중복 요청, 재시도, 상태 전이, 유니크 제약을 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[why-idempotency|멱등성이 필요한 이유]]
2. [[duplicate-request-and-retry|중복 요청과 재시도]]
3. [[idempotency-key|Idempotency Key]]
4. [[state-transition-and-unique-constraint|상태 전이와 Unique 제약]]
5. [[message-consumer-idempotency|메시지 소비 멱등성]]
6. [[payment-order-idempotency|결제와 주문 멱등성]]

## 핵심 질문

- 멱등성과 단순 중복 제거는 무엇이 다른가?
- timeout 이후 재시도할 때 왜 결과 불명 상태를 고려해야 하는가?
- idempotency key는 어디에서 만들고 얼마나 보관해야 하는가?
- unique constraint와 상태 전이는 멱등성에서 어떤 역할을 하는가?
- 메시지는 왜 중복 소비될 수 있고 소비자는 어떻게 방어해야 하는가?
- 결제와 주문 처리에서 중복 요청을 어떻게 안전하게 처리할 수 있는가?

## 실무 관점

- 멱등성은 같은 요청이 여러 번 와도 결과가 한 번 처리한 것과 같게 만드는 설계다. 네트워크 재시도, 중복 클릭, 메시지 재처리에서 필요하다.
- timeout은 실패가 아니라 "결과 모름"이다. 실패로 단정하고 새 요청을 만들면 이중 처리가 생긴다.
- lock은 동시에 들어온 요청을 줄 세울 뿐, 이미 처리된 요청을 알아보지 못한다. 10초 뒤에 온 재시도는 lock으로 막을 수 없다.
- 최종 방어선은 DB다. idempotency key 저장소가 있어도 업무 테이블의 unique 제약과 조건부 update를 같이 둔다.
- 설명할 때는 API 레벨(key), DB 제약, 상태 전이를 한 흐름으로 묶는다.

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
- [[04-interview-cases/interview-questions|technical-questions]]
