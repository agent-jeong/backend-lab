---
title: Kubernetes 로그와 메트릭 확인
description: Pod, Deployment, Service 문제를 로그와 메트릭으로 좁혀 가는 순서
tags: [concept, kubernetes]
---

# Kubernetes 로그와 메트릭 확인

Kubernetes에서 장애를 볼 때는 Pod 로그, event, 자원 사용량, rollout 상태를 함께 본다. 애플리케이션이 잘못된 건지, 클러스터 쪽 자원이나 설정이 잘못된 건지를 가르려는 것이다.

애플리케이션 로그에는 Service selector가 어긋났다거나, readiness가 실패했다거나, OOMKilled로 죽었다는 사실이 찍히지 않는다. CPU throttling이나 memory limit 초과도 겉으로는 그냥 응답이 느리거나 오류가 나는 것처럼 보인다. 여러 곳을 같이 봐야 문제가 애플리케이션, 네트워크, 스케줄링, 자원 중 어디에 있는지 좁혀진다.

## 보는 순서

1. 배포가 끝났는지 본다: `kubectl rollout status deployment/example-service`
2. Pod 상태와 재시작 횟수를 본다: `kubectl get pods`
3. 이벤트와 종료 사유를 본다: `kubectl describe pod <pod>`. image pull 실패, 스케줄링 실패, probe 실패, `OOMKilled`가 여기 남는다.
4. 로그를 본다: `kubectl logs <pod>`, 재시작했다면 `kubectl logs <pod> --previous`
5. Service가 Pod를 가리키는지 본다: `kubectl get endpointslices -l kubernetes.io/service-name=example-service`
6. CPU, memory, throttling 지표를 응답 시간·오류율 같은 애플리케이션 지표와 같은 시간축에 놓고 본다.

| 증상 | 확인 |
|---|---|
| 503 증가 | readiness, EndpointSlice, Ingress |
| 재시작 반복 | logs --previous, OOMKilled, liveness |
| 지연 증가 | CPU throttling, memory, DB/외부 API |
| Pod Pending | request, node resource, scheduling event |
| 새 버전 반영 안 됨 | rollout status, image tag, ReplicaSet |

## 자주 깨지는 곳

- `kubectl logs`만 보고 event를 보지 않으면, image pull 실패나 스케줄링 실패, probe 실패 같은 원인을 늦게 찾는다.
- 재시작된 Pod의 이전 로그를 보지 않으면, 재시작 원인을 놓친다. 원인은 지금 떠 있는 container가 아니라 죽은 container의 로그에 있다.
- Pod가 Running이면 서비스도 정상이라고 보면, readiness 실패로 트래픽을 못 받는 Pod를 놓친다.
- 자원 지표 없이 코드만 의심하면, throttling이나 OOMKilled를 코드 버그로 착각한다.

## 운영에서 볼 것

- `kubectl describe pod`로 event와 종료 사유를 본다.
- `kubectl logs --previous`로 재시작 전 로그를 본다.
- `kubectl get events --sort-by=.lastTimestamp`로 namespace 전체의 최근 이벤트를 시간순으로 본다.
- 메트릭으로는 restart count, readiness failure, CPU throttling, memory usage를 본다.

event는 클러스터에 오래 남지 않는다(기본 1시간). 지난 장애를 보려면 event와 메트릭을 따로 수집해 보관해 둬야 한다.

## 한 번에 설명하기

> Kubernetes 장애는 로그, event, 메트릭, rollout 상태를 같이 봐야 합니다. Pod가 Running이라고 요청을 받을 수 있는 건 아니어서, 503이 늘면 저는 애플리케이션 오류보다 readiness, endpoint, ingress를 먼저 봅니다.
>
> 재시작이 반복되면 `logs --previous`와 종료 사유를 확인합니다. 지연이 늘면 CPU throttling이나 OOMKilled처럼 코드 문제로 보이는 자원 문제부터 걸러 냅니다.

## 꼬리 질문

- Pod가 재시작된 원인은 어떻게 확인하나?
- 503이 늘면 Kubernetes에서 무엇부터 보나?
- CPU throttling은 어떤 지표와 증상으로 확인하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes: Resource Metrics Pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[readiness-and-liveness-probe]]
- [[resource-request-and-limit]]
- [[deployment-service-ingress]]
- [[02-practical-backend/observability/metrics|metrics]]
