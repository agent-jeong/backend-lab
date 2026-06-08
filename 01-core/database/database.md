---
title: Database
description: 데이터베이스 성능과 정합성 학습 인덱스
comments: false
---

# Database

## 운영 방식

- 이 문서는 Database 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/database/` 아래 개념별 문서로 나눈다.
- 학습한 내용은 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 조회 성능, 정합성, 장애 원인 분석, 면접 답변을 중심으로 작성한다.

## 학습 산출물

- 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-rdb|RDB를 사용하는 이유]]
2. [[table-and-key|Table, Row, Column, Key]]
3. [[db-index|Index 기본 원리]]
4. [[execution-plan|실행 계획]]
5. [[transaction-and-isolation|Transaction과 Isolation Level]]
6. [[lock|Lock]]
7. [[join|Join]]
8. [[pagination-and-bulk-query|Pagination과 대용량 조회]]

## 핵심 질문

- RDB를 실무에서 왜 사용하는가?
- 인덱스는 어떤 조건에서 효과가 있고 언제 효과가 떨어지는가?
- 실행 계획에서 무엇을 확인해야 하는가?
- 트랜잭션 격리 수준은 어떤 문제를 막기 위한 것인가?
- 비관적 락과 낙관적 락은 각각 언제 사용하는가?
- JOIN의 실행 방식은 성능에 어떤 영향을 주는가?
- OFFSET 페이징이 느린 이유와 대안은 무엇인가?
- 대용량 데이터를 조회할 때 메모리 문제를 어떻게 방지하는가?

## 실무 관점

- Database 학습은 SQL 작성보다 데이터 접근 비용, 정합성, 락 경합을 이해하는 것이 핵심이다.
- 성능 문제는 실행 계획, 인덱스 선택도, 조인 방식, 조회 범위를 함께 봐야 한다.
- 정합성 문제는 트랜잭션 경계, 격리 수준, 동시 요청을 같이 봐야 한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
