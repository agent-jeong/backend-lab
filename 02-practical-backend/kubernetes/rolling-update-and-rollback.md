---
title: Rolling Update와 Rollback
description: Kubernetes 배포 중 가용성을 유지하고 실패 시 되돌리는 기준
---

# Rolling Update와 Rollback

## 한 줄 정의

Rolling update는 새 버전 Pod를 점진적으로 늘리고 기존 Pod를 줄이는 배포 방식이며, rollback은 문제가 생긴 배포를 이전 revision으로 되돌리는 작업이다.

## 실무에서 왜 문제 되는가

- readiness가 부정확하면 준비되지 않은 새 Pod로 트래픽이 들어갈 수 있다.
- replica 수와 update strategy가 잘못되면 배포 중 가용 Pod가 부족해진다.
- DB schema 변경이나 설정 변경이 하위 호환되지 않으면 단순 rollback으로 복구되지 않을 수 있다.
- 배포 실패를 감지할 지표가 없으면 잘못된 버전이 오래 유지된다.

## 동작 원리

1. Deployment image나 template이 변경되면 새 ReplicaSet이 생성된다.
2. Kubernetes는 `maxSurge`, `maxUnavailable` 기준으로 새 Pod를 늘리고 기존 Pod를 줄인다.
3. readiness를 통과한 Pod만 Service endpoint에 포함된다.
4. 새 버전이 안정화되면 기존 ReplicaSet은 축소된다.
5. 문제가 있으면 이전 revision으로 rollback해 기존 template으로 되돌린다.

## 실무 판단 기준

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| 배포 중 503 | readiness, maxUnavailable | 가용 Pod가 부족할 수 있다 |
| 새 버전 오류 | rollout status, event, app log | 실패 지점을 확인한다 |
| 빠른 복구 필요 | rollback 가능성 | 이전 revision과 설정 호환성을 본다 |
| DB 변경 포함 | backward compatibility | rollback으로 복구 가능한지 판단한다 |
| 무중단 요구 | replica 2개 이상, readiness | 단일 Pod는 롤링 중 공백이 생길 수 있다 |

## 자주 나는 실수

- replica 1개로 무중단 rolling update를 기대한다.
- readiness 없이 배포 전략만 설정한다.
- DB migration을 새 코드와 강하게 묶어 rollback을 어렵게 만든다.
- 설정 변경과 이미지 변경을 동시에 해 원인 분리가 어렵다.
- rollout 성공만 보고 실제 비즈니스 지표를 확인하지 않는다.

## 확인 방법

- 명령: `kubectl rollout status deployment/example-service`로 배포 상태를 본다.
- 명령: `kubectl rollout history deployment/example-service`로 revision을 확인한다.
- 명령: `kubectl describe deployment`로 strategy와 event를 확인한다.
- 메트릭: error rate, latency, restart count, readiness failure를 배포 전후로 비교한다.

## 장점과 한계

| 방식 | 장점 | 한계 |
|---|---|---|
| Rolling update | 기본 배포 전략으로 점진적 전환이 가능하다 | 오류 감지가 늦으면 일부 트래픽이 실패한다 |
| Rollback | 이전 Pod template으로 빠르게 되돌릴 수 있다 | DB와 외부 상태 변경은 되돌리지 못할 수 있다 |
| Readiness 연계 | 준비된 Pod만 트래픽을 받는다 | readiness 기준이 틀리면 효과가 없다 |

## 짧은 예제

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

`maxUnavailable: 0`은 배포 중 가용 Pod 수를 유지하는 데 도움을 주지만, 새 Pod가 준비되지 않으면 배포가 오래 멈출 수 있다.

## 핵심 요약

Rolling update는 새 Pod를 늘리고 기존 Pod를 줄이며 점진적으로 버전을 바꾼다.

readiness가 정확해야 준비된 Pod에만 트래픽이 간다.

replica 수와 `maxUnavailable` 설정은 배포 중 가용성에 직접 영향을 준다.

rollback은 Pod template을 되돌릴 수 있지만 DB 변경이나 외부 상태 변경까지 되돌리지는 못한다.

배포 후에는 rollout 상태뿐 아니라 오류율, 지연 시간, 재시작 수를 함께 확인해야 한다.

## 꼬리 질문

- Rolling update가 무중단이 되려면 어떤 조건이 필요한가?
- Rollback이 어려운 배포는 어떤 경우인가?
- 배포 성공 여부를 어떤 지표로 확인할 것인가?

## 관련 문서

- [[kubernetes]]
- [[readiness-and-liveness-probe]]
- [[02-practical-backend/ci-cd/ci-cd|ci-cd]]
