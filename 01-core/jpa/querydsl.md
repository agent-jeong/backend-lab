---
title: QueryDSL
description: QueryDSL을 이용한 타입 안전 동적 쿼리와 조회 성능 설계
---

# QueryDSL

## 한 줄 정의

QueryDSL은 Java 코드로 타입 안전하게 JPQL 쿼리를 작성하게 해주는 도구로, 동적 검색 조건과 복잡한 조회 쿼리를 다룰 때 자주 사용한다.

## 실무에서 왜 중요한가

QueryDSL을 이해하지 못하면 다음 문제가 생긴다.

- 검색 조건이 늘어날수록 JPQL 문자열 조합이 복잡해지고 런타임 오류가 늘어난다.
- 동적 조건, 정렬, 페이징, DTO 조회를 일관된 방식으로 작성하지 못한다.
- QueryDSL을 쓰면 JPA 성능 문제가 자동으로 해결된다고 오해한다.
- fetch join, count query, projection을 잘못 사용해 N+1이나 느린 페이징 쿼리를 만든다.

## QueryDSL을 사용하는 이유

| 이유 | 설명 |
|---|---|
| 타입 안전성 | 컬럼명이나 필드 변경 시 컴파일 단계에서 오류를 찾기 쉽다 |
| 동적 쿼리 | 조건이 있을 때만 `where` 절에 추가하기 쉽다 |
| 가독성 | 복잡한 JPQL 문자열보다 Java 코드로 쿼리 흐름을 읽기 쉽다 |
| 재사용 | BooleanExpression, predicate helper로 조건을 분리할 수 있다 |
| DTO 조회 | 필요한 컬럼만 선택해 응답 전용 객체로 조회할 수 있다 |

## 동작 방식

1. Entity를 기준으로 Q-Type이 생성된다.
2. `JPAQueryFactory`로 쿼리를 조립한다.
3. `select`, `from`, `join`, `where`, `orderBy`, `offset`, `limit`을 Java 코드로 작성한다.
4. QueryDSL은 이를 JPQL로 변환한다.
5. Hibernate 같은 JPA 구현체가 JPQL을 SQL로 변환해 DB에 실행한다.

QueryDSL은 SQL을 직접 실행하는 도구가 아니라 JPQL 작성을 도와주는 도구다. 따라서 JPA의 fetch 전략, 영속성 컨텍스트, N+1, flush 같은 특성은 그대로 영향을 준다.

## 동적 조건 예시

```java
public List<OrderSummary> search(OrderSearchCondition condition) {
    return queryFactory
        .select(Projections.constructor(
            OrderSummary.class,
            order.id,
            order.status,
            user.name,
            order.createdAt
        ))
        .from(order)
        .join(order.user, user)
        .where(
            statusEq(condition.status()),
            createdAtGoe(condition.from()),
            createdAtLoe(condition.to())
        )
        .orderBy(order.createdAt.desc())
        .limit(50)
        .fetch();
}

private BooleanExpression statusEq(OrderStatus status) {
    return status == null ? null : order.status.eq(status);
}

private BooleanExpression createdAtGoe(LocalDateTime from) {
    return from == null ? null : order.createdAt.goe(from);
}
```

QueryDSL의 `where`는 `null` 조건을 무시할 수 있어 동적 검색 조건을 조립하기 좋다.

## 실무 판단 기준

| 상황 | QueryDSL 사용 판단 | 이유 |
|---|---|---|
| 단순 id 조회 | 불필요 | Spring Data JPA 메서드로 충분하다 |
| 조건이 여러 개이고 선택적임 | 적합 | 동적 where 조립이 쉽다 |
| 복잡한 join과 정렬이 필요함 | 적합 | JPQL 문자열보다 유지보수하기 쉽다 |
| DB 특화 문법이 많음 | 주의 | native query나 SQL mapper가 더 적합할 수 있다 |
| 대량 수정/삭제 | 주의 | 영속성 컨텍스트와 불일치가 생길 수 있다 |
| 리포트성 복잡 쿼리 | 조건부 적합 | SQL 가독성과 실행 계획 확인이 더 중요할 수 있다 |

## DTO Projection

| 방식 | 특징 | 주의점 |
|---|---|---|
| `Projections.constructor` | 생성자 기반 매핑 | 파라미터 순서가 바뀌면 위험하다 |
| `Projections.fields` | 필드명 기반 매핑 | setter/field 접근과 이름 일치에 의존한다 |
| `@QueryProjection` | 컴파일 타임 타입 체크 가능 | DTO가 QueryDSL 의존성을 가진다 |

실무에서는 API 응답 전용 조회라면 Entity를 그대로 반환하기보다 필요한 컬럼만 DTO로 조회하는 편이 낫다. 단, DTO projection을 쓴다고 자동으로 쿼리가 빨라지는 것은 아니며 join 조건, where 조건, 인덱스, 정렬 비용을 함께 봐야 한다.

## 페이징과 Count Query

```java
List<OrderSummary> content = queryFactory
    .select(...)
    .from(order)
    .join(order.user, user)
    .where(...)
    .offset(pageable.getOffset())
    .limit(pageable.getPageSize())
    .fetch();

Long total = queryFactory
    .select(order.count())
    .from(order)
    .where(...)
    .fetchOne();
```

목록 조회 쿼리와 count query는 분리해서 생각해야 한다. 목록에는 join과 projection이 필요해도 count에는 불필요한 join이 많을 수 있다. 데이터가 많고 count 비용이 크면 `Slice`, 다음 페이지 존재 여부 조회, count 생략 전략을 검토한다.

## 자주 나는 실수

- QueryDSL을 쓰면 N+1이 자동으로 사라진다고 생각한다.
- 목록 조회에 fetch join과 페이징을 무심코 함께 사용한다.
- count query에 불필요한 join을 그대로 넣는다.
- DTO projection만 적용하고 인덱스, 정렬, where 조건을 확인하지 않는다.
- BooleanExpression helper가 너무 많아져 검색 조건 흐름을 읽기 어렵게 만든다.
- QueryDSL 벌크 update/delete 후 영속성 컨텍스트를 비우지 않는다.

## 확인 방법

- 테스트: 조건 조합별 where 절이 의도대로 적용되는지 확인한다.
- 로그: 실행 SQL, 바인딩 파라미터, 쿼리 수를 확인한다.
- 실행 계획: where, join, order by, limit에 인덱스가 사용되는지 본다.
- 성능: 목록 쿼리와 count query의 실행 시간, row scan 수를 따로 본다.

## 핵심 요약

QueryDSL은 JPQL을 문자열 대신 Java 코드로 안전하게 작성하게 해주는 도구다.

가장 큰 장점은 타입 안전성과 동적 검색 조건 조립이다.

하지만 QueryDSL은 JPA 위에서 동작하므로 N+1, fetch join, 영속성 컨텍스트, 벌크 연산의 주의점은 그대로 남는다.

DTO projection은 필요한 컬럼만 조회하는 데 유용하지만, 성능은 결국 join, where, order by, 인덱스, count query 설계에 좌우된다.

실무에서는 QueryDSL을 쿼리 작성 편의 도구로 보고, 실행 SQL과 실행 계획을 반드시 확인해야 한다.

## 꼬리 질문

> [!question]- QueryDSL을 왜 사용하는가?
> 문자열 JPQL보다 타입 안전하고, 동적 조건을 조립하기 쉽기 때문입니다. 특히 검색 조건이 많고 선택적으로 적용되는 목록 API에서 유용합니다.

> [!question]- QueryDSL을 쓰면 N+1이 해결되는가?
> 아닙니다. QueryDSL은 쿼리 작성 도구일 뿐입니다. N+1은 fetch join, batch size, DTO 직접 조회 등 조회 전략을 별도로 설계해야 해결됩니다.

> [!question]- QueryDSL DTO projection의 장점과 한계는?
> 필요한 컬럼만 조회할 수 있어 API 응답 전용 조회에 유리합니다. 하지만 DTO 구조와 쿼리가 강하게 연결되고, join/where/order by가 비효율적이면 projection만으로 성능 문제가 해결되지 않습니다.

> [!question]- 페이징에서 count query를 왜 분리하는가?
> 목록 조회에는 필요한 join이 count에는 불필요할 수 있습니다. count query를 단순화하지 않으면 페이지 목록보다 count가 더 느린 병목이 될 수 있습니다.

> [!question]- QueryDSL 벌크 update/delete 후 주의할 점은?
> 벌크 연산은 영속성 컨텍스트를 거치지 않으므로 이미 로딩된 Entity와 DB 상태가 달라질 수 있습니다. 실행 후 `clear()`하거나 트랜잭션 경계를 분리해야 합니다.

## 관련 문서

- [[jpa]]
- [[n-plus-one-and-fetch-join]]
- [[transaction-and-flush]]
- [[pagination-and-bulk-query]]
- [[db-index]]
- [[performance]]
