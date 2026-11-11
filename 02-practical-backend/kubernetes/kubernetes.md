---
title: Kubernetes
description: 컨테이너로 띄운 백엔드 서비스를 Kubernetes에서 배포하고 운영할 때 읽는 노트 모음
tags: [kubernetes]
comments: false
---

# Kubernetes

Pod, Deployment·Service·Ingress, 프로브, 리소스, 롤링 업데이트, CronJob을 다룬다. 배포한 서비스가 트래픽을 받지 못할 때 무엇부터 볼지를 주로 이야기한다.

## 읽는 순서

1. [[deployment-service-ingress|Deployment, Service, Ingress]]
2. [[pod-and-container|Pod와 Container]]
3. [[configmap-and-secret|ConfigMap과 Secret]]
4. [[readiness-and-liveness-probe|Readiness Probe와 Liveness Probe]]
5. [[resource-request-and-limit|Resource Request와 Limit]]
6. [[rolling-update-and-rollback|Rolling Update와 Rollback]]
7. [[cronjob|CronJob]]
8. [[kubernetes-logging-and-metrics|로그와 메트릭 확인]]

## 먼저 답해 볼 질문

- Kubernetes에서 애플리케이션을 배포하는 단위는 무엇인가?
- 외부 요청은 어떤 경로를 거쳐 Pod까지 가는가?
- 배포 중 일부 Pod가 실패하면 트래픽은 어디로 가는가?
- 설정과 민감 정보를 컨테이너 이미지와 어떻게 떼어 놓는가?
- request와 limit을 잘못 잡으면 어떤 장애가 나는가?
- 롤링 배포와 롤백은 어떤 조건에서 안전하게 돌아가는가?
- CronJob은 일반 배치 스케줄러와 운영할 때 무엇이 다른가?

## 실무에서 보는 것

- Kubernetes는 배포 도구가 아니다. 선언해 둔 상태대로 컨테이너를 계속 맞춰 주는 운영 플랫폼이다.
- 백엔드 개발자가 내부 구현을 다 알 필요는 없다. Pod 상태, 트래픽 경로, 설정 주입, readiness 실패 원인을 설명할 수 있으면 된다.
- YAML 문법을 외우는 것보다 "장애가 나면 어떤 리소스와 이벤트부터 보나"를 말할 수 있는 쪽이 쓸모 있다.

## 관련 문서

- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/observability/observability|observability]]
- [[04-design-cases/interview-questions|technical-questions]]
