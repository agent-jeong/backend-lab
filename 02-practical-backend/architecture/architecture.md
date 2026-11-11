---
title: 아키텍처
description: 책임 분리와 변경 비용을 줄이는 설계 학습 인덱스
tags: [architecture]
comments: false
---

# 아키텍처

계층 구조, 의존성 방향, 모듈 경계, 서비스 책임을 다룬다. 자주 바뀌는 요구사항을 어느 코드에 맡길지가 중심이다.

## 읽는 순서

1. [[oop-design-principles|객체지향 설계 원칙]]
2. [[layered-architecture|계층형 아키텍처]]
3. [[service-responsibility|Controller, Service, Repository 책임]]
4. [[dto-vs-entity|DTO와 Entity 분리]]
5. [[dependency-direction|의존성 방향]]
6. [[module-boundary|모듈 경계]]
7. [[monolith-and-msa|모놀리스와 마이크로서비스]]
8. [[transaction-boundary|Transaction 경계]]
9. [[02-practical-backend/testing/testing|테스트]]: 테스트하기 쉬운 구조는 여기서 이어진다

## 먼저 답해 볼 질문

- Controller, Service, Repository는 각각 무엇을 책임지나? 경계가 무너지면 어떤 증상이 나오나?
- Entity를 API 응답으로 바로 내보내면 무엇이 깨지나?
- 도메인 코드가 JPA나 외부 API 클라이언트 같은 기술 세부에 기대면 무엇이 어려워지나?
- 모듈을 나누는 기준은 패키지 구조인가, 변경 이유인가?
- 계층을 하나 더 두는 비용은 무엇이고, 언제 그 비용을 낼 만한가?

## 실무에서 보는 것

- 구조는 고치는 비용을 줄이고 장애가 번지는 범위를 좁히려고 만든다. 보기 좋은 다이어그램을 그리려고 만드는 게 아니다.
- 계층을 나누면 누가 무엇을 맡고 누가 누구를 아는지가 코드에 드러난다. 계층이 많다고 좋은 설계가 되지는 않는다.
- 설명할 때는 "어떤 변경에 강해졌는가"와 "그 대가로 무엇이 늘었는가"를 같이 말한다.

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/testing/testing|testing]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
