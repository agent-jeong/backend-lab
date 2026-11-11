---
title: 데이터베이스
description: 느린 쿼리와 데이터 어긋남을 다루는 데이터베이스 노트 모음
tags: [database]
comments: false
---

# 데이터베이스

인덱스, 실행 계획, 락, 격리 수준을 모았다. 쿼리가 느리거나 데이터가 어긋났을 때 어디부터 의심해서 범위를 좁히는지를 주로 적었다.

## 읽는 순서

설계 → 조회 → 성능 → 동시성 → 확장 순서다. 앞 글에서 쓴 용어를 뒤 글이 그대로 쓴다.

1. [[why-rdb|관계형 DB를 사용하는 이유]]
2. [[table-and-key|테이블 설계와 키 전략]]
3. [[normalization-and-denormalization|정규화와 반정규화 판단 기준]]
4. [[join|JOIN의 종류와 동작 원리]]
5. [[db-index|인덱스 동작 원리와 설계 기준]]
6. [[execution-plan|실행 계획(EXPLAIN) 읽는 법]]
7. [[pagination-and-bulk-query|페이징과 대량 조회 전략]]
8. [[transaction-and-isolation|트랜잭션 격리 수준과 동시성 문제]]
9. [[lock|DB 락의 종류와 동작]]
10. [[replication-and-sharding|DB 복제(Replication)와 샤딩]]
11. [[nosql-and-cap|NoSQL과 CAP 정리]]

## 먼저 답해 볼 질문

- RDB를 실무에서 왜 쓰는가?
- 인덱스는 어떤 조건에서 빨라지고, 언제 소용이 없어지는가?
- 실행 계획에서 무엇부터 보는가?
- 트랜잭션 격리 수준은 어떤 문제를 막으려고 있는가?
- 비관적 락과 낙관적 락은 각각 언제 쓰는가?
- JOIN 실행 방식은 성능에 어떤 영향을 주는가?
- OFFSET 페이징은 왜 느리고, 대안은 무엇인가?
- 대용량 데이터를 조회할 때 메모리가 터지지 않게 하려면?

## 실무에서 보는 것

- 장애를 줄이는 건 SQL 문법보다, 쿼리가 데이터를 얼마나 읽는지와 락을 누가 얼마나 오래 잡는지를 아는 쪽이다.
- 쿼리가 느리면 실행 계획, 인덱스 선택도, 조인 방식, 조회 범위를 한꺼번에 본다.
- 데이터가 어긋나면 트랜잭션이 어디서 시작하고 끝나는지, 격리 수준, 같은 데이터에 동시에 들어오는 요청을 같이 본다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 함수와 인덱스, 복합 인덱스 컬럼 순서
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: UNIQUE 제약과 데드락

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
