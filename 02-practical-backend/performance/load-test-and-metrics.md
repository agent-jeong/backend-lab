---
title: 부하 테스트와 지표 해석
description: 부하 테스트로 시스템이 어디까지 버티는지, 어디가 먼저 막히는지 확인하는 방법
tags: [concept, performance]
---

# 부하 테스트와 지표 해석

부하 테스트는 목표 요청량과 데이터 조건을 맞춰 놓고 latency, throughput, error rate, 자원 포화를 재서, 시스템이 어디까지 버티고 어디가 먼저 막히는지 보는 일이다.

요청을 하나씩 보내 보는 것으로는 동시 요청, pool 고갈, DB 포화, cache miss 폭증이 드러나지 않는다. 그렇다고 조건이 운영과 다르면 결과를 믿기 어렵고, latency만 보고 DB, Redis, 외부 API, OS 지표를 안 보면 무엇이 병목인지 모른다. 테스트 트래픽이 공격처럼 몰리면 같은 환경을 쓰는 다른 서비스도 영향을 받는다.

## 진행 순서

1. 테스트 목표와 성공 기준을 정한다.
2. 데이터 크기, 캐시 상태, 사용자 분포, 요청 비율을 준비한다.
3. 요청량을 단계적으로 올린다.
4. latency, throughput, error rate, resource saturation을 동시에 모은다.
5. 한계 지점과 병목을 확인한 뒤 고치고 다시 잰다.

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

300 RPS 목표는 맞췄지만, 부하가 더 올라가면 DB pool이나 DB 처리량에서 막힐 수 있다는 뜻이다. 한계 근처에서는 throughput보다 p99 latency, timeout, pool wait가 먼저 나빠진다.

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

closed model과 open model은 결과가 다르게 나오니 구분해서 쓴다. 사용자가 응답을 기다린 뒤 다음 요청을 보내는 closed model에서는 시스템이 느려질수록 보내는 요청도 줄어서, 실제 과부하를 낮게 본다.

부하 테스트를 하면 운영에 내보내기 전에 처리 한계와 어떻게 무너지는지(failure mode)를 보고, 고치기 전후를 숫자로 비교할 수 있다. 다만 운영 트래픽을 그대로 재현하기는 어렵고, 환경을 준비하는 데 품이 들며, 시나리오가 틀리면 결론도 틀린다.

## 자주 깨지는 곳

- 평균 latency만 보고 통과라고 하면, p99에서 터지는 timeout을 놓친다.
- 운영보다 작은 데이터로 테스트하면, 운영에서는 인덱스나 정렬 비용이 달라져 결과가 맞지 않는다.
- 캐시가 warm인 상태만 재면, 배포 직후처럼 캐시가 빈 상태에서 DB로 몰리는 부하를 못 본다.
- 외부 API를 mock으로 바꿔 놓고 결과를 운영 성능처럼 읽으면, 실제 외부 지연이 빠진 숫자를 믿게 된다.
- 테스트하는 동안 DB, Redis, JVM, OS 지표를 같이 보지 않으면, 한계에 닿아도 어디서 막혔는지 모른다.
- closed model만 쓰면, 응답이 느려질수록 요청도 줄어서 과부하를 낮게 본다.
- coordinated omission(부하 도구가 느린 응답을 기다리느라 다음 요청을 늦게 보내서, 그동안 밀렸어야 할 요청의 대기 시간이 측정에서 빠지는 현상)을 모르면, 실제 tail latency보다 낮게 잰 결과를 믿게 된다. 도착률을 고정하는 open model 도구로 재면 줄어든다.

## 운영에서 볼 것

- 요청량을 단계적으로 올려 처리 한계와 어떻게 무너지는지 본다.
- endpoint, response code, elapsed time, request pattern을 로그로 남긴다.
- p50/p95/p99, RPS, error rate, CPU, GC, DB pool, Redis latency를 본다.
- 리포트에 조건, 결과, 병목 추정, 개선 전후 비교를 남긴다.
- 요청 도착률, think time, timeout, warm-up, 측정 구간을 기록한다.

## 한 번에 설명하기

> 부하 테스트는 목표 트래픽에서 시스템이 어디까지 버티는지 보는 일입니다.
>
> 운영과 비슷한 데이터 크기, 캐시 상태, 요청 비율을 준비하고, latency, throughput, error rate, 자원 포화를 같이 봅니다. 요청 도착률과 측정 방식을 잘못 잡으면 p99가 실제보다 좋게 나와서, closed model과 open model을 구분해 씁니다.
>
> 리포트에는 조건, 결과, 병목으로 짐작되는 곳, 고치기 전후 비교를 남깁니다.

## 꼬리 질문

- 부하 테스트에서 어떤 지표를 함께 봐야 하는가?
- load test와 stress test는 어떻게 다른가?
- 캐시 warm 상태만 테스트하면 어떤 문제가 있는가?

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 합격 기준을 코드로 둔 부하 테스트, p95

## 참고

2026년 11월에 확인한 공식 문서다.

- [Gatling Documentation](https://docs.gatling.io/)
- [Google SRE Book: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[latency-and-throughput]]
- [[bottleneck-analysis]]
- [[02-practical-backend/observability/observability|observability]]
