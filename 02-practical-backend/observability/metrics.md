---
title: 메트릭
description: 장애인지 판단하고 성능을 볼 때 어떤 숫자를 모으고 어떻게 읽는지
tags: [concept, observability]
---

# 메트릭

Metrics는 시간에 따라 바뀌는 시스템 상태를 숫자로 모은 것이다. 지금 장애인지, 얼마나 퍼졌는지, 나아지는지 나빠지는지를 볼 때 쓴다.

메트릭은 "무슨 일이 얼마나 자주, 얼마나 크게 일어났나"에 답한다. 주문 실패가 전체 사용자 중 얼마나 되는지, 늘고 있는지는 로그로 빨리 알기 어렵다. 반대로 메트릭으로는 왜 실패했는지 알 수 없다. 그래서 둘은 서로를 대신하지 못한다.

## 수집에서 알림까지

1. 애플리케이션과 인프라에서 카운터(계속 늘기만 하는 누적값, 예: 요청 수), 게이지(오르내리는 현재값, 예: 사용 중인 커넥션 수), 히스토그램(값의 분포, 예: 응답 시간)을 수집한다.
2. endpoint, status, dependency처럼 cardinality(label 값의 가짓수)가 낮은 label을 붙인다.
3. 정해진 주기로 수집 저장소에 쌓는다.
4. 대시보드와 알림에서 시간 범위별로 집계한다.
5. 장애 분석 때 latency, traffic, error, saturation을 같이 본다.

```text
API 기본 지표:
- http_server_requests_seconds p50/p95/p99
- http_requests_total by endpoint, status
- db_pool_active, db_pool_pending
- external_api_timeout_total
```

## 무엇을 보나

| 지표 | 보는 이유 | 예시 |
|---|---|---|
| Latency | 사용자 체감 지연 | p50, p95, p99 |
| Traffic | 요청량 변화 | RPS, QPS |
| Error | 실패 영향 | 5xx rate, timeout rate |
| Saturation | 자원 한계 | CPU, memory, pool active, queue depth |
| Business | 실제 업무 영향 | 주문 실패율, 결제 승인율 |

기술 지표가 다 정상이어도 주문 실패율 같은 비즈니스 지표가 없으면 사용자가 겪는 문제를 놓친다. 알림과 SLO도 메트릭으로 만들고, 추세와 용량 한계도 메트릭에서 읽는다. 다만 샘플링과 집계 방식에 따라 같은 숫자도 다르게 읽힌다.

## 자주 깨지는 곳

- 평균 latency만 보면, p95/p99 지연이나 인스턴스 한 대의 장애가 평균에 가려진다.
- user id, order id처럼 값 종류가 많은(high cardinality) label을 붙이면, 저장 비용과 조회 비용이 크게 는다.
- counter와 gauge를 헷갈리면, 누적값을 현재값처럼 읽어 판단이 틀린다.
- 애플리케이션 지표만 보고 DB, Redis, 외부 API 지표를 안 보면, 원인이 의존성에 있을 때 못 찾는다.
- 수집 주기와 알림 평가 주기를 맞추지 않으면, 지표 정의가 흐려지고 알림 기준도 같이 흐려진다.

## 운영에서 볼 것

- 부하를 걸어 latency, error, saturation이 예상대로 움직이는지 테스트한다.
- 지표가 튄 시간대의 request id와 error log를 대조한다.
- 대시보드는 RED 또는 USE 기준으로 구성한다. RED는 요청 기준으로 Rate(초당 요청 수), Errors(실패 수), Duration(걸린 시간)을 본다. USE는 자원 기준으로 Utilization(사용률), Saturation(대기열이 쌓인 정도), Errors를 본다.
- 지표가 나빠진 dependency 구간은 trace로 확인한다.

## 한 번에 설명하기

> 메트릭은 시스템 상태를 숫자로 보여 줍니다. 장애인지 판단할 때는 latency, traffic, error, saturation을 같이 봅니다.
>
> 평균만 보면 일부 사용자가 겪는 큰 지연이 가려지기 때문에 p95/p99를 봅니다. label에는 user id처럼 값 종류가 많은 것을 넣지 않습니다.
>
> 얼마나 퍼졌는지는 메트릭으로 보고, 왜 그랬는지는 로그와 트레이스로 좁힙니다.

## 꼬리 질문

- RED 지표와 USE 지표는 각각 무엇을 보나?
- p95/p99 latency를 보는 이유는?
- metric label cardinality가 높으면 왜 문제인가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Prometheus: Metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Micrometer Documentation](https://docs.micrometer.io/micrometer/reference/)

## 관련 문서

- [[02-practical-backend/observability/observability|observability]]
- [[logging]]
- [[alert-and-slo]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
