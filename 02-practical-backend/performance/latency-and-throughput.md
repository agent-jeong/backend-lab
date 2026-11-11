---
title: Latency와 Throughput
description: 응답 시간과 처리량을 나눠 보고, 무엇을 개선할지 먼저 정하는 방법
tags: [concept, performance]
---

# Latency와 Throughput

Latency는 요청 하나가 끝나기까지 걸리는 시간이고, Throughput은 정해진 시간 동안 끝낸 일의 양이다.

둘을 섞어 보면 엉뚱한 쪽을 고친다. 초당 처리하는 주문 수는 늘었는데 p99 latency가 나빠졌다면, 사용자는 오히려 더 느려졌다고 느낀다. connection pool, thread pool, DB pool이 꽉 차면 throughput은 더 늘지 않고 기다리는 시간만 길어진다. 그래서 손대기 전에 처리량을 늘릴지 응답 시간을 줄일지부터 정한다.

## 요청 하나가 지나가는 길

1. 요청이 서버에 들어온다.
2. 큐 대기, 애플리케이션 처리, DB/Redis/외부 API 호출을 거친다.
3. 요청 하나의 전체 시간이 latency다.
4. 같은 시간 동안 끝낸 요청 수가 throughput이다.
5. 병목 자원이 꽉 차면 throughput은 한계에 닿고 latency가 갑자기 늘어난다.

```text
낮은 부하:
- 50 RPS, p95 80ms, error 0%

한계 근처:
- 500 RPS, p95 250ms, p99 900ms, error 0.5%

과부하:
- 700 RPS, p95 2s, timeout 증가
```

throughput이 늘다가 어느 지점부터 latency와 error rate가 치솟으면, 거기가 지금 시스템이 실제로 버티는 한계에 가깝다.

## 목표별 지표

| 목표 | 주요 지표 | 개선 방향 |
|---|---|---|
| 사용자 응답 개선 | p95/p99 latency | 병목 호출 단축, 쿼리 최적화, 캐시 |
| 더 많은 요청 처리 | RPS, TPS, CPU usage | 병렬성, pool 크기, scale out |
| timeout 감소 | p99, dependency latency | timeout, fallback, pool 대기 확인 |
| 배치 시간 단축 | jobs/min, total duration | chunk, parallelism, I/O 최적화 |
| 안정성 유지 | error rate, saturation | 과부하 보호, backpressure |
| 사용자 경험 관리 | Apdex(응답 시간을 만족·참음·불만으로 나눠 0~1 점수로 낸 값), SLO | 기술 지표를 사용자가 만족하는 기준에 맞춘다 |

batch, API, 스트리밍 작업은 성능 목표가 서로 다르다. latency는 사용자가 느끼는 속도에 가깝지만 처리량 한계는 알려 주지 않는다. throughput은 얼마나 많이 처리하는지 보여 주지만, 그 사이 응답이 얼마나 늦었는지는 가린다. percentile은 꼬리 지연(tail latency)을 드러내지만, 표본이 충분하고 제대로 모았을 때만 믿을 수 있다. 사용자가 겪는 장애는 평균보다 p95/p99에서 더 잘 보일 때가 많다.

## 자주 깨지는 곳

- RPS가 올랐다고 사용자 경험도 좋아졌다고 보면, 그 사이 늘어난 응답 지연을 놓친다.
- p50만 보면, 그 사이 p99가 나빠진 것을 모른다.
- thread를 늘리면 throughput이 계속 오를 거라 믿으면, 포화 지점을 넘긴 뒤에는 대기만 는다.
- pool에서 기다린 시간을 dependency latency로 읽으면, 멀쩡한 의존 서비스를 고치려 든다.
- 부하가 낮을 때 잰 latency로 운영 성능을 짐작하면, 실제 트래픽에서 크게 빗나간다.

## 운영에서 볼 것

- 요청량을 단계적으로 올리며 latency와 throughput 변화를 본다.
- endpoint별 elapsed time과 dependency elapsed time을 나눠 로그로 남긴다.
- p50/p95/p99, RPS, error rate, active threads, pool wait를 본다.
- 대시보드에서 throughput이 한계에 닿은 뒤 latency가 치솟는 지점을 찾는다.

## 한 번에 설명하기

> Latency는 요청 하나가 끝나는 데 걸린 시간이고, throughput은 정해진 시간 동안 처리한 양입니다.
>
> 자원이 꽉 차면 throughput은 더 늘지 않고 기다리는 시간만 늘어서 latency가 갑자기 나빠집니다. 그래서 latency, throughput, error rate를 같이 보고, 평균보다 p95/p99를 봅니다.
>
> 고치기 전에 처리량을 늘릴지 응답 시간을 줄일지 먼저 정하고, 결과는 SLO나 Apdex 같은 사용자 기준에 맞춰 설명합니다.

## 꼬리 질문

- latency와 throughput은 어떻게 다른가?
- throughput이 높아졌는데 사용자 경험이 나빠질 수 있는 이유는 무엇인가?
- p99 latency가 중요한 이유는 무엇인가?

## 내 사례

- [[file-storage-migration|첨부파일 18만 건 이관]]: 작은 파일은 대역폭보다 왕복 지연이 병목

## 참고

2026년 11월에 확인한 공식 문서다.

- [Google SRE Book: Monitoring Distributed Systems (four golden signals)](https://sre.google/sre-book/monitoring-distributed-systems/)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[connection-pool-and-timeout]]
- [[01-core/os/system-resource-monitoring|system-resource-monitoring]]
