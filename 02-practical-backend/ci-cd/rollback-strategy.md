---
title: Rollback 전략
description: 배포 실패를 빠르게 되돌리기 위한 조건과 한계
tags: [concept, ci-cd]
---

# Rollback 전략

Rollback 전략은 배포 후 문제가 생겼을 때 이전에 검증된 버전과 설정으로 되돌리는 절차와 조건이다.

rollback은 배포 도구의 버튼 하나가 아니다. 되돌릴 대상은 코드뿐 아니라 설정, DB, 외부 연동 상태까지다. 애플리케이션만 되돌려도 DB schema나 메시지 포맷은 그대로 남는다. 기준을 미리 정해 두지 않으면 장애 중에 결정이 늦어진다.

## 미리 확인할 것

| 항목 | 확인 |
|---|---|
| Artifact | 이전 배포 artifact를 재사용할 수 있는가 |
| Config | 이전 설정으로 되돌릴 수 있는가 |
| DB | schema가 양방향 호환되는가 |
| Trigger | 오류율, latency, 핵심 기능 실패 기준이 있는가 |
| 권한 | 누가 rollback을 실행할 수 있는가 |

설정 변경과 코드 변경이 한 배포에 섞이면 원인 분리도, 복구도 어려워진다.

## 자주 깨지는 곳

- **rollback을 버튼 하나로 생각한다.** 설정, DB, 외부 연동이 되돌아가지 않는다.
- **DB migration을 되돌릴 수 있다고 가정한다.** schema 변경은 rollback을 어렵게 만든다. 하위 호환 설계가 필요하다.
- **이전 버전 artifact를 새로 빌드해서 배포한다.** 검증된 그 artifact가 아니다. 이미 검증된 것을 재사용한다.
- **이전 artifact를 추적하지 못한다.** 어느 버전으로 돌아갈지 모른다.
- **rollback 후 지표를 안 본다.** 되돌린 뒤에 정말 복구됐는지 모른다.

## 운영에서 볼 것

- 최근 성공한 artifact와 설정을 추적할 수 있는지 확인한다.
- rollback rehearsal이나 staging 검증을 해 둔다.
- DB 변경이 expand/contract 방식으로 호환되는지 확인한다.

## 면접에서 말하기

> Rollback은 이전 버전으로 빠르게 돌아가기 위한 운영 절차이고, 대상은 코드뿐 아니라 설정, DB, 외부 연동 상태까지입니다. 저는 이전 artifact를 새로 빌드하지 않고 이미 검증된 것을 재사용하고, DB schema 변경은 expand/contract로 하위 호환되게 합니다. rollback 기준은 오류율, latency, 핵심 기능 실패처럼 배포 전에 정해 둡니다.

## 꼬리 질문

- Rollback이 불가능하거나 어려운 배포는 어떤 경우인가?
- 이전 artifact를 새로 빌드하면 왜 위험한가?
- rollback 판단 기준은 어떻게 정하나?

## 관련 문서

- [[ci-cd]]
- [[deployment-strategy]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
