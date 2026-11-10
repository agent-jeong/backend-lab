---
title: "실행 계획(EXPLAIN) 읽는 법"
description: 실행 계획의 읽는 방법과 성능 분석 기준
---

# 실행 계획(EXPLAIN) 읽는 법

실행 계획은 DB가 쿼리를 어떻게 실행할지 보여 주는 분석 결과다. 인덱스를 쓰는지, 어떤 방식으로 접근하는지, 몇 행을 읽을 것으로 보는지가 나온다.

실행 계획을 못 읽으면 튜닝을 감으로 하게 된다. 인덱스를 걸었는데 여전히 느린 이유, 같은 테이블인데 쿼리마다 속도가 다른 이유, 실제로 어떤 인덱스가 쓰이는지를 알 수 없다.

## 사용법

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

## 먼저 볼 컬럼

### type: 접근 방식

성능에 가장 크게 영향을 준다. 아래로 갈수록 느리다.

| type | 의미 | 성능 |
|---|---|---|
| `const` | PK 또는 UNIQUE로 1건 조회 | 최고 |
| `eq_ref` | JOIN에서 PK/UNIQUE로 1건 매칭 | 매우 좋음 |
| `ref` | 인덱스로 여러 건 조회 | 좋음 |
| `range` | 인덱스 범위 스캔 (BETWEEN, >, <) | 보통 |
| `index` | 인덱스 전체 스캔 (Full Index Scan) | 느림 |
| `ALL` | 테이블 전체 스캔 (Full Table Scan) | 최악 |

`ALL`이 나오면 인덱스 추가부터 검토한다.

### key

실제로 쓴 인덱스 이름이다. `NULL`이면 인덱스를 쓰지 않았다.

### rows

DB가 예상하는 스캔 행 수다. 실제 값이 아니라 통계 기반 추정치다. 클수록 비용이 크다.

### Extra

| 값 | 의미 |
|---|---|
| `Using index` | 커버링 인덱스 (테이블 접근 없음) |
| `Using where` | WHERE 조건으로 필터링 |
| `Using filesort` | 인덱스로 정렬 불가, 별도 정렬 수행 |
| `Using temporary` | 임시 테이블 사용 (GROUP BY, DISTINCT 등) |

`Using filesort`와 `Using temporary`가 같이 나오면 손볼 쿼리다.

## 분석 예시

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

Full Table Scan에 별도 정렬까지 한다.

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

이제 인덱스가 조건 필터와 정렬을 모두 처리한다. `Backward index scan`은 인덱스를 역순으로 읽는다는 뜻이다. DESC 정렬에도 인덱스를 쓰고 있다.

## EXPLAIN ANALYZE (MySQL 8.0+)

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
```

`EXPLAIN`은 예상치를, `EXPLAIN ANALYZE`는 쿼리를 실제로 실행한 결과를 보여 준다. 실제 행 수, 실행 시간, 루프 횟수가 나온다.

## 자주 깨지는 곳

- **EXPLAIN 없이 인덱스를 추가하고 빨라졌다고 가정한다.** 옵티마이저가 그 인덱스를 안 고를 수도 있다.
- **`type: ALL`을 보고도 넘어간다.** 데이터가 늘면 그대로 느려진다.
- **`Using filesort`가 나오는데 ORDER BY에 맞는 인덱스를 만들지 않는다.**
- **rows가 예상보다 큰데 원인을 보지 않는다.**
- **rows를 정확한 값으로 믿는다.** 통계 기반 추정치라 실제와 다르다.

## 면접에서 말하기

> 실행 계획은 `EXPLAIN`으로 보고, `type`, `key`, `rows`, `Extra` 순서로 읽습니다. `type`이 `ALL`이면 Full Table Scan이라 인덱스를 검토하고, `Using filesort`가 나오면 정렬에 맞는 인덱스가 필요한지 봅니다. `rows`는 추정치라서, 정확한 수치가 필요하면 MySQL 8.0 이상에서 `EXPLAIN ANALYZE`로 실제 실행 결과를 확인합니다.

## 꼬리 질문

> [!question]- type이 ALL인데 인덱스가 있는 이유는?
> 옵티마이저가 인덱스보다 Full Table Scan이 더 빠르다고 판단한 경우입니다. 조건에 해당하는 데이터가 전체의 상당 부분이면 인덱스를 거치는 비용이 더 클 수 있습니다.

> [!question]- Using filesort는 항상 나쁜가?
> 소량 데이터의 정렬은 문제가 안 됩니다. 대용량 데이터에서 `Using filesort`가 나오면 디스크 기반 정렬이 발생할 수 있어서 인덱스로 해결하는 것이 좋습니다.

> [!question]- EXPLAIN의 rows와 실제 행 수가 다른 이유는?
> rows는 테이블 통계(cardinality) 기반 추정치입니다. 통계가 오래되었거나 데이터 분포가 불균일하면 실제와 차이가 납니다. `ANALYZE TABLE`로 통계를 갱신할 수 있습니다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 풀 스캔을 실행계획으로 찾은 과정

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[join]]
