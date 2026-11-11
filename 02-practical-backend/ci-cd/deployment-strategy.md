---
title: 배포 전략
description: 새 버전을 얼마나 넓게 내보내고 어떻게 되돌릴지에 따라 배포 방식을 고르는 법
tags: [concept, ci-cd]
---

# 배포 전략

배포 전략(deployment strategy)은 새 버전을 사용자에게 어떤 순서로, 어디까지 내보낼지 정하는 방식이다.

고를 때 따지는 건 두 가지다. 새 버전에 결함이 있으면 몇 명이 영향을 받는가, 그리고 얼마나 빨리 되돌릴 수 있는가. 결제 API 새 버전을 한 번에 전체 트래픽으로 보내면, 결함이 있을 때 모든 결제가 같이 실패한다.

## 전략별 비교

| 전략 | 적합한 상황 | 한계 |
|---|---|---|
| Rolling | 일반적인 무중단 배포 | 오류가 일부 트래픽에 노출될 수 있다 |
| Blue-Green | 빠른 전환/복구 필요 | 인프라 비용이 더 든다 |
| Canary | 영향 범위를 작게 시작 | 지표와 라우팅 제어가 필요하다 |
| Recreate | 중단 허용 가능 | 서비스 공백이 생긴다 |

Rolling이 가장 흔하지만 readiness와 replica가 받쳐 줘야 무중단이 된다. DB schema 변경이 들어가면 어떤 전략을 쓰든 하위 호환 설계를 따로 해야 한다. 애플리케이션 버전만 되돌려서는 복구되지 않을 수 있다.

## 자주 깨지는 곳

- 전략 이름만 정하고 무엇을 보고 판단할지 정하지 않으면, 배포와 모니터링이 따로 놀아 잘못된 버전이 오래 남는다.
- readiness 없이 rolling update가 안전하다고 생각하면, 무중단을 기대했는데 장애가 난다.
- DB migration과 애플리케이션 배포 순서를 생각하지 않으면, 새 버전과 옛 버전이 같이 떠 있는 동안 한쪽이 깨진다.
- canary 비율만 낮추고 사용자 영향 지표를 보지 않으면, 결함을 잡을 수 없다. 작은 범위에서 결함을 먼저 잡으려고 canary를 쓰는 것이다.

## 운영에서 볼 것

- 배포 중 error rate, latency, saturation을 본다.
- 새 버전과 이전 버전이 동시에 떠 있어도 DB schema가 양쪽과 맞는지 확인한다.
- rollback이나 traffic shift 절차를 미리 돌려 본다.

## 한 번에 설명하기

> 배포 전략은 새 버전을 얼마나 넓게 내보내고 어떻게 되돌릴지 정하는 것입니다.
>
> Rolling은 흔히 쓰지만 readiness와 replica가 받쳐 줘야 하고, Canary는 영향 범위를 줄이는 대신 지표를 보고 판단해야 하며, Blue-Green은 전환이 빠른 대신 비용이 듭니다.
>
> 저는 어떤 전략을 쓰든 DB 변경은 하위 호환되게 따로 설계하고, 배포 중 지표를 보고 계속 진행할지 정합니다.

## 꼬리 질문

- Rolling과 Blue-Green은 무엇이 다른가?
- Canary 배포에서 어떤 지표를 보나?
- DB 변경이 있는 배포는 왜 더 조심해야 하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Martin Fowler: Blue Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)

## 관련 문서

- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
- [[rollback-strategy]]
