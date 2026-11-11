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
4. 실패하면 `backoffLimit`(Job을 실패로 끝내기 전에 다시 시도할 횟수)만큼 재시도한다.
5. `concurrencyPolicy`로 앞 실행이 안 끝났을 때 어떻게 할지를, history limit으로 끝난 Job을 몇 개 남길지를 정한다.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: example-daily-job
spec:
  schedule: "0 1 * * *"      # 분 시 일 월 요일 → 매일 01:00
  timeZone: "Asia/Seoul"     # 없으면 컨트롤 플레인 시간대를 따른다
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
| 겹쳐 돌면 안 됨 | `concurrencyPolicy: Forbid` | 앞 실행이 안 끝났으면 이번 실행을 건너뛴다. 기본값 `Allow`는 겹쳐 돌린다 |
| 최신 실행만 의미 있음 | `concurrencyPolicy: Replace` | 앞 실행을 멈추고 새 실행으로 바꾼다 |
| 실패 재시도 횟수 | `backoffLimit` | 정한 횟수를 넘으면 Job이 실패로 끝난다 |
| 늦게라도 돌릴지 | `startingDeadlineSeconds` | 예정 시각을 놓친 뒤 이 초 안에 시작 못 하면 그 회차는 건너뛴다. 없으면 기한 없이 늦게라도 돈다. 다만 놓친 회차가 100번을 넘으면 Job을 만들지 않고 오류를 남긴다 |
| 끝난 Job을 몇 개 남길지 | `successfulJobsHistoryLimit`, `failedJobsHistoryLimit` | 기본값은 성공 3개, 실패 1개다. 실패 로그를 더 보려면 실패 쪽을 늘린다 |

공식 문서도 CronJob이 한 회차에 Job을 두 번 만들거나 한 번도 안 만드는 일이 드물게 있다고 적고, Job을 멱등하게(여러 번 돌려도 결과가 같게) 만들라고 한다. concurrencyPolicy는 실행이 겹치는 것만 막는다. 같은 작업이 다시 돌아도 데이터가 깨지지 않게 하는 일은 배치 코드가 해야 한다. 대상별 중복 방지와 lock을 고르는 기준은 [[duplicate-execution-prevention]]에 있다.

CronJob을 쓰면 주기 작업을 Kubernetes 안에서 YAML로 관리하고, Job마다 성공과 실패 기록이 남는다. 다만 "A 작업이 끝나면 B 작업" 같은 단계 사이의 순서는 CronJob으로 표현하지 못한다. 실패한 건만 골라 다시 처리하는 로직도 애플리케이션이 따로 만들어야 한다.

## 자주 깨지는 곳

- schedule만 걸고 중복 실행 정책을 정하지 않으면, 배치가 길어진 날 다음 실행과 겹친다.
- 배치 로직이 멱등하지 않으면, 재시도나 수동 재실행 한 번에 데이터가 중복된다.
- 실패한 Job 로그를 보관하지 않으면, 나중에 원인을 찾을 근거가 없다.
- `timeZone` 없이 schedule을 걸면, 컨트롤 플레인 시간대(대개 UTC)로 해석돼 한국 시각 기준으로 9시간 어긋나게 돈다.
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

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/batch/duplicate-execution-prevention|duplicate-execution-prevention]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
