---
title: Readiness Probe와 Liveness Probe
description: 트래픽을 받아도 되는 상태와 재시작해야 하는 상태를 나누는 법
tags: [concept, kubernetes]
---

# Readiness Probe와 Liveness Probe

Readiness probe는 Pod가 지금 요청을 받아도 되는지 묻는다. Liveness probe는 container가 재시작해야 할 만큼 망가졌는지 묻는다.

둘은 실패했을 때 일어나는 일이 다르다. readiness가 실패하면 그 Pod로 트래픽이 안 갈 뿐이지만, liveness가 실패하면 container가 재시작된다. 그래서 DB나 외부 결제 API 상태를 liveness에서 확인하면, DB가 잠깐 느려졌을 뿐인데 모든 Pod가 한꺼번에 재시작되는 재시작 폭풍이 난다.

## 동작

1. kubelet이 주기적으로 probe를 실행한다.
2. readiness가 실패하면 Service endpoint에서 Pod를 뺀다.
3. readiness가 다시 성공하면 트래픽 대상에 넣는다.
4. liveness가 반복해서 실패하면 kubelet이 container를 재시작한다.
5. startup probe가 있으면, 그게 성공할 때까지 liveness와 readiness probe가 모두 꺼져 있다. 뜨는 데 오래 걸리는 애플리케이션이 초기화 도중 liveness 실패로 재시작되지 않게 하려고 쓴다.

```yaml
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

트래픽을 받아도 되는지와 재시작이 필요한지는 다른 질문이라 endpoint도 나눈다. 하나의 endpoint로 묶으면 트래픽을 끊는 기준과 재시작하는 기준이 섞인다.

## 상태별로 어떤 probe를 쓰나

| 상태 | Probe | 기준 |
|---|---|---|
| 요청 받을 준비 안 됨 | Readiness 실패 | endpoint에서 제외한다 |
| 복구 불가능한 hang | Liveness 실패 | container 재시작을 유도한다 |
| 구동 시간이 긴 앱 | Startup probe | 초기화 중 liveness 실패를 막는다 |
| 외부 API 장애 | Readiness에 신중히 반영 | 전체 트래픽이 차단될 위험을 본다 |
| DB 연결 일시 지연 | 서비스 특성별 판단 | 재시작이 해결책인지 확인한다 |

startup probe는 초기화 시간만 다룬다. 실제로 트래픽을 받아도 되는지는 readiness 기준을 따로 둬야 한다.

## 자주 깨지는 곳

- readiness와 liveness를 같은 뜻으로 쓰다가 readiness를 빼먹으면, 초기화가 끝나기 전 Pod로 요청이 들어간다.
- liveness에서 DB, Redis, 외부 API까지 확인하면, 의존성 하나의 장애가 전체 Pod의 재시작 폭풍으로 번진다.
- timeout과 failureThreshold를 너무 낮게 잡으면, 잠깐 느려진 것만으로 container가 계속 재시작된다.
- readiness 기준을 너무 까다롭게 잡으면, 멀쩡한 Pod까지 트래픽에서 빠진다.
- 뜨는 데 오래 걸리는 앱에 startup probe 없이 liveness를 바로 걸면, 다 뜨기도 전에 재시작된다.
- 배포 중 readiness 실패 원인을 애플리케이션 로그에서만 찾으면 못 찾는다. probe 실패는 event에 남는다.

## 운영에서 볼 것

- `kubectl describe pod`로 probe 실패 event를 본다.
- `kubectl get endpoints`로 readiness가 실패한 Pod가 Service에서 빠지는지 확인한다.
- 배포 중 초기화가 끝나기 전에 요청이 들어가지 않는지 테스트한다.
- 메트릭으로는 restart count, readiness failure, liveness failure를 본다.

## 한 번에 설명하기

> Readiness는 트래픽을 받아도 되는지, Liveness는 재시작이 필요한지를 판단합니다. readiness가 실패하면 endpoint에서 빠지고 liveness가 실패하면 재시작되기 때문에, 저는 외부 의존성 상태를 liveness에 넣지 않습니다.
>
> 뜨는 데 오래 걸리는 애플리케이션에는 startup probe를 두어, 그게 성공할 때까지 다른 probe가 돌지 않게 합니다.
>
> probe를 어떻게 잡느냐에 따라 배포가 얼마나 안전한지, 장애가 났을 때 어떻게 복구되는지가 정해진다고 봅니다.

## 꼬리 질문

- Readiness와 Liveness는 어떻게 다른가?
- DB 장애를 liveness 실패로 처리하면 어떤 문제가 생기나?
- 배포 중 503이 나면 probe와 Service에서 무엇을 확인하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Spring Boot: Kubernetes Probes](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)

## 관련 문서

- [[kubernetes]]
- [[deployment-service-ingress]]
- [[02-practical-backend/observability/metrics|metrics]]
