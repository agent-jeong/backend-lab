---
title: GitOps
description: Git을 선언적 운영 상태의 단일 변경 경로로 사용하는 방식
---

# GitOps

GitOps는 Git 저장소에 선언한 desired state를 기준으로 배포 환경을 맞추고, 변경 이력을 Git으로 추적하는 운영 방식이다.

GitOps가 지키려는 것은 "운영 상태를 바꾸는 길은 Git 하나"라는 원칙이다. 수동 변경이 많으면 운영 상태와 저장소 상태가 달라지고, 누가 언제 무엇을 바꿨는지 추적할 수 없다.

## 기준

| 항목 | 기준 |
|---|---|
| 변경 이력 | Git commit과 review로 남긴다 |
| 동기화 | controller가 desired state와 실제 상태를 맞춘다 |
| 수동 변경 | 원칙적으로 금지하거나 Git에 반영한다 |
| Secret | 평문 저장을 피하고 별도 도구를 사용한다 |

controller는 클러스터 상태와 Git 상태가 어긋나는 drift를 감지해 다시 맞춘다. 그래서 Git을 거치지 않은 수동 변경은 다음 동기화 때 사라진다. Secret은 GitOps에서 따로 설계해야 하는 지점이다. 승인 흐름과 같이 설계하지 않으면 위험하다.

## 자주 깨지는 곳

- **GitOps를 YAML 저장소 정도로 생각한다.** 동기화와 drift 복구가 빠지면 이름만 GitOps다.
- **운영에서 직접 고치고 Git에 반영하지 않는다.** 긴급 수정이 다음 배포에서 덮어써진다.
- **자동 동기화 범위를 모른다.** 의도치 않게 rollback된다.
- **secret을 평문으로 commit한다.** 저장소 이력에 영원히 남는다.

## 운영에서 볼 것

- 운영 리소스를 바꾸는 경로가 Git 하나로 모여 있는지 확인한다.
- drift가 생겼을 때 감지하고 복구하는지 확인한다.
- 승인, 리뷰, rollback 절차가 Git history와 이어지는지 확인한다.

## 면접에서 말하기

> GitOps는 Git을 운영 desired state의 기준으로 삼고, controller가 실제 상태를 거기에 맞추는 방식입니다. 변경 이력과 리뷰가 Git workflow에 남고, drift도 감지해 되돌립니다. 그래서 저는 수동 변경은 다음 동기화에서 사라진다는 전제로 원칙을 정하고, secret은 평문으로 두지 않도록 별도 도구로 관리합니다.

## 꼬리 질문

- GitOps의 장점은?
- 운영에서 수동 변경하면 어떤 문제가 생기나?
- GitOps에서 secret은 어떻게 관리하나?

## 관련 문서

- [[ci-cd]]
- [[config-and-secret-management]]
- [[deployment-strategy]]
