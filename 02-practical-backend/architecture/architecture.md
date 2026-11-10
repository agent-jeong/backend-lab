---
title: Architecture
description: 책임 분리와 변경 비용을 줄이는 설계 학습 인덱스
comments: false
---

# Architecture

> 학습 인덱스다. 상세 내용은 `02-practical-backend/architecture/` 아래 개념 문서에 둔다.
> 개념 문서는 책임 분리, 의존성 방향, 변경 비용을 다룬다. 순서는 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문이다. 아직 공부하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[layered-architecture|Layered Architecture]]
2. [[service-responsibility|Controller / Service / Repository 책임]]
3. Domain Model
4. [[dto-vs-entity|DTO와 Entity 분리]]
5. [[dependency-direction|의존성 방향]]
6. [[module-boundary|모듈 분리]]
7. [[transaction-boundary|Transaction 경계]]
8. 테스트 가능한 설계

## 붙잡고 있을 질문

- Controller, Service, Repository는 각각 무엇을 책임지나? 경계가 무너지면 어떤 증상이 나오나?
- Entity를 API 응답으로 바로 내보내면 무엇이 깨지나?
- 도메인 코드가 JPA나 외부 API 클라이언트 같은 기술 세부에 기대면 무엇이 어려워지나?
- 모듈을 나누는 기준은 패키지 구조인가, 변경 이유인가?
- 계층을 하나 더 두는 비용은 무엇이고, 언제 그 비용을 낼 만한가?

## 실무 관점

- 구조는 변경 비용과 장애 범위를 줄이려고 만든다. 보기 좋은 다이어그램은 목적이 아니다.
- 계층 분리는 책임과 의존성 방향을 드러내는 수단이다. 계층이 많다고 좋은 설계가 되지 않는다.
- 설명할 때는 "어떤 변경에 강해졌는가"와 "그 대가로 무엇이 늘었는가"를 같이 말한다.

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/testing/testing|testing]]
- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|technical-questions]]
