---
title: 병목 분석 순서
description: 느린 API의 원인을 애플리케이션, DB, 캐시, 외부 API, OS 순으로 좁혀 가는 방법
tags: [concept, performance]
---

# 병목 분석 순서

병목 분석은 전체 응답 시간을 구간별로 쪼개고, 가장 오래 기다리거나 가장 꽉 찬 곳을 측정값으로 찾아 들어가는 일이다.

느린 API의 원인은 코드, DB, Redis, 외부 API, 네트워크, OS 자원 어디에든 있다. 한 구간만 보면 원인 대신 결과를 고치게 된다. 주문 조회가 느려서 DB를 의심했는데 실제로는 connection pool에서 기다리고 있었다거나, CPU는 한가한데 I/O wait, lock wait, 외부 API 대기 때문에 느린 일이 흔하다.

## 순서

1. 느린 endpoint와 시간대를 특정한다.
2. 전체 latency를 애플리케이션 내부 처리, DB, Redis, 외부 API, queue 대기로 나눈다.
3. 같은 시간대의 error rate와 resource saturation을 본다.
4. 시간을 가장 많이 쓰는 구간부터 원인을 좁힌다.
5. 고친 뒤 같은 조건에서 다시 잰다.

```text
API p95 1.2s
- controller/service: 40ms
- DB connection wait: 600ms
- query execution: 120ms
- external API: 300ms
- serialization: 20ms
```

이 경우에는 쿼리 튜닝보다 DB connection pool 대기와 외부 API 지연을 먼저 본다. 둘이 합쳐 900ms로, 쿼리 실행 120ms보다 훨씬 크다.

## 증상별로 먼저 볼 것

| 증상 | 먼저 볼 것 | 의심 원인 |
|---|---|---|
| 특정 API만 느림 | endpoint latency, query count | 쿼리, N+1, 외부 API |
| 전체 API가 느림 | CPU, GC, DB pool, thread pool | 자원 포화, 공통 의존성 |
| timeout 급증 | dependency latency, pool wait | 외부 API, DB pool 고갈 |
| CPU 낮고 latency 높음 | I/O wait, lock wait, queue | DB/Redis/외부 대기 |
| DB CPU 높음 | slow query, execution plan | 인덱스, full scan, 정렬 |

## 자주 깨지는 곳

- 애플리케이션 로그만 보고 DB가 병목이라고 단정하면, DB 지표에서 반대 증거가 나와도 놓친다.
- DB query time과 connection pool wait time을 나눠 보지 않으면, 멀쩡한 쿼리를 튜닝하게 된다.
- p99 지연을 평균 CPU 사용률로만 설명하려 하면, 잠깐 몰린 부하나 대기를 못 본다.
- 여러 개선을 한 번에 넣으면, 무엇이 효과였는지 설명할 수 없다.
- 병목이 아닌 구간을 최적화하면, 애쓴 만큼 응답 시간이 줄지 않는다.
- 계측 없이 시작하면 구간별 시간이 보이지 않는다. 그럴 때는 계측부터 붙인다. 병목이 여러 곳에 겹쳐 있으면 하나씩 보고, 운영 트래픽이 시간대마다 달라지는 것도 감안한다.

## 쓸 도구

- 같은 요청을 반복해 느린 구간이 재현되는지 본다.
- controller, service, repository, external call 시간을 나눠 로그로 남긴다.
- latency, error rate, pool active/wait, CPU, GC, DB QPS를 같은 시간축에 맞춰 본다.
- CPU profile, thread dump, DB execution plan, slowlog를 확인한다.

## 한 번에 설명하기

> 병목 분석은 전체 응답 시간을 구간별로 나눠 가장 오래 걸리는 곳을 찾는 일입니다.
>
> 느린 원인이 코드가 아니라 pool 대기, DB 실행 계획, Redis timeout, 외부 API, OS 자원에 있을 때가 많아서, 특히 DB query time과 connection wait time을 나눠 봅니다.
>
> 고칠 때는 한 번에 하나씩 바꾸고 같은 조건에서 다시 잽니다. 그래야 어떤 지표로 병목을 찾았고 무엇이 효과였는지 말할 수 있습니다.

## 꼬리 질문

- API가 느릴 때 어떤 순서로 원인을 좁힐 것인가?
- DB가 느려 보이지만 실제 원인이 pool 대기일 수 있는 이유는 무엇인가?
- CPU 사용률이 낮은데 API가 느릴 수 있는 이유는 무엇인가?

## 내 사례

- [[file-storage-migration|첨부파일 18만 건 이관]]: dry-run으로 고정 비용 분리하기

## 참고

2026년 11월에 확인한 공식 문서다.

- [Brendan Gregg: The USE Method](https://www.brendangregg.com/usemethod.html)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[db-query-performance]]
- [[connection-pool-and-timeout]]
- [[01-core/os/system-resource-monitoring|system-resource-monitoring]]
