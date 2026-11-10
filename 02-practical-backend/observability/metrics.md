---
title: 메트릭
description: 장애 판단과 성능 분석에 필요한 운영 지표의 기준
tags: [concept, observability]
---

# 메트릭

Metrics는 시간에 따라 변하는 시스템 상태를 숫자로 모은 신호다. 장애인지, 얼마나 퍼졌는지, 어느 방향으로 가는지를 판단할 때 쓴다.

메트릭은 "무슨 일이 얼마나 자주, 얼마나 크게 일어났나"에 답한다. 로그로는 전체 사용자 영향과 증가 추세를 빨리 알기 어렵고, 메트릭으로는 구체적인 실패 원인을 알 수 없다. 둘은 서로를 대신하지 못한다.

## 동작

1. 애플리케이션과 인프라에서 카운터, 게이지, 히스토그램을 수집한다.
2. endpoint, status, dependency처럼 cardinality가 낮은 label을 붙인다.
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

기술 지표가 다 정상이어도 비즈니스 지표가 없으면 사용자 문제를 놓친다. 메트릭은 알림과 SLO의 바탕이 되고 추세와 용량 한계도 보여 주지만, 샘플링과 집계 방식에 따라 해석이 달라진다.

## 자주 깨지는 곳

- **평균 latency만 본다.** p95/p99 지연이나 일부 인스턴스 장애가 평균에 가려진다.
- **user id, order id 같은 high cardinality label을 붙인다.** 저장 비용과 조회 비용이 크게 는다.
- **counter와 gauge를 헷갈린다.** 누적값을 현재값처럼 읽어 판단이 틀린다.
- **애플리케이션 지표만 본다.** DB, Redis, 외부 API 지표를 안 보면 원인이 의존성에 있을 때 못 찾는다.
- **수집 주기와 알림 평가 주기를 맞추지 않는다.** 정의가 애매한 지표에는 알림 기준도 애매해진다.

## 운영에서 볼 것

- 부하를 걸어 latency, error, saturation이 예상대로 움직이는지 테스트한다.
- 지표가 튄 시간대의 request id와 error log를 대조한다.
- 대시보드는 RED 또는 USE 기준으로 구성한다.
- 지표가 나빠진 dependency 구간은 trace로 확인한다.

## 한 번에 설명하기

> 메트릭은 시스템 상태를 숫자로 보여 주는 운영 신호이고, 저는 장애 판단에 latency, traffic, error, saturation을 같이 봅니다. 평균만 보면 일부 사용자의 큰 지연이 가려져서 p95/p99를 봅니다. label에는 user id 같은 high cardinality 값을 넣지 않고, 영향 범위는 메트릭으로, 구체적인 원인은 로그와 트레이스로 좁힙니다.

## 꼬리 질문

- RED 지표와 USE 지표는 각각 무엇을 보나?
- p95/p99 latency를 보는 이유는?
- metric label cardinality가 높으면 왜 문제인가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Prometheus: Metric types](https://prometheus.io/docs/concepts/metric_types/)
- [Micrometer Documentation](https://docs.micrometer.io/micrometer/reference/)

## 관련 문서

- [[observability]]
- [[logging]]
- [[alert-and-slo]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
