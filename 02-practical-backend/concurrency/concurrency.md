---
title: 동시성
description: 동시성 문제와 경쟁 조건 해결 학습 인덱스
comments: false
---

# 동시성

> 학습 인덱스다. 상세 내용은 `02-practical-backend/concurrency/` 아래 개념 문서에 둔다.
> 개념 문서는 race condition, lock, 트랜잭션, 멱등성을 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[why-concurrency-problem|동시성 문제가 생기는 이유]]
2. [[race-condition-and-critical-section|Race Condition과 Critical Section]]
3. [[unique-constraint-and-state-transition|Unique 제약과 상태 전이]]
4. [[optimistic-lock|낙관적 락]]
5. [[pessimistic-lock|비관적 락]]
6. [[distributed-lock|분산 락]]
7. [[concurrency-test|동시성 테스트와 재현]]

## 핵심 질문

- 어떤 공유 자원에서 경쟁 조건이 생기는가?
- 단일 요청 테스트에서는 정상인데 운영에서 데이터가 깨지는 이유는 무엇인가?
- lock보다 unique 제약, 조건부 update, 상태 전이가 더 나은 경우는 언제인가?
- 낙관적 락과 비관적 락은 어떤 기준으로 선택하는가?
- Redis 분산 락은 DB 정합성 보장과 무엇이 다른가?
- 동시성 문제를 테스트로 어떻게 재현할 수 있는가?

## 실무에서 보는 것

- 동시성 문제는 단일 요청 테스트로는 드러나지 않는다. 동시에 요청을 보내는 테스트로 재현한다.
- 해결책이 lock만 있는 건 아니다. 조건부 update(`where stock >= ?`), unique 제약, 상태 전이 조건이 더 단순하고 확실한 경우가 많다.
- lock과 멱등성은 다른 문제를 푼다. lock은 "동시에" 들어온 요청의 순서를 정하고, 멱등성은 "이미 처리된" 요청을 알아본다. 결제 재시도처럼 시간차를 두고 오는 중복은 lock으로 막히지 않는다.
- 설명할 때는 어떤 공유 자원에서 어떤 경쟁 조건이 생겼는지부터 말한다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: DB 이름 잠금(`GET_LOCK`)과 잠금이 뚫려도 한 번만 나가는 구조
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 락 대신 조건부 UPDATE로 중복 처리 막기
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 분산 락의 틈과 UNIQUE로 막는 마지막 선

## 관련 문서

- [[first-come-limited-stock|선착순 한정 수량을 초과 없이 팔기]] (면접 설계 문제)
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[01-core/database/lock|lock]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-interview-cases/interview-questions|technical-questions]]
