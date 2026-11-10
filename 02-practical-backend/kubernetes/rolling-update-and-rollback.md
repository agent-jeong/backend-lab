---
title: Rolling Update와 Rollback
description: Kubernetes 배포 중 가용성을 유지하고 실패 시 되돌리는 기준
tags: [concept, kubernetes]
---

# Rolling Update와 Rollback

Rolling update는 새 버전 Pod를 조금씩 늘리고 기존 Pod를 줄여 가는 배포 방식이다. rollback은 문제가 생긴 배포를 이전 revision으로 되돌리는 작업이다.

롤링 배포가 정말 무중단이 되려면 readiness가 정확하고, replica 수와 update strategy가 맞아야 한다. rollback도 만능이 아니다. Pod template은 되돌리지만 DB schema나 외부 상태 변경은 되돌리지 못한다.

## 동작

1. Deployment의 image나 template이 바뀌면 새 ReplicaSet이 생긴다.
2. Kubernetes는 `maxSurge`, `maxUnavailable` 기준으로 새 Pod를 늘리고 기존 Pod를 줄인다.
3. readiness를 통과한 Pod만 Service endpoint에 들어간다.
4. 새 버전이 안정되면 기존 ReplicaSet은 축소된다.
5. 문제가 있으면 이전 revision으로 rollback해 기존 template으로 돌린다.

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

`maxUnavailable: 0`은 배포 중 가용 Pod 수를 유지해 준다. 대신 새 Pod가 준비되지 않으면 배포가 오래 멈춘다.

## 상황별로 볼 것

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| 배포 중 503 | readiness, maxUnavailable | 가용 Pod가 부족할 수 있다 |
| 새 버전 오류 | rollout status, event, app log | 실패 지점을 확인한다 |
| 빠른 복구 필요 | rollback 가능성 | 이전 revision과 설정 호환성을 본다 |
| DB 변경 포함 | backward compatibility | rollback으로 복구 가능한지 판단한다 |
| 무중단 요구 | replica 2개 이상, readiness, graceful shutdown | 단일 Pod는 노드 장애나 eviction 때 대체할 Pod가 없다 |

## 자주 깨지는 곳

- **replica 1개로 무중단을 기대한다.** 롤링 자체는 새 Pod가 Ready된 뒤 기존 Pod를 내리므로 가능하다. 하지만 노드 장애나 drain 때는 공백이 생긴다.
- **종료되는 Pod의 진행 중 요청을 생각하지 않는다.** Pod가 endpoint에서 빠지는 것과 SIGTERM 전달은 동시에 진행된다. 앱이 바로 죽으면 일부 요청이 502/503으로 끊긴다. graceful shutdown과 짧은 `preStop` 지연을 둔다.
- **readiness 없이 배포 전략만 설정한다.** readiness 기준이 틀리면 준비 안 된 새 Pod로 트래픽이 들어가, 전략을 아무리 잡아도 효과가 없다.
- **DB migration을 새 코드와 강하게 묶는다.** 하위 호환이 안 되면 단순 rollback으로 복구되지 않는다.
- **설정 변경과 이미지 변경을 한 번에 한다.** 문제가 생기면 어느 쪽이 원인인지 가르기 어렵다.
- **rollout 성공만 보고 끝낸다.** 실패를 감지할 지표가 없으면 잘못된 버전이 오래 남고, 그동안 일부 트래픽이 계속 실패한다.

## 운영에서 볼 것

- `kubectl rollout status deployment/example-service`로 배포 상태를 본다.
- `kubectl rollout history deployment/example-service`로 revision을 확인한다.
- `kubectl describe deployment`로 strategy와 event를 확인한다.
- error rate, latency, restart count, readiness failure를 배포 전후로 비교한다.

## 한 번에 설명하기

> Rolling update는 새 Pod를 늘리고 기존 Pod를 줄이며 버전을 점진적으로 바꾸는 방식입니다. 무중단이 되려면 readiness가 정확해야 하고, replica 수와 `maxUnavailable`이 배포 중 가용성을 정합니다. 저는 종료되는 Pod를 위해 graceful shutdown과 `preStop` 지연을 두고, 배포 뒤에는 rollout 상태와 함께 오류율, 지연, 재시작 수를 봅니다. rollback은 Pod template만 되돌리므로 DB 변경은 하위 호환되게 따로 설계합니다.

## 꼬리 질문

- Rolling update가 무중단이 되려면 어떤 조건이 필요한가?
- Rollback이 어려운 배포는 어떤 경우인가?
- 배포 성공 여부를 어떤 지표로 확인하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Kubernetes: Deployments (rolling update, rollback)](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

## 관련 문서

- [[kubernetes]]
- [[readiness-and-liveness-probe]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
