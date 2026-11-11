---
title: 실패 상태 관리
description: 배치가 실패했을 때 다시 돌릴지 손으로 고칠지 정할 수 있게 상태를 남기는 방법
tags: [concept, batch]
---

# 실패 상태 관리

실패 상태 관리는 배치 작업마다 성공했는지, 실패했는지, 다시 시도해도 되는지, 왜 실패했는지를 적어 두는 일이다.

이 기록은 읽고 넘기는 로그가 아니다. 포인트 지급 배치가 새벽에 실패했다면, 아침에 이 기록을 보고 다시 돌릴지 손으로 보정할지 정한다.

## 상태를 어떻게 나누나

성공/실패 boolean 하나로는 모자란다. 처리 상태와 실패 사유를 따로 둔다.

| 상태 | 의미 |
|---|---|
| pending | 아직 처리 전 |
| processing | 처리 중 |
| completed | 처리 완료 |
| failed_retryable | 다시 시도해도 되는 실패 |
| failed_final | 사람이 확인하거나 보정해야 함 |

상태와 함께 실패 사유, 재시도 횟수, 마지막 시도 시각을 남긴다. 재시도 횟수와 마지막 시도 시각이 있어야 같은 실패가 끝없이 되풀이되는 것을 끊는다.

## 자주 깨지는 곳

- 실패를 boolean 하나로만 저장하면, 두 번 처리된 건과 빠진 건을 구분할 수 없다.
- 실패 사유와 stack trace를 남기지 않으면, 다시 돌릴지 손으로 보정할지 정할 근거가 없다.
- processing에서 멈춘 작업을 되살릴 기준이 없으면, 그 작업은 계속 처리 중으로 남는다. 일정 시간이 지나면 멈춘 것으로 보는 timeout 기준을 둔다.
- 재시도 횟수와 마지막 시도 시각을 남기지 않으면 재시도 상한을 걸 수 없어서, 같은 실패가 반복된다.
- 실패 알림에 어떤 대상을 처리하다 실패했는지 없으면, 그걸 찾느라 복구가 늦어진다.

## 운영에서 볼 것

- 운영자가 실패한 작업 목록과 실패 이유를 조회할 수 있는지 확인한다.
- 오래 머문 processing 상태를 감지할 수 있는지 확인한다.
- 재시도 횟수를 넘기면 final 실패로 바뀌는지 테스트한다.

## 한 번에 설명하기

> 배치 실패 상태는 다시 돌릴지 말지 정하려고 남기는 데이터라고 봅니다.
>
> 그래서 성공/실패 boolean 대신 pending, processing, completed, 재시도 가능 실패, 최종 실패로 나누고 실패 사유를 같이 남깁니다.
>
> processing에서 멈춘 작업은 timeout 기준으로 되살리고, 재시도 횟수와 마지막 시도 시각으로 같은 실패가 반복되는 걸 끊습니다.

## 꼬리 질문

- 배치 상태는 어떤 값으로 나누나?
- processing에서 멈춘 작업은 어떻게 복구하나?
- 실패 사유는 어디까지 저장하나?

## 내 사례

- [[inherited-access-system-incidents|이어받은 시스템의 장애 추적]]: 한 건 오류가 배치 전체를 멈춘 사례

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Batch: Configuring a Job (restartability)](https://docs.spring.io/spring-batch/reference/job/configuring-job.html)
- [Spring Batch: The Domain Language of Batch](https://docs.spring.io/spring-batch/reference/domain.html)

## 관련 문서

- [[batch-processing]]
- [[retryable-batch-design]]
- [[batch-monitoring]]
