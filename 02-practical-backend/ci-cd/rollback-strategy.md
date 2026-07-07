---
title: Rollback 전략
description: 배포 실패를 빠르게 되돌리기 위한 조건과 한계
---

# Rollback 전략

## 한 줄 정의

Rollback 전략은 배포 후 문제가 생겼을 때 이전에 검증된 버전과 설정으로 되돌리는 절차와 조건이다.

## 실무에서 왜 문제 되는가

- rollback 기준이 없으면 장애 중 의사결정이 늦어진다.
- 애플리케이션만 되돌려도 DB schema나 메시지 포맷은 되돌아가지 않을 수 있다.
- 설정 변경과 코드 변경이 섞이면 원인 분리와 복구가 어렵다.
- 이전 artifact를 추적하지 못하면 어떤 버전으로 돌아갈지 모른다.

## 실무 판단 기준

| 항목 | 확인 |
|---|---|
| Artifact | 이전 배포 artifact를 재사용할 수 있는가 |
| Config | 이전 설정으로 되돌릴 수 있는가 |
| DB | schema가 양방향 호환되는가 |
| Trigger | 오류율, latency, 핵심 기능 실패 기준이 있는가 |
| 권한 | 누가 rollback을 실행할 수 있는가 |

## 자주 나는 실수

- rollback을 배포 도구 버튼 하나로만 생각한다.
- DB migration을 되돌릴 수 있다고 가정한다.
- 이전 버전 artifact를 새로 빌드해서 배포한다.
- rollback 후 검증 지표를 보지 않는다.

## 확인 방법

- 최근 성공 artifact와 설정을 추적할 수 있는지 확인한다.
- rollback rehearsal 또는 staging 검증을 수행한다.
- DB 변경이 expand/contract 방식으로 호환되는지 확인한다.

## 핵심 요약

Rollback은 이전 버전으로 빠르게 돌아가기 위한 운영 절차다.

되돌릴 대상은 코드뿐 아니라 설정, DB, 외부 연동 상태까지 포함된다.

이전 artifact는 새로 빌드하지 않고 이미 검증된 것을 재사용하는 편이 안전하다.

DB schema 변경은 rollback을 어렵게 만들 수 있어 하위 호환 설계가 필요하다.

rollback 기준은 오류율, latency, 핵심 기능 실패처럼 사전에 정해야 한다.

## 꼬리 질문

- Rollback이 불가능하거나 어려운 배포는 어떤 경우인가?
- 이전 artifact를 새로 빌드하면 왜 위험한가?
- rollback 판단 기준은 어떻게 정할 것인가?

## 관련 문서

- [[ci-cd]]
- [[deployment-strategy]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
