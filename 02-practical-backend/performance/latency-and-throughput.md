---
title: Latency와 Throughput
description: 응답 시간과 처리량을 구분해 성능 목표를 잡는 기준
---

# Latency와 Throughput

Latency는 요청 하나가 끝나기까지 걸리는 시간이고, Throughput은 단위 시간 동안 처리하는 작업량이다.

둘을 구분하지 않으면 개선 방향이 흔들린다. 처리량을 높였는데 p99 latency가 나빠지면 사용자는 오히려 더 느리다고 느낀다. connection pool, thread pool, DB pool이 포화되면 throughput은 더 늘지 않고 대기 시간만 늘어난다. 그래서 개선을 시작하기 전에 처리량을 높이려는 건지 응답 시간을 줄이려는 건지부터 정한다.

## 동작

1. 요청이 서버에 들어온다.
2. 큐 대기, 애플리케이션 처리, DB/Redis/외부 API 호출을 거친다.
3. 요청 하나의 전체 시간이 latency다.
4. 같은 시간 동안 끝낸 요청 수가 throughput이다.
5. 병목 자원이 포화되면 throughput은 한계에 닿고 latency가 급격히 늘어난다.

```text
낮은 부하:
- 50 RPS, p95 80ms, error 0%

한계 근처:
- 500 RPS, p95 250ms, p99 900ms, error 0.5%

과부하:
- 700 RPS, p95 2s, timeout 증가
```

throughput이 늘다가 어느 지점부터 latency와 error rate가 급증하면, 그 지점이 현재 시스템의 실질적인 처리 한계에 가깝다.

## 목표별 지표

| 목표 | 주요 지표 | 개선 방향 |
|---|---|---|
| 사용자 응답 개선 | p95/p99 latency | 병목 호출 단축, 쿼리 최적화, 캐시 |
| 더 많은 요청 처리 | RPS, TPS, CPU usage | 병렬성, pool 크기, scale out |
| timeout 감소 | p99, dependency latency | timeout, fallback, pool 대기 확인 |
| 배치 시간 단축 | jobs/min, total duration | chunk, parallelism, I/O 최적화 |
| 안정성 유지 | error rate, saturation | 과부하 보호, backpressure |
| 사용자 경험 관리 | Apdex, SLO | 기술 지표를 사용자 만족 기준과 연결한다 |

batch, API, 스트리밍 작업은 성능 목표가 서로 다르다. latency는 사용자 체감에 가깝지만 처리량 한계를 직접 말해 주지 않고, throughput은 처리 능력을 보여 주지만 응답 품질을 가린다. percentile은 tail latency를 드러내지만 표본이 충분하고 수집이 정확해야 믿을 수 있다. 평균보다 p95/p99가 사용자 장애를 더 잘 드러낼 때가 많다.

## 자주 깨지는 곳

- **RPS가 올랐으니 사용자 경험도 좋아졌다고 판단한다.**
- **p50이 좋아진 사이 p99가 나빠진 것을 놓친다.**
- **thread 수를 늘리면 throughput이 항상 오른다고 생각한다.** 포화 지점 이후에는 대기만 는다.
- **pool 대기 시간을 dependency latency로 오해한다.**
- **부하가 낮을 때의 latency로 운영 성능을 예측한다.**

## 운영에서 볼 것

- 요청량을 단계적으로 올리며 latency와 throughput 변화를 본다.
- endpoint별 elapsed time과 dependency elapsed time을 나눠 로그로 남긴다.
- p50/p95/p99, RPS, error rate, active threads, pool wait를 본다.
- 대시보드에서 throughput이 한계에 닿은 뒤 latency가 급증하는 지점을 찾는다.

## 면접에서 말하기

> Latency는 요청 하나의 완료 시간이고 throughput은 단위 시간 처리량입니다. 자원이 포화되면 throughput은 더 늘지 않고 대기 시간이 늘어 latency가 급격히 나빠지기 때문에, 저는 latency, throughput, error rate를 같이 보고 평균보다 p95/p99를 봅니다. 개선을 시작하기 전에 처리량을 높이는 건지 응답 시간을 줄이는 건지 먼저 정하고, SLO나 Apdex 같은 사용자 기준에 연결해서 설명합니다.

## 꼬리 질문

- latency와 throughput은 어떻게 다른가?
- throughput이 높아졌는데 사용자 경험이 나빠질 수 있는 이유는 무엇인가?
- p99 latency가 중요한 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[connection-pool-and-timeout]]
- [[01-core/os/system-resource-monitoring|system-resource-monitoring]]
