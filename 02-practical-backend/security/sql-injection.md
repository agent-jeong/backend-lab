---
title: SQL Injection
description: 사용자 입력이 SQL 구조를 바꾸는 취약점과 방어 기준
---

# SQL Injection

SQL Injection은 사용자 입력이 SQL 값이 아니라 SQL 문법의 일부로 해석돼 의도하지 않은 조회, 변경, 인증 우회가 일어나는 취약점이다. 로그인 우회, 데이터 유출, 대량 수정·삭제로 이어진다. 방어의 원칙은 하나다. SQL 구조와 값을 분리한다.

## 공격이 성립하는 순서

1. 서버가 사용자 입력을 받는다.
2. 입력값을 SQL 문자열에 그대로 이어 붙인다.
3. DB는 그 입력을 데이터가 아니라 SQL 문법으로 해석한다.
4. 공격자는 조건을 우회하거나 SQL 조각을 더 끼워 넣는다.

```java
@Query("select o from Order o where o.userId = :userId and o.status = :status")
List<Order> findOrders(long userId, OrderStatus status);
```

입력값은 SQL 문자열에 붙이지 않고 parameter로 넘긴다. 정렬 컬럼처럼 binding할 수 없는 값은 enum이나 allowlist로 제한한다.

## 상황별 대응

검색, 정렬, 동적 조건처럼 사용자 입력이 SQL에 들어가는 경로에서 자주 터진다.

| 상황 | 대응 | 이유 |
|---|---|---|
| where 조건 값 | parameter binding | 값을 SQL 문법과 분리한다 |
| 동적 정렬 컬럼 | allowlist 매핑 | 컬럼명은 binding 대상이 아니므로 허용 목록이 필요하다 |
| 검색 조건 조립 | Query Builder 사용 | 문자열 연결 실수를 줄인다 |
| native query | binding과 리뷰 강화 | ORM 보호 범위 밖으로 나갈 수 있다 |
| 에러 응답 | 일반화된 메시지 | DB 구조 노출을 줄인다 |

| 방어 | 막는 것 | 약한 곳 |
|---|---|---|
| Parameter binding | 값 자리에 들어오는 injection | 컬럼명, 정렬 방향 같은 SQL 구조에는 직접 적용되지 않는다 |
| Allowlist | 동적 컬럼과 정렬을 안전하게 제한한다 | 허용 목록을 관리해야 한다 |
| Query Builder | 동적 query 조립 실수를 줄인다 | 잘못 쓰면 여전히 위험하다 |

컬럼명, 정렬 방향, 테이블명처럼 SQL 구조를 바꾸는 입력은 allowlist로 제한한다.

## 자주 깨지는 곳

- **ORM을 쓰면 SQL Injection이 불가능하다고 생각한다.** native query, 문자열 기반 동적 query, order by 조립에는 위험이 그대로 남는다.
- **`order by` 컬럼명을 사용자 입력으로 그대로 붙인다.**
- **검색어를 문자열 연결로 `like '%...%'`에 넣는다.**
- **관리자용 내부 도구라서 입력 검증을 생략한다.** 내부 도구도 같은 binding 기준을 적용한다.
- **SQL 에러 원문을 API 응답으로 내보낸다.** 테이블 구조와 쿼리 형태가 드러난다.

## 확인하는 법

- 코드 리뷰: SQL 문자열 연결 지점을 검색한다.
- 테스트: 특수 문자와 SQL 예약어가 값으로 처리되는지 본다.
- 정적 분석: native query, raw query, 문자열 기반 동적 query를 점검한다.
- 로그: SQL 에러가 외부 응답으로 나가지 않는지 확인한다.

## 면접에서 말하기

> SQL Injection은 사용자 입력이 값이 아니라 SQL 문법으로 해석될 때 생깁니다. 그래서 값은 parameter binding으로 SQL 구조와 분리합니다. ORM을 써도 native query나 동적 정렬처럼 문자열로 조립하는 곳은 위험이 남기 때문에, 컬럼명이나 정렬 방향처럼 binding할 수 없는 입력은 allowlist로 제한합니다. SQL 에러 원문은 응답에 노출하지 않고, 내부 도구에도 같은 기준을 적용합니다.

## 꼬리 질문

- Parameter binding은 SQL Injection을 어떻게 막나?
- ORM을 쓰는데도 SQL Injection이 생기는 경우는?
- 동적 정렬 조건은 어떻게 안전하게 처리하나?

## 관련 문서

- [[security]]
- [[01-core/database/database|database]]
- [[01-core/jpa/querydsl|querydsl]]
