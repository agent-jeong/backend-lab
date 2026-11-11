---
title: "JOIN의 종류와 동작 원리"
description: JOIN 종류별 결과 차이와, MySQL이 JOIN을 실행하는 방식
tags: [concept, database]
---

# JOIN의 종류와 동작 원리

JOIN은 테이블 두 개 이상을 공통 컬럼으로 이어 붙여 한 번에 조회하는 SQL 연산이다. 주문 목록에 회원 이름을 붙여 보여 줄 때 쓴다.

JOIN 쿼리가 느리면 범인은 대개 JOIN 자체가 아니라 JOIN 컬럼에 인덱스가 없거나 결과 행이 너무 많은 것이다. 결과가 이상하게 나오면 INNER와 OUTER, 또는 ON과 WHERE를 헷갈린 경우가 많다.

## 종류

### INNER JOIN

```sql
SELECT o.id, u.name
FROM orders o
INNER JOIN users u ON o.user_id = u.id;
```

양쪽 테이블에 다 짝이 있는 행만 돌려준다. 가장 많이 쓴다.

### LEFT (OUTER) JOIN

```sql
SELECT u.name, o.id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

왼쪽 테이블의 행은 전부 돌려주고, 짝이 없는 오른쪽 값은 NULL로 채운다. 주문이 없는 회원까지 목록에 넣어야 할 때 쓴다.

### RIGHT (OUTER) JOIN

LEFT JOIN의 반대다. 실무에서는 보통 LEFT JOIN으로 통일한다.

### CROSS JOIN

```sql
SELECT * FROM colors CROSS JOIN sizes;
```

가능한 모든 행 조합(카테시안 곱)을 돌려준다. 결과가 N * M 행이라, 일부러 원한 게 아니면 쓰지 않는다.

| JOIN 종류 | 결과 | 실무 빈도 |
|---|---|---|
| INNER JOIN | 양쪽에 짝이 있는 행만 | 가장 많음 |
| LEFT JOIN | 왼쪽 전체 + 오른쪽은 짝이 있을 때만 | 자주 |
| RIGHT JOIN | 오른쪽 전체 + 왼쪽은 짝이 있을 때만 | 거의 안 씀 |
| CROSS JOIN | 모든 조합 | 드묾 |

## MySQL이 JOIN을 실행하는 방식

### Nested Loop Join (NLJ)

```
FOR each row in 드라이빙 테이블:
    FOR each row in 드리븐 테이블 WHERE 조건 매칭:
        결과에 추가
```

MySQL이 기본으로 쓰는 방식이다. 먼저 읽는 쪽(드라이빙 테이블)의 행마다 나중에 읽는 쪽(드리븐 테이블)을 뒤지므로, 드리븐 테이블의 JOIN 컬럼에 인덱스가 있어야 빠르다. 인덱스가 없으면 드라이빙 테이블의 행 하나마다 드리븐 테이블을 처음부터 끝까지 읽는다.

### Hash Join (MySQL 8.0.18+)

- 드리븐 테이블에 쓸 인덱스가 없으면 옵티마이저가 Hash Join을 고를 수 있다.
- 한쪽 테이블로 해시 테이블을 만들고, 다른 쪽을 한 줄씩 읽으며 짝을 찾는다.
- 동등 조건(=) JOIN에서만 쓴다.

## 빠르게 만드는 법

드리븐 테이블의 JOIN 컬럼에 인덱스를 건다. 대부분은 이것으로 해결된다.

```sql
-- orders.user_id에 인덱스가 없으면 매 행마다 Full Scan
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id;
```

드라이빙 테이블은 작을수록 좋다. 옵티마이저는 결과 행이 적은 테이블을 드라이빙 테이블로 고른다. WHERE 조건으로 많이 걸러지는 테이블이 먼저 읽히면 바깥 루프가 짧아진다.

SELECT에는 필요한 컬럼만 적는다.

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

MySQL 옵티마이저는 서브쿼리를 대부분 JOIN으로 바꿔서 실행한다. 그래서 둘의 속도 차이가 크지 않은 경우가 많다. 확실히 알고 싶으면 실행 계획을 본다.

## 자주 깨지는 곳

- JOIN 컬럼에 인덱스가 없으면, Nested Loop가 드리븐 테이블을 매번 처음부터 끝까지 읽는다.
- LEFT JOIN을 써야 할 자리에 INNER JOIN을 쓰면, 짝이 없는 행이 결과에서 조용히 빠진다.
- `SELECT *`로 JOIN하면, 필요 없는 컬럼까지 양쪽에서 다 가져온다.
- ON 조건과 WHERE 조건을 헷갈리면, OUTER JOIN 결과가 의도와 다르게 나온다.
- JOIN을 늘리면서 실행 계획을 안 보면, 어느 단계에서 Full Scan이 나는지 모른다.

## 한 번에 설명하기

> JOIN은 테이블을 공통 컬럼으로 이어 붙이는 연산이고, 실무에서는 INNER JOIN과 LEFT JOIN을 주로 씁니다. INNER JOIN은 양쪽에 짝이 있는 행만 돌려주고, LEFT JOIN은 짝이 없는 행도 NULL로 채워 남깁니다.
>
> MySQL은 기본이 Nested Loop Join이라서, 저는 드리븐 테이블의 JOIN 컬럼에 인덱스가 있는지부터 봅니다. JOIN이 들어간 쿼리는 실행 계획으로 인덱스를 타는지 확인합니다.

## 꼬리 질문

> [!question]- INNER JOIN과 LEFT JOIN의 성능 차이는?
> 인덱스 조건이 같으면 속도 차이는 거의 없습니다. 다른 건 결과입니다. LEFT JOIN은 짝이 없는 행도 넣으니 결과 행이 더 많을 수 있고, 그만큼 처리할 양이 늘 수는 있습니다.

> [!question]- ON 조건과 WHERE 조건의 차이는?
> INNER JOIN에서는 같습니다. LEFT JOIN에서는 다릅니다. ON 조건은 짝을 지을 때 쓰는 기준이고, WHERE 조건은 JOIN이 끝난 결과를 거르는 조건입니다. 그래서 LEFT JOIN에서 오른쪽 테이블 조건을 WHERE에 쓰면, NULL로 채운 행이 걸러져서 INNER JOIN과 같은 결과가 됩니다.

> [!question]- JOIN을 많이 하면 성능이 나빠지는가?
> JOIN 개수보다는 인덱스가 있는지와 결과 행이 몇 개인지가 속도를 정합니다. JOIN 컬럼에 맞는 인덱스가 있으면 테이블 3~4개를 JOIN해도 빠릅니다. 실제로 그런지는 실행 계획으로 확인합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Nested-Loop Join Algorithms](https://dev.mysql.com/doc/refman/8.4/en/nested-loop-joins.html)
- [MySQL 8.4: Hash Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[db-index]]
- [[execution-plan]]
