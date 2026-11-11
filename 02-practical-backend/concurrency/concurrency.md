---
title: 동시성
description: 같은 데이터에 요청이 동시에 몰릴 때 무엇이 깨지고 어떻게 막는지 다룬 글 모음
tags: [concurrency]
comments: false
---

# 동시성

경쟁 조건, 낙관적 락과 비관적 락, 분산 락, UNIQUE 제약과 상태 전이, 동시성 테스트를 다룬다. 같은 요청이 동시에 들어오면 무엇이 깨지는지를 주로 이야기한다.

## 읽는 순서

1. [[why-concurrency-problem|동시성 문제가 생기는 이유]]
2. [[race-condition-and-critical-section|Race Condition과 Critical Section]]
3. [[unique-constraint-and-state-transition|Unique 제약과 상태 전이]]
4. [[optimistic-lock|낙관적 락]]
5. [[pessimistic-lock|비관적 락]]
6. [[distributed-lock|분산 락]]
7. [[concurrency-test|동시성 테스트와 재현]]

## 먼저 답해 볼 질문

- 어떤 공유 자원에서 경쟁 조건이 생기나?
- 요청을 하나씩 보내는 테스트는 통과하는데 운영에서 데이터가 깨지는 이유는?
- 락보다 unique 제약, 조건부 update, 상태 전이가 나은 경우는 언제인가?
- 낙관적 락과 비관적 락은 무엇을 보고 고르나?
- Redis 분산 락과 DB가 지켜 주는 정합성은 무엇이 다른가?
- 동시성 문제를 테스트로 어떻게 재현하나?

## 실무에서 보는 것

- 동시성 문제는 요청을 하나씩 보내는 테스트로는 드러나지 않는다. 요청을 동시에 보내는 테스트로 재현한다.
- 락만 답이 아니다. 조건부 update(`where stock >= ?`), unique 제약, 상태 전이 조건이 더 단순하고 확실한 경우가 많다.
- 락과 멱등성은 막는 문제가 다르다. 락은 "동시에" 들어온 요청을 줄 세우고, 멱등성은 "이미 처리된" 요청을 알아본다. 결제 재시도처럼 시간을 두고 다시 오는 중복은 락으로 막히지 않는다.
- 설명할 때는 어떤 공유 자원에서 어떤 경쟁 조건이 생겼는지부터 말한다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: DB 이름 잠금(`GET_LOCK`)과 잠금이 뚫려도 한 번만 나가는 구조
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 락 대신 조건부 UPDATE로 중복 처리 막기
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 분산 락의 틈과 UNIQUE로 막는 마지막 선

## 관련 문서

- [[first-come-limited-stock|선착순 한정 수량을 초과 없이 팔기]] (설계 사례)
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[01-core/database/lock|lock]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
