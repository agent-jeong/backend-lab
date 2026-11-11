---
title: Rolling Update와 Rollback
description: Kubernetes에서 서비스를 멈추지 않고 배포하고, 문제가 생기면 되돌리는 법
tags: [concept, kubernetes]
---

# Rolling Update와 Rollback

Rolling update는 새 버전 Pod를 조금씩 늘리면서 기존 Pod를 줄여 가는 배포 방식이다. rollback은 문제가 생긴 배포를 이전 revision(Deployment의 Pod template이 바뀔 때마다 남는 번호 붙은 이력)으로 되돌리는 작업이다.

롤링 배포가 정말 무중단이 되려면 readiness가 정확해야 하고, replica 수와 update strategy가 맞아야 한다. rollback도 모든 걸 되돌려 주지는 않는다. Pod template은 되돌리지만 DB schema나 외부 시스템에 이미 반영된 변경은 그대로 남는다.

## 동작

1. Deployment의 image나 template이 바뀌면 새 ReplicaSet이 생긴다.
2. Kubernetes는 `maxSurge`(원래 replica 수보다 더 띄워도 되는 Pod 수)와 `maxUnavailable`(배포 중 모자라도 되는 준비된 Pod 수)에 맞춰 새 Pod를 늘리고 기존 Pod를 줄인다.
3. readiness를 통과한 Pod만 Service endpoint에 들어간다.
4. 새 버전이 안정되면 기존 ReplicaSet은 축소된다.
5. 문제가 있으면 `kubectl rollout undo`로 이전 revision의 template을 다시 적용한다. 이것도 롤링 방식으로 진행된다.

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

replica가 4개일 때 위 설정이면 새 Pod 1개를 더 띄워 5개가 되고, 새 Pod가 준비되면 옛 Pod 1개를 내리는 일을 반복한다. `maxUnavailable: 0`이라 배포 중에도 준비된 Pod가 4개 아래로 떨어지지 않는다. 대신 새 Pod가 준비되지 않으면 배포가 그 자리에서 멈춰 있다.

## 상황별로 볼 것

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| 배포 중 503 | readiness, `maxUnavailable` | 준비된 Pod가 모자란 순간이 있었다 |
| 새 버전이 오류를 냄 | rollout status, event, 앱 로그 | 새 Pod가 뜨다 죽는지, 떴는데 요청을 실패하는지 가른다 |
| 당장 되돌려야 함 | `kubectl rollout undo` | Pod template만 되돌린다. 같이 바꾼 ConfigMap·Secret 내용은 그대로라 따로 되돌린다 |
| DB 변경이 같이 나감 | 옛 코드가 새 스키마에서도 도는지 | 안 돌면 rollback해도 옛 Pod가 실패한다 |
| 무중단이 꼭 필요함 | replica 2개 이상, readiness, graceful shutdown | Pod가 1개면 노드 장애나 노드 drain(점검 전에 노드의 Pod를 비우는 작업) 때 대신 받을 Pod가 없다 |

## 자주 깨지는 곳

- replica 1개로 무중단을 기대하면, 노드 장애나 drain 때 공백이 생긴다. 롤링 배포 자체는 새 Pod가 Ready된 뒤 기존 Pod를 내리니 replica 1개로도 된다.
- 종료되는 Pod가 처리 중이던 요청을 생각하지 않으면, 일부 요청이 502/503으로 끊긴다. Pod가 endpoint에서 빠지는 일과 SIGTERM이 전달되는 일은 동시에 일어나서, 앱이 바로 죽으면 아직 들어오던 요청이 실패한다. graceful shutdown과 짧은 `preStop` 지연을 둔다.
- readiness 없이 배포 전략만 잡으면, 준비 안 된 새 Pod로 트래픽이 들어간다. readiness 기준이 틀리면 전략을 아무리 잡아도 소용없다.
- DB migration을 새 코드와 강하게 묶으면, 하위 호환이 안 될 때 단순 rollback으로 복구되지 않는다.
- 설정 변경과 이미지 변경을 한 번에 하면, 문제가 생겼을 때 어느 쪽이 원인인지 가르기 어렵다.
- rollout이 성공한 것만 보고 끝내면, 실패를 알려 줄 지표가 없어 잘못된 버전이 오래 남고, 그동안 일부 트래픽이 계속 실패한다.

## 운영에서 볼 것

- `kubectl rollout status deployment/example-service`로 배포 상태를 본다.
- `kubectl rollout history deployment/example-service`로 revision을 확인한다.
- `kubectl describe deployment`로 strategy와 event를 확인한다.
- 되돌릴 때는 `kubectl rollout undo deployment/example-service`를 쓰고, 특정 revision으로 가려면 `--to-revision=번호`를 붙인다.
- error rate, latency, restart count, readiness failure를 배포 전후로 비교한다.

## 한 번에 설명하기

> Rolling update는 새 Pod를 늘리고 기존 Pod를 줄이면서 버전을 조금씩 바꾸는 방식입니다. 무중단이 되려면 readiness가 정확해야 하고, 배포 중 가용 Pod가 얼마나 남는지는 replica 수와 `maxUnavailable`이 정합니다.
>
> 저는 종료되는 Pod를 위해 graceful shutdown과 `preStop` 지연을 두고, 배포가 끝나면 rollout 상태와 함께 오류율, 지연, 재시작 수를 봅니다.
>
> rollback은 Pod template만 되돌리기 때문에, DB 변경은 하위 호환되게 따로 설계합니다.

## 꼬리 질문

- Rolling update가 무중단이 되려면 어떤 조건이 필요한가?
- Rollback이 어려운 배포는 어떤 경우인가?
- 배포 성공 여부를 어떤 지표로 확인하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Deployments (rolling update, rollback)](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[readiness-and-liveness-probe]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
- [[graceful-shutdown]]
