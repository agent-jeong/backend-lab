---
title: 부하 테스트와 지표 해석
description: 부하 테스트로 처리 한계와 병목을 검증하는 실무 기준
tags: [concept, performance]
---

# 부하 테스트와 지표 해석

부하 테스트는 목표 요청량과 데이터 조건에서 latency, throughput, error rate, 자원 포화를 측정해 시스템의 한계와 병목을 확인하는 작업이다.

단일 요청 테스트로는 동시 요청, pool 고갈, DB 포화, cache miss 폭증을 볼 수 없다. 하지만 조건이 운영과 다르면 결과도 믿기 어렵고, latency만 보고 DB, Redis, 외부 API, OS 지표를 안 보면 병목을 모른다. 테스트가 공격 트래픽처럼 동작하면 공유 환경에도 영향을 준다.

## 진행 순서

1. 테스트 목표와 성공 기준을 정한다.
2. 데이터 크기, 캐시 상태, 사용자 분포, 요청 비율을 준비한다.
3. 요청량을 단계적으로 올린다.
4. latency, throughput, error rate, resource saturation을 동시에 수집한다.
5. 한계 지점과 병목을 확인한 뒤 개선하고 다시 측정한다.

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

300 RPS 목표는 만족하지만, 더 높은 부하에서는 DB pool 또는 DB 처리량이 병목이 될 수 있다는 결과다. 한계 근처에서는 throughput보다 p99 latency, timeout, pool wait가 먼저 나빠진다.

## 테스트 종류

| 테스트 | 목적 | 확인 지표 |
|---|---|---|
| smoke test | 기본 동작 확인 | error, 기본 latency |
| load test | 목표 트래픽 검증 | p95/p99, RPS, resource usage |
| stress test | 한계 지점 확인 | saturation, timeout, failure mode |
| spike test | 급증 트래픽 확인 | queue, autoscaling, cache miss |
| soak test | 장시간 안정성 확인 | memory leak, GC, connection leak |
| closed model | 제한된 동시 사용자 재현 | 사용자가 응답을 기다린 뒤 다음 요청을 보내는 상황 |
| open model | 고정 도착률 재현 | 응답 지연과 무관하게 요청이 계속 들어오는 상황 |

closed model과 open model의 차이를 알고 써야 한다. 사용자가 응답을 기다린 뒤 다음 요청을 보내는 모델은 시스템이 느려질수록 요청 발생량도 줄어서 실제 과부하를 낮게 본다.

부하 테스트로 운영 전에 처리 한계와 failure mode를 확인하고 개선 전후를 숫자로 비교할 수 있다. 다만 운영 트래픽을 완전히 재현하기는 어렵고, 환경을 준비하는 비용이 들며, 시나리오가 틀리면 결론도 틀린다.

## 자주 깨지는 곳

- **평균 latency만 보고 성공으로 판단한다.**
- **운영보다 작은 데이터로 테스트한다.**
- **캐시가 warm인 상태만 측정한다.**
- **외부 API를 mock으로 바꾸고도 운영 성능처럼 해석한다.**
- **테스트 중 DB, Redis, JVM, OS 지표를 같이 보지 않는다.**
- **closed model만 본다.** 응답이 느려지면 요청량도 줄어 과부하를 과소평가한다.
- **coordinated omission을 모른다.** 실제 tail latency보다 낮게 측정된 결과를 믿게 된다.

## 운영에서 볼 것

- 요청량을 단계적으로 올려 처리 한계와 장애 양상을 확인한다.
- endpoint, response code, elapsed time, request pattern을 로그로 남긴다.
- p50/p95/p99, RPS, error rate, CPU, GC, DB pool, Redis latency를 본다.
- 리포트에 조건, 결과, 병목 추정, 개선 전후 비교를 남긴다.
- 요청 도착률, think time, timeout, warm-up, 측정 구간을 기록한다.

## 한 번에 설명하기

> 부하 테스트는 목표 트래픽에서 시스템이 어디까지 버티는지 확인하는 작업입니다. 저는 운영과 비슷한 데이터 크기, 캐시 상태, 요청 비율을 준비하고, latency, throughput, error rate, 자원 포화를 같이 봅니다. 요청 도착률과 측정 방식을 잘못 잡으면 p99가 실제보다 좋게 보여서 closed model과 open model을 구분하고, 리포트에는 조건, 결과, 병목 추정, 개선 전후 비교를 남깁니다.

## 꼬리 질문

- 부하 테스트에서 어떤 지표를 함께 봐야 하는가?
- load test와 stress test는 어떻게 다른가?
- 캐시 warm 상태만 테스트하면 어떤 문제가 있는가?

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 합격 기준을 코드로 둔 부하 테스트, p95

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Gatling Documentation](https://docs.gatling.io/)
- [Google SRE Book: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[latency-and-throughput]]
- [[bottleneck-analysis]]
- [[02-practical-backend/observability/observability|observability]]
