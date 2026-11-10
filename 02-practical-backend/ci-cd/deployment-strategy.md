---
title: 배포 전략
description: 서비스 중단과 변경 위험을 줄이는 배포 전략 선택 기준
tags: [concept, ci-cd]
---

# 배포 전략

Deployment Strategy는 새 버전을 사용자에게 어떤 순서로, 어느 범위까지 내보낼지 정하는 배포 방식이다.

전략을 고르는 기준은 두 가지다. 결함이 생겼을 때 몇 명이 영향을 받는가, 그리고 얼마나 빨리 되돌릴 수 있는가. 한 번에 전체 트래픽을 새 버전으로 보내면 결함 영향도 전체로 간다.

## 전략별 비교

| 전략 | 적합한 상황 | 한계 |
|---|---|---|
| Rolling | 일반적인 무중단 배포 | 오류가 일부 트래픽에 노출될 수 있다 |
| Blue-Green | 빠른 전환/복구 필요 | 인프라 비용이 더 든다 |
| Canary | 영향 범위를 작게 시작 | 지표와 라우팅 제어가 필요하다 |
| Recreate | 중단 허용 가능 | 서비스 공백이 생긴다 |

Rolling은 가장 흔하지만 readiness와 replica가 받쳐 줘야 무중단이 된다. DB schema 변경이 들어가면 어떤 전략을 쓰든 하위 호환 설계가 따로 필요하다. 애플리케이션 버전만 되돌려서는 복구되지 않을 수 있다.

## 자주 깨지는 곳

- **전략 이름만 정하고 검증 지표는 안 정한다.** 배포 전략과 모니터링이 이어지지 않으면 잘못된 버전이 오래 남는다.
- **readiness 없이 rolling update가 안전하다고 생각한다.** 무중단을 기대해도 장애가 난다.
- **DB migration과 애플리케이션 배포 순서를 생각하지 않는다.** 새 버전과 옛 버전이 같이 떠 있는 동안 한쪽이 깨진다.
- **canary 비율만 낮추고 사용자 영향 지표를 안 본다.** 작은 범위에서 결함을 잡으려고 canary를 쓰는데, 지표를 안 보면 잡을 방법이 없다.

## 운영에서 볼 것

- 배포 중 error rate, latency, saturation을 본다.
- 새 버전과 이전 버전이 동시에 떠 있어도 DB schema가 호환되는지 확인한다.
- rollback이나 traffic shift 절차를 미리 검증한다.

## 면접에서 말하기

> 배포 전략은 새 버전을 얼마나 넓게 노출하고 어떻게 되돌릴지 정하는 것입니다. Rolling은 일반적이지만 readiness와 replica가 받쳐 줘야 하고, Canary는 영향 범위를 줄이는 대신 지표로 판단해야 하며, Blue-Green은 전환이 빠른 대신 비용이 듭니다. 저는 어떤 전략이든 DB 변경은 하위 호환되게 따로 설계하고, 배포 중 지표를 보고 진행 여부를 정합니다.

## 꼬리 질문

- Rolling과 Blue-Green은 무엇이 다른가?
- Canary 배포에서 어떤 지표를 보나?
- DB 변경이 있는 배포는 왜 더 조심해야 하나?

## 관련 문서

- [[ci-cd]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
- [[rollback-strategy]]
