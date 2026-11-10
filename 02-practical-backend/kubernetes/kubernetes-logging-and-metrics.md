---
title: Kubernetes 로그와 메트릭 확인
description: Pod, Deployment, Service 문제를 로그와 메트릭으로 좁히는 기준
tags: [concept, kubernetes]
---

# Kubernetes 로그와 메트릭 확인

Kubernetes에서 장애를 볼 때는 Pod 로그, event, resource 사용량, rollout 상태를 같이 본다. 목적은 애플리케이션 문제인지 클러스터 리소스 문제인지 가르는 것이다.

애플리케이션 로그만 보면 Service selector, readiness, OOMKilled 같은 원인은 보이지 않는다. CPU throttling이나 memory limit 초과도 겉으로는 애플리케이션 지연과 오류로 나타난다. 이렇게 보면 문제 위치가 app, network, scheduling, resource 중 하나로 좁혀진다.

## 보는 순서

1. Deployment rollout 상태와 replica 수를 본다.
2. Pod 상태, restart count, event를 본다.
3. container 로그와 이전 container 로그를 본다.
4. Service endpoint와 Ingress routing을 본다.
5. CPU, memory, throttling, network 지표를 애플리케이션 지표와 나란히 본다.

| 증상 | 확인 |
|---|---|
| 503 증가 | readiness, endpoints, ingress |
| 재시작 반복 | logs --previous, OOMKilled, liveness |
| 지연 증가 | CPU throttling, memory, DB/외부 API |
| Pod Pending | request, node resource, scheduling event |
| 새 버전 반영 안 됨 | rollout status, image tag, ReplicaSet |

## 자주 깨지는 곳

- **`kubectl logs`만 보고 event를 안 본다.** image pull, scheduling, probe 실패 원인을 늦게 찾는다.
- **재시작된 Pod의 이전 로그를 안 본다.** 재시작 원인은 지금 container가 아니라 죽은 container 로그에 있다.
- **Pod Running을 서비스 정상으로 본다.** Running이어도 readiness가 실패하면 트래픽을 받지 못한다.
- **리소스 지표 없이 코드만 의심한다.** throttling과 OOMKilled는 코드 문제처럼 보인다.

## 운영에서 볼 것

- `kubectl describe pod`로 event와 종료 사유를 본다.
- `kubectl logs --previous`로 재시작 전 로그를 본다.
- `kubectl get endpoints`로 Service가 가리키는 Pod를 확인한다.
- 메트릭은 restart count, readiness failure, CPU throttling, memory usage.

이렇게 하려면 클러스터 접근 권한과 관측 도구가 있어야 한다. 메트릭 보관 기간이 짧으면 지난 장애는 분석하기 어렵다.

## 한 번에 설명하기

> Kubernetes 장애는 로그, event, metric, rollout 상태를 같이 봐야 합니다. Pod가 Running이라고 서비스 가능한 건 아니어서, 503이 늘면 저는 애플리케이션 오류보다 readiness, endpoint, ingress를 먼저 봅니다. 재시작이 반복되면 `logs --previous`와 종료 사유를 확인하고, 지연이 늘면 CPU throttling과 OOMKilled처럼 코드 문제로 보이는 리소스 문제부터 걸러 냅니다.

## 꼬리 질문

- Pod가 재시작된 원인은 어떻게 확인하나?
- 503이 늘면 Kubernetes에서 무엇부터 보나?
- CPU throttling은 어떤 지표와 증상으로 확인하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Kubernetes: Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes: Resource Metrics Pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)

## 관련 문서

- [[kubernetes]]
- [[readiness-and-liveness-probe]]
- [[resource-request-and-limit]]
- [[deployment-service-ingress]]
- [[02-practical-backend/observability/metrics|metrics]]
