---
title: 대시보드
description: 장애 판단과 원인 분석에 바로 사용할 수 있는 대시보드 설계
tags: [concept, observability]
---

# 대시보드

Dashboard는 서비스 상태, 사용자 영향, 원인 후보를 빨리 판단할 수 있게 핵심 지표를 한 화면에 모은 운영 도구다.

대시보드는 그래프 모음이 아니라 장애 대응 흐름이어야 한다. 그래프가 많아도 보는 순서가 없으면 장애 상황에서 시간만 쓴다. 서비스마다 기준이 다르면 서로 비교하기도 어렵다.

## 만드는 순서

1. 서비스의 핵심 사용자 흐름과 SLI를 정한다.
2. 첫 화면에 traffic, latency, error, saturation을 둔다.
3. endpoint, instance, dependency별로 파고드는 화면을 준비한다.
4. 배포 시점, 설정 변경, 장애 이벤트를 지표 위에 같이 표시한다.
5. 장애 회고 후 필요한 그래프는 더하고 안 쓰는 그래프는 뺀다.

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
| 서비스 개요 | RPS, p95/p99, error rate | 장애 여부를 빠르게 본다 |
| 의존성 | DB/Redis/API latency, timeout | 원인 후보를 나눈다 |
| 자원 | CPU, memory, pool, queue | 포화 상태를 본다 |
| 배포 | release marker, instance version | 최근 변경과 연결한다 |
| 비즈니스 | 주문 실패율, 결제 승인율 | 사용자 영향을 확인한다 |

잘 만든 대시보드는 팀의 분석 순서를 표준화한다. 그래도 모든 원인을 한 화면에서 설명하지는 못하고, 서비스가 바뀌면 같이 손봐야 한다.

## 자주 깨지는 곳

- **그래프만 많고 질문별 배치가 없다.** 무엇부터 봐야 할지 몰라 시간을 쓴다.
- **평균 latency만 보여 준다.** tail latency와 일부 인스턴스 문제가 숨는다.
- **endpoint별 breakdown 없이 전체 API 지표만 본다.** 특정 API 하나의 장애가 전체 평균에 묻힌다.
- **배포 marker가 없다.** 최근 변경과 지표 변화를 연결하지 못해 원인 후보가 줄지 않는다.
- **알림에서 연결되는 대시보드가 분석에 부족하다.** 알림을 받고 다시 여기저기 찾아다닌다.

## 운영에서 볼 것

- 장애 상황을 가정하고 5분 안에 영향 범위와 원인 후보를 찾을 수 있는지 시험한다.
- 대시보드에서 trace id나 로그 검색으로 바로 넘어갈 수 있는지 확인한다.
- p95/p99, error rate, dependency, saturation이 한 화면에 같이 보이는지 확인한다.
- 안 쓰는 패널과 중복 그래프는 정기적으로 지운다.

## 면접에서 말하기

> 대시보드는 장애 판단과 원인 분석을 빠르게 하려고 만드는 운영 화면입니다. 저는 첫 화면을 traffic, latency, error, saturation으로 구성하고, 평균보다 p95/p99와 endpoint별 breakdown을 둡니다. 배포 marker와 의존성 지표를 같이 띄워 원인 후보를 줄이고, 알림에서 바로 이 화면으로 들어와 다음 행동을 정할 수 있게 연결합니다.

## 꼬리 질문

- 장애 대시보드 첫 화면에는 어떤 지표가 있어야 하나?
- 대시보드에 배포 marker가 필요한 이유는?
- 평균 latency만 있는 대시보드는 무엇을 놓치나?

## 관련 문서

- [[observability]]
- [[metrics]]
- [[alert-and-slo]]
- [[incident-analysis-flow]]
