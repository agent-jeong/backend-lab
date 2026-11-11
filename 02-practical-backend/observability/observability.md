---
title: 관측성
description: 로그, 메트릭, 트레이스 기반 장애 분석 학습 인덱스
tags: [observability]
comments: false
---

# 관측성

로그, 메트릭, 분산 추적, traceId, 알림과 SLO, 장애 분석 순서를 다룬다. 장애가 나기 전에 무엇을 남겨 둬야 나중에 원인을 찾을 수 있는지가 이 폴더의 주제다.

## 읽는 순서

1. [[why-observability|Observability가 필요한 이유]]
2. [[logging|로깅]]
3. [[metrics|메트릭]]
4. [[distributed-tracing|분산 추적]]
5. [[trace-id-and-correlation-id|traceId와 correlationId]]
6. [[alert-and-slo|Alert와 SLO]]
7. [[dashboard|대시보드]]
8. [[incident-analysis-flow|장애 분석 흐름]]

## 먼저 답해 볼 질문

- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하는가?
- 장애 상황에서 어떤 지표를 먼저 보고, 어떤 로그로 좁힐 것인가?
- traceId는 왜 필요하고 어디까지 전파해야 하는가?
- 알림은 단순 임계치 말고 사용자가 겪는 어떤 영향을 기준으로 울려야 하는가?
- 대시보드는 보기 좋은 화면보다 어떤 판단을 도와야 하는가?

## 실무에서 보는 것

- Observability는 장애가 난 뒤 원인을 빨리 좁히려고 미리 해 두는 준비다.
- 로그, 메트릭, 트레이스는 서로 다른 질문에 답한다.
- 모든 값을 모으지 않는다. 장애인지 판단하고 원인을 찾는 데 쓰는 신호만 모은다.
- 알림은 운영자가 바로 손쓸 수 있는 문제에만 울린다.
- 면접에서는 어떤 지표와 로그로 원인을 좁혔는지 순서대로 말한다.

## 내 사례

- [[inherited-access-system-incidents|이어받은 시스템의 장애 추적]]: 성공한 날과 실패한 날을 대조해 원인 좁히기, 삼켜지던 에러에 로그 붙이기

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/kubernetes/kubernetes-logging-and-metrics|kubernetes-logging-and-metrics]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
