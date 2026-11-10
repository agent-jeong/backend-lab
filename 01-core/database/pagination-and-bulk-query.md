---
title: "페이징과 대량 조회 전략"
description: 페이징 처리와 대용량 조회의 성능 문제와 해결
tags: [concept, database]
---

# 페이징과 대량 조회 전략

페이징은 많은 데이터를 일정 단위로 나눠 조회하는 것이다. 대용량 조회는 수십만~수백만 건을 메모리와 DB를 터뜨리지 않고 처리하는 방법이다.

목록 API가 데이터가 늘수록 느려진다면 원인은 대개 셋 중 하나다. OFFSET이 커져서 뒷페이지가 느리거나, 매 요청 `SELECT COUNT(*)`가 병목이거나, 한 번에 너무 많이 가져와 메모리가 모자란다.

## OFFSET 페이징이 느린 이유

```sql
-- 1페이지: 빠름
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- 5000페이지: 느림
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
```

OFFSET 100000이면 DB는 100,020건을 읽고 앞의 100,000건을 버린다. OFFSET이 커질수록 버리려고 읽는 양이 늘어난다.

## 대안 1: 커서 기반 페이징 (No-Offset)

```sql
-- 첫 페이지
SELECT * FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- 다음 페이지: 마지막 항목의 값을 기준으로 조회
SELECT * FROM orders
WHERE (created_at, id) < ('2024-06-01 10:00:00', 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

OFFSET 대신 마지막으로 본 항목의 값을 기준으로 다음 페이지를 읽는다. 몇 번째 페이지든 속도가 같다. 대신 "5페이지로 바로 이동"은 안 된다. 무한 스크롤 UI에 맞다.

## 대안 2: 커버링 인덱스 + 서브쿼리

```sql
-- OFFSET 페이징이 필요한 경우 개선
SELECT o.*
FROM orders o
JOIN (
    SELECT id FROM orders
    ORDER BY created_at DESC
    LIMIT 20 OFFSET 100000
) sub ON o.id = sub.id;
```

페이지 번호 UI가 꼭 필요할 때 쓴다. 서브쿼리가 커버링 인덱스로 ID만 빠르게 가져오고, 그 20건만 원본 테이블과 JOIN한다. OFFSET이 커도 건너뛰는 구간은 인덱스만 읽는다.

## COUNT 줄이기

```sql
-- 느림: 전체 건수 정확히 계산
SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED';

-- 대안 1: 대략적 건수 (매우 빠름)
EXPLAIN SELECT * FROM orders WHERE status = 'COMPLETED';
-- → rows 값으로 대략적인 건수 추정

-- 대안 2: 건수 캐싱
-- 전체 건수를 별도 테이블이나 Redis에 캐시하고 주기적으로 갱신
```

- 정확한 건수가 필요 없으면 "이전/다음" 버튼만 두고 전체 건수를 뺀다.
- 정확한 건수가 필요하면 캐싱해서 매 요청마다 계산하지 않는다.

## 대용량 데이터 처리

### Chunk 단위 조회

```java
// Spring Data JPA: Slice 사용 (COUNT 쿼리 없음)
Slice<Order> slice = orderRepository.findByStatus("COMPLETED", PageRequest.of(0, 1000));

while (slice.hasNext()) {
    process(slice.getContent());
    slice = orderRepository.findByStatus("COMPLETED", slice.nextPageable());
}
```

### Stream 조회

```java
@Transactional(readOnly = true)
@QueryHints(@QueryHint(name = HINT_FETCH_SIZE, value = "1000"))
@Query("SELECT o FROM Order o WHERE o.status = :status")
Stream<Order> findByStatusAsStream(@Param("status") String status);
```

전체를 메모리에 올리지 않고 한 건씩 처리한다. 트랜잭션 안에서만 쓸 수 있고, 다 쓰면 Stream을 닫아야 한다.

## 자주 깨지는 곳

- **대량 데이터에 OFFSET 페이징을 쓴다.** 뒷페이지로 갈수록 느려진다.
- **매 요청 `COUNT(*)`를 실행한다.** 목록 API 전체가 COUNT 속도에 묶인다.
- **수십만 건을 `findAll()`로 한 번에 가져온다.** OOM이 난다.
- **커서 페이징의 정렬 기준이 유일하지 않다.** 같은 값을 가진 행이 페이지 경계에서 빠진다. 그래서 `id` 같은 유일 컬럼을 정렬에 같이 넣는다.
- **Slice로 충분한데 항상 Page를 쓴다.** 필요 없는 COUNT 쿼리가 매번 나간다.

## 면접에서 말하기

> OFFSET 페이징은 앞의 행을 다 읽고 버리기 때문에 OFFSET이 커질수록 느려집니다. 그래서 저는 무한 스크롤처럼 페이지 번호가 필요 없으면 마지막 항목 값을 기준으로 읽는 커서 기반 페이징을 쓰고, 번호가 필요하면 커버링 인덱스 서브쿼리로 ID만 먼저 찾습니다. `COUNT(*)`가 병목이면 캐싱하거나 전체 건수 표시를 뺍니다. 대량 처리는 Chunk나 Stream으로 나눠 OOM을 막습니다.

## 꼬리 질문

> [!question]- 커서 기반 페이징의 단점은?
> 특정 페이지로 바로 이동할 수 없습니다. "이전/다음" 또는 무한 스크롤 UI에 적합하고, 페이지 번호가 필요한 UI에서는 OFFSET 기반을 사용해야 합니다.

> [!question]- Page와 Slice의 차이는?
> Page는 `COUNT(*)` 쿼리를 추가로 실행해서 전체 건수와 전체 페이지 수를 제공합니다. Slice는 COUNT 없이 다음 페이지 존재 여부만 확인합니다. 전체 건수가 필요 없으면 Slice가 성능상 유리합니다.

> [!question]- OFFSET 페이징을 개선하는 방법은?
> 커버링 인덱스 + 서브쿼리 방식으로 ID만 빠르게 가져온 뒤 원본 테이블과 JOIN합니다. OFFSET 범위를 인덱스만으로 처리할 수 있어 성능이 개선됩니다.

> [!question]- 대용량 데이터를 JPA로 처리할 때 주의점은?
> 영속성 컨텍스트에 모든 Entity가 쌓이면 메모리 부족이 발생합니다. 일정 건수마다 `flush()`와 `clear()`를 호출하거나, `@Transactional(readOnly = true)`로 변경 감지를 생략해야 합니다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: `ROW_NUMBER()` 페이징을 `LIMIT/OFFSET`으로

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]
