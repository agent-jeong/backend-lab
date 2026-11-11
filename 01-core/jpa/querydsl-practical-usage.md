---
title: QueryDSL 실무 활용
description: Spring Data JPA Repository에 QueryDSL을 붙여 검색 목록 API를 만드는 흔한 코드 모양
tags: [concept, jpa]
---

# QueryDSL 실무 활용

실무에서 QueryDSL은 거의 이 모양으로 쓴다. Spring Data JPA Repository에 Custom Repository를 붙이고, 구현체에서 `JPAQueryFactory`로 동적 조건, DTO 조회, 페이징 쿼리를 직접 쓴다.

가장 흔한 쓰임은 주문 관리 화면처럼 상태, 기간, 회원 같은 검색 조건이 골라서 들어오는 목록 API다. 코드는 길어도 구조는 단순하다. 속도는 QueryDSL을 썼느냐가 아니라, 목록 쿼리와 count query를 어떻게 나누고 정렬을 인덱스에 맞췄느냐에서 갈린다.

> [!tip] 함께 읽기
> - [[querydsl]]: QueryDSL을 왜, 언제 쓰는지와 동적 쿼리를 짜는 법

## 파일 구조

```text
order/
├── OrderRepository.java
├── OrderRepositoryCustom.java
├── OrderRepositoryImpl.java
├── OrderSearchCondition.java
└── OrderSummaryResponse.java
```

| 파일 | 하는 일 |
|---|---|
| `OrderRepository` | 기본 CRUD, 단순 조회 |
| `OrderRepositoryCustom` | QueryDSL로 만들 조회 메서드를 선언한다 |
| `OrderRepositoryImpl` | `JPAQueryFactory`로 실제 쿼리를 짠다 |
| `OrderSearchCondition` | 검색 조건 DTO |
| `OrderSummaryResponse` | 조회 결과 DTO |

예제 코드는 `QOrder.order`, `QUser.user`를 static import했다고 치고 읽는다. Spring Boot 3 이상이면 `EntityManager`를 `jakarta.persistence.EntityManager`에서 import했는지 확인한다.

## JPAQueryFactory 설정

```java
@Configuration
public class QuerydslConfig {

    @Bean
    public JPAQueryFactory jpaQueryFactory(EntityManager entityManager) {
        return new JPAQueryFactory(entityManager);
    }
}
```

`JPAQueryFactory`는 여러 스레드가 같이 써도 안전해서, Bean으로 하나 등록해 두고 Repository 구현체에 주입하는 방식을 가장 많이 쓴다.

## Repository 구성

```java
public interface OrderRepository
        extends JpaRepository<Order, Long>, OrderRepositoryCustom {
}
```

```java
public interface OrderRepositoryCustom {

    Page<OrderSummaryResponse> searchOrders(
            OrderSearchCondition condition,
            Pageable pageable
    );

    Slice<OrderSummaryResponse> searchOrdersSlice(
            OrderSearchCondition condition,
            Pageable pageable
    );
}
```

`OrderRepositoryCustom`을 `OrderRepository`에 붙이고, 구현체는 따로 클래스로 둔다. 구현체 이름은 프로젝트의 Spring Data JPA 버전과 팀 규칙에 맞춰 `OrderRepositoryImpl`이나 `OrderRepositoryCustomImpl`로 정한다.

## 검색 조건 DTO

```java
public record OrderSearchCondition(
        OrderStatus status,
        Long userId,
        LocalDateTime from,
        LocalDateTime to,
        Integer minPrice,
        Integer maxPrice
) {
}
```

조건 DTO는 Controller 요청 객체와 따로 둔다. 그래야 API 요청 형식이 바뀌어도 Repository 조회 조건은 손대지 않아도 된다.

## 응답 DTO

```java
public record OrderSummaryResponse(
        Long orderId,
        String userName,
        OrderStatus status,
        Integer totalPrice,
        LocalDateTime orderedAt
) {
}
```

목록 API에서는 Entity를 조회해서 응답 DTO로 바꾸기보다, 필요한 컬럼만 DTO로 바로 받는 경우가 많다.

## Custom Repository 구현

```java
@Repository
@RequiredArgsConstructor
public class OrderRepositoryImpl implements OrderRepositoryCustom {

    private final JPAQueryFactory queryFactory;

    @Override
    public Page<OrderSummaryResponse> searchOrders(
            OrderSearchCondition condition,
            Pageable pageable
    ) {
        List<OrderSummaryResponse> content = queryFactory
                .select(Projections.constructor(
                        OrderSummaryResponse.class,
                        order.id,
                        user.name,
                        order.status,
                        order.totalPrice,
                        order.createdAt
                ))
                .from(order)
                .join(order.user, user)
                .where(
                        statusEq(condition.status()),
                        userIdEq(condition.userId()),
                        orderedAtGoe(condition.from()),
                        orderedAtLoe(condition.to()),
                        priceGoe(condition.minPrice()),
                        priceLoe(condition.maxPrice())
                )
                .orderBy(toOrderSpecifiers(pageable.getSort()))
                .offset(pageable.getOffset())
                .limit(pageable.getPageSize())
                .fetch();

        Long total = queryFactory
                .select(order.count())
                .from(order)
                .where(
                        statusEq(condition.status()),
                        userIdEq(condition.userId()),
                        orderedAtGoe(condition.from()),
                        orderedAtLoe(condition.to()),
                        priceGoe(condition.minPrice()),
                        priceLoe(condition.maxPrice())
                )
                .fetchOne();

        return new PageImpl<>(content, pageable, total == null ? 0 : total);
    }
}
```

목록 쿼리와 count query는 나눈다. 목록에는 DTO projection과 join이 필요하지만, count query에서는 필요 없는 join을 뺄 수 있다.

이때 조건 메서드가 join한 별칭(`user`)을 쓰면 안 된다. join이 없는 count query에서 `user.id`를 쓰면 쿼리가 깨지거나 엉뚱한 결과가 나온다. 그래서 `userIdEq`는 `user.id`가 아니라 `order.user.id`를 쓴다. 이렇게 쓰면 Hibernate는 join 없이 `orders.user_id` 컬럼으로 거른다.

## 동적 조건 메서드

```java
private BooleanExpression statusEq(OrderStatus status) {
    return status == null ? null : order.status.eq(status);
}

private BooleanExpression userIdEq(Long userId) {
    return userId == null ? null : order.user.id.eq(userId); // user join 없이 orders.user_id로 거른다
}

private BooleanExpression orderedAtGoe(LocalDateTime from) {
    return from == null ? null : order.createdAt.goe(from);
}

private BooleanExpression orderedAtLoe(LocalDateTime to) {
    return to == null ? null : order.createdAt.loe(to);
}

private BooleanExpression priceGoe(Integer minPrice) {
    return minPrice == null ? null : order.totalPrice.goe(minPrice);
}

private BooleanExpression priceLoe(Integer maxPrice) {
    return maxPrice == null ? null : order.totalPrice.loe(maxPrice);
}
```

QueryDSL의 `where`는 `null` 조건을 건너뛰어서, 들어온 검색 조건만 깔끔하게 붙는다. 다만 이런 조건 메서드가 너무 많아지면 흐름이 오히려 안 보이니, 같은 도메인에서 여러 번 쓰는 조건만 떼어 낸다. OR 조합이 복잡하면 `BooleanBuilder`가 더 편할 때도 있다.

## 정렬 처리

```java
private OrderSpecifier<?>[] toOrderSpecifiers(Sort sort) {
    List<OrderSpecifier<?>> orders = new ArrayList<>();

    for (Sort.Order sortOrder : sort) {
        com.querydsl.core.types.Order direction = sortOrder.isAscending()
                ? com.querydsl.core.types.Order.ASC
                : com.querydsl.core.types.Order.DESC;

        switch (sortOrder.getProperty()) {
            case "orderedAt" -> orders.add(new OrderSpecifier<>(direction, order.createdAt));
            case "totalPrice" -> orders.add(new OrderSpecifier<>(direction, order.totalPrice));
            default -> {
                // 허용하지 않는 정렬 필드는 무시하거나 예외로 처리한다.
            }
        }
    }

    if (orders.isEmpty()) {
        orders.add(order.createdAt.desc());
    }

    return orders.toArray(OrderSpecifier[]::new);
}
```

정렬 필드는 요청으로 들어온 값을 그대로 경로로 바꾸지 말고, 허용하는 필드 목록을 정해 둔다. 정렬 컬럼을 하나 늘릴 때마다 그 정렬이 인덱스를 타는지 실행 계획으로 확인한다.

## Slice 조회

```java
@Override
public Slice<OrderSummaryResponse> searchOrdersSlice(
        OrderSearchCondition condition,
        Pageable pageable
) {
    List<OrderSummaryResponse> content = queryFactory
            .select(Projections.constructor(
                    OrderSummaryResponse.class,
                    order.id,
                    user.name,
                    order.status,
                    order.totalPrice,
                    order.createdAt
            ))
            .from(order)
            .join(order.user, user)
            .where(
                    statusEq(condition.status()),
                    userIdEq(condition.userId()),
                    orderedAtGoe(condition.from()),
                    orderedAtLoe(condition.to())
            )
            .orderBy(order.createdAt.desc())
            .offset(pageable.getOffset())
            .limit(pageable.getPageSize() + 1)
            .fetch();

    boolean hasNext = content.size() > pageable.getPageSize();
    if (hasNext) {
        content.remove(pageable.getPageSize());
    }

    return new SliceImpl<>(content, pageable, hasNext);
}
```

전체 개수가 필요 없는 무한 스크롤이나 더보기 API는 `Page`보다 `Slice`가 낫다. `pageSize + 1`건을 읽어 보면 count query 없이도 다음 페이지가 있는지 안다.

## 무엇으로 조회하나

| 상황 | 이걸 쓴다 |
|---|---|
| 단순 CRUD | Spring Data JPA 기본 메서드 |
| 조건이 고정된 단순 조회 | 메서드 쿼리나 `@Query` |
| 골라서 들어오는 검색 조건이 많다 | QueryDSL |
| 목록 API 응답을 DTO로 받는다 | QueryDSL DTO projection |
| 전체 개수가 필요하다 | `Page` + count query 따로 |
| 전체 개수가 필요 없다 | `Slice` |
| 복잡한 통계나 DB 함수 | native query나 SQL mapper를 따져 본다 |

## 자주 깨지는 곳

- 검색 조건 DTO나 응답 DTO를 Entity와 섞어 쓰면, API 형식이 바뀔 때 Repository까지 고쳐야 한다.
- where 조건 메서드가 null을 처리하지 않으면, 선택 조건이 비었을 때 NPE가 나거나 조건이 잘못 붙는다.
- 모든 조회를 메서드 하나에 몰아넣으면, QueryDSL 코드가 길어져서 읽을 수가 없다.
- count query에 목록용 join을 그대로 두면, DTO projection을 써도 필요 없는 join 때문에 count가 느려진다.
- `Page`가 필요 없는데 습관처럼 count query를 돌리면, `Slice`로 충분한 곳에서 비용만 쓴다.
- 정렬 파라미터를 검증하지 않으면, 생각지 못한 정렬이나 인덱스를 못 타는 정렬이 들어온다.
- `offset`이 큰 페이지도 같은 방식으로 조회하면, 데이터가 커질수록 느려진다. 그때는 마지막으로 본 값 다음부터 읽는 커서 기반 페이징(keyset pagination)을 따져 본다([[pagination-and-bulk-query]]).
- QueryDSL을 썼으니 됐다고 실행 계획을 안 보면, 느린 SQL은 그대로 남는다.
- 벌크 연산 뒤 영속성 컨텍스트를 정리하지 않으면, 이미 불러온 Entity와 DB 값이 어긋난다.

## 한 번에 설명하기

> 실무에서는 Spring Data JPA Repository에 Custom Repository를 붙이고, 구현체에서 `JPAQueryFactory`로 검색 조건이 많은 목록 API를 만듭니다. 조건은 `BooleanExpression`을 돌려주는 메서드로 나누고, 값이 없으면 null을 돌려줘서 `where`가 건너뛰게 합니다.
>
> 목록 쿼리와 count query는 나누고, 전체 개수가 필요 없으면 `Slice`로 count를 아예 안 돌립니다.
>
> 속도는 QueryDSL을 썼는지가 아니라 실제로 나가는 SQL, 인덱스, join, 정렬, count를 어떻게 짰는지로 확인합니다.

## 꼬리 질문

> [!question]- QueryDSL을 Repository 어디에 두는가?
> 보통 Spring Data JPA Repository에 Custom Repository 인터페이스를 붙이고, 따로 만든 구현체에서 `JPAQueryFactory`를 씁니다. 구현체 이름은 프로젝트의 Spring Data JPA 버전과 팀 규칙에 맞춥니다.

> [!question]- Page와 Slice는 언제 나누는가?
> 전체 개수가 필요하면 `Page`, 다음 페이지가 있는지만 알면 되면 `Slice`를 씁니다. `Slice`는 count query를 안 돌려도 돼서 데이터가 많은 목록에서 덕을 볼 수 있습니다.

> [!question]- 동적 조건은 `BooleanBuilder`와 `BooleanExpression` 중 무엇을 쓰는가?
> 둘 다 되지만, 저는 조건마다 `BooleanExpression`을 돌려주는 메서드를 만드는 쪽을 주로 씁니다. 다른 쿼리에서 다시 쓰기 쉽고 읽기도 편해서요. OR 조합이 복잡하면 `BooleanBuilder`가 더 편할 때도 있습니다.

> [!question]- DTO projection을 쓰면 Entity 조회보다 항상 좋은가?
> 아닙니다. 필요한 컬럼만 가져오는 건 좋지만, join과 정렬이 비효율적이면 여전히 느립니다. 응답에만 쓸 목록 조회에는 쓸 만해도, 실행 계획은 따로 봐야 합니다.

> [!question]- QueryDSL 목록 API에서 가장 먼저 확인할 성능 포인트는?
> 실제로 나가는 SQL부터 봅니다. 그다음 where 조건이 인덱스를 타는지, order by가 얼마나 비싼지, count query가 얼마나 걸리는지, 필요 없는 join이 붙어 있지 않은지를 봅니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Page와 Slice를 나누는 실무 기준은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="전체 개수가 꼭 필요하면 Page, 다음 페이지 존재 여부만 필요하면 count query를 피할 수 있는 Slice를 고려한다." aria-pressed="false">A. 전체 count 필요 여부</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Slice가 항상 모든 경우에 더 적합한 것은 아니다." aria-pressed="false">B. 데이터가 하나라도 있으면 무조건 Slice만 쓴다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DTO 사용 여부만으로 Page/Slice가 결정되지는 않는다." aria-pressed="false">C. DTO projection을 쓰면 항상 Page를 금지한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>동적 조건을 BooleanExpression helper로 분리하면 조건 재사용과 테스트가 쉬워질 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="null이면 조건에서 제외되는 방식으로 조합하면 검색 조건이 늘어도 가독성을 유지하기 쉽다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="BooleanExpression helper는 동적 조건을 명시적으로 구성하는 데 유용하다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>QueryDSL 목록 API에서 가장 먼저 확인할 성능 포인트는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="join으로 인한 row 증가, N+1, count query 비용, 정렬 인덱스 사용 여부를 확인해야 한다." aria-pressed="false">A. join/N+1/count/정렬 인덱스</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="메서드명이 짧다고 성능이 보장되지 않는다." aria-pressed="false">B. Repository 메서드명 길이</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="패키지 경로 길이와 SQL 성능은 직접 관련이 없다." aria-pressed="false">C. Q클래스 패키지 경로 길이</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Querydsl Reference](http://querydsl.com/static/querydsl/latest/reference/html/)
- [Querydsl (OpenFeign fork, maintained)](https://github.com/OpenFeign/querydsl)
- [Spring Data JPA: Querydsl Extension](https://docs.spring.io/spring-data/jpa/reference/repositories/core-extensions.html)

## 관련 문서

- [[querydsl]]
- [[01-core/jpa/jpa|jpa]]
- [[n-plus-one-and-fetch-join]]
- [[pagination-and-bulk-query]]
- [[db-index]]
- [[02-practical-backend/performance/performance|performance]]
