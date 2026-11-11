---
title: DB 조회 성능
description: 느린 조회를 쿼리 수, 실행 계획, 인덱스, 가져오는 데이터 양으로 나눠 보는 방법
tags: [concept, performance]
---

# DB 조회 성능

DB 조회 성능을 올린다는 건, 쿼리 수, 실행 계획, 인덱스, 정렬과 페이징, 돌려받는 데이터 양을 살펴서 DB가 덜 읽고도 필요한 행을 찾게 만드는 일이다.

백엔드 성능 문제는 대개 느린 조회나 늘어난 쿼리 수에서 시작한다. 인덱스가 있어도 조건, 정렬, 선택도(selectivity)에 따라 안 쓰일 때가 있다. N+1은 개발 환경처럼 데이터가 적을 때는 숨어 있다가, 주문이 수십만 건 쌓인 운영에서 갑자기 느려진다. 그래서 explain을 보고 실제로 재기 전에는 짐작으로 튜닝하지 않는다.

## 순서

1. 느린 API에서 실행된 SQL과 쿼리 수를 확인한다.
2. slow query와 execution plan을 본다.
3. where, join, order by, limit 조건이 인덱스와 맞는지 확인한다.
4. 돌려받는 row 수와 컬럼 수가 꼭 필요한 만큼인지 본다.
5. 쿼리를 바꾸거나 인덱스를 더하거나 fetch 전략을 조정한 뒤 다시 잰다.

```sql
select o.id, o.status, o.created_at
from orders o
where o.user_id = ?
  and o.created_at < ?
order by o.created_at desc
limit 20;
```

이 쿼리라면 `user_id`, `created_at` 순서의 복합 인덱스를 먼저 떠올릴 만하다. 다만 실제 선택도와 실행 계획을 보고 나서 정한다.

## 문제별 개선 방향

| 문제 | 확인 지표 | 개선 방향 |
|---|---|---|
| 쿼리 수 많음 | query count, N+1 로그 | fetch join, batch size, DTO 조회 |
| full scan | execution plan, rows examined | 인덱스, 조건 변경 |
| 정렬 느림 | filesort, sort memory | 복합 인덱스, 정렬 조건 조정 |
| offset 느림 | large offset, scan rows | keyset pagination |
| 반환 데이터 큼 | response size, row count | projection, limit, summary API |
| 집계 쿼리 느림 | group by, temp table | 사전 집계, summary table, 비동기 집계 |

| 개선 | 장점 | 한계 |
|---|---|---|
| 인덱스 | 조회 비용을 크게 줄인다 | 쓰기 비용과 저장 공간이 늘어난다 |
| fetch 전략 조정 | N+1을 줄인다 | join 폭증과 중복 row를 만들 수 있다 |
| projection | 네트워크와 매핑 비용을 줄인다 | 재사용성이 낮아질 수 있다 |
| keyset pagination | 큰 offset 비용을 줄인다 | 임의 페이지 이동이 어렵다 |
| 사전 집계 | 반복 집계 비용을 줄인다 | 정합성 지연과 갱신 비용이 생긴다 |

## 자주 깨지는 곳

- 인덱스를 더하면 무조건 빨라진다고 믿으면, where와 order by 조건, 선택도, 데이터 분포에 맞지 않는 인덱스를 만들고 효과를 못 본다.
- explain 없이 쿼리 문장만 보고 병목을 짐작하면, 실제로 느린 단계를 놓친다.
- 로컬의 작은 데이터로 성능을 판단하면, 운영 데이터에서 다시 느려진다.
- JPA fetch join을 마구 늘리면, join 결과 row가 폭증한다.
- offset이 커져도 비용이 같다고 보면, 뒤 페이지로 갈수록 scan이 늘어 느려지는 걸 놓친다.
- count 쿼리와 목록 쿼리의 비용이 같다고 보면, 목록은 빠른데 count나 group by에서 막히는 걸 놓친다.
- 조회용 인덱스가 쓰기 성능과 lock 경합에 주는 영향을 확인하지 않으면, 조회는 빨라지고 쓰기가 느려진다.
- 필요한 것보다 많이 가져오면, 컬럼과 row만큼 DB, 네트워크, 애플리케이션 비용이 모두 는다.

## 운영에서 볼 것

- 운영과 비슷한 데이터 크기에서 조회 시간을 비교한다.
- SQL, query count, bind parameter, elapsed time을 로그로 확인한다.
- execution plan, rows examined, index usage, sort 방식, temporary table을 본다.
- DB CPU, buffer hit ratio, slow query count, connection usage를 본다.

## 한 번에 설명하기

> DB 조회가 느리면 쿼리 수, 실행 계획, 인덱스, 가져오는 데이터 양을 같이 봅니다.
>
> 먼저 느린 API가 날린 SQL과 쿼리 수를 보고 N+1인지 확인합니다. 그다음 explain으로 인덱스가 where와 order by 조건에 맞게 쓰이는지 봅니다. offset이 크면 keyset pagination을 검토하고, 목록이 빨라도 count나 group by에서 막힐 수 있어서 따로 확인합니다.
>
> 판단은 짐작이 아니라 explain과 실제로 잰 값으로 합니다.

## 꼬리 질문

- 느린 조회 API를 만나면 DB에서 무엇부터 확인할 것인가?
- 인덱스가 있는데도 느릴 수 있는 이유는 무엇인가?
- N+1 문제를 어떻게 발견하고 해결할 것인가?

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 서브쿼리와 함수 때문에 못 탄 인덱스

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Optimizing SELECT Statements](https://dev.mysql.com/doc/refman/8.4/en/select-optimization.html)
- [MySQL 8.4: EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/database/db-index|db-index]]
- [[01-core/database/execution-plan|execution-plan]]
- [[01-core/jpa/n-plus-one-and-fetch-join|n-plus-one-and-fetch-join]]
