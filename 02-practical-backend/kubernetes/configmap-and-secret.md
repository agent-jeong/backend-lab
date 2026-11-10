---
title: ConfigMap과 Secret
description: 컨테이너 이미지와 환경별 설정, 민감 정보를 분리하는 기준
tags: [concept, kubernetes]
---

# ConfigMap과 Secret

ConfigMap은 일반 설정을, Secret은 민감 정보를 Pod에 넣어 주는 Kubernetes 리소스다.

설정을 이미지에 넣어 버리면 환경별 배포와 롤백이 어려워진다. 그래서 이미지는 하나로 두고 값만 환경에서 주입한다. 다만 Secret은 기본적으로 인코딩일 뿐 암호화가 아니다. 이름만 믿지 말고 접근 권한과 저장소 암호화를 따로 챙긴다.

## 동작

1. 환경별 설정을 ConfigMap이나 Secret으로 뺀다.
2. Pod는 환경 변수나 volume mount로 값을 받는다.
3. 애플리케이션은 시작할 때, 또는 파일이 바뀔 때 설정을 읽는다.
4. 설정이 바뀌어도 애플리케이션이 자동 reload하지 않으면 Pod를 재시작해야 반영된다.
5. Secret은 RBAC, 암호화, 외부 secret manager와 같이 관리한다.

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

배포 파이프라인에서 이 값을 어떻게 추적하고 되돌릴지는 [[config-and-secret-management]]에서 다룬다.

## 값별로 어디에 두나

| 값 | 리소스 | 이유 |
|---|---|---|
| feature flag, endpoint | ConfigMap | 민감하지 않은 환경 설정이다 |
| DB password, API key | Secret | 접근 제어가 필요한 값이다 |
| 대량 설정 파일 | Volume mount | 파일 형태로 관리하기 쉽다. 단 reload 동작은 애플리케이션마다 다르다 |
| 자주 바뀌는 설정 | reload 전략 검토 | Pod 재시작 여부를 정해야 한다 |
| Git 저장 | 암호화 또는 외부 관리 | 민감 정보를 평문으로 두지 않는다 |

## 자주 깨지는 곳

- **Secret을 암호화된 값이라고 믿는다.** 기본값만으로는 강한 보안이 안 된다. RBAC와 저장소 암호화가 따로 필요하다.
- **ConfigMap에 API key를 넣는다.** ConfigMap은 민감 정보용이 아니다. Git이나 배포 로그로 그대로 새어 나간다.
- **설정을 바꾸면 Pod가 알아서 새 값을 읽는다고 생각한다.** 주입 방식과 애플리케이션 동작에 따라 재시작이 필요하다. 이걸 모르면 장애 대응이 늦어진다.
- **환경 변수 전체를 로그로 찍는다.** Secret 값이 로그에 남는다.
- **Secret 조회 권한을 넓게 준다.** 필요한 주체만 볼 수 있어야 한다.

## 운영에서 볼 것

- `kubectl describe pod`로 어떤 ConfigMap/Secret이 주입됐는지 본다.
- `kubectl get secret` 권한이 필요한 주체로만 제한돼 있는지 확인한다.
- 설정을 바꾼 뒤 애플리케이션이 재시작 없이 반영하는지 테스트해 둔다.
- 민감 정보가 Git, 로그, 이미지 layer에 남지 않았는지 리뷰한다.

## 면접에서 말하기

> ConfigMap은 일반 설정, Secret은 민감 정보를 Pod에 주입하는 리소스입니다. Secret은 기본적으로 인코딩일 뿐이라, 저는 RBAC로 조회 권한을 좁히고 저장소 암호화나 외부 secret manager를 같이 씁니다. 설정을 바꿨을 때 자동 반영되는지는 주입 방식과 애플리케이션에 달려 있어서 재시작이 필요한지 미리 확인해 두고, 배포 이력과 접근 권한은 별도로 관리합니다.

## 꼬리 질문

- ConfigMap과 Secret은 어떤 기준으로 나누나?
- Secret을 안전하게 관리하려면 무엇이 더 필요한가?
- 설정 변경 후 Pod 재시작이 필요한지 어떻게 판단하나?

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
- [[02-practical-backend/ci-cd/config-and-secret-management|config-and-secret-management]]
