---
title: Performance
description: 백엔드 성능 문제 분석과 개선 학습 인덱스
comments: false
---

# Performance

## 운영 방식

- 이 문서는 Performance 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/performance/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 병목 원인, 측정 방법, 개선 방법, 한계를 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-performance-problem|성능 문제를 정의하는 기준]]
2. [[latency-and-throughput|Latency와 Throughput]]
3. [[bottleneck-analysis|병목 분석 순서]]
4. [[db-query-performance|DB 조회 성능]]
5. [[cache-performance|Cache 적용]]
6. [[connection-pool-and-timeout|Connection Pool과 Timeout]]
7. [[load-test-and-metrics|부하 테스트와 지표 해석]]

## 핵심 질문

- Performance 영역에서 실무적으로 중요한 문제는 무엇인가?
- 느린 API를 성능 문제라고 판단하는 기준은 무엇인가?
- 평균 latency보다 p95/p99를 봐야 하는 이유는 무엇인가?
- 병목을 애플리케이션, DB, Redis, 외부 API, OS 중 어디서부터 좁힐 것인가?
- DB 조회 성능은 인덱스, 실행 계획, 쿼리 수 중 무엇부터 확인할 것인가?
- 캐시는 언제 성능 개선이 아니라 장애 전파를 만들 수 있는가?
- connection pool 고갈과 timeout은 어떤 증상으로 드러나는가?
- 부하 테스트 결과를 운영 지표와 어떻게 연결할 것인가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- 성능 문제는 먼저 측정 기준과 재현 조건을 정의한다.
- 개선 전후를 숫자로 비교한다.
- 캐시, 인덱스, 비동기, 스케일아웃은 각각 다른 부작용을 만든다.
- 면접에서는 "무엇을 개선했다"보다 "어떻게 병목을 찾았는가"를 설명한다.

## 관련 문서

- [[01-core/database/database|database]]
- [[01-core/jpa/jpa|jpa]]
- [[01-core/redis/redis|redis]]
- [[01-core/network/network|network]]
- [[01-core/os/os|os]]
- [[02-practical-backend/observability/observability|observability]]
- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|interview-questions]]
