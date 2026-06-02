---
title: 부하 테스트와 지표 해석
description: 부하 테스트로 처리 한계와 병목을 검증하는 실무 기준
---

# 부하 테스트와 지표 해석

## 한 줄 정의

부하 테스트는 목표 요청량과 데이터 조건에서 latency, throughput, error rate, 자원 포화를 측정해 시스템 한계와 병목을 확인하는 작업이다.

## 실무에서 왜 문제 되는가

- 단일 요청 테스트로는 동시 요청, pool 고갈, DB 포화, cache miss 폭증을 확인하기 어렵다.
- 부하 테스트 조건이 운영과 다르면 결과를 신뢰하기 어렵다.
- latency만 보고 DB, Redis, 외부 API, OS 자원 지표를 보지 않으면 병목을 알 수 없다.
- 테스트가 공격 트래픽처럼 동작하면 공유 환경에 영향을 줄 수 있다.

## 동작 원리

1. 테스트 목표와 성공 기준을 정한다.
2. 데이터 크기, 캐시 상태, 사용자 분포, 요청 비율을 준비한다.
3. 요청량을 단계적으로 증가시킨다.
4. latency, throughput, error rate, resource saturation을 동시에 수집한다.
5. 한계 지점과 병목을 확인한 뒤 개선하고 재측정한다.

## 실무 판단 기준

| 테스트 | 목적 | 확인 지표 |
|---|---|---|
| smoke test | 기본 동작 확인 | error, 기본 latency |
| load test | 목표 트래픽 검증 | p95/p99, RPS, resource usage |
| stress test | 한계 지점 확인 | saturation, timeout, failure mode |
| spike test | 급증 트래픽 확인 | queue, autoscaling, cache miss |
| soak test | 장시간 안정성 확인 | memory leak, GC, connection leak |
| closed model | 제한된 동시 사용자 재현 | 사용자가 응답을 기다린 뒤 다음 요청을 보내는 상황 |
| open model | 고정 도착률 재현 | 응답 지연과 무관하게 요청이 계속 들어오는 상황 |

## 자주 나는 실수

- 평균 latency만 보고 성공으로 판단한다.
- 운영보다 작은 데이터로 테스트한다.
- 캐시가 warm인 상태만 측정한다.
- 외부 API를 mock으로 바꾸고도 운영 성능처럼 해석한다.
- 테스트 중 DB, Redis, JVM, OS 지표를 함께 보지 않는다.
- 응답이 느려지면 요청 발생량도 줄어드는 테스트 모델만 보고 과부하 상황을 과소평가한다.
- coordinated omission 때문에 실제 tail latency보다 낮게 측정된 결과를 믿는다.

## 확인 방법

- 테스트: 요청량을 단계적으로 올려 처리 한계와 장애 양상을 확인한다.
- 로그: endpoint, response code, elapsed time, request pattern을 남긴다.
- 메트릭: p50/p95/p99, RPS, error rate, CPU, GC, DB pool, Redis latency를 본다.
- 리포트: 조건, 결과, 병목 추정, 개선 전후 비교를 남긴다.
- 도구 설정: 요청 도착률, think time, timeout, warm-up, 측정 구간을 명확히 기록한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 운영 전 처리 한계를 예측할 수 있다 | 운영 트래픽을 완전히 재현하기 어렵다 |
| 병목과 failure mode를 확인할 수 있다 | 테스트 환경 비용과 준비가 필요하다 |
| 개선 전후를 숫자로 비교할 수 있다 | 잘못된 시나리오는 잘못된 결론을 만든다 |

## 짧은 예제

```text
목표:
- 300 RPS에서 p95 < 300ms
- p99 < 800ms
- error rate < 0.1%

결과:
- 300 RPS p95 240ms, p99 620ms
- 500 RPS부터 DB pool wait 증가
- 650 RPS부터 timeout 증가
```

이 결과는 300 RPS 목표는 만족하지만, 더 높은 부하에서는 DB pool 또는 DB 처리량이 병목이 될 수 있음을 보여준다.

부하 테스트에서는 closed model과 open model의 차이를 이해해야 한다. 사용자가 응답을 기다린 뒤 다음 요청을 보내는 모델은 시스템이 느려질수록 요청 발생량도 줄어 실제 과부하를 낮게 볼 수 있다.

## 핵심 요약

부하 테스트는 목표 트래픽에서 시스템이 어느 지점까지 안정적인지 확인하는 작업이다.

결과는 latency, throughput, error rate, resource saturation을 함께 봐야 한다.

운영과 비슷한 데이터 크기, 캐시 상태, 요청 비율을 준비해야 의미 있는 결과가 나온다.

한계 지점에서는 throughput보다 p99 latency와 timeout, pool wait이 먼저 나빠질 수 있다.

부하 테스트 리포트에는 조건, 결과, 병목 추정, 개선 전후 비교가 남아야 한다.

요청 도착률과 측정 방식을 잘못 잡으면 p99 latency가 실제보다 좋게 보일 수 있다.

## 꼬리 질문

- 부하 테스트에서 어떤 지표를 함께 봐야 하는가?
- load test와 stress test는 어떻게 다른가?
- 캐시 warm 상태만 테스트하면 어떤 문제가 있는가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[latency-and-throughput]]
- [[bottleneck-analysis]]
- [[02-practical-backend/observability/observability|observability]]
