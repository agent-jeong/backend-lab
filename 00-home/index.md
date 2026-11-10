---
title: Backend Lab
description: 실무 중심 백엔드 CS 학습과 기술 질문 대응을 위한 학습 노트
comments: false
---

# Backend Lab

백엔드 주제를 실무 판단 기준과 말로 설명할 수 있는 기술 답변으로 정리하는 작업대다.

## 시작하기

1. [[00-home/daily-study-board|daily-study-board]]에서 학습할 주제를 고른다.
2. 해당 주제 인덱스를 열고 핵심 질문 하나를 선택한다.
3. 개념 문서 하나를 보강한다.
4. [[04-interview-cases/interview-questions|technical-questions]]에 짧은 설명으로 압축한다.

결과물은 긴 글이 아니라 이 네 가지면 된다.

- 한 줄 정의
- 실무에서 문제가 되는 상황
- 판단 기준 또는 해결 절차
- 말로 할 짧은 답변

## 학습 흐름

| 단계 | 할 일 | 산출물 |
|---:|---|---|
| 1 | 기존 문서 읽기와 빈칸 찾기 | 다룰 질문 1개 |
| 2 | 공식 문서, 코드, 예제, 장애 패턴 확인 | 핵심 원리와 주의점 |
| 3 | 실무 판단 기준으로 정리 | 체크리스트 3-5개 |
| 4 | 설명 가능한 답변으로 압축 | 1분 요약과 꼬리 질문 |

## 바로가기

- [[00-home/daily-study-board|daily-study-board]]: 영역별 학습 주제와 산출물 가이드
- [[00-home/mastery-map|mastery-map]]: 전체 주제와 목표 숙련도
- [[00-home/learning-principles|learning-principles]]: 문서 작성 기준과 완료 조건
- [[04-interview-cases/interview-questions|technical-questions]]: 기술 질문과 답변 구조
- [[03-work-cases/work-cases|work-cases]]: 직접 겪은 문제를 일반화한 실무 사례
- [[04-interview-cases/design-cases|design-cases]]: 면접에서 자주 나오는 설계 문제
- [[00-home/glossary|glossary]]: 실무 핵심 용어 정리

## 1단계: Core

기초 지식은 실무 문제를 설명하는 언어다. 문법보다 “왜 이런 문제가 생기고 어떻게 판단하는가”를 먼저 본다.

- [[01-core/java/java|java]]
- [[01-core/kotlin/kotlin|kotlin]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[01-core/database/database|database]]
- [[01-core/redis/redis|redis]]
- [[01-core/network/network|network]]
- [[01-core/os/os|os]]

## 2단계: Practical Backend

실무에서 되풀이되는 장애, 성능, 정합성, 운영 문제를 해결 절차 위주로 정리한다.

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]
- [[02-practical-backend/architecture/architecture|architecture]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/security/security|security]]
- [[02-practical-backend/testing/testing|testing]]
- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]

## 3단계: Questions / Case / AI

공부한 개념은 짧은 기술 답변과 공개 가능한 사례로 다시 만든다.

- [[04-interview-cases/interview-questions|technical-questions]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-interview-cases/design-cases|design-cases]]
- [[05-ai-workflows/ai-workflows|ai-workflows]]

## 좋은 문서 기준

- 첫 화면에서 “무엇을 해결하는 개념인지”가 보인다.
- 추상 설명보다 장애 양상, 판단 기준, 트레이드오프가 먼저 나온다.
- 예시는 `order`, `payment`, `user`, `example-service`처럼 공개 가능한 이름만 쓴다.
- 끝에 질문을 받으면 바로 말할 수 있는 짧은 답변이 있다.
