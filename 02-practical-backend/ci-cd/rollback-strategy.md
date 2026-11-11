---
title: Rollback 전략
description: 잘못된 배포를 빨리 되돌리려면 미리 갖춰야 할 것과, 되돌려지지 않는 것
tags: [concept, ci-cd]
---

# Rollback 전략

Rollback 전략은 배포 뒤 문제가 생겼을 때 이전에 검증된 버전과 설정으로 되돌리는 절차와, 언제 되돌릴지에 대한 조건이다.

rollback은 배포 도구의 버튼 하나로 끝나지 않는다. 되돌려야 하는 건 코드만이 아니라 설정, DB, 외부 연동 상태까지다. 애플리케이션을 이전 버전으로 돌려도 이미 바꾼 DB schema나 메시지 포맷은 그대로 남는다. 언제 되돌릴지 미리 정해 두지 않으면 장애가 난 와중에 결정이 늦어진다.

## 미리 확인할 것

| 항목 | 확인 |
|---|---|
| Artifact | 이전 배포 artifact를 재사용할 수 있는가 |
| Config | 이전 설정으로 되돌릴 수 있는가 |
| DB | schema가 양방향 호환되는가 |
| Trigger | 오류율, latency, 핵심 기능 실패 기준이 있는가 |
| 권한 | 누가 rollback을 실행할 수 있는가 |

설정 변경과 코드 변경이 한 배포에 섞이면 원인을 가르기도, 복구하기도 어려워진다.

## 자주 깨지는 곳

- rollback을 버튼 하나로 생각하면, 설정, DB, 외부 연동은 되돌아가지 않은 채 남는다.
- DB migration도 되돌릴 수 있다고 가정하면, 막상 rollback할 때 막힌다. schema 변경은 rollback을 어렵게 만들어서 하위 호환 설계가 필요하다.
- 이전 버전 artifact를 새로 빌드해서 배포하면, 검증했던 바로 그 artifact가 아니게 된다. 이미 검증된 것을 그대로 다시 쓴다.
- 이전 artifact를 추적하지 못하면, 어느 버전으로 돌아가야 할지 모른다.
- rollback 뒤 지표를 보지 않으면, 정말 복구됐는지 모른다.

## 운영에서 볼 것

- 최근에 성공한 artifact와 설정을 찾아낼 수 있는지 확인한다.
- rollback을 미리 연습하거나 staging에서 검증해 둔다.
- DB 변경이 expand/contract 방식으로 이전 버전과도 맞는지 확인한다.

## 한 번에 설명하기

> Rollback은 이전 버전으로 빨리 돌아가기 위한 운영 절차이고, 되돌릴 대상은 코드뿐 아니라 설정, DB, 외부 연동 상태까지입니다.
>
> 저는 이전 artifact를 새로 빌드하지 않고 이미 검증된 것을 그대로 쓰고, DB schema 변경은 expand/contract로 하위 호환되게 합니다.
>
> 언제 rollback할지는 오류율, latency, 핵심 기능 실패처럼 배포 전에 미리 정해 둡니다.

## 꼬리 질문

- Rollback이 불가능하거나 어려운 배포는 어떤 경우인가?
- 이전 artifact를 새로 빌드하면 왜 위험한가?
- rollback 판단 기준은 어떻게 정하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Rolling Back a Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)

## 관련 문서

- [[ci-cd]]
- [[deployment-strategy]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
