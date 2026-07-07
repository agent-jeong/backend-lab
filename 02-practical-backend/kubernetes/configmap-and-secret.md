---
title: ConfigMap과 Secret
description: 컨테이너 이미지와 환경별 설정, 민감 정보를 분리하는 기준
---

# ConfigMap과 Secret

## 한 줄 정의

ConfigMap은 일반 설정을, Secret은 민감 정보를 Pod에 주입하기 위한 Kubernetes 리소스다.

## 실무에서 왜 문제 되는가

- 설정을 이미지에 넣으면 환경별 배포와 롤백이 어려워진다.
- 민감 정보를 ConfigMap이나 Git에 평문으로 두면 공개 저장소와 배포 로그를 통해 노출될 수 있다.
- Secret은 기본적으로 인코딩일 뿐 암호화가 아니므로 접근 권한과 저장소 암호화가 필요하다.
- 설정 변경이 Pod에 자동 반영되는지, 재시작이 필요한지 이해하지 못하면 장애 대응이 늦어진다.

## 동작 원리

1. 환경별 설정을 ConfigMap이나 Secret으로 분리한다.
2. Pod는 환경 변수나 volume mount 방식으로 값을 주입받는다.
3. 애플리케이션은 시작 시점 또는 파일 변경 시점에 설정을 읽는다.
4. 설정이 바뀌어도 애플리케이션이 자동 reload하지 않으면 Pod 재시작이 필요하다.
5. Secret은 RBAC, 암호화, 외부 secret manager와 함께 관리한다.

## 실무 판단 기준

| 값 | 리소스 | 이유 |
|---|---|---|
| feature flag, endpoint | ConfigMap | 민감하지 않은 환경 설정이다 |
| DB password, API key | Secret | 접근 제어가 필요한 값이다 |
| 대량 설정 파일 | Volume mount | 파일 형태 관리가 쉽다 |
| 자주 바뀌는 설정 | reload 전략 검토 | Pod 재시작 여부를 결정해야 한다 |
| Git 저장 | 암호화 또는 외부 관리 | 민감 정보 평문 저장을 피한다 |

## 자주 나는 실수

- Secret을 암호화된 값이라고 오해한다.
- ConfigMap에 API key를 넣는다.
- 설정 변경 후 Pod가 자동으로 새 값을 읽는다고 생각한다.
- 환경 변수 전체를 로그로 출력한다.
- Secret 조회 권한을 너무 넓게 부여한다.

## 확인 방법

- 명령: `kubectl describe pod`로 어떤 ConfigMap/Secret이 주입되는지 확인한다.
- 명령: `kubectl get secret` 접근 권한이 필요한 주체로 제한되는지 확인한다.
- 테스트: 설정 변경 후 애플리케이션이 재시작 없이 반영하는지 확인한다.
- 리뷰: 민감 정보가 Git, 로그, 이미지 layer에 남지 않는지 확인한다.

## 장점과 한계

| 리소스 | 장점 | 한계 |
|---|---|---|
| ConfigMap | 이미지와 설정을 분리한다 | 민감 정보 저장에 부적합하다 |
| Secret | 민감 정보 접근을 별도 리소스로 관리한다 | 기본값만으로 강한 보안을 제공하지 않는다 |
| Volume mount | 파일 기반 설정에 적합하다 | reload 동작은 애플리케이션마다 다르다 |

## 짧은 예제

```yaml
env:
  - name: APP_PROFILE
    valueFrom:
      configMapKeyRef:
        name: example-config
        key: profile
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: example-secret
        key: db-password
```

설정과 민감 정보는 이미지에 bake하지 않고 배포 환경에서 주입한다. 배포 파이프라인에서 이 값을 어떻게 추적하고 되돌릴지는 [[config-and-secret-management]]에서 다룬다.

## 핵심 요약

ConfigMap은 일반 설정, Secret은 민감 정보를 Pod에 주입하는 리소스다.

Secret은 기본적으로 인코딩된 값이므로 접근 제어와 저장소 암호화를 함께 고려해야 한다.

설정 변경이 애플리케이션에 자동 반영되는지는 주입 방식과 애플리케이션 동작에 따라 다르다.

민감 정보는 Git, 로그, 이미지 layer에 남기지 않아야 한다.

환경별 설정 분리는 재배포와 롤백을 단순하게 만들지만, 배포 이력과 접근 권한 관리는 별도로 설계해야 한다.

## 꼬리 질문

- ConfigMap과 Secret은 어떤 기준으로 나누는가?
- Secret을 안전하게 관리하려면 무엇을 추가로 고려해야 하는가?
- 설정 변경 후 Pod 재시작이 필요한지 어떻게 판단할 것인가?

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
- [[02-practical-backend/ci-cd/config-and-secret-management|config-and-secret-management]]
