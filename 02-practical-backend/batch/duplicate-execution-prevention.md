---
title: 중복 실행 방지
description: 같은 배치가 두 번 돌아도 같은 대상을 두 번 처리하지 않게 막는 방법
tags: [concept, batch]
---

# 중복 실행 방지

중복 실행 방지는 같은 배치가 동시에, 또는 여러 번 돌아도 같은 대상을 두 번 처리하지 않게 막는 일이다.

배치는 스케줄이 겹치거나, 서버가 여러 대이거나, 누군가 손으로 다시 돌려서 언제든 두 번 돈다. 포인트 지급 배치가 두 번 돌면 포인트가 두 번 나간다. 그래서 lock 하나로 끝내지 않고, 대상 데이터 쪽에서도 한 번 더 막는다.

## 언제 두 번 도나

- 스케줄이 겹친다. 이전 실행이 안 끝났는데 다음 실행이 시작된다.
- 서버가 여러 대라 인스턴스마다 같은 배치를 실행한다.
- 이전 실행이 비정상 종료돼 lock이나 processing 상태가 남은 채로 재실행된다.

## 어떻게 막나

| 상황 | 선택 |
|---|---|
| Kubernetes CronJob | `concurrencyPolicy` |
| 단일 스케줄러 | 실행 중 플래그 또는 스케줄러 옵션 |
| 다중 인스턴스 | DB lock 또는 distributed lock |
| 대상별 중복 방지 | unique constraint |
| 재실행 허용 | 멱등한 상태 전이 |

스케줄러 정책과 lock은 두 번 실행되는 일 자체를 줄인다. 하지만 그것만으로 데이터가 맞는다고 장담할 수는 없다. 대상마다 처리 결과는 unique 제약이나 상태 전이로 한 번 더 막는다.

## 자주 깨지는 곳

- scheduler가 딱 한 번만 실행해 줄 거라고 믿으면, 위에 적은 경우 중 하나로 두 번 돌 때 막을 장치가 없다.
- lock TTL을 작업 시간보다 짧게 두면, 작업 도중 lock이 풀려 다른 인스턴스가 같은 작업을 시작한다.
- lock을 못 잡은 걸 성공처럼 처리하면, 돌지도 않은 배치가 성공으로 기록된다.
- lock만 믿고 로직 자체를 멱등하게 짜지 않으면, lock이 한 번 실패하는 순간 데이터가 깨진다.
- 비정상 종료 뒤 남은 lock과 processing 상태를 되살릴 기준이 없으면, 다음 실행이 막히거나 사람이 손대야 한다.

## 확인하는 법

- 같은 배치를 동시에 두 번 실행해도 결과가 깨지지 않는지 본다.
- lock 만료, 프로세스 종료, 재시작 상황을 테스트한다.
- unique 제약이나 상태 전이가 중복 결과를 막는지 확인한다.

## 한 번에 설명하기

> 배치는 스케줄이 겹치거나, 서버가 여러 대이거나, 손으로 다시 돌려서 두 번 실행될 수 있다고 보고 짭니다.
>
> 스케줄러 정책이나 lock으로 두 번 도는 일을 줄이지만, lock만으로 데이터가 맞는다고 장담할 수는 없습니다. 그래서 대상마다 결과는 unique 제약이나 상태 전이로 한 번 더 막습니다.
>
> lock TTL은 작업 시간보다 길게 잡고, 비정상 종료 뒤 남은 lock과 processing 상태를 되살리는 기준도 둡니다.

## 꼬리 질문

- 배치 중복 실행은 어떤 상황에서 생기나?
- Distributed lock만으로 충분하지 않은 이유는?
- 중복 실행 테스트는 어떻게 하나?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 두 번 돌아도 한 번만 지급
- [[file-storage-migration|첨부파일 18만 건 이관]]: `flock`으로 중복 실행 막기

## 참고

2026년 11월에 확인한 공식 문서다.

- [ShedLock](https://github.com/lukas-krecan/ShedLock)
- [Kubernetes: CronJob concurrencyPolicy](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)

## 관련 문서

- [[batch-processing]]
- [[distributed-lock]]
- [[unique-constraint-and-state-transition]]
- [[02-practical-backend/kubernetes/cronjob|cronjob]]
