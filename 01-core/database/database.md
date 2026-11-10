---
title: Database
description: 데이터베이스 성능과 정합성 학습 인덱스
comments: false
---

# Database

> 학습 인덱스다. 상세 내용은 `01-core/database/` 아래 개념 문서에 둔다.
> 초점은 조회 성능, 정합성, 장애 원인 분석이다. 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓰고, 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[why-rdb|RDB를 사용하는 이유]]
2. [[table-and-key|Table, Row, Column, Key]]
3. [[db-index|Index 기본 원리]]
4. [[execution-plan|실행 계획]]
5. [[transaction-and-isolation|Transaction과 Isolation Level]]
6. [[lock|Lock]]
7. [[normalization-and-denormalization|정규화와 반정규화]]
8. [[join|Join]]
9. [[replication-and-sharding|Replication과 Sharding]]
10. [[pagination-and-bulk-query|Pagination과 대용량 조회]]

## 스스로 답해 볼 질문

- RDB를 실무에서 왜 쓰는가?
- 인덱스는 어떤 조건에서 빨라지고, 언제 소용이 없어지는가?
- 실행 계획에서 무엇부터 보는가?
- 트랜잭션 격리 수준은 어떤 문제를 막으려고 있는가?
- 비관적 락과 낙관적 락은 각각 언제 쓰는가?
- JOIN 실행 방식은 성능에 어떤 영향을 주는가?
- OFFSET 페이징은 왜 느리고, 대안은 무엇인가?
- 대용량 데이터를 조회할 때 메모리가 터지지 않게 하려면?

## 실무에서 보는 순서

- SQL 문법보다 데이터 접근 비용, 정합성, 락 경합을 이해하는 쪽이 장애를 더 많이 줄인다.
- 성능 문제는 실행 계획, 인덱스 선택도, 조인 방식, 조회 범위를 한꺼번에 본다.
- 정합성 문제는 트랜잭션 경계, 격리 수준, 동시 요청을 같이 본다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 함수와 인덱스, 복합 인덱스 컬럼 순서
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: UNIQUE 제약과 데드락

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview-cases/interview-questions|technical-questions]]
