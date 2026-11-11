---
title: 대시보드
description: 장애가 났을 때 열자마자 영향과 원인 후보가 보이는 대시보드를 만드는 방법
tags: [concept, observability]
---

# 대시보드

Dashboard는 서비스가 지금 괜찮은지, 사용자가 피해를 보는지, 원인이 어디쯤인지 빨리 알 수 있게 꼭 필요한 지표만 한 화면에 모은 운영 화면이다.

대시보드는 그래프를 모아 둔 곳이 아니라, 장애가 났을 때 위에서 아래로 따라 내려가며 보는 순서여야 한다. 그래프가 많아도 보는 순서가 없으면 장애 중에 이것저것 열어 보느라 시간만 간다. 서비스마다 구성이 다르면 서로 비교하기도 어렵다.

## 만드는 순서

1. 주문, 결제처럼 가장 중요한 사용자 흐름과 SLI를 정한다.
2. 첫 화면에 traffic, latency, error, saturation을 둔다.
3. endpoint, instance, dependency별로 파고드는 화면을 준비한다.
4. 배포 시점, 설정 변경, 장애 이벤트를 지표 위에 같이 표시한다.
5. 장애 회고가 끝나면 필요했던 그래프는 더하고 안 쓴 그래프는 뺀다.

```text
첫 화면 순서:
1. 사용자 영향: error rate, p95/p99 latency
2. 트래픽: RPS, endpoint별 요청량
3. 의존성: DB, Redis, 외부 API latency
4. 포화: thread pool, connection pool, queue depth
5. 변경: deploy marker
```

## 화면별로 넣을 지표

| 화면 | 포함할 지표 | 이유 |
|---|---|---|
| 서비스 개요 | RPS, p95/p99, error rate | 장애인지 빠르게 본다 |
| 의존성 | DB/Redis/API latency, timeout | 원인 후보를 나눈다 |
| 자원 | CPU, memory, pool, queue | 꽉 찬 자원이 있는지 본다 |
| 배포 | release marker, instance version | 최근 변경과 맞춰 본다 |
| 비즈니스 | 주문 실패율, 결제 승인율 | 사용자가 피해를 보는지 본다 |

잘 만든 대시보드가 있으면 팀 누구든 같은 순서로 장애를 본다. 그래도 모든 원인을 한 화면에서 설명하지는 못하고, 서비스가 바뀌면 대시보드도 같이 손봐야 한다.

## 자주 깨지는 곳

- 그래프만 많고 질문 순서대로 놓여 있지 않으면, 무엇부터 봐야 할지 몰라 시간을 쓴다.
- 평균 latency만 보여 주면, tail latency와 인스턴스 몇 대의 문제가 숨는다.
- endpoint별로 쪼개 보지 않고 전체 API 지표만 보면, API 하나의 장애가 전체 평균에 묻힌다.
- 배포 marker가 없으면, 최근 변경과 지표 변화를 맞춰 보지 못해 원인 후보가 줄지 않는다.
- 알림에서 열리는 대시보드로 분석이 안 되면, 알림을 받고 다시 여기저기 찾아다닌다.

## 운영에서 볼 것

- 장애 상황을 가정하고 5분 안에 영향 범위와 원인 후보를 찾을 수 있는지 시험한다.
- 대시보드에서 trace id나 로그 검색으로 바로 넘어갈 수 있는지 확인한다.
- p95/p99, error rate, dependency, saturation이 한 화면에 같이 보이는지 확인한다.
- 안 쓰는 패널과 중복 그래프는 정기적으로 지운다.

## 한 번에 설명하기

> 대시보드는 장애인지 빨리 판단하고 원인 후보를 좁히려고 만드는 화면입니다.
>
> 첫 화면은 traffic, latency, error, saturation으로 채우고, 평균 대신 p95/p99와 endpoint별 지표를 둡니다. 배포 marker와 의존성 지표도 같이 띄워서 원인 후보를 줄입니다.
>
> 알림을 누르면 바로 이 화면이 열려서, 다음에 무엇을 할지 정할 수 있게 해 둡니다.

## 꼬리 질문

- 장애 대시보드 첫 화면에는 어떤 지표가 있어야 하나?
- 대시보드에 배포 marker가 필요한 이유는?
- 평균 latency만 있는 대시보드는 무엇을 놓치나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Grafana: Dashboard best practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

## 관련 문서

- [[02-practical-backend/observability/observability|observability]]
- [[metrics]]
- [[alert-and-slo]]
- [[incident-analysis-flow]]
