---
title: QueryDSL 실무 활용
description: Spring Data JPA에서 QueryDSL을 가장 자주 사용하는 Repository 코드 패턴
---

# QueryDSL 활용

## 한 줄 정의

QueryDSL 의 표준 패턴은 Spring Data JPA Repository에 Custom Repository를 붙이고, `JPAQueryFactory`로 동적 조건, DTO 조회, 페이징 쿼리를 명시적으로 작성하는 것이다.

## 실무에서 가장 많이 쓰는 구조

```text
order/
├── OrderRepository.java
├── OrderRepositoryCustom.java
├── OrderRepositoryImpl.java
├── OrderSearchCondition.java
└── OrderSummaryResponse.java
```

| 파일 | 역할 |
|---|---|
| `OrderRepository` | 기본 CRUD, 단순 조회 |
| `OrderRepositoryCustom` | QueryDSL로 구현할 조회 메서드 선언 |
| `OrderRepositoryImpl` | `JPAQueryFactory`를 사용한 실제 QueryDSL 구현 |
| `OrderSearchCondition` | 검색 조건 DTO |
| `OrderSummaryResponse` | 조회 결과 DTO |

예제 코드는 `QOrder.order`, `QUser.user`를 static import했다고 가정한다. Spring Boot 3 이상에서는 `EntityManager` import가 `jakarta.persistence.EntityManager`인지 확인한다.

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

`JPAQueryFactory`는 thread-safe하게 사용할 수 있으므로 Bean으로 등록해 Repository 구현체에 주입하는 패턴을 가장 자주 쓴다.

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

실무에서는 `OrderRepositoryCustom`을 `OrderRepository`에 붙이고, 구현체를 별도 클래스로 둔다. 구현체 이름은 프로젝트의 Spring Data JPA 버전과 컨벤션에 맞춰 `OrderRepositoryImpl` 또는 `OrderRepositoryCustomImpl`처럼 정한다.

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

조건 DTO는 Controller 요청 객체와 분리하는 편이 좋다. API 요청 형식이 바뀌어도 Repository 조회 조건은 안정적으로 유지할 수 있다.

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

목록 API에서는 Entity를 그대로 조회한 뒤 응답 DTO로 변환하기보다, 필요한 컬럼만 DTO로 직접 조회하는 패턴을 자주 사용한다.

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

실무에서는 목록 조회 쿼리와 count query를 분리한다. 목록 조회에는 DTO projection과 join이 필요하지만, count query에는 불필요한 join을 제거할 수 있기 때문이다.

## 동적 조건 Helper

```java
private BooleanExpression statusEq(OrderStatus status) {
    return status == null ? null : order.status.eq(status);
}

private BooleanExpression userIdEq(Long userId) {
    return userId == null ? null : user.id.eq(userId);
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

QueryDSL의 `where`는 `null` 조건을 무시하므로 선택 검색 조건을 깔끔하게 조립할 수 있다. 다만 helper가 너무 많아지면 오히려 흐름이 안 보이므로, 같은 도메인에서 재사용되는 조건만 분리한다.

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

정렬 필드는 외부 입력을 그대로 경로로 변환하지 말고 허용 목록을 둔다. 정렬 컬럼이 많아질수록 인덱스와 실행 계획 확인이 중요하다.

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

전체 개수가 꼭 필요하지 않은 무한 스크롤, 더보기 API는 `Page`보다 `Slice`가 실무적으로 유리하다. count query를 실행하지 않아도 다음 페이지 존재 여부를 알 수 있다.

## 자주 쓰는 선택 기준

| 상황 | 추천 |
|---|---|
| 단순 CRUD | Spring Data JPA 기본 메서드 |
| 단순 고정 조건 조회 | 메서드 쿼리 또는 `@Query` |
| 선택 검색 조건이 많음 | QueryDSL |
| 목록 API 응답 DTO 조회 | QueryDSL DTO projection |
| 전체 개수 필요 | `Page` + count query 분리 |
| 전체 개수 불필요 | `Slice` |
| 복잡한 통계/DB 함수 | native query 또는 SQL mapper 검토 |

## 실무 체크리스트

- 검색 조건 DTO와 응답 DTO를 Entity와 분리했는가?
- where 조건 helper가 null을 안전하게 처리하는가?
- 목록 query와 count query를 분리했는가?
- count query에 불필요한 join이 들어가지 않았는가?
- 정렬 필드를 허용 목록으로 제한했는가?
- `offset` 페이징이 느려질 데이터 규모라면 keyset pagination을 검토했는가?
- 실행 SQL과 실행 계획을 확인했는가?
- QueryDSL 벌크 연산 후 영속성 컨텍스트를 정리했는가?

## 자주 나는 실수

- QueryDSL 코드가 길어지는데도 모든 조회를 하나의 메서드에 몰아넣는다.
- DTO projection을 쓰면서도 불필요한 join을 많이 남긴다.
- `Page`가 필요 없는데 습관적으로 count query를 실행한다.
- 정렬 파라미터를 검증하지 않아 의도하지 않은 정렬을 허용한다.
- `offset`이 큰 페이지에서도 같은 방식으로 조회한다.
- QueryDSL을 썼다는 이유로 실행 계획 확인을 생략한다.

## 핵심 요약

실무에서 QueryDSL은 보통 Spring Data JPA Custom Repository 구현체 안에서 사용한다.

가장 흔한 용도는 선택 검색 조건이 많은 목록 API, DTO projection, 페이징 조회다.

동적 조건은 `BooleanExpression` helper로 분리하고, `where`에서 null 조건을 무시하는 특성을 활용한다.

목록 조회와 count query는 분리해서 작성하고, 전체 개수가 필요 없으면 `Slice`로 count query를 피한다.

QueryDSL은 쿼리 작성 편의 도구이므로 성능은 실행 SQL, 인덱스, join, 정렬, count query 설계로 검증해야 한다.

## 꼬리 질문

> [!question]- QueryDSL을 Repository 어디에 두는가?
> 보통 Spring Data JPA Repository에 Custom Repository 인터페이스를 붙이고, 별도 구현체에서 `JPAQueryFactory`를 사용합니다. 구현체 이름은 프로젝트의 Spring Data JPA 버전과 컨벤션에 맞춥니다.

> [!question]- Page와 Slice는 언제 나누는가?
> 전체 개수가 필요하면 `Page`, 다음 페이지 존재 여부만 필요하면 `Slice`를 사용합니다. `Slice`는 count query를 피할 수 있어 대용량 목록에서 유리할 수 있습니다.

> [!question]- 동적 조건은 `BooleanBuilder`와 `BooleanExpression` 중 무엇을 쓰는가?
> 둘 다 가능하지만, 실무에서는 재사용성과 가독성을 위해 조건별 `BooleanExpression` helper를 많이 사용합니다. 복잡한 OR 조합이 많으면 `BooleanBuilder`가 더 편할 수 있습니다.

> [!question]- DTO projection을 쓰면 Entity 조회보다 항상 좋은가?
> 아닙니다. 필요한 컬럼만 조회하는 장점은 있지만, join과 정렬이 비효율적이면 여전히 느립니다. 응답 전용 목록 조회에는 유용하지만 실행 계획 확인은 필요합니다.

> [!question]- QueryDSL 목록 API에서 가장 먼저 확인할 성능 포인트는?
> 실행 SQL, where 조건의 인덱스 사용 여부, order by 비용, count query 비용, 불필요한 join 여부를 확인합니다.

## 관련 문서

- [[querydsl]]
- [[jpa]]
- [[n-plus-one-and-fetch-join]]
- [[pagination-and-bulk-query]]
- [[db-index]]
- [[performance]]
