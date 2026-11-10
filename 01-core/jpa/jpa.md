---
title: JPA
description: JPA 동작 원리와 성능 문제 학습 인덱스
tags: [jpa]
comments: false
---

# JPA

영속성 컨텍스트, flush, 지연 로딩, N+1, QueryDSL을 다룬다. 쿼리 수와 트랜잭션 경계를 어떻게 확인하는지가 중심이다.

## 읽는 순서

1. [[why-jpa|JPA를 사용하는 이유]]
2. [[entity-table-mapping|Entity와 Table 매핑]]
3. [[persistence-context|영속성 컨텍스트]]
4. [[dirty-checking|Dirty Checking]]
5. [[association-mapping|연관관계 매핑]]
6. [[lazy-and-eager-loading|지연 로딩과 즉시 로딩]]
7. [[n-plus-one-and-fetch-join|N+1과 Fetch Join]]
8. [[transaction-and-flush|Transaction과 flush]]
9. [[osiv|OSIV]]
10. [[querydsl|QueryDSL]]
11. [[querydsl-practical-usage|QueryDSL 실무 활용]]

## 핵심 질문

- JPA를 실무에서 왜 사용하는가?
- 영속성 컨텍스트는 어떤 문제를 해결하는가?
- flush는 언제 발생하고 어떤 영향을 주는가?
- N+1은 왜 발생하고 어떻게 줄이는가?
- QueryDSL은 어떤 문제를 해결하고 어떤 JPA 성능 문제를 그대로 남기는가?
- 동적 검색 조건, DTO projection, count query는 어떻게 설계하는가?
- QueryDSL Custom Repository는 어떤 구조로 작성하는가?

## 실무에서 보는 것

- JPA는 SQL을 없애는 도구가 아니라 객체와 관계형 데이터베이스 사이의 불일치를 관리하는 도구다.
- 영속성 컨텍스트, fetch 전략, 트랜잭션 범위를 모르면 성능 문제와 데이터 불일치가 생긴다.
- 쿼리 수, flush 시점, 변경 감지 범위는 항상 같이 본다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
