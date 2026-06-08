---
title: Observability
description: 로그, 메트릭, 트레이스 기반 장애 분석 학습 인덱스
comments: false
---

# Observability

## 운영 방식

- 이 문서는 Observability 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/observability/` 아래 개념별 문서로 나눈다.
- 학습한 내용은 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 로그, 메트릭, 트레이스, 알림, 장애 분석, 면접 답변을 중심으로 작성한다.

## 학습 산출물

- 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-observability|Observability가 필요한 이유]]
2. [[logging|Logging]]
3. [[metrics|Metrics]]
4. [[distributed-tracing|Distributed Tracing]]
5. [[trace-id-and-correlation-id|traceId와 correlationId]]
6. [[alert-and-slo|Alert와 SLO]]
7. [[dashboard|Dashboard]]
8. [[incident-analysis-flow|장애 분석 흐름]]

## 핵심 질문

- Observability 영역에서 실무적으로 중요한 문제는 무엇인가?
- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하는가?
- 장애 상황에서 어떤 지표를 먼저 보고, 어떤 로그로 좁힐 것인가?
- traceId는 왜 필요하고 어디까지 전파해야 하는가?
- 알림은 단순 임계치가 아니라 어떤 사용자 영향 기준으로 설계해야 하는가?
- 대시보드는 보기 좋은 화면보다 어떤 의사결정을 도와야 하는가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- Observability는 장애가 난 뒤 원인을 빠르게 좁히기 위한 준비다.
- 로그, 메트릭, 트레이스는 서로 다른 질문에 답한다.
- 모든 값을 수집하는 것이 아니라 장애 판단과 원인 분석에 필요한 신호를 수집한다.
- 알림은 운영자가 행동할 수 있는 문제에만 울려야 한다.
- 면접에서는 어떤 지표와 로그로 원인을 좁혔는지 순서대로 설명한다.

## 관련 문서

- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|interview-questions]]
