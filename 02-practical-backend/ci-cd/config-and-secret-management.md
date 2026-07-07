---
title: Config와 Secret 관리
description: 배포 환경별 설정과 민감 정보를 안전하게 분리하는 기준
---

# Config와 Secret 관리

## 한 줄 정의

Config와 Secret 관리는 코드와 이미지에서 환경별 설정과 민감 정보를 분리하고, 배포 시점에 안전하게 주입하는 방식이다.

## 실무에서 왜 문제 되는가

- 설정이 이미지에 들어가면 환경별 배포와 rollback이 어렵다.
- secret이 Git, log, image layer에 남으면 유출 위험이 커진다.
- 설정 변경과 코드 변경이 섞이면 장애 원인을 분리하기 어렵다.
- 환경별 값 차이가 문서화되지 않으면 재현이 어렵다.
- Kubernetes의 ConfigMap/Secret은 주입 수단이고, 이 문서는 배포 이력, 권한, 회전, rollback 기준을 다룬다.

## 실무 판단 기준

| 값 | 관리 방식 |
|---|---|
| endpoint, feature flag | Config |
| password, token, key | Secret |
| 환경별 profile | 배포 설정 |
| 민감 값 회전 | Secret manager 또는 rotation 절차 |

## 자주 나는 실수

- secret을 환경 변수로 넣은 뒤 전체 env를 로그로 출력한다.
- 설정 파일을 이미지에 포함해 환경마다 이미지를 따로 만든다.
- secret 변경 후 어떤 Pod가 새 값을 쓰는지 확인하지 않는다.
- GitOps 저장소에 민감 값을 평문으로 둔다.

## 확인 방법

- Git과 image layer에 secret이 없는지 확인한다.
- 배포된 Pod가 의도한 설정 값을 쓰는지 확인한다.
- secret 접근 권한과 rotation 절차를 확인한다.

## 핵심 요약

설정과 secret은 코드와 이미지에서 분리해야 한다.

민감 정보는 Git, 로그, 이미지 layer에 남기지 않는다.

설정 변경은 배포와 rollback 절차에 포함되어야 한다.

Secret은 접근 권한과 rotation 기준이 필요하다.

Kubernetes에서는 ConfigMap과 Secret을 주입 수단으로 쓰되, 배포 이력과 접근 권한은 CI/CD 관점에서 함께 관리해야 한다.

## 꼬리 질문

- Config와 Secret은 어떤 기준으로 나누는가?
- Secret이 이미지 layer에 남으면 왜 위험한가?
- 설정 변경 장애는 어떻게 원인을 좁힐 것인가?

## 관련 문서

- [[ci-cd]]
- [[02-practical-backend/kubernetes/configmap-and-secret|configmap-and-secret]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
