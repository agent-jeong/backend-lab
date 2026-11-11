---
title: ConfigMap과 Secret
description: 환경마다 다른 설정과 비밀번호 같은 값을 이미지 밖에 두는 방법
tags: [concept, kubernetes]
---

# ConfigMap과 Secret

ConfigMap은 일반 설정을, Secret은 비밀번호나 API key 같은 민감한 값을 Pod에 넣어 주는 Kubernetes 리소스다.

설정을 이미지에 같이 구워 넣으면 개발, 스테이징, 운영마다 이미지를 따로 만들어야 하고, 롤백할 때도 이미지와 설정이 함께 묶여 돌아간다. 그래서 이미지는 하나로 두고 값만 환경에서 넣어 준다. 다만 Secret은 기본 상태에서 인코딩만 돼 있을 뿐 암호화되지 않는다. 이름만 보고 안전하다고 믿지 말고, 누가 읽을 수 있는지와 저장소 암호화를 따로 챙긴다.

## 동작

1. 환경마다 다른 설정을 ConfigMap이나 Secret으로 뺀다.
2. Pod는 환경 변수나 volume mount로 값을 받는다.
3. 애플리케이션은 시작할 때, 또는 파일이 바뀔 때 설정을 읽는다.
4. 설정을 바꿔도 애플리케이션이 알아서 다시 읽지(reload) 않으면 Pod를 재시작해야 반영된다.
5. Secret은 RBAC, 암호화, 외부 secret manager와 함께 관리한다.

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

배포 파이프라인에서 이 값의 변경 이력을 남기고 되돌리는 방법은 [[config-and-secret-management]]에 있다.

## 값별로 어디에 두나

| 값 | 리소스 | 이유 |
|---|---|---|
| feature flag, endpoint | ConfigMap | 민감하지 않은 환경 설정이다 |
| DB password, API key | Secret | 접근 제어가 필요한 값이다 |
| 대량 설정 파일 | Volume mount | 파일 형태로 관리하기 쉽다. 단 reload 동작은 애플리케이션마다 다르다 |
| 자주 바뀌는 설정 | reload 전략 검토 | Pod 재시작 여부를 정해야 한다 |
| Git 저장 | 암호화 또는 외부 관리 | 민감 정보를 평문으로 두지 않는다 |

## 자주 깨지는 곳

- Secret에 넣었으니 암호화됐다고 믿으면, 기본 설정 그대로 두게 된다. RBAC와 저장소 암호화를 따로 걸어야 실제로 보호된다.
- API key를 ConfigMap에 넣으면, Git이나 배포 로그로 그대로 새어 나간다. ConfigMap은 민감한 값을 담는 곳이 아니다.
- 설정만 바꾸면 Pod가 새 값을 읽는다고 생각하면, 재시작이 필요한 상황에서 옛 값으로 계속 돌고 장애 대응이 늦어진다. 재시작이 필요한지는 주입 방식과 애플리케이션 동작에 달려 있다.
- 환경 변수 전체를 로그로 찍으면, Secret 값이 로그에 남는다.
- Secret 조회 권한을 넓게 주면, 볼 필요 없는 사람과 서비스까지 값을 읽을 수 있다.

## 운영에서 볼 것

- `kubectl describe pod`로 어떤 ConfigMap과 Secret이 들어갔는지 본다.
- `kubectl get secret` 권한이 필요한 주체에게만 있는지 확인한다.
- 설정을 바꾼 뒤 애플리케이션이 재시작 없이 새 값을 쓰는지 미리 테스트해 둔다.
- 민감 정보가 Git, 로그, 이미지 layer에 남지 않았는지 리뷰한다.

## 한 번에 설명하기

> ConfigMap은 일반 설정을, Secret은 민감한 값을 Pod에 넣어 주는 리소스입니다. Secret은 기본적으로 인코딩만 돼 있어서, 저는 RBAC로 조회 권한을 좁히고 저장소 암호화나 외부 secret manager를 같이 씁니다.
>
> 설정을 바꿨을 때 바로 반영되는지는 주입 방식과 애플리케이션에 따라 다릅니다. 그래서 재시작이 필요한지 미리 확인해 두고, 변경 이력과 접근 권한은 따로 관리합니다.

## 꼬리 질문

- ConfigMap과 Secret은 어떤 기준으로 나누나?
- Secret을 안전하게 관리하려면 무엇이 더 필요한가?
- 설정 변경 후 Pod 재시작이 필요한지 어떻게 판단하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes: Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
- [[02-practical-backend/ci-cd/config-and-secret-management|config-and-secret-management]]
