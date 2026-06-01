---
title: Architecture
description: 책임 분리와 변경 비용을 줄이는 설계 학습 인덱스
---

# Architecture

## 운영 방식

- 이 문서는 Architecture 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/architecture/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 책임 분리, 의존성 방향, 변경 비용, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. Layered Architecture
2. Controller / Service / Repository 책임
3. Domain Model
4. DTO와 Entity 분리
5. 의존성 방향
6. 모듈 분리
7. Transaction 경계
8. 테스트 가능한 설계

## 핵심 질문

- Architecture 영역에서 실무적으로 중요한 문제는 무엇인가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- Architecture는 멋진 구조보다 변경 비용과 장애 범위를 줄이는 데 목적이 있다.
- 계층 분리는 책임과 의존성 방향을 명확히 하기 위한 수단이다.
- 면접에서는 어떤 변경에 강해지는지와 어떤 비용이 생기는지를 함께 설명한다.

## 관련 문서

- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|interview-questions]]
