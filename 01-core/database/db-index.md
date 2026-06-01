---
title: Index
description: 데이터베이스 인덱스의 동작 원리와 실무 설계 기준
---

# Index

## 한 줄 정의

인덱스는 테이블의 데이터를 빠르게 조회하기 위해 별도로 유지하는 정렬된 자료구조(B-Tree)다.

## 실무에서 왜 중요한가

인덱스는 쿼리 성능의 핵심이다. 이해하지 못하면 다음 문제가 생긴다.

- 데이터가 늘어날수록 조회가 비례해서 느려진다.
- 인덱스를 걸었는데 타지 않는 이유를 모른다.
- 인덱스를 너무 많이 만들어서 INSERT/UPDATE 성능이 떨어진다.
- 커버링 인덱스, 복합 인덱스의 컬럼 순서를 모르고 설계한다.

## B-Tree 인덱스 구조

```
              [30]
            /      \
       [10, 20]    [40, 50]
       / |  \      / |   \
    [1-9][10-19][20-29][30-39][40-49][50-59]
                              (리프 노드 → 실제 데이터 위치)
```

- 루트 → 브랜치 → 리프 순서로 탐색한다.
- 리프 노드가 실제 데이터의 위치(포인터)를 가진다.
- 데이터가 1000만 건이어도 3~4번의 디스크 접근으로 찾는다.
- **정렬된 상태를 유지**하기 때문에 범위 검색과 정렬에 유리하다.

## Clustered vs Non-Clustered Index

| 구분 | Clustered Index | Non-Clustered Index (Secondary) |
|---|---|---|
| 정의 | 데이터 자체가 인덱스 순서로 저장 | 별도 인덱스 구조에 데이터 위치 저장 |
| 개수 | 테이블당 1개 (보통 PK) | 여러 개 가능 |
| 리프 노드 | 실제 데이터 행 | PK 값 (→ Clustered Index로 다시 조회) |
| 조회 | PK 조회가 가장 빠름 | PK를 거쳐 데이터 접근 (이중 탐색) |

InnoDB에서 PK가 Clustered Index다. Secondary Index의 리프 노드에는 PK 값이 저장되어 있어서, Secondary Index로 조회하면 PK로 다시 Clustered Index를 탐색한다.

## 복합 인덱스

```sql
CREATE INDEX idx_user_status_created ON orders (user_id, status, created_at);
```

### 컬럼 순서가 중요한 이유

복합 인덱스는 **왼쪽 컬럼부터 순서대로** 사용된다.

```sql
-- 인덱스 사용 O
WHERE user_id = 1
WHERE user_id = 1 AND status = 'COMPLETED'
WHERE user_id = 1 AND status = 'COMPLETED' AND created_at > '2024-01-01'

-- 인덱스 사용 X (첫 번째 컬럼 누락)
WHERE status = 'COMPLETED'
WHERE created_at > '2024-01-01'
```

### 복합 인덱스 설계 기준

1. **동등 조건(=)** 컬럼을 앞에 둔다.
2. **범위 조건(>, <, BETWEEN)** 컬럼을 뒤에 둔다. 범위 조건 이후 컬럼은 인덱스를 타지 않는다.
3. **카디널리티(고유값 수)가 높은** 컬럼을 앞에 둔다.

## 커버링 인덱스

```sql
-- 인덱스: (user_id, status, created_at)

-- 커버링 인덱스 O: SELECT 컬럼이 모두 인덱스에 포함
SELECT user_id, status, created_at FROM orders WHERE user_id = 1;

-- 커버링 인덱스 X: amount는 인덱스에 없어서 테이블 접근 필요
SELECT user_id, amount FROM orders WHERE user_id = 1;
```

커버링 인덱스는 인덱스만으로 쿼리를 처리해서 테이블 데이터에 접근하지 않는다. 실행 계획에서 `Using index`로 확인할 수 있다.

## 인덱스가 타지 않는 경우

| 경우 | 이유 |
|---|---|
| `WHERE YEAR(created_at) = 2024` | 컬럼에 함수를 적용하면 인덱스 무효화 |
| `WHERE name LIKE '%검색어'` | 앞쪽 와일드카드는 B-Tree 탐색 불가 |
| `WHERE status != 'DELETED'` | 부정 조건은 인덱스 효율이 낮음 |
| `WHERE amount + 100 > 500` | 컬럼에 연산을 적용하면 인덱스 무효화 |
| 데이터 대부분이 조건에 해당 | 옵티마이저가 Full Scan이 더 빠르다고 판단 |

```sql
-- 잘못된 예: 함수 사용
WHERE YEAR(created_at) = 2024

-- 올바른 예: 범위 조건으로 변경
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
```

## 인덱스의 비용

인덱스는 공짜가 아니다.

- **INSERT**: 인덱스에도 데이터를 추가해야 한다.
- **UPDATE**: 인덱스 컬럼이 변경되면 인덱스도 수정된다.
- **DELETE**: 인덱스에서도 삭제 처리가 필요하다.
- **저장 공간**: 인덱스는 별도 공간을 차지한다.

**실무 원칙**: WHERE, JOIN, ORDER BY에 자주 사용되는 컬럼에만 인덱스를 건다. 불필요한 인덱스는 쓰기 성능을 떨어뜨린다.

## 자주 나는 실수

- WHERE 절 컬럼에 함수나 연산을 적용해서 인덱스가 무효화된다.
- 복합 인덱스의 컬럼 순서를 고려하지 않고 만든다.
- 카디널리티가 낮은 컬럼(예: 성별)에 단독 인덱스를 건다.
- 인덱스를 과도하게 많이 만들어서 쓰기 성능이 떨어진다.
- LIKE 검색에서 앞쪽 와일드카드를 사용하면서 인덱스를 기대한다.

## 핵심 요약

인덱스는 B-Tree 기반의 정렬된 자료구조로, 데이터를 빠르게 조회하기 위해 사용합니다.
InnoDB에서 PK는 Clustered Index이고, Secondary Index는 PK를 통해 데이터에 접근합니다.

복합 인덱스는 왼쪽 컬럼부터 순서대로 사용되므로 동등 조건 → 범위 조건 순으로 설계합니다.
컬럼에 함수나 연산을 적용하면 인덱스가 무효화되고, 불필요한 인덱스는 쓰기 성능을 떨어뜨립니다.

## 꼬리 질문

> [!question]- 인덱스를 걸었는데 안 타는 이유는?
> 컬럼에 함수/연산을 적용했거나, 복합 인덱스의 선행 컬럼이 조건에 없거나, 데이터 대부분이 조건에 해당해서 옵티마이저가 Full Scan을 선택한 경우입니다.

> [!question]- 커버링 인덱스란?
> SELECT, WHERE에 사용된 모든 컬럼이 인덱스에 포함되어 테이블 데이터에 접근하지 않고 인덱스만으로 쿼리를 처리하는 것입니다. 실행 계획에서 `Using index`로 확인합니다.

> [!question]- 인덱스를 많이 만들면 안 되는 이유는?
> INSERT, UPDATE, DELETE 시 모든 관련 인덱스를 함께 수정해야 해서 쓰기 성능이 떨어집니다. 저장 공간도 추가로 필요합니다.

> [!question]- PK가 BIGINT여야 하는 이유는?
> PK는 Clustered Index이자 모든 Secondary Index의 리프에 저장되는 값입니다. UUID(16~36 bytes)보다 BIGINT(8 bytes)가 인덱스 크기가 작아 캐시 효율과 조회 성능이 좋습니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[table-and-key]]
- [[execution-plan]]