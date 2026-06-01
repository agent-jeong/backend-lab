---
title: Concurrency
description: 동시성 문제와 경쟁 조건 해결 학습 인덱스
---

# Concurrency

## 운영 방식

- 이 문서는 Concurrency 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/concurrency/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 race condition, lock, transaction, idempotency, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. 동시성 문제가 생기는 이유
2. Race Condition
3. Critical Section
4. Optimistic Lock
5. Pessimistic Lock
6. Distributed Lock
7. Idempotency
8. 테스트와 재현

## 핵심 질문

- Concurrency 영역에서 실무적으로 중요한 문제는 무엇인가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- 동시성 문제는 단일 요청 테스트로는 드러나지 않는다.
- 해결책은 lock만이 아니라 유니크 제약, 상태 전이, 멱등성 설계까지 포함한다.
- 면접에서는 어떤 공유 자원에서 어떤 경쟁 조건이 생겼는지 설명한다.

## 관련 문서

- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|interview-questions]]
