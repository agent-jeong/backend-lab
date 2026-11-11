---
title: 성능
description: 백엔드 성능 문제 분석과 개선 학습 인덱스
tags: [performance]
comments: false
---

# 성능

지연과 처리량, 병목 분석, DB 쿼리, 캐시, 커넥션 풀, 부하 테스트를 다룬다. 어디가 느린지 재서 찾고, 고친 뒤 정말 빨라졌는지 숫자로 보여 주는 것까지가 이 폴더의 범위다.

## 읽는 순서

1. [[why-performance-problem|성능 문제를 정의하는 기준]]
2. [[latency-and-throughput|Latency와 Throughput]]
3. [[bottleneck-analysis|병목 분석 순서]]
4. [[db-query-performance|DB 조회 성능]]
5. [[cache-performance|Cache 적용]]
6. [[connection-pool-and-timeout|Connection Pool과 Timeout]]
7. [[rate-limiting|처리율 제한(Rate Limiting)]]
8. [[load-test-and-metrics|부하 테스트와 지표 해석]]

## 먼저 답해 볼 질문

- 느린 API를 성능 문제라고 판단하는 기준은 무엇인가?
- 평균 latency보다 p95/p99를 봐야 하는 이유는 무엇인가?
- 병목을 애플리케이션, DB, Redis, 외부 API, OS 중 어디서부터 좁힐 것인가?
- DB 조회 성능은 인덱스, 실행 계획, 쿼리 수 중 무엇부터 확인할 것인가?
- 캐시가 오히려 장애를 퍼뜨리는 때는 언제인가?
- connection pool 고갈과 timeout은 어떤 증상으로 드러나는가?
- 부하 테스트 결과를 운영 지표와 어떻게 연결할 것인가?

## 실무에서 보는 것

- 손대기 전에 무엇을 잴지, 어떤 조건에서 재현할지부터 적는다.
- 고치기 전과 후를 같은 조건에서 숫자로 비교한다.
- 캐시, 인덱스, 비동기, 스케일아웃은 부작용이 저마다 다르다.
- 설명할 때는 "무엇을 고쳤다"보다 "병목을 어떻게 찾았다"를 먼저 말한다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 실행계획으로 원인 좁히기, p95로 확인하기
- [[file-storage-migration|첨부파일 18만 건 이관]]: 고정 비용을 분리해 추정 바로잡기, 왕복 지연과 병렬도

## 관련 문서

- [[01-core/database/database|database]]
- [[01-core/jpa/jpa|jpa]]
- [[01-core/redis/redis|redis]]
- [[01-core/network/network|network]]
- [[01-core/os/os|os]]
- [[02-practical-backend/observability/observability|observability]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
