---
title: Config와 Secret 관리
description: 배포 환경별 설정과 민감 정보를 안전하게 분리하는 기준
---

# Config와 Secret 관리

환경별 설정과 민감 정보는 코드와 이미지에서 빼내고, 배포할 때 안전하게 넣어 준다.

설정이 이미지에 들어가면 환경별 배포와 rollback이 어려워지고, secret이 Git, log, image layer에 남으면 유출된다. Kubernetes의 ConfigMap/Secret은 값을 넣는 수단일 뿐이다. 이 문서는 그 바깥, 즉 배포 이력, 권한, 회전, rollback 기준을 다룬다.

## 값별 관리 방식

| 값 | 관리 방식 |
|---|---|
| endpoint, feature flag | Config |
| password, token, key | Secret |
| 환경별 profile | 배포 설정 |
| 민감 값 회전 | Secret manager 또는 rotation 절차 |

설정 변경도 배포와 rollback 절차에 넣는다. 설정 변경과 코드 변경이 섞이면 장애가 났을 때 어느 쪽이 원인인지 가르기 어렵다. 환경별 값 차이를 기록해 두지 않으면 재현도 어렵다.

## 자주 깨지는 곳

- **secret을 환경 변수로 넣고 전체 env를 로그로 찍는다.** secret이 로그에 그대로 남는다.
- **설정 파일을 이미지에 넣는다.** 환경마다 이미지를 따로 만들게 된다.
- **secret을 바꾼 뒤 어떤 Pod가 새 값을 쓰는지 확인하지 않는다.** 옛 값과 새 값이 섞여 돈다.
- **GitOps 저장소에 민감 값을 평문으로 둔다.** 저장소 접근 권한이 곧 secret 접근 권한이 된다.

## 운영에서 볼 것

- Git과 image layer에 secret이 없는지 확인한다.
- 배포된 Pod가 의도한 설정 값을 쓰는지 확인한다.
- secret 접근 권한과 rotation 절차를 확인한다.

## 면접에서 말하기

> 설정과 secret은 코드와 이미지에서 분리하고 배포 시점에 주입합니다. 민감 정보는 Git, 로그, 이미지 layer에 남기지 않고, secret에는 접근 권한과 rotation 기준을 둡니다. Kubernetes에서는 ConfigMap과 Secret을 주입 수단으로 쓰되, 설정 변경도 배포 이력과 rollback 절차에 넣어 CI/CD 관점에서 같이 관리합니다.

## 꼬리 질문

- Config와 Secret은 어떤 기준으로 나누나?
- Secret이 이미지 layer에 남으면 왜 위험한가?
- 설정 변경으로 생긴 장애는 어떻게 원인을 좁히나?

## 관련 문서

- [[ci-cd]]
- [[02-practical-backend/kubernetes/configmap-and-secret|configmap-and-secret]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
