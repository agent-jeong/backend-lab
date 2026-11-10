---
title: QueryDSL
description: QueryDSL을 이용한 타입 안전 동적 쿼리와 조회 성능 설계
tags: [concept, jpa]
---

# QueryDSL

QueryDSL은 JPQL을 문자열 대신 Java 코드로, 타입 안전하게 쓰게 해 주는 도구다. 동적 검색 조건과 복잡한 조회 쿼리에 주로 쓴다.

검색 조건이 늘수록 JPQL 문자열 조합은 복잡해지고 런타임 오류가 늘어난다. QueryDSL은 이걸 컴파일 단계로 끌어온다. 다만 **JPA 위에서 도는 쿼리 작성 도구일 뿐**이라 N+1, fetch join, 영속성 컨텍스트 문제는 그대로 남는다.

> [!tip] 함께 읽기
> - [[querydsl-practical-usage]]: Repository에서 자주 쓰는 코드 패턴 모음

## 왜 쓰나

| 이유 | 설명 |
|---|---|
| 타입 안전성 | 컬럼명이나 필드 변경 시 컴파일 단계에서 오류를 찾기 쉽다 |
| 동적 쿼리 | 조건이 있을 때만 `where` 절에 추가하기 쉽다 |
| 가독성 | 복잡한 JPQL 문자열보다 Java 코드로 쿼리 흐름을 읽기 쉽다 |
| 재사용 | BooleanExpression, predicate helper로 조건을 분리할 수 있다 |
| DTO 조회 | 필요한 컬럼만 선택해 응답 전용 객체로 조회할 수 있다 |

## 동작

1. Entity를 기준으로 Q-Type이 생성된다.
2. `JPAQueryFactory`로 쿼리를 조립한다.
3. `select`, `from`, `join`, `where`, `orderBy`, `offset`, `limit`을 Java 코드로 쓴다.
4. QueryDSL이 이를 JPQL로 바꾼다.
5. Hibernate 같은 JPA 구현체가 JPQL을 SQL로 바꿔 DB에 실행한다.

QueryDSL이 SQL을 직접 실행하는 게 아니다. 그래서 JPA의 fetch 전략, 영속성 컨텍스트, N+1, flush 같은 특성이 그대로 영향을 준다.

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

`where`가 `null` 조건을 무시하기 때문에, 조건 메서드가 값이 없을 때 `null`을 돌려주게 하면 동적 검색 조건이 깔끔하게 조립된다.

## 언제 쓰나

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

API 응답 전용 조회라면 Entity를 그대로 돌려주기보다 필요한 컬럼만 DTO로 조회하는 편이 낫다. 그렇다고 projection만으로 쿼리가 빨라지지는 않는다. 성능은 join 조건, where 조건, 인덱스, 정렬 비용이 정한다.

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

목록 쿼리와 count query는 따로 설계한다. 목록에 필요한 join과 projection이 count에는 대개 필요 없다. 데이터가 많아 count 비용이 크면 `Slice`, 다음 페이지 존재 여부만 조회, count 생략을 검토한다.

## 자주 깨지는 곳

- **QueryDSL을 쓰면 N+1이 사라진다고 믿는다.** 조회 전략은 따로 설계해야 한다.
- **목록 조회에 fetch join과 페이징을 같이 쓴다.** 컬렉션이면 메모리 페이징이 된다.
- **count query에 목록용 join을 그대로 넣는다.** count가 목록보다 느린 병목이 된다.
- **DTO projection만 하고 끝낸다.** 인덱스, 정렬, where 조건을 보지 않으면 느린 건 그대로다.
- **BooleanExpression helper를 계속 늘린다.** 검색 조건 흐름이 오히려 안 읽힌다.
- **벌크 update/delete 뒤 영속성 컨텍스트를 비우지 않는다.** 이미 로딩된 Entity와 DB 값이 어긋난다.

## 운영에서 볼 것

- 테스트: 조건 조합별로 where 절이 의도대로 붙는지 확인한다.
- 로그: 실행 SQL, 바인딩 파라미터, 쿼리 수.
- 실행 계획: where, join, order by, limit에 인덱스가 쓰이는지.
- 성능: 목록 쿼리와 count query의 실행 시간과 row scan 수를 따로 본다.

## 한 번에 설명하기

> QueryDSL은 JPQL을 Java 코드로 타입 안전하게 쓰게 해 주는 도구이고, 가장 큰 장점은 동적 검색 조건을 조립하기 쉽다는 점입니다. 하지만 JPA 위에서 동작하므로 N+1, fetch join, 벌크 연산의 주의점은 그대로 남습니다. 그래서 저는 QueryDSL을 쿼리 작성 편의 도구로 보고, 실행 SQL과 실행 계획을 꼭 확인하며, 페이징에서는 count query를 따로 단순하게 만듭니다.

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

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>QueryDSL을 사용하는 주된 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="동적 쿼리와 복잡한 조건을 타입 안전하게 작성하고 컴파일 시점에 필드 변경을 일부 잡을 수 있다." aria-pressed="false">A. 타입 안전한 동적 쿼리 작성을 돕기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="QueryDSL이 N+1을 자동으로 해결하지는 않는다." aria-pressed="false">B. QueryDSL을 쓰면 모든 N+1이 자동 해결된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="QueryDSL은 DB 인덱스를 자동 설계하지 않는다." aria-pressed="false">C. 인덱스를 자동으로 생성하기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>QueryDSL DTO projection은 필요한 컬럼만 조회할 수 있지만 Entity 변경 감지 대상은 아니다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="DTO는 영속성 컨텍스트가 관리하는 Entity가 아니므로 dirty checking 대상이 아니다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DTO projection과 Entity 조회는 목적과 동작이 다르다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>QueryDSL 벌크 update/delete 후 주의할 점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="벌크 연산은 영속성 컨텍스트를 우회하므로 기존 managed Entity와 DB 상태가 불일치할 수 있다." aria-pressed="false">A. 영속성 컨텍스트 clear 또는 동기화 전략이 필요하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="벌크 연산이 Entity 객체를 자동 갱신하지 않는다." aria-pressed="false">B. managed Entity 필드도 자동으로 모두 바뀐다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="벌크 연산이 DB 스키마를 자동 변경하는 기능은 아니다." aria-pressed="false">C. 테이블 컬럼 타입도 자동 변경된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Querydsl Reference](http://querydsl.com/static/querydsl/latest/reference/html/)
- [Querydsl (OpenFeign fork, maintained)](https://github.com/OpenFeign/querydsl)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[n-plus-one-and-fetch-join]]
- [[transaction-and-flush]]
- [[pagination-and-bulk-query]]
- [[db-index]]
- [[02-practical-backend/performance/performance|performance]]
