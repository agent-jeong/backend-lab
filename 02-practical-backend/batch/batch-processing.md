---
title: 배치 처리
description: 재처리 가능한 배치 처리 설계 학습 인덱스
tags: [batch]
comments: false
---

# 배치 처리

청크 처리, 대량 조회, 실패 상태와 재처리, 중복 실행 방지, 모니터링을 다룬다. 배치가 중간에 실패했을 때 어디서부터 다시 돌려야 데이터가 꼬이지 않는지가 이 폴더의 주제다.

## 읽는 순서

1. [[02-practical-backend/kubernetes/cronjob|CronJob]]: 정해진 시각에 배치를 띄우는 법
2. [[chunk-processing|Chunk 처리]]
3. [[retryable-batch-design|재처리 설계]]
4. [[batch-failure-state|실패 상태 관리]]
5. [[large-data-query|대용량 조회]]
6. [[duplicate-execution-prevention|중복 실행 방지]]
7. [[batch-monitoring|배치 모니터링]]

## 먼저 답해 볼 질문

- 배치가 중간에 실패하면 처음부터 다시 돌리나, 실패 지점부터 이어서 돌리나?
- 같은 배치를 두 번 실행해도 결과가 같으려면 무엇이 필요한가?
- chunk 크기는 무엇을 기준으로 정하나? 너무 크거나 작으면 어떤 문제가 생기나?
- 대량 조회에서 offset 페이징이 느려지는 이유와 대안은?
- 여러 인스턴스에서 같은 배치가 동시에 뜨는 것을 어떻게 막나?
- 배치가 "조용히" 실패하거나 평소보다 적게 처리한 것을 어떻게 알아채나?

## 실무에서 보는 것

- 배치는 정해진 시간에 대량 작업을 끝내는 일이다. 빨리 끝내는 것보다 실패 뒤 어디서부터 다시 시작할 수 있는지가 먼저다.
- 설명할 때도 처리량보다 다시 돌려도 안전한지, 데이터가 맞는지를 먼저 말한다.

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 멱등 지급 배치와 스케줄러 데드락
- [[file-storage-migration|첨부파일 18만 건 이관]]: 중복 실행 차단, 끊겨도 이어 가는 대량 작업
- [[inherited-access-system-incidents|이어받은 시스템의 장애 추적]]: 배치 시작 시각 충돌, 한 건이 전체를 멈추는 배치

## 관련 문서

- [[02-practical-backend/kubernetes/cronjob|cronjob]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
