---
title: Observability
description: 로그, 메트릭, 트레이스 기반 장애 분석 학습 인덱스
comments: false
---

# Observability

> 학습 인덱스다. 상세 내용은 `02-practical-backend/observability/` 아래 개념 문서에 둔다.
> 개념 문서는 로그, 메트릭, 트레이스, 알림, 장애 분석을 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

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

- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하는가?
- 장애 상황에서 어떤 지표를 먼저 보고, 어떤 로그로 좁힐 것인가?
- traceId는 왜 필요하고 어디까지 전파해야 하는가?
- 알림은 단순 임계치가 아니라 어떤 사용자 영향 기준으로 설계해야 하는가?
- 대시보드는 보기 좋은 화면보다 어떤 의사결정을 도와야 하는가?

## 기준

- Observability는 장애가 난 뒤 원인을 빨리 좁히려고 미리 해 두는 준비다.
- 로그, 메트릭, 트레이스는 서로 다른 질문에 답한다.
- 모든 값을 모으지 않는다. 장애 판단과 원인 분석에 쓰는 신호만 모은다.
- 알림은 운영자가 행동할 수 있는 문제에만 울린다.
- 면접에서는 어떤 지표와 로그로 원인을 좁혔는지 순서대로 말한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/kubernetes/kubernetes-logging-and-metrics|kubernetes-logging-and-metrics]]
- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|technical-questions]]
