---
title: Config와 Secret 관리
description: 환경마다 다른 설정과 민감한 값을 코드 밖에 두고 배포 때 넣어 주는 법
tags: [concept, ci-cd]
---

# Config와 Secret 관리

환경마다 다른 설정과 비밀번호 같은 민감한 값은 코드와 이미지 밖에 두고, 배포할 때 넣어 준다.

설정이 이미지에 들어가 있으면 환경마다 이미지를 따로 만들어야 하고 rollback도 번거로워진다. secret이 Git, 로그, image layer에 남으면 그대로 유출된다. Kubernetes의 ConfigMap과 Secret은 값을 Pod에 넣어 주는 수단일 뿐이다. 이 문서는 그 바깥, 즉 변경 이력, 권한, 주기적 교체(rotation), rollback을 다룬다.

## 값별 관리 방식

| 값 | 관리 방식 |
|---|---|
| endpoint, feature flag | Config |
| password, token, key | Secret |
| 환경별 profile | 배포 설정 |
| 민감 값 회전 | Secret manager 또는 rotation 절차 |

설정 변경도 배포와 rollback 절차에 넣는다. 설정 변경과 코드 변경이 한 번에 나가면, 장애가 났을 때 어느 쪽이 원인인지 가르기 어렵다. 환경마다 값이 어떻게 다른지 기록해 두지 않으면 문제를 재현하기도 어렵다.

## 자주 깨지는 곳

- secret을 환경 변수로 넣고 env 전체를 로그로 찍으면, secret이 로그에 그대로 남는다.
- 설정 파일을 이미지에 넣으면, 환경마다 이미지를 따로 만들게 된다.
- secret을 바꾼 뒤 어떤 Pod가 새 값을 쓰는지 확인하지 않으면, 옛 값과 새 값을 쓰는 Pod가 섞여 돈다.
- GitOps 저장소에 민감한 값을 평문으로 두면, 저장소를 읽을 수 있는 사람은 누구나 secret도 읽을 수 있다.

## 운영에서 볼 것

- Git과 image layer에 secret이 없는지 확인한다.
- 배포된 Pod가 의도한 설정 값을 쓰는지 확인한다.
- secret 접근 권한과 rotation 절차를 확인한다.

## 한 번에 설명하기

> 설정과 secret은 코드와 이미지에서 떼어 내고 배포할 때 넣어 줍니다. 민감한 값은 Git, 로그, 이미지 layer에 남기지 않고, secret마다 누가 읽을 수 있는지와 언제 교체할지를 정해 둡니다.
>
> Kubernetes에서는 ConfigMap과 Secret으로 값을 넣되, 설정 변경도 배포 이력과 rollback 절차에 포함해서 CI/CD 안에서 같이 관리합니다.

## 꼬리 질문

- Config와 Secret은 어떤 기준으로 나누나?
- Secret이 이미지 layer에 남으면 왜 위험한가?
- 설정 변경으로 생긴 장애는 어떻게 원인을 좁히나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [The Twelve-Factor App: Config](https://12factor.net/config)
- [Kubernetes: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## 관련 문서

- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/kubernetes/configmap-and-secret|configmap-and-secret]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
