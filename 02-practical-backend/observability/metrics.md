---
title: Metrics
description: 장애 판단과 성능 분석에 필요한 운영 지표의 기준
---

# Metrics

## 한 줄 정의

Metrics는 시간에 따라 변하는 시스템 상태를 숫자로 수집해 장애 여부, 영향 범위, 추세를 판단하게 해주는 신호다.

## 실무에서 왜 문제 되는가

- 로그만으로는 전체 사용자 영향과 증가 추세를 빠르게 알기 어렵다.
- 평균값만 보면 p95/p99 지연이나 일부 인스턴스 장애가 가려진다.
- 지표 label을 과도하게 늘리면 저장 비용과 조회 비용이 커진다.
- 비즈니스 지표가 없으면 기술 지표가 정상이어도 사용자 문제를 놓칠 수 있다.
- 지표 정의가 애매하면 알림 기준도 애매해진다.

## 동작 원리

1. 애플리케이션과 인프라에서 카운터, 게이지, 히스토그램을 수집한다.
2. endpoint, status, dependency 같은 낮은 cardinality label을 붙인다.
3. 일정 주기로 수집 저장소에 적재한다.
4. 대시보드와 알림에서 시간 범위별로 집계한다.
5. 장애 분석 시 latency, traffic, error, saturation을 함께 본다.

## 실무 판단 기준

| 지표 | 보는 이유 | 예시 |
|---|---|---|
| Latency | 사용자 체감 지연 | p50, p95, p99 |
| Traffic | 요청량 변화 | RPS, QPS |
| Error | 실패 영향 | 5xx rate, timeout rate |
| Saturation | 자원 한계 | CPU, memory, pool active, queue depth |
| Business | 실제 업무 영향 | 주문 실패율, 결제 승인율 |

## 자주 나는 실수

- 평균 latency만 보고 tail latency를 놓친다.
- user id, order id 같은 high cardinality label을 붙인다.
- counter와 gauge의 의미를 혼동한다.
- 애플리케이션 지표만 보고 DB, Redis, 외부 API 지표를 보지 않는다.
- 지표 수집 주기와 알림 평가 주기를 고려하지 않는다.

## 확인 방법

- 테스트: 부하를 걸어 latency, error, saturation이 기대대로 변하는지 확인한다.
- 로그: 지표 이상 시간대의 request id와 error log를 대조한다.
- 메트릭: RED 또는 USE 기준으로 대시보드를 구성한다.
- 트레이스: 지표가 나빠진 dependency 구간을 trace로 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 장애 여부와 영향 범위를 빠르게 판단한다 | 구체적인 실패 원인은 로그가 필요하다 |
| 추세와 용량 한계를 볼 수 있다 | label 설계가 잘못되면 비용이 커진다 |
| 알림과 SLO의 기반이 된다 | 샘플링과 집계 방식에 따라 해석이 달라진다 |

## 짧은 예제

```text
API 기본 지표:
- http_server_requests_seconds p50/p95/p99
- http_requests_total by endpoint, status
- db_pool_active, db_pool_pending
- external_api_timeout_total
```

메트릭은 "무슨 일이 얼마나 자주, 얼마나 크게 발생했는가"를 답해야 한다.

## 핵심 요약

메트릭은 시스템 상태를 숫자로 보여주는 운영 신호다.

장애 판단에는 latency, traffic, error, saturation을 함께 본다.

p95/p99를 보지 않으면 일부 사용자의 심각한 지연이 평균에 가려질 수 있다.

label cardinality가 높으면 비용과 조회 성능 문제가 생긴다.

메트릭은 영향 범위 판단에 강하고, 구체적인 원인은 로그와 트레이스로 좁힌다.

## 꼬리 질문

- RED 지표와 USE 지표는 각각 무엇을 보는가?
- p95/p99 latency가 중요한 이유는 무엇인가?
- metric label cardinality가 높으면 왜 문제가 되는가?

## 관련 문서

- [[observability]]
- [[logging]]
- [[alert-and-slo]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
