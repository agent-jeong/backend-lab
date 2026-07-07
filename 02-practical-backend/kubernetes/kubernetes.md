---
title: Kubernetes
description: 컨테이너 기반 백엔드 서비스를 배포하고 운영하기 위한 Kubernetes 학습 인덱스
comments: false
---

# Kubernetes

## 운영 방식

- 이 문서는 Kubernetes 학습 인덱스로만 사용한다.
- 상세 내용은 `02-practical-backend/kubernetes/` 아래 개념별 문서로 나눈다.
- 학습한 내용은 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 배포 단위, 트래픽 경로, 설정, 장애 복구, 운영 안정성을 중심으로 작성한다.

## 학습 산출물

- 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[deployment-service-ingress|Deployment, Service, Ingress]]
2. [[pod-and-container|Pod와 Container]]
3. [[configmap-and-secret|ConfigMap과 Secret]]
4. [[readiness-and-liveness-probe|Readiness Probe와 Liveness Probe]]
5. [[resource-request-and-limit|Resource Request와 Limit]]
6. [[rolling-update-and-rollback|Rolling Update와 Rollback]]
7. [[cronjob|CronJob]]
8. [[kubernetes-logging-and-metrics|로그와 메트릭 확인]]

## 핵심 질문

- Kubernetes에서 애플리케이션 배포 단위는 무엇인가?
- 외부 요청은 어떤 경로로 Pod까지 전달되는가?
- 배포 중 일부 Pod가 실패하면 트래픽은 어떻게 제어되는가?
- 설정과 민감 정보는 컨테이너 이미지와 어떻게 분리하는가?
- request와 limit을 잘못 설정하면 어떤 장애가 생기는가?
- 롤링 배포와 롤백은 어떤 조건에서 안전하게 동작하는가?
- CronJob은 일반 배치 스케줄러와 어떤 운영 차이가 있는가?

## 실무 관점

- Kubernetes는 배포 도구가 아니라 컨테이너 워크로드를 선언한 상태로 유지하는 운영 플랫폼이다.
- 백엔드 개발자는 모든 내부 구현을 알 필요는 없지만, Pod 상태, 트래픽 경로, 설정 주입, readiness 실패 원인은 설명할 수 있어야 한다.
- YAML 암기보다 장애가 났을 때 어떤 리소스와 이벤트를 확인할지 설명하는 것이 중요하다.

## 관련 문서

- [[deployment-service-ingress]]
- [[pod-and-container]]
- [[configmap-and-secret]]
- [[readiness-and-liveness-probe]]
- [[resource-request-and-limit]]
- [[rolling-update-and-rollback]]
- [[cronjob]]
- [[kubernetes-logging-and-metrics]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/observability/observability|observability]]
- [[04-interview/interview-questions|technical-questions]]
