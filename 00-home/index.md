---
title: Backend Lab
description: 실무 대비와 기술 면접 준비를 위한 백엔드 엔지니어링 학습 노트
---

# Backend Lab

## 이 문서의 목적

매일 하나의 백엔드 주제를 공부하고, 실무 판단 기준과 기술 면접 답변으로 남기기 위한 작업대다.

## 오늘 시작

1. [[00-home/daily-study-board|daily-study-board]]에서 오늘 볼 주제 하나를 고른다.
2. 해당 주제 인덱스를 열고 핵심 질문 하나를 선택한다.
3. 30-60분 안에 작은 개념 문서 하나를 보강한다.
4. 마지막 10분은 [[04-interview/interview-questions|interview-questions]]에 1분 답변으로 압축한다.

오늘의 결과물은 긴 글이 아니라 아래 4가지면 충분하다.

- 한 줄 정의
- 실무에서 문제가 되는 상황
- 판단 기준 또는 해결 절차
- 면접 답변 1분 버전

## 학습 루틴

| 시간 | 할 일 | 산출물 |
|---:|---|---|
| 15분 | 기존 문서 읽기와 빈칸 찾기 | 오늘 다룰 질문 1개 |
| 30분 | 공식 문서, 코드, 예제, 장애 패턴 확인 | 핵심 원리와 주의점 |
| 15분 | 실무 판단 기준으로 정리 | 체크리스트 3-5개 |
| 10분 | 면접 답변으로 압축 | 1분 답변과 꼬리 질문 |

## 바로가기

- [[00-home/daily-study-board|daily-study-board]]: 20일 기본 학습 루트
- [[00-home/mastery-map|mastery-map]]: 전체 주제와 목표 숙련도
- [[00-home/learning-principles|learning-principles]]: 문서 작성 기준과 완료 조건
- [[04-interview/interview-questions|interview-questions]]: 면접 질문과 답변 구조
- [[03-case-studies/case-studies|case-studies]]: 공개 가능한 실무 사례 정리

## 1단계: Core

기초 지식은 실무 문제를 설명하는 언어다. 문법 자체보다 “왜 이런 문제가 생기고 어떻게 판단하는가”를 우선한다.

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[01-core/database/database|database]]
- [[01-core/redis/redis|redis]]
- [[01-core/network/network|network]]
- [[01-core/os/os|os]]

## 2단계: Practical Backend

실무에서 반복되는 장애, 성능, 정합성, 운영 문제를 해결 절차 중심으로 정리한다.

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/security/security|security]]
- [[02-practical-backend/architecture/architecture|architecture]]
- [[02-practical-backend/observability/observability|observability]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/testing/testing|testing]]

## 3단계: Interview / Case / AI

학습한 개념은 반드시 면접 답변과 공개 가능한 사례로 재가공한다.

- [[04-interview/interview-questions|interview-questions]]
- [[03-case-studies/case-studies|case-studies]]
- [[05-ai-workflows/ai-workflows|ai-workflows]]

## 좋은 문서 기준

- 첫 화면에서 “무엇을 해결하는 개념인지” 보인다.
- 추상 설명보다 장애 양상, 판단 기준, 트레이드오프가 먼저 나온다.
- 예시는 `order`, `payment`, `user`, `example-service`처럼 공개 가능한 이름만 쓴다.
- 마지막에는 면접에서 말할 수 있는 짧은 답변이 있다.
