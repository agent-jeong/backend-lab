---
title: Kubernetes 로그와 메트릭 확인
description: Pod, Deployment, Service 문제를 로그와 메트릭으로 좁히는 기준
---

# Kubernetes 로그와 메트릭 확인

## 한 줄 정의

Kubernetes 로그와 메트릭 확인은 애플리케이션 문제와 클러스터 리소스 문제를 구분하기 위해 Pod 로그, event, resource 사용량, rollout 상태를 함께 보는 과정이다.

## 실무에서 왜 문제 되는가

- 애플리케이션 로그만 보면 Service selector, readiness, OOMKilled 같은 원인을 놓칠 수 있다.
- Pod가 재시작되면 이전 container 로그를 따로 확인해야 한다.
- CPU throttling이나 memory limit 초과는 애플리케이션 지연과 오류로 나타난다.
- event를 보지 않으면 image pull, scheduling, probe 실패 원인을 늦게 찾는다.

## 동작 원리

1. Deployment rollout 상태와 replica 수를 확인한다.
2. Pod 상태, restart count, event를 확인한다.
3. container 로그와 이전 container 로그를 확인한다.
4. Service endpoint와 Ingress routing을 확인한다.
5. CPU, memory, throttling, network 지표를 애플리케이션 지표와 함께 본다.

## 실무 판단 기준

| 증상 | 확인 |
|---|---|
| 503 증가 | readiness, endpoints, ingress |
| 재시작 반복 | logs --previous, OOMKilled, liveness |
| 지연 증가 | CPU throttling, memory, DB/외부 API |
| Pod Pending | request, node resource, scheduling event |
| 새 버전 반영 안 됨 | rollout status, image tag, ReplicaSet |

## 자주 나는 실수

- `kubectl logs`만 보고 event를 보지 않는다.
- 재시작된 Pod의 이전 로그를 확인하지 않는다.
- Pod Running 상태를 정상 서비스 상태로 판단한다.
- 리소스 지표 없이 애플리케이션 코드만 의심한다.

## 확인 방법

- 명령: `kubectl describe pod`로 event와 종료 사유를 본다.
- 명령: `kubectl logs --previous`로 재시작 전 로그를 본다.
- 명령: `kubectl get endpoints`로 Service 대상 Pod를 확인한다.
- 메트릭: restart count, readiness failure, CPU throttling, memory usage를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 문제 위치를 app, network, scheduling, resource로 나눌 수 있다 | 클러스터 접근 권한과 관측 도구가 필요하다 |
| event와 metric을 함께 보면 재현 어려운 장애를 좁힐 수 있다 | 메트릭 보관 기간이 짧으면 과거 분석이 어렵다 |

## 핵심 요약

Kubernetes 장애 분석은 로그, event, metric, rollout 상태를 함께 봐야 한다.

Pod Running은 서비스 가능 상태와 같지 않다.

재시작 문제는 현재 로그뿐 아니라 previous log와 종료 사유가 중요하다.

503은 애플리케이션 오류뿐 아니라 readiness, endpoint, ingress 문제일 수 있다.

CPU throttling과 OOMKilled는 애플리케이션 성능 문제처럼 보일 수 있다.

## 꼬리 질문

- Pod가 재시작된 원인은 어떻게 확인할 것인가?
- 503이 증가하면 Kubernetes에서 무엇부터 볼 것인가?
- CPU throttling은 어떤 지표와 증상으로 확인할 것인가?

## 관련 문서

- [[kubernetes]]
- [[readiness-and-liveness-probe]]
- [[resource-request-and-limit]]
- [[deployment-service-ingress]]
- [[02-practical-backend/observability/metrics|metrics]]
