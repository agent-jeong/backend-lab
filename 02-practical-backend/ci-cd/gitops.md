---
title: GitOps
description: 운영 환경을 바꾸는 길을 Git 하나로 모으는 방식
tags: [concept, ci-cd]
---

# GitOps

GitOps는 Git 저장소에 적어 둔 원하는 상태(desired state)에 맞춰 배포 환경을 맞추고, 변경 이력을 Git으로 남기는 운영 방식이다.

GitOps가 지키려는 원칙은 "운영 환경을 바꾸는 길은 Git 하나"다. 누군가 서버나 클러스터를 손으로 직접 고치는 일이 잦아지면 실제 운영 상태와 저장소 내용이 달라지고, 누가 언제 무엇을 바꿨는지 알 수 없게 된다.

## 기준

| 항목 | 기준 |
|---|---|
| 변경 이력 | Git commit과 review로 남긴다 |
| 동기화 | controller가 desired state와 실제 상태를 맞춘다 |
| 수동 변경 | 원칙적으로 금지하거나 Git에 반영한다 |
| Secret | 평문 저장을 피하고 별도 도구를 사용한다 |

controller는 클러스터 상태가 Git과 달라진 것(drift)을 감지한다. 자동 동기화와 drift 자동 복구(Argo CD의 `selfHeal`)를 켜 두면 Git을 거치지 않고 손으로 바꾼 내용이 다음 동기화 때 되돌아간다. 이 기능은 기본으로 꺼져 있을 수 있으니 설정부터 확인한다. Secret은 GitOps에서 따로 설계해야 하는 부분이다. 승인 흐름과 함께 설계하지 않으면 위험하다.

## 자주 깨지는 곳

- GitOps를 YAML을 모아 둔 저장소 정도로 생각하면, 동기화와 drift 복구가 빠진 채 이름만 GitOps가 된다.
- 운영에서 직접 고치고 Git에 반영하지 않으면, 긴급 수정이 다음 배포에서 덮어써진다.
- 자동 동기화가 어디까지 적용되는지 모르면, 의도하지 않은 rollback이 일어난다.
- secret을 평문으로 commit하면, 저장소 이력에 영원히 남는다.

## 운영에서 볼 것

- 운영 리소스를 바꾸는 경로가 Git 하나로 모여 있는지 확인한다.
- drift가 생겼을 때 감지하고 되돌리는지 확인한다.
- 승인, 리뷰, rollback 절차가 Git history와 이어지는지 확인한다.

## 한 번에 설명하기

> GitOps는 Git에 적어 둔 원하는 상태를 운영 환경의 기준으로 삼고, controller가 실제 상태를 거기에 맞추는 방식입니다. 변경 이력과 리뷰가 Git에 남고, 누가 손으로 바꾼 부분도 감지합니다. 자동 복구를 켜 두면 그 부분을 Git 상태로 되돌립니다.
>
> 그래서 저는 자동 복구가 켜져 있는지 먼저 확인하고, 손으로 바꾼 내용은 다음 동기화 때 사라진다는 전제로 운영 규칙을 정하고, secret은 평문으로 두지 않고 별도 도구로 관리합니다.

## 꼬리 질문

- GitOps의 장점은?
- 운영에서 수동 변경하면 어떤 문제가 생기나?
- GitOps에서 secret은 어떻게 관리하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OpenGitOps Principles](https://opengitops.dev/)
- [Argo CD Documentation](https://argo-cd.readthedocs.io/en/stable/)
- [Argo CD: Automated Sync Policy](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)

## 관련 문서

- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[config-and-secret-management]]
- [[deployment-strategy]]
