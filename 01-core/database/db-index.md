---
title: "인덱스 동작 원리와 설계 기준"
description: 인덱스가 어떻게 생겼고, 어떤 컬럼에 어떤 순서로 거는지
tags: [concept, database]
---

# 인덱스 동작 원리와 설계 기준

인덱스는 테이블의 데이터를 빨리 찾으려고 따로 만들어 두는 정렬된 자료구조(B-Tree)다. 책 뒤의 찾아보기와 비슷하다.

주문이 수백만 건 쌓인 테이블에서 "이 회원의 최근 주문"을 찾을 때 인덱스가 없으면 전부 읽는다. 그렇다고 아무 데나 걸면 주문이 들어올 때마다 고칠 인덱스가 늘어 쓰기가 느려진다. 걸어 놓고도 컬럼 순서가 쿼리와 안 맞으면 DB가 인덱스를 쓰지 않는다. 그래서 어디에 걸지와 함께, 걸었는데 왜 안 타는지, 몇 개까지 둘지를 같이 따진다.

## B-Tree

B-Tree(Balanced Tree)는 디스크를 덜 읽도록 만든 트리로, 넣고 지우는 동안 스스로 균형을 맞춘다.

- 이진 트리와 달리 한 노드에 키를 여러 개 넣는다.
- 모든 리프 노드가 같은 깊이에 있다.
- 노드가 꽉 차면 둘로 나누고(split), 비면 합쳐서(merge) 균형을 맞춘다.
- 노드 크기를 디스크 블록 크기에 맞추면 디스크를 가장 적게 읽는다.

```
              [30]                    ← 루트 노드
            /      \
       [10, 20]    [40, 50]          ← 브랜치 노드 (내부 노드에도 데이터 존재)
       / |  \      / |   \
    [1-9][10-19][20-29][30-39][40-49][50-59]  ← 리프 노드
```

B-Tree는 루트, 브랜치, 리프 어느 노드에든 키와 데이터를 저장한다.

## DB가 쓰는 건 B+ Tree

DB 인덱스가 실제로 쓰는 것은 B-Tree의 변형인 B+ Tree다.

```
B-Tree:
         [30(data)]
        /          \
  [10(data), 20(data)]  [40(data), 50(data)]
  → 모든 노드에 데이터 존재

B+ Tree:
              [30]                         ← 내부 노드: 키만 저장 (라우팅 역할)
            /      \
       [10, 20]    [40, 50]               ← 내부 노드: 키만 저장
       / |  \      / |   \
    [1-9]→[10-19]→[20-29]→[30-39]→[40-49]→[50-59]  ← 리프 노드: 키+데이터, 연결 리스트
```

| 구분 | B-Tree | B+ Tree |
|---|---|---|
| 데이터 위치 | 모든 노드 | 리프 노드에만 |
| 내부 노드 역할 | 키 + 데이터 | 키만 (라우팅) |
| 리프 노드 연결 | 없음 | Linked List로 연결 |
| 범위 검색 | 트리를 다시 탐색해야 함 | 리프 노드를 순차 탐색 |
| 내부 노드 fan-out | 낮음 (데이터 공간 차지) | 높음 (키만 저장하므로 더 많은 키 수용) |

DB가 B+ Tree를 쓰는 이유는 네 가지다.

1. 리프끼리 연결 리스트로 이어져 있어서, `WHERE id BETWEEN 10 AND 50` 같은 범위 검색은 리프만 차례로 읽으면 된다.
2. 내부 노드에 데이터가 없으니 한 노드에 키를 더 많이 넣는다(fan-out이 높다). 그만큼 트리가 낮아지고 디스크를 덜 읽는다.
3. 데이터가 모두 리프에 있어서 어떤 키를 찾든 내려가는 깊이가 같다. 성능을 미리 짐작하기 쉽다.
4. Full Scan이나 ORDER BY는 리프의 연결 리스트를 따라가기만 하면 끝난다.

## InnoDB의 B+ Tree 인덱스

```
              [30]
            /      \
       [10, 20]    [40, 50]
       / |  \      / |   \
    [1-9][10-19][20-29][30-39][40-49][50-59]
        (Clustered: 리프 = 행 데이터 / Secondary: 리프 = PK 값)
```

- 루트 → 브랜치 → 리프 순서로 내려간다.
- 리프에 무엇이 있는지는 인덱스 종류에 따라 다르다. InnoDB의 PK(Clustered) 인덱스는 리프에 행 데이터 자체가 있고, Secondary 인덱스는 리프에 PK 값이 있다. 리프에 행 주소(포인터)를 두는 건 MyISAM이나 PostgreSQL heap 쪽 이야기다.
- 1000만 건이어도 디스크를 3~4번 읽으면 찾는다.
- 늘 정렬된 상태라 범위 검색과 정렬이 빠르다.
- 리프끼리 연결되어 있어 범위 검색 중에 트리를 다시 탈 필요가 없다.

### Clustered vs Non-Clustered

| 구분 | Clustered Index | Non-Clustered Index (Secondary) |
|---|---|---|
| 정의 | 데이터 자체가 인덱스 순서로 저장 | 별도 인덱스 구조에 데이터 위치 저장 |
| 개수 | 테이블당 1개 (보통 PK) | 여러 개 가능 |
| 리프 노드 | 실제 데이터 행 | PK 값 (→ Clustered Index로 다시 조회) |
| 조회 | PK 조회가 가장 빠름 | PK를 거쳐 데이터 접근 (이중 탐색) |

InnoDB에서는 PK가 Clustered Index다. Secondary Index로 찾으면 리프에서 PK 값을 얻고, 그 PK로 Clustered Index를 한 번 더 탐색한다.

## 복합 인덱스

```sql
CREATE INDEX idx_user_status_created ON orders (user_id, status, created_at);
```

복합 인덱스는 왼쪽 컬럼부터 순서대로 쓰인다.

```sql
-- 인덱스 사용 O
WHERE user_id = 1
WHERE user_id = 1 AND status = 'COMPLETED'
WHERE user_id = 1 AND status = 'COMPLETED' AND created_at > '2024-01-01'

-- 인덱스 사용 X (첫 번째 컬럼 누락)
WHERE status = 'COMPLETED'
WHERE created_at > '2024-01-01'
```

예외는 있다. MySQL 8.0.13+는 선두 컬럼의 카디널리티가 낮으면 Index Skip Scan을 쓸 때가 있고, 조회하는 컬럼이 모두 인덱스에 있으면 인덱스 전체를 훑기도 한다. 둘 다 보통의 range 탐색보다 느리다. 그러니 설계할 때는 선두 컬럼부터 조건이 걸리게 만든다.

컬럼 순서는 이렇게 정한다.

1. 동등 조건(=) 컬럼을 앞에 둔다.
2. 범위 조건(>, <, BETWEEN) 컬럼을 뒤에 둔다. 범위 조건 뒤의 컬럼은 인덱스를 타지 않는다.
3. 동등 조건끼리는 카디널리티(고유값 수)가 높은 컬럼을 앞에 두는 편이 낫다. 다만 1, 2번의 조건 형태와 실제로 들어오는 쿼리가 카디널리티보다 먼저다.

## 커버링 인덱스

```sql
-- 인덱스: (user_id, status, created_at)

-- 커버링 인덱스 O: SELECT 컬럼이 모두 인덱스에 포함
SELECT user_id, status, created_at FROM orders WHERE user_id = 1;

-- 커버링 인덱스 X: amount는 인덱스에 없어서 테이블 접근 필요
SELECT user_id, amount FROM orders WHERE user_id = 1;
```

쿼리에 필요한 컬럼이 모두 인덱스에 있으면 테이블은 읽지 않고 인덱스만 읽고 끝낸다. 이걸 커버링 인덱스라고 하고, 실행 계획에 `Using index`가 보이면 그렇게 처리된 것이다.

## 인덱스를 안 타는 경우

| 경우 | 이유 |
|---|---|
| `WHERE YEAR(created_at) = 2024` | 컬럼에 함수를 씌우면 인덱스를 못 쓴다 |
| `WHERE name LIKE '%검색어'` | 앞이 와일드카드면 B-Tree로 찾아 내려갈 수 없다 |
| `WHERE status != 'DELETED'` | 부정 조건은 인덱스로 걸러지는 양이 적다 |
| `WHERE amount + 100 > 500` | 컬럼에 연산을 하면 인덱스를 못 쓴다 |
| 데이터 대부분이 조건에 해당 | 옵티마이저가 Full Scan이 더 빠르다고 본다 |

```sql
-- 잘못된 예: 함수 사용
WHERE YEAR(created_at) = 2024

-- 올바른 예: 범위 조건으로 변경
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
```

## 인덱스의 비용

인덱스를 하나 걸 때마다 쓰기에 일이 붙는다.

- INSERT하면 인덱스에도 값을 넣는다.
- UPDATE로 인덱스 컬럼이 바뀌면 인덱스도 고친다.
- DELETE하면 인덱스에서도 지운다.
- 인덱스마다 저장 공간을 따로 쓴다.

그래서 WHERE, JOIN, ORDER BY에 자주 쓰이는 컬럼에만 건다. 아무도 안 쓰는 인덱스는 쓰기만 느리게 한다.

## 자주 깨지는 곳

- WHERE 컬럼에 함수나 연산을 씌우면, 인덱스가 있어도 타지 않는다.
- 복합 인덱스 컬럼 순서를 쿼리와 상관없이 정하면, 선두 컬럼이 조건에 없는 쿼리에서는 쓸모가 없다.
- 성별처럼 카디널리티가 낮은 컬럼에 단독 인덱스를 걸면, 옵티마이저가 거의 고르지 않는다.
- 인덱스를 너무 많이 만들면, 쓰기마다 고칠 인덱스가 늘어 INSERT와 UPDATE가 느려진다.
- `LIKE '%검색어'`처럼 앞이 와일드카드인 검색은, 인덱스를 걸어도 B-Tree로 찾지 못한다.

## 한 번에 설명하기

> 인덱스는 B+ Tree로 된 정렬된 자료구조입니다. InnoDB에서는 PK가 Clustered Index이고, Secondary Index는 리프에 PK를 들고 있어서 그 PK로 한 번 더 찾아갑니다.
>
> 복합 인덱스는 왼쪽 컬럼부터 쓰이기 때문에, 저는 동등 조건을 앞에 두고 범위 조건을 뒤에 둡니다.
>
> 컬럼에 함수나 연산을 씌우면 인덱스를 못 타고, 안 쓰는 인덱스는 쓰기만 느리게 합니다. 그래서 실제로 들어오는 쿼리를 보고 필요한 만큼만 만듭니다.

## 꼬리 질문

> [!question]- 인덱스를 걸었는데 안 타는 이유는?
> 먼저 컬럼에 함수나 연산을 씌웠는지 봅니다. 다음은 복합 인덱스의 첫 컬럼이 조건에 빠졌는지입니다. 둘 다 아니면 조건에 걸리는 데이터가 너무 많아서 옵티마이저가 Full Scan이 낫다고 판단한 경우가 많습니다.

> [!question]- 커버링 인덱스란?
> SELECT와 WHERE에 쓴 컬럼이 전부 인덱스에 들어 있어서, 테이블은 읽지 않고 인덱스만 읽고 끝나는 경우입니다. 실행 계획에 `Using index`가 뜨면 그렇게 처리된 겁니다.

> [!question]- 인덱스를 많이 만들면 안 되는 이유는?
> INSERT, UPDATE, DELETE를 할 때마다 걸린 인덱스를 전부 같이 고쳐야 해서 쓰기가 느려집니다. 인덱스마다 저장 공간도 따로 듭니다.

> [!question]- PK가 BIGINT여야 하는 이유는?
> PK는 Clustered Index의 키이면서, 모든 Secondary Index의 리프에도 들어가는 값입니다. UUID(16~36 bytes)보다 BIGINT(8 bytes)가 작으니 인덱스가 작아지고, 메모리에 더 많이 올라가서 조회도 빨라집니다.

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 등호 → 범위 → GROUP BY 순 복합 인덱스

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Optimization and Indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html)
- [MySQL 8.4: Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[table-and-key]]
- [[execution-plan]]
