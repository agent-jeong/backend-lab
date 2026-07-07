---
title: SQL Injection
description: 사용자 입력이 SQL 구조를 바꾸는 취약점과 방어 기준
---

# SQL Injection

## 한 줄 정의

SQL Injection은 사용자 입력이 SQL 값이 아니라 SQL 문법의 일부로 해석되어, 의도하지 않은 조회, 변경, 인증 우회가 발생하는 취약점이다.

## 실무에서 왜 문제 되는가

- 로그인 우회, 데이터 유출, 대량 수정/삭제 같은 큰 사고로 이어질 수 있다.
- 검색, 정렬, 동적 조건처럼 사용자 입력이 SQL에 들어가는 경로에서 자주 발생한다.
- ORM을 사용해도 native query, 문자열 기반 동적 query, order by 조립에서는 위험이 남는다.
- 에러 메시지가 자세하면 테이블 구조와 쿼리 형태가 노출될 수 있다.

## 동작 원리

1. 서버가 사용자 입력을 받는다.
2. 입력값을 SQL 문자열에 직접 이어 붙인다.
3. DB는 입력값을 데이터가 아니라 SQL 문법으로 해석한다.
4. 공격자는 조건을 우회하거나 추가 SQL 조각을 삽입한다.
5. 서버는 parameter binding과 허용 목록 기반 조립으로 SQL 구조와 값을 분리해야 한다.

## 실무 판단 기준

| 상황 | 대응 | 이유 |
|---|---|---|
| where 조건 값 | parameter binding | 값을 SQL 문법과 분리한다 |
| 동적 정렬 컬럼 | allowlist 매핑 | 컬럼명은 binding 대상이 아니므로 허용 목록이 필요하다 |
| 검색 조건 조립 | Query Builder 사용 | 문자열 연결 실수를 줄인다 |
| native query | binding과 리뷰 강화 | ORM 보호 범위 밖으로 나갈 수 있다 |
| 에러 응답 | 일반화된 메시지 | DB 구조 노출을 줄인다 |

## 자주 나는 실수

- ORM을 쓰면 SQL Injection이 불가능하다고 생각한다.
- `order by` 컬럼명을 사용자 입력으로 그대로 붙인다.
- 검색어를 문자열 연결로 `like '%...%'`에 넣는다.
- 관리자용 내부 도구라서 입력 검증을 생략한다.
- SQL 에러 원문을 API 응답으로 노출한다.

## 확인 방법

- 코드 리뷰: SQL 문자열 연결 지점을 검색한다.
- 테스트: 특수 문자와 SQL 예약어가 값으로 처리되는지 확인한다.
- 정적 분석: native query, raw query, 문자열 기반 동적 query를 점검한다.
- 로그: SQL 에러 응답이 외부로 노출되지 않는지 확인한다.

## 장점과 한계

| 방어 | 장점 | 한계 |
|---|---|---|
| Parameter binding | 값 기반 injection을 효과적으로 막는다 | 컬럼명, 정렬 방향 같은 SQL 구조에는 직접 적용되지 않는다 |
| Allowlist | 동적 컬럼과 정렬을 안전하게 제한한다 | 허용 목록 관리가 필요하다 |
| Query Builder | 동적 query 조립 실수를 줄인다 | 잘못 사용하면 여전히 위험하다 |

## 짧은 예제

```java
@Query("select o from Order o where o.userId = :userId and o.status = :status")
List<Order> findOrders(long userId, OrderStatus status);
```

입력값은 SQL 문자열에 직접 붙이지 않고 parameter로 전달한다. 정렬 컬럼처럼 binding할 수 없는 값은 enum이나 allowlist로 제한한다.

## 핵심 요약

SQL Injection은 사용자 입력이 SQL 문법으로 해석될 때 발생한다.

값은 parameter binding으로 SQL 구조와 분리해야 한다.

ORM을 사용해도 문자열 기반 native query와 동적 정렬에서는 위험이 남는다.

컬럼명, 정렬 방향, 테이블명처럼 SQL 구조를 바꾸는 입력은 allowlist로 제한한다.

SQL 에러 원문은 외부 응답에 노출하지 않는다.

내부 도구도 입력 검증과 binding 기준을 동일하게 적용해야 한다.

## 꼬리 질문

- Parameter binding은 SQL Injection을 어떻게 막는가?
- ORM을 쓰는데도 SQL Injection이 생길 수 있는 경우는 무엇인가?
- 동적 정렬 조건은 어떻게 안전하게 처리할 것인가?

## 관련 문서

- [[security]]
- [[01-core/database/database|database]]
- [[01-core/jpa/querydsl|querydsl]]
