---
title: Dashboard
description: 장애 판단과 원인 분석에 바로 사용할 수 있는 대시보드 설계
---

# Dashboard

## 한 줄 정의

Dashboard는 운영자가 서비스 상태, 사용자 영향, 원인 후보를 빠르게 판단할 수 있도록 핵심 지표를 한 화면에 배치한 도구다.

## 실무에서 왜 문제 되는가

- 보기 좋은 그래프가 많아도 장애 판단에 필요한 순서가 없으면 시간이 낭비된다.
- 서비스별 대시보드 기준이 다르면 장애 상황에서 비교가 어렵다.
- 평균값 위주의 화면은 tail latency와 일부 인스턴스 문제를 숨긴다.
- 배포, 트래픽 변화, 의존성 상태가 없으면 원인 후보를 좁히기 어렵다.

## 동작 원리

1. 서비스의 핵심 사용자 흐름과 SLI를 정한다.
2. 첫 화면에 traffic, latency, error, saturation을 배치한다.
3. endpoint, instance, dependency별 drill-down 화면을 준비한다.
4. 배포 시점, 설정 변경, 장애 이벤트를 지표와 함께 표시한다.
5. 장애 회고 후 필요한 그래프를 추가하고 불필요한 그래프를 제거한다.

## 실무 판단 기준

| 화면 | 포함할 지표 | 이유 |
|---|---|---|
| 서비스 개요 | RPS, p95/p99, error rate | 장애 여부를 빠르게 본다 |
| 의존성 | DB/Redis/API latency, timeout | 원인 후보를 나눈다 |
| 자원 | CPU, memory, pool, queue | 포화 상태를 본다 |
| 배포 | release marker, instance version | 최근 변경과 연결한다 |
| 비즈니스 | 주문 실패율, 결제 승인율 | 사용자 영향을 확인한다 |

## 자주 나는 실수

- 대시보드에 그래프를 많이 넣지만 질문별 배치가 없다.
- 평균 latency만 보여준다.
- endpoint별 breakdown 없이 전체 API 지표만 본다.
- 배포 marker가 없어 최근 변경과 지표 변화를 연결하지 못한다.
- 알림에서 연결되는 대시보드가 원인 분석에 충분하지 않다.

## 확인 방법

- 테스트: 장애 상황에서 5분 안에 영향 범위와 원인 후보를 찾을 수 있는지 확인한다.
- 로그: 대시보드에서 trace id나 로그 검색으로 이동할 수 있는지 확인한다.
- 메트릭: p95/p99, error rate, dependency, saturation이 함께 보이는지 확인한다.
- 운영 점검: 사용하지 않는 패널과 중복 그래프를 제거한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 장애 판단 속도를 높인다 | 잘못 구성하면 지표만 많아진다 |
| 팀의 분석 순서를 표준화한다 | 모든 원인을 한 화면에서 설명하지는 못한다 |
| 알림과 장애 대응을 연결한다 | 서비스 변화에 맞춰 계속 관리해야 한다 |

## 짧은 예제

```text
첫 화면 순서:
1. 사용자 영향: error rate, p95/p99 latency
2. 트래픽: RPS, endpoint별 요청량
3. 의존성: DB, Redis, 외부 API latency
4. 포화: thread pool, connection pool, queue depth
5. 변경: deploy marker
```

대시보드는 그래프 모음이 아니라 장애 대응 흐름이어야 한다.

## 핵심 요약

Dashboard는 장애 판단과 원인 분석을 빠르게 하기 위한 운영 화면이다.

첫 화면은 traffic, latency, error, saturation을 중심으로 구성한다.

평균값보다 p95/p99와 endpoint별 breakdown이 중요하다.

배포 시점과 의존성 지표를 함께 봐야 원인 후보를 줄일 수 있다.

좋은 대시보드는 알림에서 바로 연결되고 대응자가 다음 행동을 결정하게 해준다.

## 꼬리 질문

- 장애 대시보드 첫 화면에는 어떤 지표가 있어야 하는가?
- 대시보드에 배포 marker가 필요한 이유는 무엇인가?
- 평균 latency만 있는 대시보드의 한계는 무엇인가?

## 관련 문서

- [[observability]]
- [[metrics]]
- [[alert-and-slo]]
- [[incident-analysis-flow]]
