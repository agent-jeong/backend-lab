---
title: "JOIN의 종류와 동작 원리"
description: SQL JOIN의 종류와 동작 방식별 성능 차이
tags: [concept, database]
---

# JOIN의 종류와 동작 원리

JOIN은 두 개 이상의 테이블을 공통 컬럼으로 묶어 하나의 결과로 조회하는 SQL 연산이다.

JOIN 쿼리가 느릴 때 원인은 대개 JOIN 자체가 아니라 JOIN 컬럼의 인덱스와 결과 행 수다. 결과가 틀릴 때는 INNER와 OUTER, ON과 WHERE를 헷갈린 경우가 많다.

## 종류

### INNER JOIN

```sql
SELECT o.id, u.name
FROM orders o
INNER JOIN users u ON o.user_id = u.id;
```

양쪽 테이블에 모두 매칭되는 행만 돌려준다. 가장 많이 쓴다.

### LEFT (OUTER) JOIN

```sql
SELECT u.name, o.id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

왼쪽 테이블의 행은 전부 돌려주고, 매칭되지 않은 오른쪽은 NULL로 채운다. "주문이 없는 사용자도 포함"할 때 쓴다.

### RIGHT (OUTER) JOIN

LEFT JOIN의 반대다. 실무에서는 보통 LEFT JOIN으로 통일한다.

### CROSS JOIN

```sql
SELECT * FROM colors CROSS JOIN sizes;
```

모든 행의 조합(카테시안 곱)을 돌려준다. N * M 행이 생기므로 의도한 경우가 아니면 피한다.

| JOIN 종류 | 결과 | 실무 빈도 |
|---|---|---|
| INNER JOIN | 양쪽 매칭만 | 가장 많음 |
| LEFT JOIN | 왼쪽 전체 + 오른쪽 매칭 | 자주 |
| RIGHT JOIN | 오른쪽 전체 + 왼쪽 매칭 | 거의 안 씀 |
| CROSS JOIN | 모든 조합 | 특수 경우 |

## MySQL이 JOIN을 실행하는 방식

### Nested Loop Join (NLJ)

```
FOR each row in 드라이빙 테이블:
    FOR each row in 드리븐 테이블 WHERE 조건 매칭:
        결과에 추가
```

MySQL의 기본 방식이다. 드라이빙 테이블의 행마다 드리븐 테이블을 찾으므로, 드리븐 테이블의 JOIN 컬럼에 인덱스가 있어야 빠르다. 인덱스가 없으면 드리븐 테이블을 매번 Full Scan한다.

### Hash Join (MySQL 8.0.18+)

- 드리븐 테이블에 인덱스가 없을 때 옵티마이저가 Hash Join을 고를 수 있다.
- 한쪽 테이블로 해시 테이블을 만들고, 다른 쪽을 순회하며 매칭한다.
- 동등 조건(=) JOIN에서만 쓸 수 있다.

## 빠르게 만드는 법

**드리븐 테이블의 JOIN 컬럼에 인덱스를 건다.** 이게 거의 전부다.

```sql
-- orders.user_id에 인덱스가 없으면 매 행마다 Full Scan
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id;
```

**드라이빙 테이블은 작게.** 옵티마이저는 결과 행이 적은 테이블을 드라이빙 테이블로 고른다. WHERE 조건으로 많이 걸러지는 테이블이 드라이빙 테이블이 되면 바깥 루프가 짧아진다.

**필요한 컬럼만 SELECT한다.**

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

MySQL 옵티마이저는 대부분의 서브쿼리를 JOIN으로 바꿔 실행한다. 그래서 성능 차이가 크지 않은 경우가 많다. 확실히 하려면 실행 계획을 본다.

## 자주 깨지는 곳

- **JOIN 컬럼에 인덱스가 없다.** Nested Loop가 드리븐 테이블을 매번 Full Scan한다.
- **LEFT JOIN 자리에 INNER JOIN을 쓴다.** 매칭되지 않는 행이 결과에서 빠진다.
- **`SELECT *`로 JOIN한다.** 필요 없는 컬럼까지 가져온다.
- **ON 조건과 WHERE 조건을 헷갈린다.** OUTER JOIN 결과가 의도와 달라진다.
- **JOIN이 늘어나는데 실행 계획을 안 본다.** 어느 단계에서 Full Scan이 나는지 모른다.

## 면접에서 말하기

> JOIN은 테이블을 공통 컬럼으로 묶는 연산이고, 실무에서는 INNER JOIN과 LEFT JOIN을 주로 씁니다. LEFT JOIN은 매칭되지 않는 행도 NULL로 남기고, INNER JOIN은 매칭되는 행만 돌려줍니다. MySQL은 기본적으로 Nested Loop Join이라서 저는 드리븐 테이블의 JOIN 컬럼에 인덱스가 있는지부터 확인하고, JOIN이 들어간 쿼리는 실행 계획으로 인덱스를 타는지 봅니다.

## 꼬리 질문

> [!question]- INNER JOIN과 LEFT JOIN의 성능 차이는?
> 같은 인덱스 조건이면 성능 차이는 거의 없습니다. 차이는 결과에 있습니다. LEFT JOIN은 매칭되지 않는 행도 포함하므로 결과 행 수가 더 많을 수 있고, 그만큼 처리량이 늘어날 수 있습니다.

> [!question]- ON 조건과 WHERE 조건의 차이는?
> INNER JOIN에서는 동일합니다. LEFT JOIN에서는 다릅니다. ON 조건은 JOIN 시 매칭 기준이고, WHERE 조건은 JOIN 결과에 대한 필터입니다. LEFT JOIN에서 WHERE로 오른쪽 테이블을 필터하면 INNER JOIN과 같은 결과가 됩니다.

> [!question]- JOIN을 많이 하면 성능이 나빠지는가?
> JOIN 자체보다 인덱스 유무와 결과 행 수가 성능을 결정합니다. JOIN 컬럼에 맞는 인덱스가 있으면 3~4개 테이블 JOIN도 빠르게 동작합니다. 실행 계획으로 확인해야 합니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Nested-Loop Join Algorithms](https://dev.mysql.com/doc/refman/8.4/en/nested-loop-joins.html)
- [MySQL 8.4: Hash Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]
