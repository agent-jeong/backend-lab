---
title: Latency와 Throughput
description: 응답 시간과 처리량을 구분해 성능 목표를 잡는 기준
---

# Latency와 Throughput

## 한 줄 정의

Latency는 요청 하나가 완료되기까지 걸리는 시간이고, Throughput은 단위 시간 동안 처리할 수 있는 작업량이다.

## 실무에서 왜 문제 되는가

- latency와 throughput을 구분하지 않으면 개선 방향이 흔들린다.
- 처리량을 높였지만 p99 latency가 나빠지면 사용자는 더 느리게 느낄 수 있다.
- connection pool, thread pool, DB pool이 포화되면 throughput이 늘지 않고 대기 시간만 증가한다.
- batch, API, 스트리밍 작업은 성능 목표가 서로 다르다.
- tail latency는 사용자가 실제로 체감하는 장애와 직접 연결될 수 있다.

## 동작 원리

1. 요청이 서버에 들어온다.
2. 큐 대기, 애플리케이션 처리, DB/Redis/외부 API 호출을 거친다.
3. 요청 하나의 전체 시간이 latency가 된다.
4. 같은 시간 동안 완료한 요청 수가 throughput이 된다.
5. 병목 자원이 포화되면 throughput은 한계에 도달하고 latency가 급격히 증가한다.

## 실무 판단 기준

| 목표 | 주요 지표 | 개선 방향 |
|---|---|---|
| 사용자 응답 개선 | p95/p99 latency | 병목 호출 단축, 쿼리 최적화, 캐시 |
| 더 많은 요청 처리 | RPS, TPS, CPU usage | 병렬성, pool 크기, scale out |
| timeout 감소 | p99, dependency latency | timeout, fallback, pool 대기 확인 |
| 배치 시간 단축 | jobs/min, total duration | chunk, parallelism, I/O 최적화 |
| 안정성 유지 | error rate, saturation | 과부하 보호, backpressure |
| 사용자 경험 관리 | Apdex, SLO | 기술 지표를 사용자 만족 기준과 연결한다 |

## 자주 나는 실수

- RPS가 높아졌다는 이유만으로 사용자 경험이 좋아졌다고 판단한다.
- p50이 좋아졌지만 p99가 나빠진 것을 놓친다.
- thread 수를 늘리면 항상 throughput이 올라간다고 생각한다.
- pool 대기 시간을 dependency latency로 오해한다.
- 부하가 낮은 상태의 latency만 보고 운영 성능을 예측한다.

## 확인 방법

- 테스트: 요청량을 단계적으로 올리며 latency와 throughput 변화를 본다.
- 로그: endpoint별 elapsed time과 dependency elapsed time을 분리한다.
- 메트릭: p50/p95/p99, RPS, error rate, active threads, pool wait를 본다.
- 대시보드: throughput 한계 이후 latency가 급증하는 지점을 찾는다.

## 장점과 한계

| 관점 | 장점 | 한계 |
|---|---|---|
| latency | 사용자 체감과 가깝다 | 처리량 한계를 직접 말해주지는 않는다 |
| throughput | 시스템 처리 능력을 보여준다 | 응답 품질을 가릴 수 있다 |
| percentile | tail latency를 드러낸다 | 충분한 표본과 정확한 수집이 필요하다 |

## 짧은 예제

```text
낮은 부하:
- 50 RPS, p95 80ms, error 0%

한계 근처:
- 500 RPS, p95 250ms, p99 900ms, error 0.5%

과부하:
- 700 RPS, p95 2s, timeout 증가
```

throughput이 증가하다가 특정 지점부터 latency와 error rate가 급증하면, 그 지점이 현재 시스템의 실질적인 처리 한계에 가깝다.

## 핵심 요약

Latency는 요청 하나의 완료 시간이고, throughput은 단위 시간 처리량이다.

성능 목표는 둘 중 하나만 보는 것이 아니라 latency, throughput, error rate를 함께 봐야 한다.

자원이 포화되면 throughput은 더 늘지 않고 대기 시간이 증가해 latency가 급격히 나빠진다.

평균보다 p95/p99 tail latency가 사용자 장애를 더 잘 드러낼 때가 많다.

성능 개선은 처리량을 높이는 것인지 응답 시간을 줄이는 것인지 먼저 구분해야 한다.

SLO나 Apdex처럼 사용자 관점의 기준을 함께 두면 기술 지표를 제품 영향으로 설명하기 쉽다.

## 꼬리 질문

- latency와 throughput은 어떻게 다른가?
- throughput이 높아졌는데 사용자 경험이 나빠질 수 있는 이유는 무엇인가?
- p99 latency가 중요한 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[connection-pool-and-timeout]]
- [[01-core/os/system-resource-monitoring|system-resource-monitoring]]
