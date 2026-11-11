---
title: "실행 계획(EXPLAIN) 읽는 법"
description: EXPLAIN 결과에서 무엇부터 보고, 느린 쿼리를 어떻게 찾는지
tags: [concept, database]
---

# 실행 계획(EXPLAIN) 읽는 법

실행 계획은 DB가 쿼리를 어떻게 처리할지 미리 보여 주는 결과다. 인덱스를 쓰는지, 테이블에 어떻게 접근하는지, 몇 행쯤 읽을 것 같은지가 나온다.

주문 목록 조회가 갑자기 느려졌을 때 실행 계획을 못 읽으면 감으로 인덱스를 추가하게 된다. 인덱스를 걸었는데 왜 여전히 느린지, 같은 테이블인데 쿼리마다 왜 속도가 다른지, 실제로 어떤 인덱스를 쓰는지는 실행 계획을 봐야 안다.

## 사용법

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 1 AND status = 'COMPLETED';
```

```
+----+-------+--------+-----------------+------+-------------+
| id | type  | table  | key             | rows | Extra       |
+----+-------+--------+-----------------+------+-------------+
|  1 | ref   | orders | idx_user_status |   15 | Using where |
+----+-------+--------+-----------------+------+-------------+
```

실제 출력에는 컬럼이 더 있다(`possible_keys`, `key_len`, `filtered` 등). 처음에는 아래 네 개만 보면 된다.

## 먼저 볼 컬럼

### type: 접근 방식

속도를 가장 크게 가르는 컬럼이다. 아래로 갈수록 느리다.

| type | 뜻 | 성능 |
|---|---|---|
| `const` | PK나 UNIQUE로 1건 조회 | 최고 |
| `eq_ref` | JOIN에서 PK/UNIQUE로 1건씩 매칭 | 매우 좋음 |
| `ref` | 인덱스로 여러 건 조회 | 좋음 |
| `range` | 인덱스를 범위로 읽음 (BETWEEN, >, <) | 보통 |
| `index` | 인덱스를 처음부터 끝까지 읽음 (Full Index Scan) | 느림 |
| `ALL` | 테이블을 처음부터 끝까지 읽음 (Full Table Scan) | 최악 |

`ALL`이 보이면 인덱스를 추가해야 하는지부터 본다.

### key

실제로 쓴 인덱스 이름이다. `NULL`이면 인덱스를 쓰지 않았다.

### rows

DB가 읽을 거라고 예상하는 행 수다. 실제로 센 값이 아니라 통계로 짐작한 값이다. 클수록 비싸다.

### Extra

| 값 | 뜻 |
|---|---|
| `Using index` | 커버링 인덱스 (테이블은 읽지 않음) |
| `Using where` | 읽은 행을 WHERE 조건으로 거름 |
| `Using filesort` | 인덱스로 정렬하지 못해 따로 정렬함 |
| `Using temporary` | 임시 테이블을 만듦 (GROUP BY, DISTINCT 등) |

`Using filesort`와 `Using temporary`가 같이 보이면 손봐야 할 쿼리다.

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

테이블을 전부 읽고, 정렬도 따로 한다.

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

이제 인덱스 하나로 조건 거르기와 정렬을 다 한다. `Backward index scan`은 인덱스를 거꾸로 읽었다는 뜻이고, DESC 정렬에도 인덱스를 쓰고 있다는 얘기다.

## EXPLAIN ANALYZE (MySQL 8.0.18+)

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
```

`EXPLAIN`은 예상치만 보여 주고, `EXPLAIN ANALYZE`는 쿼리를 실제로 돌린 결과를 보여 준다. 실제로 읽은 행 수, 걸린 시간, 루프를 몇 번 돌았는지가 나온다.

## 자주 깨지는 곳

- 인덱스를 추가하고 EXPLAIN을 보지 않으면, 옵티마이저가 그 인덱스를 안 골랐는데도 빨라졌다고 믿게 된다.
- `type: ALL`을 보고 넘어가면, 데이터가 늘어나는 만큼 쿼리가 그대로 느려진다.
- `Using filesort`가 보이는데 ORDER BY에 맞는 인덱스를 만들지 않으면, 매번 따로 정렬하는 비용을 계속 낸다.
- rows가 예상보다 큰데 원인을 보지 않으면, 어디서 행이 불어나는지 놓친다.
- rows를 정확한 값으로 믿으면 판단이 틀어진다. 통계로 짐작한 값이라 실제와 다르다.

## 한 번에 설명하기

> 실행 계획은 `EXPLAIN`으로 보고, `type`, `key`, `rows`, `Extra` 순서로 읽습니다.
>
> `type`이 `ALL`이면 테이블을 전부 읽는다는 뜻이라 인덱스를 추가할지 봅니다. `Using filesort`가 나오면 정렬에 맞는 인덱스가 필요한지 봅니다.
>
> `rows`는 추정치라서, 정확한 숫자가 필요하면 MySQL 8.0.18 이상에서 `EXPLAIN ANALYZE`로 실제로 돌려 본 결과를 확인합니다.

## 꼬리 질문

> [!question]- type이 ALL인데 인덱스가 있는 이유는?
> 옵티마이저가 인덱스보다 테이블을 통째로 읽는 게 빠르다고 본 겁니다. 조건에 걸리는 데이터가 전체의 상당 부분이면, 인덱스를 거쳐 한 건씩 찾아가는 쪽이 오히려 더 비쌀 수 있습니다.

> [!question]- Using filesort는 항상 나쁜가?
> 아닙니다. 몇 건 안 되는 데이터를 정렬하는 건 문제가 안 됩니다. 데이터가 많을 때 `Using filesort`가 나오면 디스크를 써서 정렬할 수도 있으니, 그때는 인덱스로 정렬을 대신하게 합니다.

> [!question]- EXPLAIN의 rows와 실제 행 수가 다른 이유는?
> rows는 테이블 통계(cardinality)로 짐작한 값이라서요. 통계가 오래됐거나 데이터가 한쪽에 몰려 있으면 실제와 차이가 납니다. 통계는 `ANALYZE TABLE`로 새로 갱신할 수 있습니다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 풀 스캔을 실행계획으로 찾은 과정

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html)
- [MySQL 8.4: Index Hints](https://dev.mysql.com/doc/refman/8.4/en/index-hints.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[join]]
