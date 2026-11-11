---
title: "페이징과 대량 조회 전략"
description: 목록 API가 뒷페이지에서 느려지는 이유와, 수십만 건을 메모리 걱정 없이 읽는 법
tags: [concept, database]
---

# 페이징과 대량 조회 전략

페이징은 많은 데이터를 20건, 50건씩 나눠서 보여 주는 것이다. 대량 조회는 수십만~수백만 건을 애플리케이션 메모리도, DB도 버티게 나눠 읽는 방법이다.

주문 목록 API가 데이터가 쌓일수록 느려진다면 원인은 대개 셋 중 하나다. OFFSET이 커져서 뒷페이지가 느리거나, 요청마다 도는 `SELECT COUNT(*)`가 느리거나, 한 번에 너무 많이 가져와 메모리가 모자란다.

## OFFSET 페이징이 느린 이유

```sql
-- 1페이지: 빠름
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- 5000페이지: 느림
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
```

OFFSET 100000이면 DB는 100,020건을 읽고 앞의 100,000건을 버린다. OFFSET이 커질수록 버릴 행을 읽는 데 시간을 더 쓴다.

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

OFFSET 대신 마지막으로 본 항목의 값을 기준으로 그다음을 읽는다. 몇 번째 페이지든 속도가 같다. 대신 5페이지로 바로 건너뛰는 건 안 된다. 무한 스크롤 화면에 맞다.

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

화면에 페이지 번호가 꼭 있어야 할 때 쓴다. 서브쿼리는 커버링 인덱스로 ID만 빠르게 가져오고, 그 20건만 원본 테이블과 JOIN한다. OFFSET이 커도 건너뛰는 구간은 인덱스만 읽고 지나간다.

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

- 정확한 건수가 필요 없으면 "이전/다음" 버튼만 두고 전체 건수는 보여 주지 않는다.
- 정확한 건수가 필요하면 캐시해 두고 요청마다 다시 세지 않는다.

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

전체를 메모리에 올리지 않고 한 건씩 처리한다. 트랜잭션 안에서만 쓸 수 있고, 다 쓰고 나면 Stream을 닫아야 한다.

## 자주 깨지는 곳

- 데이터가 많은 테이블에 OFFSET 페이징을 쓰면, 뒷페이지로 갈수록 느려진다.
- 요청마다 `COUNT(*)`를 돌리면, 목록 API 전체가 COUNT 속도만큼 느려진다.
- 수십만 건을 `findAll()`로 한 번에 가져오면, OOM이 난다.
- 커서 페이징의 정렬 기준에 같은 값이 있으면, 페이지 경계에서 행이 빠진다. 그래서 `id` 같은 유일한 컬럼을 정렬에 같이 넣는다.
- Slice로 충분한데 늘 Page를 쓰면, 필요 없는 COUNT 쿼리가 매번 나간다.

## 한 번에 설명하기

> OFFSET 페이징은 앞의 행을 다 읽고 버리기 때문에 OFFSET이 커질수록 느려집니다.
>
> 그래서 무한 스크롤처럼 페이지 번호가 필요 없으면, 마지막 항목 값을 기준으로 읽는 커서 기반 페이징을 씁니다. 번호가 필요하면 커버링 인덱스 서브쿼리로 ID만 먼저 찾고 나머지를 붙입니다.
>
> `COUNT(*)`가 느리면 캐시하거나 전체 건수를 아예 안 보여 줍니다. 대량 처리는 Chunk나 Stream으로 나눠서 OOM을 막습니다.

## 꼬리 질문

> [!question]- 커서 기반 페이징의 단점은?
> 특정 페이지로 바로 건너뛸 수가 없습니다. "이전/다음" 버튼이나 무한 스크롤에는 잘 맞지만, 페이지 번호를 보여 줘야 하는 화면이면 OFFSET 방식을 써야 합니다.

> [!question]- Page와 Slice의 차이는?
> Page는 `COUNT(*)` 쿼리를 한 번 더 날려서 전체 건수와 전체 페이지 수까지 알려 줍니다. Slice는 COUNT 없이 다음 페이지가 있는지만 봅니다. 전체 건수가 필요 없으면 Slice가 더 빠릅니다.

> [!question]- OFFSET 페이징을 개선하는 방법은?
> 서브쿼리에서 커버링 인덱스로 ID만 먼저 가져오고, 그 ID로 원본 테이블과 JOIN합니다. 건너뛰는 구간을 인덱스만 읽고 지나가니까 빨라집니다.

> [!question]- 대용량 데이터를 JPA로 처리할 때 주의점은?
> 읽은 Entity가 영속성 컨텍스트에 다 쌓이면 메모리가 모자랍니다. 그래서 일정 건수마다 `flush()`와 `clear()`를 부르거나, 처음부터 Entity 대신 DTO로 읽습니다. `@Transactional(readOnly = true)`는 변경 감지용 스냅샷을 만들지 않아 조금 가벼워질 뿐, Entity가 쌓이는 것까지 막지는 못합니다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: `ROW_NUMBER()` 페이징을 `LIMIT/OFFSET`으로

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]
