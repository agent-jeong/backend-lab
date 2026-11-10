---
title: 재처리 설계
description: 실패한 배치를 안전하게 다시 실행하기 위한 상태와 멱등성 기준
tags: [concept, batch]
---

# 재처리 설계

재처리 설계는 배치가 중간에 실패해도 어디까지 끝났고 무엇이 실패했는지를 기준으로 다시 돌릴 수 있게 만드는 일이다. 재처리는 장애가 났을 때 정하는 운영 절차가 아니라 처음부터 넣어야 하는 설계 요구사항이다.

기준이 없으면 실패할 때마다 처음부터 다시 돌리거나, 수동 DB 수정과 임시 스크립트로 메우게 된다.

## 단위별 설계

| 상황 | 설계 |
|---|---|
| row 단위 작업 | 대상별 처리 상태 저장 |
| chunk 단위 작업 | chunk checkpoint 저장 |
| 외부 호출 포함 | idempotency key와 결과 기록 |
| 실패 원인 분류 | retryable/non-retryable 구분 |

이미 끝난 작업은 다시 돌 때 건너뛰거나, 다시 해도 같은 결과로 수렴해야 한다. 그렇지 않으면 중복 알림, 중복 정산, 중복 상태 변경이 생긴다. 외부 API 호출이 끼면 내부 상태만으로는 완료 여부를 알 수 없으니 idempotency key와 결과 확인이 필요하다.

## 자주 깨지는 곳

- **배치 전체 성공/실패만 기록한다.** 실패 지점을 몰라 처음부터 다시 돌려야 한다.
- **실패한 데이터를 다시 찾을 기준을 남기지 않는다.**
- **재실행해도 같은 결과로 수렴하는지 테스트하지 않는다.**
- **실패 사유 없이 `failed` 상태만 남긴다.** 재시도할 실패인지 사람이 볼 실패인지 구분할 수 없다.

## 확인하는 법

- 중간 실패를 일부러 만들고 재실행 결과를 확인한다.
- 같은 batch를 두 번 실행해도 결과가 깨지지 않는지 본다.
- 실패 사유, 재시도 횟수, 마지막 처리 시각이 남는지 확인한다.

## 한 번에 설명하기

> 재처리 가능한 배치는 실패 지점과 처리 상태를 남깁니다. 저는 이미 끝난 작업은 건너뛰거나 다시 해도 같은 결과가 나오게 만들고, 실패는 재시도 가능한 것과 불가능한 것으로 나눕니다. 외부 API가 끼면 idempotency key와 결과 기록으로 중복을 막습니다. 재처리는 운영 절차가 아니라 설계 요구사항으로 다룹니다.

## 꼬리 질문

- 실패한 배치를 어디서부터 다시 시작하나?
- 재처리 때 중복 처리를 어떻게 막나?
- retryable 실패와 non-retryable 실패를 어떻게 구분하나?

## 내 사례

- [[file-storage-migration|첨부파일 18만 건 이관]]: 중간에 멈춰도 남은 것만 다시 옮기기

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Spring Batch: Retry](https://docs.spring.io/spring-batch/reference/retry.html)
- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

## 관련 문서

- [[batch-processing]]
- [[batch-failure-state]]
- [[idempotency]]
