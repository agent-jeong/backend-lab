---
title: 병목 분석 순서
description: API 지연을 애플리케이션, DB, 캐시, 외부 API, OS 관점에서 좁히는 절차
---

# 병목 분석 순서

병목 분석은 전체 응답 시간을 구간별로 나누고, 가장 큰 대기나 포화가 생기는 지점을 증거로 좁혀 가는 작업이다.

느린 API의 원인은 코드, DB, Redis, 외부 API, 네트워크, OS 자원 어디에든 있다. 한 구간만 보면 원인이 아니라 결과를 고치게 된다. DB가 느려 보이는데 실제로는 connection pool 대기이거나, CPU는 낮은데 I/O wait, lock wait, 외부 API 대기로 느린 경우가 흔하다.

## 순서

1. 느린 endpoint와 시간대를 특정한다.
2. 전체 latency를 애플리케이션 내부 처리, DB, Redis, 외부 API, queue 대기로 나눈다.
3. 같은 시간대의 error rate와 resource saturation을 확인한다.
4. 가장 큰 시간을 차지하는 구간부터 원인을 좁힌다.
5. 개선 후 같은 조건에서 다시 측정한다.

```text
API p95 1.2s
- controller/service: 40ms
- DB connection wait: 600ms
- query execution: 120ms
- external API: 300ms
- serialization: 20ms
```

이 경우 쿼리 튜닝보다 DB connection pool 대기와 외부 API 지연을 먼저 본다.

## 증상별로 먼저 볼 것

| 증상 | 먼저 볼 것 | 의심 원인 |
|---|---|---|
| 특정 API만 느림 | endpoint latency, query count | 쿼리, N+1, 외부 API |
| 전체 API가 느림 | CPU, GC, DB pool, thread pool | 자원 포화, 공통 의존성 |
| timeout 급증 | dependency latency, pool wait | 외부 API, DB pool 고갈 |
| CPU 낮고 latency 높음 | I/O wait, lock wait, queue | DB/Redis/외부 대기 |
| DB CPU 높음 | slow query, execution plan | 인덱스, full scan, 정렬 |

## 자주 깨지는 곳

- **애플리케이션 로그만 보고 DB 병목을 단정한다.**
- **DB query time과 connection pool wait time을 구분하지 않는다.** 엉뚱한 쿼리를 튜닝하게 된다.
- **p99 지연을 평균 CPU 사용률로만 해석한다.**
- **여러 개선을 한 번에 적용한다.** 무엇이 효과였는지 설명할 수 없다.
- **병목이 아닌 구간을 최적화한다.**
- **계측 없이 시작한다.** 구간별 시간이 안 보이면 계측부터 한다. 복합 병목은 단계적으로 보고, 운영 트래픽 변동도 감안한다.

## 쓸 도구

- 같은 요청을 반복해 느린 구간이 재현되는지 본다.
- controller, service, repository, external call 시간을 나눠 로그로 남긴다.
- latency, error rate, pool active/wait, CPU, GC, DB QPS를 같은 시간축에 맞춰 본다.
- CPU profile, thread dump, DB execution plan, slowlog를 확인한다.

## 면접에서 말하기

> 병목 분석은 전체 응답 시간을 구간별로 나눠 가장 큰 지연을 찾는 작업입니다. 느린 원인은 코드가 아니라 pool 대기, DB 실행 계획, Redis timeout, 외부 API, OS 자원일 수 있어서, 저는 특히 DB query time과 connection wait time을 나눠 봅니다. 개선은 한 번에 하나씩 하고 같은 조건에서 다시 측정해, 어떤 지표로 병목을 좁혔고 무엇이 효과였는지 설명할 수 있게 합니다.

## 꼬리 질문

- API가 느릴 때 어떤 순서로 원인을 좁힐 것인가?
- DB가 느려 보이지만 실제 원인이 pool 대기일 수 있는 이유는 무엇인가?
- CPU 사용률이 낮은데 API가 느릴 수 있는 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[db-query-performance]]
- [[connection-pool-and-timeout]]
- [[01-core/os/system-resource-monitoring|system-resource-monitoring]]
