---
title: Pagination And Bulk Query
description: 페이징 처리와 대용량 조회의 성능 문제와 해결
---

# Pagination And Bulk Query

## 한 줄 정의

페이징은 대량 데이터를 일정 단위로 나눠서 조회하는 것이고, 대용량 조회는 수십만~수백만 건의 데이터를 효율적으로 처리하는 전략이다.

## 실무에서 왜 중요한가

페이징과 대용량 조회를 잘못하면 다음 문제가 생긴다.

- OFFSET이 커질수록 페이지 로딩이 느려진다.
- `SELECT COUNT(*)`가 느려서 전체 건수 조회가 병목이 된다.
- 대량 데이터를 한 번에 가져와서 메모리가 부족해진다.
- 목록 API 응답 시간이 데이터가 늘수록 느려진다.

## OFFSET 기반 페이징의 문제

```sql
-- 1페이지: 빠름
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- 5000페이지: 느림
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
```

OFFSET 100000이면 DB가 100,020건을 읽고 앞의 100,000건을 버린다. **OFFSET이 커질수록 불필요한 읽기가 늘어나서 느려진다.**

## 해결 방법 1: 커서 기반 페이징 (No-Offset)

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

- OFFSET을 사용하지 않고 마지막 조회 항목의 값을 기준으로 다음 페이지를 조회한다.
- 몇 번째 페이지든 동일한 성능이다.
- **단점**: "5페이지로 바로 이동"이 불가능하다. 무한 스크롤 UI에 적합하다.

## 해결 방법 2: 커버링 인덱스 + 서브쿼리

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

서브쿼리에서 커버링 인덱스로 ID만 빠르게 가져온 뒤, 원본 테이블과 JOIN한다. OFFSET이 커도 인덱스만 스캔하므로 성능이 개선된다.

## COUNT 최적화

```sql
-- 느림: 전체 건수 정확히 계산
SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED';

-- 대안 1: 대략적 건수 (매우 빠름)
EXPLAIN SELECT * FROM orders WHERE status = 'COMPLETED';
-- → rows 값으로 대략적인 건수 추정

-- 대안 2: 건수 캐싱
-- 전체 건수를 별도 테이블이나 Redis에 캐시하고 주기적으로 갱신
```

- 정확한 COUNT가 필요 없으면 "이전/다음" 버튼만 제공하고 전체 건수를 생략한다.
- 정확한 COUNT가 필요하면 캐싱해서 매 요청마다 계산하지 않는다.

## 대용량 데이터 처리

### 배치 조회 (Chunk 처리)

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

전체 데이터를 메모리에 올리지 않고 한 건씩 처리한다. 반드시 트랜잭션 안에서 사용해야 하며, 처리 후 Stream을 닫아야 한다.

## 자주 나는 실수

- 대량 데이터에 OFFSET 기반 페이징을 사용해서 뒷페이지가 느리다.
- 매 요청마다 `COUNT(*)`를 실행해서 목록 API가 느리다.
- 수십만 건을 한 번에 `findAll()`로 가져와서 OOM이 발생한다.
- 커서 기반 페이징에서 정렬 기준이 유일하지 않아서 데이터가 누락된다.
- Slice와 Page의 차이를 모르고 항상 Page를 사용한다.

## 핵심 요약

OFFSET 기반 페이징은 OFFSET이 커질수록 느려집니다.
커서 기반 페이징(No-Offset)은 마지막 항목의 값을 기준으로 조회해서 일정한 성능을 유지합니다.

`COUNT(*)`가 병목이면 건수를 캐싱하거나 전체 건수 표시를 생략합니다.
대용량 데이터는 한 번에 가져오지 않고 Chunk 단위나 Stream으로 처리해야 OOM을 방지할 수 있습니다.

## 꼬리 질문

> [!question]- 커서 기반 페이징의 단점은?
> 특정 페이지로 바로 이동할 수 없습니다. "이전/다음" 또는 무한 스크롤 UI에 적합하고, 페이지 번호가 필요한 UI에서는 OFFSET 기반을 사용해야 합니다.

> [!question]- Page와 Slice의 차이는?
> Page는 `COUNT(*)` 쿼리를 추가로 실행해서 전체 건수와 전체 페이지 수를 제공합니다. Slice는 COUNT 없이 다음 페이지 존재 여부만 확인합니다. 전체 건수가 필요 없으면 Slice가 성능상 유리합니다.

> [!question]- OFFSET 페이징을 개선하는 방법은?
> 커버링 인덱스 + 서브쿼리 방식으로 ID만 빠르게 가져온 뒤 원본 테이블과 JOIN합니다. OFFSET 범위를 인덱스만으로 처리할 수 있어 성능이 개선됩니다.

> [!question]- 대용량 데이터를 JPA로 처리할 때 주의점은?
> 영속성 컨텍스트에 모든 Entity가 쌓이면 메모리 부족이 발생합니다. 일정 건수마다 `flush()`와 `clear()`를 호출하거나, `@Transactional(readOnly = true)`로 변경 감지를 생략해야 합니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]