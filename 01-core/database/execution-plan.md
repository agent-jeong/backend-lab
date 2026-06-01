---
title: Execution Plan
description: 실행 계획의 읽는 방법과 성능 분석 기준
---

# Execution Plan

## 한 줄 정의

실행 계획은 쿼리를 DB가 어떻게 실행할지 보여주는 분석 결과로, 인덱스 사용 여부, 접근 방식, 예상 비용을 확인할 수 있다.

## 실무에서 왜 중요한가

실행 계획을 읽지 못하면 다음 상황에서 원인을 찾을 수 없다.

- 인덱스를 걸었는데 쿼리가 여전히 느리다.
- 같은 테이블인데 쿼리마다 성능이 크게 다르다.
- 어떤 인덱스가 실제로 사용되는지 모른다.
- 쿼리 튜닝을 "감"으로 한다.

## EXPLAIN 사용법

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 1 AND status = 'COMPLETED';
```

```
+----+------+-------+------+----------+-------------+
| id | type | table | key  | rows     | Extra       |
+----+------+-------+------+----------+-------------+
|  1 | ref  | orders| idx_user_status | 15 | Using where |
+----+------+-------+------+----------+-------------+
```

## 핵심 확인 항목

### type (접근 방식)

성능에 가장 큰 영향을 준다. 위에서 아래로 갈수록 느리다.

| type | 의미 | 성능 |
|---|---|---|
| `const` | PK 또는 UNIQUE로 1건 조회 | 최고 |
| `eq_ref` | JOIN에서 PK/UNIQUE로 1건 매칭 | 매우 좋음 |
| `ref` | 인덱스로 여러 건 조회 | 좋음 |
| `range` | 인덱스 범위 스캔 (BETWEEN, >, <) | 보통 |
| `index` | 인덱스 전체 스캔 (Full Index Scan) | 느림 |
| `ALL` | 테이블 전체 스캔 (Full Table Scan) | 최악 |

**`ALL`이 나오면 반드시 인덱스 추가를 검토**한다.

### key

실제로 사용된 인덱스 이름이다. `NULL`이면 인덱스를 사용하지 않은 것이다.

### rows

DB가 예상하는 스캔 행 수다. 실제 값이 아니라 통계 기반 추정치다. 값이 클수록 비용이 높다.

### Extra

| 값 | 의미 |
|---|---|
| `Using index` | 커버링 인덱스 (테이블 접근 없음) |
| `Using where` | WHERE 조건으로 필터링 |
| `Using filesort` | 인덱스로 정렬 불가, 별도 정렬 수행 |
| `Using temporary` | 임시 테이블 사용 (GROUP BY, DISTINCT 등) |

**`Using filesort`와 `Using temporary`가 함께 나오면 성능 개선이 필요**하다.

## 실무 분석 예시

```sql
-- 느린 쿼리
EXPLAIN SELECT * FROM orders
WHERE status = 'COMPLETED'
ORDER BY created_at DESC
LIMIT 20;
```

```
type: ALL | key: NULL | rows: 500000 | Extra: Using where; Using filesort
```

**문제**: Full Table Scan + 별도 정렬

```sql
-- 인덱스 추가 후
CREATE INDEX idx_status_created ON orders (status, created_at);

EXPLAIN SELECT * FROM orders
WHERE status = 'COMPLETED'
ORDER BY created_at DESC
LIMIT 20;
```

```
type: ref | key: idx_status_created | rows: 20 | Extra: Using where; Backward index scan
```

**개선**: 인덱스로 조건 필터 + 정렬까지 처리. `Backward index scan`은 인덱스를 역순으로 스캔하는 것으로, DESC 정렬에서도 인덱스를 활용하고 있다는 의미다.

## EXPLAIN ANALYZE (MySQL 8.0+)

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
```

`EXPLAIN`은 예상치이고, `EXPLAIN ANALYZE`는 **실제 실행 결과**를 보여준다. 실제 행 수, 실행 시간, 루프 횟수를 확인할 수 있다.

## 자주 나는 실수

- EXPLAIN 없이 인덱스를 추가하고 "빨라졌겠지"라고 가정한다.
- `type: ALL`을 무시하고 넘어간다.
- `Using filesort`가 나오는데 ORDER BY에 맞는 인덱스를 만들지 않는다.
- rows 값이 예상보다 큰데 원인을 분석하지 않는다.
- EXPLAIN의 rows가 추정치인 것을 모르고 정확한 값으로 믿는다.

## 핵심 요약

실행 계획은 `EXPLAIN`으로 확인하며, `type`, `key`, `rows`, `Extra`를 중심으로 읽습니다.
`type: ALL`은 Full Table Scan이므로 인덱스 추가를 검토하고, `Using filesort`는 정렬용 인덱스가 필요합니다.

`EXPLAIN ANALYZE`(MySQL 8.0+)는 실제 실행 결과를 보여주므로 더 정확한 분석이 가능합니다.
쿼리 튜닝은 반드시 실행 계획을 먼저 확인하고 진행해야 합니다.

## 꼬리 질문

> [!question]- type이 ALL인데 인덱스가 있는 이유는?
> 옵티마이저가 인덱스보다 Full Table Scan이 더 빠르다고 판단한 경우입니다. 조건에 해당하는 데이터가 전체의 상당 부분이면 인덱스를 거치는 비용이 더 클 수 있습니다.

> [!question]- Using filesort는 항상 나쁜가?
> 소량 데이터의 정렬은 문제가 안 됩니다. 대용량 데이터에서 `Using filesort`가 나오면 디스크 기반 정렬이 발생할 수 있어서 인덱스로 해결하는 것이 좋습니다.

> [!question]- EXPLAIN의 rows와 실제 행 수가 다른 이유는?
> rows는 테이블 통계(cardinality) 기반 추정치입니다. 통계가 오래되었거나 데이터 분포가 불균일하면 실제와 차이가 납니다. `ANALYZE TABLE`로 통계를 갱신할 수 있습니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[join]]