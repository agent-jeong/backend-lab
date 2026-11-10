---
title: DB 조회 성능
description: 느린 조회를 쿼리 수, 실행 계획, 인덱스, 데이터 크기로 분석하는 기준
tags: [concept, performance]
---

# DB 조회 성능

DB 조회 성능 개선은 쿼리 수, 실행 계획, 인덱스, 정렬/페이징, 반환 데이터 크기를 확인해 DB가 적은 비용으로 필요한 데이터를 찾게 만드는 작업이다.

대부분의 백엔드 성능 문제는 DB 조회 지연이나 쿼리 수 증가에서 시작한다. 인덱스가 있어도 조건, 정렬, selectivity에 따라 안 쓰일 수 있고, N+1은 데이터가 적을 때 숨어 있다가 운영 데이터에서 급격히 느려진다. 그래서 explain과 실제 측정 없이 추측으로 튜닝하지 않는다.

## 순서

1. 느린 API에서 실행된 SQL과 쿼리 수를 확인한다.
2. slow query와 execution plan을 본다.
3. where, join, order by, limit 조건이 인덱스와 맞는지 확인한다.
4. 반환 row 수와 컬럼 수가 필요한 범위인지 확인한다.
5. 쿼리 변경, 인덱스 추가, fetch 전략 조정 후 다시 측정한다.

```sql
select o.id, o.status, o.created_at
from orders o
where o.user_id = ?
  and o.created_at < ?
order by o.created_at desc
limit 20;
```

이 쿼리는 `user_id`, `created_at` 순서의 복합 인덱스를 검토할 만하다. 단, 실제 선택도와 실행 계획을 확인한 뒤에 정한다.

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

- **인덱스를 추가하면 항상 빨라진다고 생각한다.** 인덱스는 where와 order by 조건, 선택도, 데이터 분포에 맞아야 효과가 있다.
- **explain 없이 쿼리만 보고 병목을 추측한다.**
- **로컬의 작은 데이터로 성능을 판단한다.**
- **JPA fetch join을 무분별하게 늘린다.** row가 폭증한다.
- **offset pagination이 커져도 비용이 같다고 생각한다.** offset이 커질수록 scan 비용이 커진다.
- **count query와 목록 query의 비용이 같다고 생각한다.** 목록은 빨라도 count나 group by가 병목일 수 있다.
- **조회용 인덱스가 쓰기 성능과 lock 경합에 미치는 영향을 확인하지 않는다.**
- **필요 이상으로 가져온다.** 컬럼과 row가 많으면 DB, 네트워크, 애플리케이션 모두 비용이 는다.

## 운영에서 볼 것

- 운영과 비슷한 데이터 크기에서 조회 시간을 비교한다.
- SQL, query count, bind parameter, elapsed time을 로그로 확인한다.
- execution plan, rows examined, index usage, sort 방식, temporary table을 본다.
- DB CPU, buffer hit ratio, slow query count, connection usage를 본다.

## 한 번에 설명하기

> DB 조회 성능은 쿼리 수, 실행 계획, 인덱스, 반환 데이터 크기를 같이 봐야 합니다. 저는 먼저 느린 API의 SQL과 쿼리 수를 보고 N+1인지 확인한 뒤, explain으로 인덱스가 where와 order by 조건에 맞게 쓰이는지 봅니다. 큰 offset은 keyset pagination을 검토하고, 목록이 빨라도 count나 group by가 병목일 수 있어 따로 확인합니다. 추측이 아니라 explain과 실제 측정으로 판단합니다.

## 꼬리 질문

- 느린 조회 API를 만나면 DB에서 무엇부터 확인할 것인가?
- 인덱스가 있는데도 느릴 수 있는 이유는 무엇인가?
- N+1 문제를 어떻게 발견하고 해결할 것인가?

## 내 사례

- [[slow-admin-query-tuning|5초 걸리던 조회를 실행계획으로 고치기]]: 서브쿼리와 함수 때문에 못 탄 인덱스

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Optimizing SELECT Statements](https://dev.mysql.com/doc/refman/8.4/en/select-optimization.html)
- [MySQL 8.4: EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/database/db-index|db-index]]
- [[01-core/database/execution-plan|execution-plan]]
- [[01-core/jpa/n-plus-one-and-fetch-join|n-plus-one-and-fetch-join]]
