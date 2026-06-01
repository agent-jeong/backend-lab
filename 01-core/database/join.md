---
title: Join
description: SQL JOIN의 종류와 동작 방식별 성능 차이
---

# Join

## 한 줄 정의

JOIN은 두 개 이상의 테이블을 공통 컬럼을 기준으로 결합해서 하나의 결과로 조회하는 SQL 연산이다.

## 실무에서 왜 중요한가

JOIN을 잘못 사용하면 다음 문제가 생긴다.

- 불필요한 Full Table Scan이 발생해서 쿼리가 느리다.
- OUTER JOIN과 INNER JOIN의 차이를 모르고 사용해서 결과가 틀리다.
- JOIN 조건에 인덱스가 없어서 성능이 급격히 떨어진다.
- 서브쿼리와 JOIN 중 어떤 것이 적합한지 판단하지 못한다.

## JOIN 종류

### INNER JOIN

```sql
SELECT o.id, u.name
FROM orders o
INNER JOIN users u ON o.user_id = u.id;
```

양쪽 테이블에 모두 매칭되는 행만 반환한다. 가장 많이 사용한다.

### LEFT (OUTER) JOIN

```sql
SELECT u.name, o.id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

왼쪽 테이블의 모든 행을 반환하고, 매칭되지 않는 오른쪽은 NULL로 채운다. "주문이 없는 사용자도 포함"할 때 사용한다.

### RIGHT (OUTER) JOIN

LEFT JOIN과 반대. 실무에서는 LEFT JOIN으로 통일하는 것이 일반적이다.

### CROSS JOIN

```sql
SELECT * FROM colors CROSS JOIN sizes;
```

모든 행의 조합(카테시안 곱)을 반환한다. N * M 행이 생성되므로 의도적으로 사용하는 경우가 아니면 피한다.

### 비교

| JOIN 종류 | 결과 | 실무 빈도 |
|---|---|---|
| INNER JOIN | 양쪽 매칭만 | 가장 많음 |
| LEFT JOIN | 왼쪽 전체 + 오른쪽 매칭 | 자주 |
| RIGHT JOIN | 오른쪽 전체 + 왼쪽 매칭 | 거의 안 씀 |
| CROSS JOIN | 모든 조합 | 특수 경우 |

## JOIN 실행 방식 (MySQL)

### Nested Loop Join (NLJ)

```
FOR each row in 드라이빙 테이블:
    FOR each row in 드리븐 테이블 WHERE 조건 매칭:
        결과에 추가
```

- MySQL의 기본 JOIN 실행 방식이다.
- 드리븐 테이블의 JOIN 컬럼에 인덱스가 있어야 효율적이다.
- 인덱스가 없으면 드리븐 테이블을 매번 Full Scan한다.

### Hash Join (MySQL 8.0.18+)

- 드리븐 테이블에 인덱스가 없을 때 옵티마이저가 Hash Join을 선택할 수 있다.
- 한쪽 테이블로 해시 테이블을 만들고 다른 쪽을 순회하면서 매칭한다.
- 동등 조건(=) JOIN에서만 사용 가능하다.

## JOIN 성능 최적화

### 1. JOIN 컬럼에 인덱스

```sql
-- orders.user_id에 인덱스가 없으면 매 행마다 Full Scan
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id;
```

**JOIN 조건의 드리븐 테이블 컬럼에 인덱스가 필수**다.

### 2. 드라이빙 테이블 선택

옵티마이저는 결과 행이 적은 테이블을 드라이빙 테이블로 선택한다. WHERE 조건으로 필터링이 많이 되는 테이블이 드라이빙 테이블이 되면 효율적이다.

### 3. 필요한 컬럼만 SELECT

```sql
-- 비효율: 불필요한 컬럼까지 조회
SELECT * FROM users u JOIN orders o ON u.id = o.user_id;

-- 효율: 필요한 컬럼만
SELECT u.name, o.id, o.status FROM users u JOIN orders o ON u.id = o.user_id;
```

## 서브쿼리 vs JOIN

```sql
-- 서브쿼리
SELECT * FROM orders
WHERE user_id IN (SELECT id FROM users WHERE status = 'ACTIVE');

-- JOIN
SELECT o.* FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.status = 'ACTIVE';
```

MySQL 옵티마이저는 대부분의 서브쿼리를 JOIN으로 변환해서 실행한다. 성능 차이가 크지 않은 경우가 많지만, 실행 계획으로 확인하는 것이 확실하다.

## 자주 나는 실수

- JOIN 컬럼에 인덱스를 걸지 않아서 Nested Loop이 Full Scan으로 동작한다.
- LEFT JOIN을 사용해야 하는데 INNER JOIN을 사용해서 데이터가 누락된다.
- `SELECT *`로 JOIN해서 불필요한 컬럼까지 가져온다.
- ON 조건과 WHERE 조건을 혼동해서 OUTER JOIN 결과가 의도와 다르다.
- JOIN이 많아질수록 실행 계획 확인 없이 쿼리를 작성한다.

## 핵심 요약

JOIN은 테이블을 공통 컬럼으로 결합하는 연산이며, INNER JOIN과 LEFT JOIN이 실무에서 가장 많이 사용됩니다.
MySQL은 기본적으로 Nested Loop Join을 사용하므로, 드리븐 테이블의 JOIN 컬럼에 인덱스가 필수입니다.

LEFT JOIN은 매칭되지 않는 행도 NULL로 포함하고, INNER JOIN은 매칭되는 행만 반환합니다.
JOIN이 포함된 쿼리는 반드시 실행 계획으로 인덱스 사용 여부를 확인해야 합니다.

## 꼬리 질문

> [!question]- INNER JOIN과 LEFT JOIN의 성능 차이는?
> 같은 인덱스 조건이면 성능 차이는 거의 없습니다. 차이는 결과에 있습니다. LEFT JOIN은 매칭되지 않는 행도 포함하므로 결과 행 수가 더 많을 수 있고, 그만큼 처리량이 늘어날 수 있습니다.

> [!question]- ON 조건과 WHERE 조건의 차이는?
> INNER JOIN에서는 동일합니다. LEFT JOIN에서는 다릅니다. ON 조건은 JOIN 시 매칭 기준이고, WHERE 조건은 JOIN 결과에 대한 필터입니다. LEFT JOIN에서 WHERE로 오른쪽 테이블을 필터하면 INNER JOIN과 같은 결과가 됩니다.

> [!question]- JOIN을 많이 하면 성능이 나빠지는가?
> JOIN 자체보다 인덱스 유무와 결과 행 수가 성능을 결정합니다. 적절한 인덱스가 있으면 3~4개 테이블 JOIN도 빠르게 동작합니다. 실행 계획으로 확인하는 것이 중요합니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]