---
title: 대용량 조회
description: 배치에서 많은 데이터를 빠짐없이, 두 번 읽지 않고 끝까지 읽는 방법
tags: [concept, batch]
---

# 대용량 조회

배치의 대용량 조회는 많은 데이터를 나눠 읽는 일이다. 메모리와 DB 부하를 버티는지, 정렬이 흔들리지 않는지, 중간에 끊겨도 다시 시작할 수 있는지를 따진다.

정산 배치가 주문 수백만 건을 읽는다면, 빨리 읽는 것보다 한 건도 빠뜨리지 않고 두 번 읽지 않으면서 끝까지 도는 게 먼저다.

## 상황별 선택

| 상황 | 선택 |
|---|---|
| 큰 목록 순차 처리 | keyset pagination |
| 정렬 기준 필요 | unique하고 증가하는 key |
| 읽기 전용 대량 처리 | stream/cursor 검토 |
| 재시작 필요 | 마지막 처리 key 저장 |

keyset 방식은 마지막으로 처리한 key 다음부터 읽는다. 그 key를 저장해 두면 실패한 뒤 거기서부터 다시 시작할 수 있다. 정렬 기준은 순서가 흔들리지 않아야 하고 unique해야 한다. unique하지 않은 컬럼이면 같은 값이 chunk 경계에 걸릴 때 행이 빠지므로, `(created_at, id)`처럼 id를 뒤에 붙여 순서를 하나로 정한다.

## 자주 깨지는 곳

- 전체 데이터를 한 번에 올리면, OOM이 나거나 GC가 길어진다.
- offset pagination으로 배치 전체를 돌면, 뒤 페이지로 갈수록 scan 비용이 커지고, 처리 중에 데이터가 바뀌면 빠지거나 두 번 읽는 행이 생긴다.
- 정렬 조건 없이 limit만 쓰면, 순서가 흔들려 같은 데이터를 여러 번 읽거나 빠뜨린다.
- `select *`로 필요 없는 컬럼까지 읽으면, 그만큼 메모리와 네트워크를 더 쓴다.
- count query 비용을 무시하면, 목록 조회는 빠른데 전체 건수를 세다가 느려진다.

## 확인하는 법

- 실행 계획에서 scan row, index 사용, filesort 여부를 본다.
- 처리 중에 데이터가 추가되거나 수정돼도 빠지는 행이 없는지 테스트한다.
- 메모리 사용량과 fetch size를 확인한다.

## 한 번에 설명하기

> 배치에서 많은 데이터를 읽을 때는 빨리 읽는 것보다 빠짐없이 끝까지 도는 게 먼저입니다.
>
> offset은 데이터가 많을수록 느려지고, 처리 중에 데이터가 바뀌면 빠지거나 두 번 읽는 행이 생깁니다. 그래서 unique한 key 기준 keyset으로 읽고, 마지막으로 처리한 key를 저장해 다시 시작할 지점으로 씁니다.
>
> 필요한 컬럼만 읽고, 실행 계획으로 비용을 확인합니다.

## 꼬리 질문

- Batch에서 offset pagination이 위험한 이유는?
- 마지막 처리 위치는 무엇으로 저장하나?
- Stream 조회와 chunk 조회는 어떻게 고르나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Batch: Item Readers](https://docs.spring.io/spring-batch/reference/readers-and-writers/item-reader.html)
- [MySQL 8.4: LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)

## 관련 문서

- [[batch-processing]]
- [[chunk-processing]]
- [[pagination-and-bulk-query]]
