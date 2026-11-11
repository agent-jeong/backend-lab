---
title: QueryDSL
description: QueryDSL이 동적 검색 조건을 어떻게 쉽게 만들고, 무엇은 여전히 직접 챙겨야 하는지
tags: [concept, jpa]
---

# QueryDSL

QueryDSL은 JPQL을 문자열 대신 Java 코드로 쓰게 해 주는 도구다. 필드 이름을 잘못 쓰면 컴파일할 때 잡힌다. 주문 검색처럼 조건이 선택적으로 붙는 쿼리와 복잡한 조회 쿼리에 주로 쓴다.

검색 조건이 늘수록 JPQL 문자열을 이어 붙이는 코드는 복잡해지고, 오타는 실행해 봐야 터진다. QueryDSL은 이런 실수를 컴파일할 때 잡아 준다. 다만 JPA 위에서 쿼리를 쓰는 도구일 뿐이라 N+1, fetch join, 영속성 컨텍스트 문제는 그대로 남는다.

> [!tip] 함께 읽기
> - [[querydsl-practical-usage]]: Repository에서 자주 쓰는 코드 패턴 모음

## 왜 쓰나

| 이유 | 설명 |
|---|---|
| 타입 안전성 | 컬럼명이나 필드가 바뀌면 컴파일할 때 오류가 난다 |
| 동적 쿼리 | 조건이 있을 때만 `where` 절에 넣기 쉽다 |
| 가독성 | 긴 JPQL 문자열보다 Java 코드가 쿼리 흐름을 읽기 쉽다 |
| 재사용 | BooleanExpression이나 조건 메서드로 조건을 떼어 낼 수 있다 |
| DTO 조회 | 필요한 컬럼만 골라 응답 전용 객체로 받을 수 있다 |

## 동작

1. Entity마다 Q-Type 클래스가 만들어진다.
2. `JPAQueryFactory`로 쿼리를 조립한다.
3. `select`, `from`, `join`, `where`, `orderBy`, `offset`, `limit`을 Java 코드로 쓴다.
4. QueryDSL이 이를 JPQL로 바꾼다.
5. Hibernate 같은 JPA 구현체가 JPQL을 SQL로 바꿔 DB에 실행한다.

QueryDSL이 SQL을 직접 실행하는 게 아니다. 그래서 JPA의 fetch 전략, 영속성 컨텍스트, N+1, flush가 그대로 따라온다.

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

private BooleanExpression createdAtLoe(LocalDateTime to) {
    return to == null ? null : order.createdAt.loe(to);
}
```

`where`는 `null` 조건을 그냥 건너뛴다. 그래서 조건 메서드가 값이 없을 때 `null`을 돌려주게 만들면, 들어온 조건만 붙는 쿼리가 깔끔하게 만들어진다.

## 언제 쓰나

| 상황 | QueryDSL을 쓸까 | 이유 |
|---|---|---|
| 단순 id 조회 | 필요 없다 | Spring Data JPA 메서드로 충분하다 |
| 조건이 여러 개이고 선택적으로 붙는다 | 쓴다 | 동적 where를 만들기 쉽다 |
| join과 정렬이 복잡하다 | 쓴다 | JPQL 문자열보다 고치기 쉽다 |
| DB 전용 문법이 많다 | 조심 | native query나 SQL mapper가 나을 수 있다 |
| 대량 수정/삭제 | 조심 | 영속성 컨텍스트와 DB 값이 어긋날 수 있다 |
| 복잡한 리포트 쿼리 | 경우에 따라 | SQL로 읽히고 실행 계획을 보기 쉬운 게 더 중요할 수 있다 |

## DTO Projection

| 방식 | 특징 | 주의점 |
|---|---|---|
| `Projections.constructor` | 생성자 인자 순서대로 넣는다 | 파라미터 순서가 바뀌면 값이 엉뚱한 데 들어간다 |
| `Projections.fields` | 필드 이름으로 넣는다 | setter나 필드 접근이 되고 이름이 같아야 한다 |
| `@QueryProjection` | 컴파일할 때 타입을 검사한다 | DTO가 QueryDSL에 의존하게 된다 |

API 응답에만 쓸 조회라면 Entity를 통째로 가져오기보다 필요한 컬럼만 DTO로 받는 편이 낫다. 그렇다고 projection만 한다고 쿼리가 빨라지지는 않는다. 속도는 join 조건, where 조건, 인덱스, 정렬 비용이 정한다.

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

목록 쿼리와 count query는 따로 짠다. 목록에 필요한 join과 projection이 count에는 대개 필요 없다. 데이터가 많아 count가 비싸면 `Slice`를 쓰거나, 다음 페이지가 있는지만 보거나, count를 아예 빼는 쪽을 따져 본다.

## 자주 깨지는 곳

- QueryDSL을 쓰면 N+1이 사라진다고 믿으면, 조회 전략을 안 짜서 N+1이 그대로 난다.
- 목록 조회에 fetch join과 페이징을 같이 쓰면, 컬렉션일 때 메모리에서 페이징한다.
- count query에 목록용 join을 그대로 넣으면, count가 목록보다 더 느려진다.
- DTO projection만 하고 끝내면, 인덱스, 정렬, where 조건이 그대로라 느린 것도 그대로다.
- BooleanExpression 조건 메서드를 자꾸 늘리면, 검색 조건이 어떻게 붙는지 오히려 안 읽힌다.
- 벌크 update/delete 뒤 영속성 컨텍스트를 비우지 않으면, 이미 불러온 Entity와 DB 값이 어긋난다.

## 운영에서 볼 것

- 테스트로 조건 조합마다 where 절이 생각대로 붙는지 확인한다.
- 로그에서 실제로 나간 SQL, 바인딩된 파라미터, 쿼리 수를 본다.
- 실행 계획으로 where, join, order by, limit에 인덱스가 쓰이는지 본다.
- 목록 쿼리와 count query의 실행 시간과 읽은 행 수를 따로 본다.

## 한 번에 설명하기

> QueryDSL은 JPQL을 Java 코드로 쓰게 해서 오타를 컴파일할 때 잡아 주는 도구이고, 무엇보다 선택적인 검색 조건을 붙이기 쉽습니다.
>
> 하지만 JPA 위에서 도는 거라 N+1, fetch join, 벌크 연산에서 조심할 점은 그대로입니다.
>
> 그래서 저는 QueryDSL을 쿼리를 편하게 쓰는 도구 정도로 보고, 실제로 나가는 SQL과 실행 계획은 꼭 확인합니다. 페이징에서는 count query를 따로, 단순하게 만듭니다.

## 꼬리 질문

> [!question]- QueryDSL을 왜 사용하는가?
> 문자열 JPQL과 달리 오타가 컴파일할 때 잡히고, 조건을 골라 붙이기 쉬워서입니다. 검색 조건이 많고 그중 일부만 들어오는 목록 API에서 특히 편합니다.

> [!question]- QueryDSL을 쓰면 N+1이 해결되는가?
> 아닙니다. QueryDSL은 쿼리를 쓰는 도구일 뿐입니다. N+1은 fetch join, batch size, DTO 직접 조회 같은 조회 방법을 따로 정해야 풀립니다.

> [!question]- QueryDSL DTO projection의 장점과 한계는?
> 필요한 컬럼만 가져오니까 API 응답에만 쓸 조회에 좋습니다. 대신 DTO 구조와 쿼리가 단단히 묶이고, join, where, order by가 비효율적이면 projection만으로는 빨라지지 않습니다.

> [!question]- 페이징에서 count query를 왜 분리하는가?
> 목록에는 필요한 join이 count에는 필요 없는 경우가 많아서입니다. count query를 단순하게 만들지 않으면, 페이지 목록보다 count가 더 느려질 수 있습니다.

> [!question]- QueryDSL 벌크 update/delete 후 주의할 점은?
> 벌크 연산은 영속성 컨텍스트를 거치지 않아서, 이미 불러온 Entity와 DB 값이 달라질 수 있습니다. 실행한 뒤 `clear()`하거나, 트랜잭션을 아예 나눠야 합니다.

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

2026년 11월에 확인한 공식 문서다.

- [Querydsl Reference](http://querydsl.com/static/querydsl/latest/reference/html/)
- [Querydsl (OpenFeign fork, maintained)](https://github.com/OpenFeign/querydsl)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[n-plus-one-and-fetch-join]]
- [[transaction-and-flush]]
- [[pagination-and-bulk-query]]
- [[db-index]]
- [[02-practical-backend/performance/performance|performance]]
