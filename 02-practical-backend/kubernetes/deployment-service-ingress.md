---
title: Deployment, Service, Ingress
description: Kubernetes에서 백엔드 애플리케이션을 띄우고 외부 요청이 Pod까지 가는 경로
tags: [concept, kubernetes]
---

# Deployment, Service, Ingress

Deployment는 Pod를 몇 개 띄울지와 어떤 버전으로 띄울지를 관리한다. Service는 여러 Pod 앞에 바뀌지 않는 내부 주소를 하나 주고, Ingress는 외부 HTTP 요청을 알맞은 Service로 보낸다.

Pod는 언제든 사라지고 새로 생기기 때문에 Pod IP를 직접 부르지 않고 Service를 앞에 둔다. 주문 API가 갑자기 응답하지 않으면 코드보다 이 경로를 먼저 의심한다. 요청이 Ingress, Service, Pod 중 어디에서 멈췄는지에 따라 볼 곳이 다르다.

```text
외부 요청
  → Ingress   host·path 규칙으로 어느 Service인지 고른다
  → Service   고정 주소. 준비된(ready) Pod 중 하나로 보낸다
  → Pod 여러 개
      ↑ Deployment가 Pod 개수와 버전을 관리한다
```

## 동작

1. Deployment에 원하는 replica 수와 Pod template을 적는다.
2. Deployment는 ReplicaSet(같은 Pod를 정해진 개수만큼 유지하는 리소스)을 만들고, ReplicaSet이 그 수만큼 Pod를 유지한다. 버전이 바뀔 때마다 ReplicaSet이 하나씩 새로 생긴다.
3. Service는 selector(어떤 label을 단 Pod를 고를지 적은 조건)에 맞는 Pod를 찾아 endpoint(요청을 실제로 받을 Pod 주소 목록)로 묶는다. 그리고 바뀌지 않는 DNS 이름과 가상 IP를 준다.
4. Ingress Controller(클러스터에 따로 설치하는 프록시. Ingress 규칙을 읽어 실제로 요청을 나눠 준다)가 외부 HTTP 요청의 host와 path를 보고 Service로 보낸다.
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
    - port: 80          # Service가 받는 포트
      targetPort: 8080  # Pod 안 container가 실제로 듣는 포트
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-service
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /orders
            pathType: Prefix
            backend:
              service:
                name: example-service
                port:
                  number: 80
```

세 리소스는 이름표로 이어진다. Service의 `selector`(`app: example-service`)가 Pod의 `labels`와 같아야 endpoint가 생기고, Ingress의 `backend.service`가 Service 이름과 포트를 가리켜야 요청이 Service까지 간다.

Deployment는 Pod 개수 유지와 버전 교체를 맡을 뿐, 잘못 잡은 probe나 resource 값까지 고쳐 주지는 않는다. Ingress는 규칙만 적는 리소스라서, 실제 동작(타임아웃, 헤더 처리 등)은 클러스터에 설치된 Ingress Controller 종류와 설정에 따라 다르다.

## 증상별로 어디를 보나

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| API가 503 응답 | Service endpoint, readiness | 요청을 받을 준비된 Pod가 하나도 없으면 대부분의 Ingress Controller가 503을 돌려준다 |
| Pod는 Running인데 요청 실패 | Service selector, `targetPort` | label이나 포트가 어긋나면 정상 Pod가 있어도 요청이 닿지 않는다 |
| 배포 중에만 잠깐 실패 | replica 수, rolling update 설정, readiness | 준비 안 된 새 Pod로 요청이 갔거나, 옛 Pod를 너무 빨리 내렸다 |
| 특정 경로만 404 | Ingress host, path 규칙 | 규칙에 안 맞는 요청은 애플리케이션까지 오지 않는다 |
| 새 버전이 반영 안 됨 | rollout 상태, Pod image | 새 ReplicaSet이 만들어졌는지, Pod가 새 image로 떴는지 본다 |

## 자주 깨지는 곳

- Pod가 `Running`이면 요청을 받을 준비가 됐다고 생각하면, 아직 뜨는 중인 Pod로 요청이 들어간다. 준비 여부는 readiness probe가 판단하고, readiness probe가 없으면 이 판단 자체가 없다([[readiness-and-liveness-probe]]).
- Service의 `port`와 Pod의 `targetPort`를 헷갈리면, 정상 Pod가 있어도 트래픽이 닿지 않는다.
- Deployment label과 Service selector가 다르면, endpoint가 비어 트래픽이 어디로도 가지 않는다.
- readiness probe 없이 롤링 배포가 안전하다고 보면, 배포 중 가용 Pod가 모자란다. 롤링 배포가 안전한지는 replica 수, readiness probe, update strategy가 함께 정하고, 하나라도 빠지면 틈이 생긴다.
- Ingress 문제를 애플리케이션 로그에서 찾으면 아무것도 안 나온다. host나 path가 틀리면 요청이 애플리케이션까지 오지도 않는다.

## 운영에서 볼 것

- `kubectl get pods`, `kubectl describe pod`, `kubectl logs`로 Pod 상태와 이벤트를 본다.
- `kubectl get endpointslices -l kubernetes.io/service-name=example-service`로 Service가 실제 Pod를 가리키는지 확인한다. 예전 명령인 `kubectl get endpoints`는 Endpoints API가 v1.33부터 지원 중단(deprecated)되어 EndpointSlice로 보는 쪽이 맞다.
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
- [Kubernetes: EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[pod-and-container]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/observability/observability|observability]]
- [[01-core/network/network|network]]
