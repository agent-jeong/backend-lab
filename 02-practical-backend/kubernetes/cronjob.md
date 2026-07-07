---
title: CronJob
description: Kubernetes에서 주기적 배치 작업을 실행하고 실패를 관리하는 기준
---

# CronJob

## 한 줄 정의

CronJob은 정해진 schedule에 따라 Job을 생성해 주기적 배치 작업을 실행하는 Kubernetes 리소스다.

## 실무에서 왜 문제 되는가

- 중복 실행을 허용하면 정산, 알림, 데이터 보정 작업이 여러 번 처리될 수 있다.
- 실패한 Job의 재시도와 재처리 기준이 없으면 데이터 누락이나 중복이 생긴다.
- 배치 시간이 길어 다음 schedule과 겹치면 동시 실행 문제가 발생할 수 있다.
- 로그와 성공/실패 지표가 없으면 작업이 조용히 실패해도 늦게 발견된다.

## 동작 원리

1. CronJob controller가 schedule에 맞춰 Job을 만든다.
2. Job은 지정된 Pod template으로 배치 Pod를 실행한다.
3. Pod가 성공하면 Job이 완료 상태가 된다.
4. 실패하면 backoffLimit과 restart policy에 따라 재시도한다.
5. concurrencyPolicy와 history limit으로 동시 실행과 기록 보관을 제어한다.

## 실무 판단 기준

| 상황 | 설정 | 이유 |
|---|---|---|
| 중복 실행 위험 | `concurrencyPolicy: Forbid` | 이전 실행이 끝나기 전 새 실행을 막는다 |
| 최신 실행만 중요 | `concurrencyPolicy: Replace` | 오래 걸린 작업을 새 작업으로 대체한다 |
| 실패 재시도 | `backoffLimit` | 무한 재시도를 막는다 |
| 실행 누락 허용 범위 | `startingDeadlineSeconds` | 늦게 시작할 작업의 기준을 정한다 |
| 기록 관리 | history limit | 완료 Job이 계속 쌓이지 않게 한다 |

## 자주 나는 실수

- CronJob schedule만 설정하고 중복 실행 정책을 정하지 않는다.
- 배치 로직 자체의 멱등성을 고려하지 않는다.
- 실패한 Job 로그를 보관하지 않아 원인 분석이 어렵다.
- timezone을 확인하지 않고 schedule을 설정한다.
- Job 성공 여부만 보고 실제 처리 건수와 누락 건수를 보지 않는다.

## 확인 방법

- 명령: `kubectl get cronjob`, `kubectl get jobs`로 실행 상태를 확인한다.
- 명령: 실패한 Job의 Pod 로그와 event를 확인한다.
- 메트릭: 성공/실패 횟수, 처리 건수, 실행 시간, 재시도 횟수를 본다.
- 테스트: 같은 작업이 두 번 실행되어도 결과가 깨지지 않는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| Kubernetes 안에서 주기적 작업을 선언적으로 관리한다 | 복잡한 workflow orchestration에는 부족할 수 있다 |
| Job 단위로 성공/실패 기록을 남긴다 | 애플리케이션 수준 재처리 설계는 별도로 필요하다 |
| concurrencyPolicy로 겹침을 제어할 수 있다 | 로직 자체의 멱등성을 대체하지는 않는다 |

## 짧은 예제

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

중복 실행이 위험한 작업은 schedule보다 재처리 가능성과 멱등성을 먼저 설계해야 한다. 대상별 중복 방지와 lock 선택 기준은 [[duplicate-execution-prevention]]에서 다룬다.

## 핵심 요약

CronJob은 schedule에 맞춰 Job을 생성하는 Kubernetes 리소스다.

중복 실행 정책을 정하지 않으면 긴 작업이 다음 실행과 겹칠 수 있다.

실패 재시도는 `backoffLimit`으로 제한하고, 애플리케이션 수준 재처리 기준을 따로 둔다.

배치 작업은 성공/실패뿐 아니라 처리 건수와 누락 여부를 관측해야 한다.

timezone, history limit, 동시 실행 정책은 운영 장애를 줄이는 중요한 설정이다.

CronJob 설정은 멱등한 배치 로직을 대체하지 않으며, 데이터 정합성 보장은 배치 설계에서 한 번 더 다뤄야 한다.

## 꼬리 질문

- CronJob과 Job의 관계는 무엇인가?
- 배치 중복 실행을 어떻게 막을 것인가?
- 실패한 배치를 어디서부터 다시 처리할 수 있게 만들려면 무엇을 기록해야 하는가?

## 관련 문서

- [[kubernetes]]
- [[02-practical-backend/batch/batch-processing|batch-processing]]
- [[02-practical-backend/batch/duplicate-execution-prevention|duplicate-execution-prevention]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
