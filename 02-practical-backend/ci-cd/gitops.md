---
title: GitOps
description: Git을 선언적 운영 상태의 단일 변경 경로로 사용하는 방식
---

# GitOps

## 한 줄 정의

GitOps는 Git 저장소에 선언된 desired state를 기준으로 배포 환경을 동기화하고 변경 이력을 추적하는 운영 방식이다.

## 실무에서 왜 문제 되는가

- 수동 변경이 많으면 현재 운영 상태와 코드 저장소 상태가 달라진다.
- 누가 언제 어떤 설정을 바꿨는지 추적하기 어렵다.
- 긴급 수정이 Git을 우회하면 다음 배포에서 덮어써질 수 있다.
- secret 관리와 승인 흐름을 함께 설계하지 않으면 위험하다.

## 실무 판단 기준

| 항목 | 기준 |
|---|---|
| 변경 이력 | Git commit과 review로 남긴다 |
| 동기화 | controller가 desired state와 실제 상태를 맞춘다 |
| 수동 변경 | 원칙적으로 금지하거나 Git에 반영한다 |
| Secret | 평문 저장을 피하고 별도 도구를 사용한다 |

## 자주 나는 실수

- GitOps를 단순 YAML 저장소로만 생각한다.
- 운영에서 직접 수정한 뒤 Git에 반영하지 않는다.
- 자동 동기화 범위를 이해하지 못해 의도치 않게 rollback된다.
- secret을 평문으로 commit한다.

## 확인 방법

- 운영 리소스 변경 경로가 Git으로 통일되어 있는지 확인한다.
- drift가 발생했을 때 감지하고 복구하는지 확인한다.
- 승인, 리뷰, rollback 절차가 Git history와 연결되는지 확인한다.

## 핵심 요약

GitOps는 Git을 운영 desired state의 기준으로 삼는다.

변경 이력과 리뷰를 Git workflow로 남길 수 있다.

실제 클러스터 상태와 Git 상태의 drift를 감지하고 동기화한다.

수동 변경은 다음 동기화에서 사라질 수 있으므로 원칙을 정해야 한다.

Secret 관리는 GitOps에서 별도 설계가 필요한 핵심 지점이다.

## 꼬리 질문

- GitOps의 장점은 무엇인가?
- 운영에서 수동 변경하면 어떤 문제가 생기는가?
- GitOps에서 secret은 어떻게 관리할 것인가?

## 관련 문서

- [[ci-cd]]
- [[config-and-secret-management]]
- [[deployment-strategy]]
