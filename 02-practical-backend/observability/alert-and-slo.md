---
title: Alert와 SLO
description: 사용자가 겪는 문제를 기준으로 알림을 걸고, 쓸데없는 알림을 줄이는 방법
tags: [concept, observability]
---

# Alert와 SLO

Alert는 사용자가 피해를 보고 있거나 곧 볼 것 같을 때 운영자를 부르는 신호다. SLO는 "결제 요청의 99.9%는 성공해야 한다"처럼 서비스가 지키기로 한 신뢰성 목표다.

알림은 "누군가 한번 봐 두면 좋은 정보"가 아니라 "누군가 지금 손을 써야 하는 일"에만 울려야 한다. SLO가 없으면 어떤 지표가 얼마나 나빠져야 장애인지 팀이 합의할 수 없고, 알림 기준도 감으로 정하게 된다.

## 설계 순서

1. 사용자가 실제로 겪는 것을 재는 SLI(Service Level Indicator)를 정한다. 예: 결제 요청 중 성공한 비율, 1초 안에 끝난 비율.
2. 그 SLI가 지켜야 할 목표인 SLO를 정한다. 예: 30일 동안 성공 비율 99.9%.
3. SLO를 어길 것 같은 상황에 알림 조건을 건다.
4. 알림에 영향 범위, 최근 변경, 대시보드, 대응 문서를 넣는다.
5. 장애가 끝나면 알림이 제때 울렸는지, 쓸데없이 울리지 않았는지 보고 조정한다.

```text
알림 조건:
- checkout API 5xx rate > 2% for 5m
- checkout API p95 latency > 1s for 10m
- db_pool_pending > 0 for 3m
```

## 상황별 알림 기준

| 상황 | 알림 기준 | 이유 |
|---|---|---|
| API 장애 | 5xx rate, timeout rate | 사용자 실패와 직접 연결된다 |
| 지연 장애 | p95/p99 latency | 사용자가 느끼는 지연에 가깝다 |
| 자원 고갈 | pool pending, queue depth | 장애가 나기 전에 잡는다 |
| 배치 실패 | 처리 실패율, 지연 시간 | 사용자 API와 기준이 다르다 |
| 외부 API 장애 | dependency error/timeout | 의존성 문제를 따로 떼어 본다 |

CPU나 메모리 같은 자원 지표만으로는 사용자가 피해를 보는지 알기 어렵다. 사용자가 겪는 지표로 알림을 걸면 장애를 더 빨리 알아채고 무엇부터 할지도 정하기 쉽다. 그래도 모든 장애를 미리 잡아 주지는 않는다.

## 자주 깨지는 곳

- WARN 로그마다 알림을 걸면, 알림이 너무 많아서 진짜 장애를 놓친다.
- CPU 80% 같은 임계치 하나만 쓰면, 사용자는 멀쩡한데 알림이 울린다.
- 알림에 무엇을 어떻게 확인할지 적혀 있지 않으면, 알림은 울려도 대응 절차가 없어 복구 시간이 줄지 않는다.
- 업무 시간 알림과 야간 알림의 긴급도를 나누지 않으면, 급하지 않은 일로 밤에 사람을 깨운다.
- 알림이 울린 뒤 실제로 손쓴 일이 있었는지 돌아보지 않으면, 알림이 늦었는지 시끄러웠는지 고칠 기회를 놓친다.

## 운영에서 볼 것

- 장애 시나리오에서 알림이 정해 둔 시간 안에 울리는지 테스트한다.
- 알림 시간대의 error log와 배포 이력을 확인한다.
- 메트릭으로는 SLI, error budget, burn rate를 본다. error budget은 SLO가 허용하는 실패량이다. 99.9%면 30일 요청 중 0.1%까지는 실패해도 된다. burn rate는 그 예산을 평소보다 몇 배 빨리 쓰고 있는지다. burn rate가 높으면 아직 실패율이 낮아 보여도 며칠 안에 SLO를 어기게 되니 알림을 건다.
- 알림에서 바로 원인 후보를 볼 수 있는 대시보드로 이어지는지 확인한다.

## 한 번에 설명하기

> 알림은 사용자가 피해를 보고 있어서 누군가 손을 써야 할 때 울려야 합니다. SLO는 서비스가 어느 수준까지 안정적이어야 하는지 정한 목표입니다.
>
> 그래서 CPU 같은 자원 지표보다 5xx rate나 p95 latency처럼 사용자가 겪는 지표로 알림을 겁니다.
>
> 알림에는 영향 범위, 원인 후보, 확인 링크, 대응 절차를 같이 넣습니다. 장애가 끝나면 알림이 늦지 않았는지, 시끄럽지 않았는지 보고 조정합니다.

## 꼬리 질문

- SLI, SLO, SLA는 어떻게 다른가?
- 좋은 알림과 나쁜 알림의 차이는?
- error budget burn rate는 왜 쓰나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Google SRE Book: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)

## 관련 문서

- [[02-practical-backend/observability/observability|observability]]
- [[metrics]]
- [[dashboard]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
