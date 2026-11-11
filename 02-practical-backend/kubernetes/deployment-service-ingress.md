---
title: Deployment, Service, Ingress
description: Kubernetes에서 백엔드 애플리케이션을 띄우고 외부 요청이 Pod까지 가는 경로
tags: [concept, kubernetes]
---

# Deployment, Service, Ingress

Deployment는 Pod를 몇 개 띄울지와 어떤 버전으로 띄울지를 관리한다. Service는 여러 Pod 앞에 바뀌지 않는 내부 주소를 하나 주고, Ingress는 외부 HTTP 요청을 알맞은 Service로 보낸다.

Pod는 언제든 사라지고 새로 생기기 때문에 Pod IP를 직접 부르지 않고 Service를 앞에 둔다. 주문 API가 갑자기 응답하지 않을 때 원인이 애플리케이션 코드가 아니라 Ingress에서 Service를 거쳐 Pod로 가는 이 경로 어딘가에 있는 경우가 많다.

## 동작

1. Deployment에 원하는 replica 수와 Pod template을 적는다.
2. Kubernetes는 ReplicaSet으로 적힌 수만큼 Pod를 유지한다.
3. Service는 selector와 맞는 Pod들을 endpoint로 묶고, 바뀌지 않는 DNS 이름과 가상 IP를 준다.
4. Ingress Controller는 외부 HTTP 요청의 host와 path를 보고 Service로 보낸다.
5. Deployment가 바뀌면 새 Pod를 띄우고, 준비된 Pod로 트래픽을 옮기면서 기존 Pod를 줄인다.

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

Service의 selector와 Deployment Pod의 label이 맞아야 Service endpoint가 생긴다.

각 리소스가 해 주지 않는 일도 있다. Deployment는 replica 유지, rolling update, rollback을 YAML 선언만으로 처리해 주지만, 잘못 잡은 probe나 resource 값까지 고쳐 주지는 않는다. Ingress는 외부 HTTP 라우팅을 한곳에 모아 두지만, 어떤 Controller를 쓰는지와 클러스터 설정에 따라 동작이 다르다.

## 증상별로 어디를 보나

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| API가 503 응답 | Ingress, Service endpoint, readiness | 라우팅 대상 Pod가 준비되지 않았을 가능성이 크다 |
| Pod는 Running인데 요청 실패 | Service selector, port mapping | label 또는 targetPort가 어긋났을 수 있다 |
| 배포 중 순간 장애 | replica, rolling update, readiness | 준비 전 트래픽 유입이나 가용 Pod 부족을 확인한다 |
| 특정 경로만 실패 | Ingress host, path rule | 애플리케이션보다 라우팅 규칙 문제일 수 있다 |
| 새 버전 반영 안 됨 | Deployment rollout 상태 | 새 ReplicaSet 생성과 Pod image를 확인한다 |

## 자주 깨지는 곳

- Pod가 `Running`이면 요청을 받을 준비가 됐다고 생각하면, 아직 뜨는 중인 Pod로 요청이 들어간다. 준비 여부는 readiness가 판단하고, readiness probe가 없으면 이 판단 자체가 없다.
- Service의 `port`와 Pod의 `targetPort`를 헷갈리면, 정상 Pod가 있어도 트래픽이 닿지 않는다.
- Deployment label과 Service selector가 다르면, endpoint가 비어 트래픽이 어디로도 가지 않는다.
- readiness probe 없이 롤링 배포가 안전하다고 보면, 배포 중 가용 Pod가 모자란다. 롤링 배포가 안전한지는 replica 수, readiness probe, update strategy가 함께 정하고, 하나라도 빠지면 틈이 생긴다.
- Ingress 문제를 애플리케이션 로그에서 찾으면 아무것도 안 나온다. host나 path가 틀리면 요청이 애플리케이션까지 오지도 않는다.

## 운영에서 볼 것

- `kubectl get pods`, `kubectl describe pod`, `kubectl logs`로 Pod 상태와 이벤트를 본다.
- `kubectl get endpoints`로 Service가 실제 Pod를 가리키는지 확인한다.
- `kubectl describe ingress`로 host, path, backend Service를 확인한다.
- 배포 중 readiness를 통과한 Pod에만 트래픽이 가는지 테스트한다.
- Ingress Controller 로그와 애플리케이션 access log를 같이 본다.

## 한 번에 설명하기

> Deployment는 Pod 개수와 배포 상태를 유지하고, Service는 계속 바뀌는 Pod 앞에 고정된 주소를 주고, Ingress는 외부 HTTP 요청을 host와 path로 나눠 Service에 보냅니다.
>
> 그래서 API 장애가 나면 저는 애플리케이션 로그만 보지 않고 Ingress, Service endpoint, Pod event를 같이 봅니다. 롤링 배포는 replica 수, readiness probe, update strategy가 함께 맞아야 안전하다고 봅니다.

## 꼬리 질문

- Deployment, Service, Ingress는 각각 어떤 문제를 해결하나?
- Pod가 Running인데 Service로 요청이 가지 않는다면 무엇을 확인하나?
- 롤링 배포 중 순간 장애를 줄이려면 어떤 설정이 필요한가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes: Service](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes: Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/observability/observability|observability]]
- [[01-core/network/network|network]]
