---
title: JPA
description: JPA 동작 원리와 성능 문제 학습 인덱스
comments: false
---

# JPA

## 운영 방식

- 이 문서는 JPA 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/jpa/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 동작 원리, 성능 문제, 트랜잭션 경계, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-jpa|JPA를 사용하는 이유]]
2. [[entity-table-mapping|Entity와 Table 매핑]]
3. [[persistence-context|영속성 컨텍스트]]
4. [[dirty-checking|Dirty Checking]]
5. [[association-mapping|연관관계 매핑]]
6. [[lazy-and-eager-loading|지연 로딩과 즉시 로딩]]
7. [[n-plus-one-and-fetch-join|N+1과 Fetch Join]]
8. [[transaction-and-flush|Transaction과 flush]]
9. [[querydsl|QueryDSL]]
10. [[querydsl-practical-usage|QueryDSL 실무 활용]]

## 핵심 질문

- JPA를 실무에서 왜 사용하는가?
- 영속성 컨텍스트는 어떤 문제를 해결하는가?
- flush는 언제 발생하고 어떤 영향을 주는가?
- N+1은 왜 발생하고 어떻게 줄이는가?
- QueryDSL은 어떤 문제를 해결하고 어떤 JPA 성능 문제를 그대로 남기는가?
- 동적 검색 조건, DTO projection, count query는 어떻게 설계해야 하는가?
- QueryDSL Custom Repository는 어떤 구조로 작성하는가?
- 이 주제의 핵심 동작 원리는 무엇인가?
- 실무에서 자주 발생하는 문제는 무엇인가?
- 어떤 상황에서 주의해야 하는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- JPA는 SQL을 없애는 도구가 아니라 객체와 관계형 데이터베이스 사이의 불일치를 관리하는 도구다.
- 실무에서는 영속성 컨텍스트, fetch 전략, 트랜잭션 범위를 모르면 성능 문제와 데이터 불일치가 생기기 쉽다.
- 쿼리 수, flush 시점, 변경 감지 범위를 항상 같이 봐야 한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
