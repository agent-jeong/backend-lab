---
title: Deployment, Service, Ingress
description: Kubernetes에서 백엔드 애플리케이션을 배포하고 외부 트래픽을 전달하는 기본 경로
---

# Deployment, Service, Ingress

## 한 줄 정의

Deployment는 Pod 복제본과 배포 상태를 관리하고, Service는 Pod 집합에 안정적인 내부 접근점을 제공하며, Ingress는 외부 HTTP 요청을 Service로 라우팅한다.

## 실무에서 왜 문제 되는가

- Pod는 생성되고 사라질 수 있으므로 Pod IP에 직접 의존하면 장애와 재배포에 취약하다.
- Deployment 설정이 잘못되면 배포 중 가용 Pod 수가 부족해질 수 있다.
- Service selector가 Pod label과 맞지 않으면 정상 Pod가 있어도 트래픽이 전달되지 않는다.
- Ingress 경로와 host 설정이 틀리면 애플리케이션 문제가 아닌데도 API가 응답하지 않는다.
- readiness probe가 없으면 준비되지 않은 Pod로 요청이 들어갈 수 있다.

## 동작 원리

1. Deployment는 원하는 replica 수와 Pod template을 선언한다.
2. Kubernetes는 ReplicaSet을 통해 선언된 수만큼 Pod를 유지한다.
3. Service는 selector와 일치하는 Pod들을 endpoint로 묶고 안정적인 DNS 이름과 가상 IP를 제공한다.
4. Ingress Controller는 외부 HTTP 요청의 host와 path를 보고 Service로 라우팅한다.
5. Deployment가 업데이트되면 새 Pod를 띄우고 준비된 Pod로 트래픽을 옮기며 기존 Pod를 줄인다.

## 실무 판단 기준

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| API가 503 응답 | Ingress, Service endpoint, readiness | 라우팅 대상 Pod가 준비되지 않았을 수 있다 |
| Pod는 Running인데 요청 실패 | Service selector, port mapping | label 또는 targetPort 불일치 가능성이 있다 |
| 배포 중 순간 장애 | replica, rolling update, readiness | 준비 전 트래픽 유입이나 가용 Pod 부족을 확인한다 |
| 특정 경로만 실패 | Ingress host, path rule | 애플리케이션보다 라우팅 규칙 문제일 수 있다 |
| 새 버전 반영 안 됨 | Deployment rollout 상태 | 새 ReplicaSet 생성과 Pod image를 확인한다 |

## 자주 나는 실수

- Pod가 `Running`이면 요청을 받을 준비가 끝났다고 생각한다.
- Service의 `port`와 Pod의 `targetPort`를 혼동한다.
- Deployment label과 Service selector를 다르게 설정한다.
- readiness probe 없이 롤링 배포를 안전하다고 판단한다.
- Ingress 문제를 애플리케이션 로그만 보고 찾으려 한다.

## 확인 방법

- 명령: `kubectl get pods`, `kubectl describe pod`, `kubectl logs`로 Pod 상태와 이벤트를 확인한다.
- 명령: `kubectl get endpoints`로 Service가 실제 Pod를 바라보는지 확인한다.
- 명령: `kubectl describe ingress`로 host, path, backend Service를 확인한다.
- 테스트: 배포 중 readiness가 통과한 Pod에만 트래픽이 가는지 확인한다.
- 로그: Ingress Controller 로그와 애플리케이션 access log를 함께 본다.

## 장점과 한계

| 리소스 | 장점 | 한계 |
|---|---|---|
| Deployment | replica 유지, rolling update, rollback을 선언적으로 관리한다 | 잘못된 probe나 resource 설정까지 자동으로 해결하지는 않는다 |
| Service | 변하는 Pod 뒤에 안정적인 접근점을 제공한다 | selector와 port 설정이 틀리면 트래픽이 끊긴다 |
| Ingress | 외부 HTTP 라우팅을 중앙에서 관리한다 | Controller 구현과 클러스터 설정에 따라 동작 차이가 있다 |

## 짧은 예제

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: example-service
  template:
    metadata:
      labels:
        app: example-service
    spec:
      containers:
        - name: app
          image: example-service:1.0.0
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: example-service
spec:
  selector:
    app: example-service
  ports:
    - port: 80
      targetPort: 8080
```

Service의 selector와 Deployment Pod label이 일치해야 Service endpoint가 생성된다. 이 예제는 공개 가능한 일반 이름만 사용한다.

## 핵심 요약

Deployment는 원하는 Pod 복제본과 배포 상태를 유지한다.

Service는 사라지고 다시 생기는 Pod 앞에 안정적인 내부 접근점을 제공한다.

Ingress는 외부 HTTP 요청을 host와 path 기준으로 Service에 전달한다.

Pod가 Running이어도 readiness가 실패하면 트래픽을 받지 않아야 한다.

API 장애를 볼 때는 애플리케이션 로그만 보지 말고 Ingress, Service endpoint, Pod event를 함께 확인한다.

롤링 배포의 안전성은 replica 수, readiness probe, update strategy가 함께 결정한다.

## 꼬리 질문

- Deployment, Service, Ingress는 각각 어떤 문제를 해결하는가?
- Pod가 Running인데 Service로 요청이 가지 않는다면 무엇을 확인할 것인가?
- 롤링 배포 중 순간 장애를 줄이려면 어떤 설정이 필요한가?

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/observability/observability|observability]]
- [[01-core/network/network|network]]
