---
title: CronJob
description: Kubernetes에서 주기 배치를 돌리고, 겹치거나 실패했을 때 대처하는 법
tags: [concept, kubernetes]
---

# CronJob

CronJob은 정해 둔 schedule마다 Job을 만들어 배치 작업을 주기적으로 돌리는 Kubernetes 리소스다.

schedule을 거는 건 쉽다. 문제는 작업이 두 번 돌거나 중간에 실패했을 때다. 정산이나 알림 발송 배치가 겹쳐 돌면 같은 정산이 두 번 잡히고 같은 알림이 두 번 나간다. 그래서 schedule보다 "다시 돌려도 결과가 같은가"를 먼저 설계한다.

## 동작

1. CronJob controller가 schedule에 맞춰 Job을 만든다.
2. Job은 지정된 Pod template으로 배치 Pod를 띄운다.
3. Pod가 성공하면 Job이 완료 상태가 된다.
4. 실패하면 backoffLimit과 restart policy에 따라 재시도한다.
5. concurrencyPolicy로 동시 실행을, history limit으로 남겨 둘 기록 수를 정한다.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: example-daily-job
spec:
  schedule: "0 1 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: job
              image: example-service:1.0.0
              args: ["run-daily-job"]
```

## 상황별 설정

| 상황 | 설정 | 이유 |
|---|---|---|
| 중복 실행 위험 | `concurrencyPolicy: Forbid` | 이전 실행이 끝나기 전 새 실행을 막는다 |
| 최신 실행만 중요 | `concurrencyPolicy: Replace` | 오래 걸린 작업을 새 작업으로 대체한다 |
| 실패 재시도 | `backoffLimit` | 무한 재시도를 막는다 |
| 실행 누락 허용 범위 | `startingDeadlineSeconds` | 늦게 시작할 작업의 기준을 정한다 |
| 기록 관리 | history limit | 완료 Job이 계속 쌓이지 않게 한다 |

concurrencyPolicy는 실행이 겹치는 것만 막는다. 같은 작업이 다시 돌아도 데이터가 깨지지 않게 하는 일은 배치 코드가 해야 한다. 대상별 중복 방지와 lock을 고르는 기준은 [[duplicate-execution-prevention]]에 있다.

CronJob을 쓰면 주기 작업을 Kubernetes 안에서 YAML로 관리하고, Job마다 성공과 실패 기록이 남는다. 다만 여러 단계가 얽힌 workflow를 돌리기에는 모자랄 수 있고, 실패한 건을 다시 처리하는 로직은 애플리케이션에서 따로 만들어야 한다.

## 자주 깨지는 곳

- schedule만 걸고 중복 실행 정책을 정하지 않으면, 배치가 길어진 날 다음 실행과 겹친다.
- 배치 로직이 멱등하지 않으면, 재시도나 수동 재실행 한 번에 데이터가 중복된다.
- 실패한 Job 로그를 보관하지 않으면, 나중에 원인을 찾을 근거가 없다.
- timezone을 확인하지 않고 schedule을 걸면, 생각한 시각과 다른 시각에 돈다.
- Job 성공 여부만 보면, 처리 건수가 0이거나 일부가 빠진 실행도 성공으로 넘어간다. 처리 건수 지표가 없으면 이런 조용한 실패를 늦게 알게 된다.

## 운영에서 볼 것

- `kubectl get cronjob`, `kubectl get jobs`로 실행 상태를 본다.
- 실패한 Job은 Pod 로그와 event를 확인한다.
- 메트릭으로는 성공/실패 횟수, 처리 건수, 실행 시간, 재시도 횟수를 본다.
- 같은 작업을 두 번 실행해도 결과가 깨지지 않는지 테스트한다.

## 한 번에 설명하기

> CronJob은 schedule에 맞춰 Job을 만드는 리소스입니다. 저는 concurrencyPolicy로 긴 작업이 다음 실행과 겹치지 않게 하고, backoffLimit으로 재시도 횟수를 제한하고, timezone과 history limit도 확인합니다.
>
> 그래도 CronJob 설정이 배치 로직의 멱등성을 대신해 주지는 않습니다. 그래서 다시 실행해도 안전하게 만들고, 처리 건수와 빠진 건이 있는지를 지표로 봅니다.

## 꼬리 질문

- CronJob과 Job은 어떤 관계인가?
- 배치 중복 실행을 어떻게 막나?
- 실패한 배치를 중간부터 다시 처리하려면 무엇을 기록해야 하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/batch/duplicate-execution-prevention|duplicate-execution-prevention]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
