---
title: JPA
description: JPA가 언제 어떤 쿼리를 날리는지 따라가는 노트 모음
tags: [jpa]
comments: false
---

# JPA

영속성 컨텍스트, flush, 지연 로딩, N+1, QueryDSL을 모았다. 요청 하나에 쿼리가 몇 개 나가는지, 트랜잭션이 어디서 시작하고 끝나는지를 어떻게 확인하는지를 주로 적었다.

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

## 먼저 답해 볼 질문

- JPA를 실무에서 왜 사용하는가?
- 영속성 컨텍스트는 어떤 문제를 해결하는가?
- flush는 언제 발생하고 어떤 영향을 주는가?
- N+1은 왜 발생하고 어떻게 줄이는가?
- QueryDSL은 어떤 문제를 해결하고 어떤 JPA 성능 문제를 그대로 남기는가?
- 동적 검색 조건, DTO projection, count query는 어떻게 설계하는가?
- QueryDSL Custom Repository는 어떤 구조로 작성하는가?

## 실무에서 보는 것

- JPA를 쓴다고 SQL이 사라지지 않는다. 객체와 테이블이 어긋나는 부분을 대신 맞춰 줄 뿐이다.
- 영속성 컨텍스트, fetch 전략, 트랜잭션 범위를 모르고 쓰면 쿼리가 쏟아지거나 저장한 줄 알았던 값이 DB에 없다.
- 쿼리가 몇 개 나가는지, flush가 언제 일어나는지, 변경 감지가 어느 Entity까지 미치는지는 늘 같이 본다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
