---
title: Performance
description: 백엔드 성능 문제 분석과 개선 학습 인덱스
comments: false
---

# Performance

> 학습 인덱스다. 상세 내용은 `02-practical-backend/performance/` 아래 개념 문서에 둔다.
> 개념 문서는 병목 원인, 측정 방법, 개선 방법과 한계를 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[why-performance-problem|성능 문제를 정의하는 기준]]
2. [[latency-and-throughput|Latency와 Throughput]]
3. [[bottleneck-analysis|병목 분석 순서]]
4. [[db-query-performance|DB 조회 성능]]
5. [[cache-performance|Cache 적용]]
6. [[connection-pool-and-timeout|Connection Pool과 Timeout]]
7. [[load-test-and-metrics|부하 테스트와 지표 해석]]

## 핵심 질문

- 느린 API를 성능 문제라고 판단하는 기준은 무엇인가?
- 평균 latency보다 p95/p99를 봐야 하는 이유는 무엇인가?
- 병목을 애플리케이션, DB, Redis, 외부 API, OS 중 어디서부터 좁힐 것인가?
- DB 조회 성능은 인덱스, 실행 계획, 쿼리 수 중 무엇부터 확인할 것인가?
- 캐시는 언제 성능 개선이 아니라 장애 전파를 만들 수 있는가?
- connection pool 고갈과 timeout은 어떤 증상으로 드러나는가?
- 부하 테스트 결과를 운영 지표와 어떻게 연결할 것인가?

## 실무 관점

- 성능 문제는 먼저 측정 기준과 재현 조건을 정의한다.
- 개선 전후를 숫자로 비교한다.
- 캐시, 인덱스, 비동기, 스케일아웃은 각각 다른 부작용을 만든다.
- 설명할 때는 "무엇을 개선했다"보다 "어떻게 병목을 찾았는가"를 먼저 말한다.

## 관련 문서

- [[01-core/database/database|database]]
- [[01-core/jpa/jpa|jpa]]
- [[01-core/redis/redis|redis]]
- [[01-core/network/network|network]]
- [[01-core/os/os|os]]
- [[02-practical-backend/observability/observability|observability]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-interview-cases/interview-questions|technical-questions]]
