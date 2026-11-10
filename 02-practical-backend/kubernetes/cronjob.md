---
title: CronJob
description: Kubernetes에서 주기적 배치 작업을 실행하고 실패를 관리하는 기준
---

# CronJob

CronJob은 정해진 schedule마다 Job을 만들어 주기적인 배치 작업을 돌리는 Kubernetes 리소스다.

schedule을 거는 건 쉽다. 어려운 건 두 번 돌거나 실패했을 때다. 정산, 알림, 데이터 보정 작업이 겹쳐 실행되면 같은 일이 여러 번 처리된다. 그래서 schedule보다 재처리 가능성과 멱등성을 먼저 설계한다.

## 동작

1. CronJob controller가 schedule에 맞춰 Job을 만든다.
2. Job은 지정된 Pod template으로 배치 Pod를 띄운다.
3. Pod가 성공하면 Job이 완료 상태가 된다.
4. 실패하면 backoffLimit과 restart policy에 따라 재시도한다.
5. concurrencyPolicy와 history limit으로 동시 실행과 기록 보관을 제어한다.

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

concurrencyPolicy는 실행이 겹치는 것만 막는다. 같은 작업이 다시 돌아도 결과가 깨지지 않게 하는 건 배치 로직의 몫이다. 대상별 중복 방지와 lock 선택 기준은 [[duplicate-execution-prevention]]에서 다룬다.

CronJob은 Kubernetes 안에서 주기 작업을 선언적으로 관리하고 Job 단위로 성공/실패 기록을 남긴다. 다만 복잡한 workflow orchestration에는 부족할 수 있고, 애플리케이션 수준의 재처리 설계는 따로 필요하다.

## 자주 깨지는 곳

- **schedule만 걸고 중복 실행 정책을 안 정한다.** 배치가 길어지면 다음 실행과 겹친다.
- **배치 로직 자체가 멱등하지 않다.** 재시도나 수동 재실행 한 번에 데이터가 중복된다.
- **실패한 Job 로그를 보관하지 않는다.** 원인을 분석할 근거가 사라진다.
- **timezone을 확인하지 않고 schedule을 건다.** 의도한 시각과 다른 시각에 돈다.
- **Job 성공 여부만 본다.** 성공으로 끝났어도 실제 처리 건수가 0이거나 누락이 있을 수 있다. 지표가 없으면 조용한 실패를 늦게 발견한다.

## 운영에서 볼 것

- `kubectl get cronjob`, `kubectl get jobs`로 실행 상태를 본다.
- 실패한 Job은 Pod 로그와 event를 확인한다.
- 메트릭은 성공/실패 횟수, 처리 건수, 실행 시간, 재시도 횟수.
- 같은 작업을 두 번 실행해도 결과가 깨지지 않는지 테스트한다.

## 면접에서 말하기

> CronJob은 schedule에 맞춰 Job을 만드는 리소스입니다. 저는 먼저 concurrencyPolicy로 긴 작업이 다음 실행과 겹치지 않게 하고, backoffLimit으로 재시도를 제한하고, timezone과 history limit을 확인합니다. 그래도 CronJob 설정이 배치 로직의 멱등성을 대신하지는 않아서, 다시 실행해도 안전하게 만들고 처리 건수와 누락 여부를 지표로 봅니다.

## 꼬리 질문

- CronJob과 Job은 어떤 관계인가?
- 배치 중복 실행을 어떻게 막나?
- 실패한 배치를 중간부터 다시 처리하려면 무엇을 기록해야 하나?

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/batch/duplicate-execution-prevention|duplicate-execution-prevention]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
