---
title: HashMap
description: Java HashMap의 동작 원리와 실무 사용 기준
---

# HashMap

## 한 줄 정의

`HashMap`은 key의 `hashCode()`로 저장 위치를 찾고, `equals()`로 같은 key인지 확인해서 값을 저장하고 조회하는 `Map` 구현체다.

## 실무에서 왜 중요한가

백엔드에서 `HashMap`은 DB 조회 결과를 id 기준으로 매핑하고, 여러 목록을 하나의 응답으로 조립하고, 반복적인 `List` 조회를 줄이는 기본 도구다.

하지만 key의 동등성 기준, 중복 key, 순서, 동시성 요구사항을 놓치면 조회 실패나 데이터 정합성 문제가 생긴다.

## 동작 원리

`HashMap`의 핵심은 두 단계다.

1. `hashCode()`로 bucket 위치를 찾는다.
2. 같은 bucket 안에서 `equals()`로 같은 key인지 확인한다.

같은 key면 값을 덮어쓰고, 다른 key면 같은 bucket 안에 함께 저장한다. 데이터가 많아지면 내부 배열을 늘리고 다시 배치한다.

## 언제 쓰는가

| 상황 | 선택 |
|---|---|
| key로 빠르게 찾아야 함 | `HashMap` |
| 입력 순서를 유지해야 함 | `LinkedHashMap` |
| key 정렬이 필요함 | `TreeMap` |
| 여러 스레드가 동시에 읽고 씀 | `ConcurrentHashMap` |
| key가 enum임 | `EnumMap` |
| 데이터가 작고 한 번만 순회함 | `List` 유지도 가능 |

## 실무 패턴: List를 Map으로 바꾸기

주문 목록을 응답으로 만들 때 사용자 목록을 매번 순회하면 비용이 커진다.

```java
for (Order order : orders) {
    User user = users.stream()
        .filter(it -> it.getId().equals(order.getUserId()))
        .findFirst()
        .orElseThrow();
}
```

먼저 `HashMap`으로 바꾸면 id로 바로 찾을 수 있다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

for (Order order : orders) {
    User user = userMap.get(order.getUserId());
}
```

데이터가 작고 한 번만 순회한다면 `Map` 변환이 오히려 코드를 복잡하게 만들 수 있다. 반복 조회가 있을 때 효과가 크다.

## key 설계가 중요하다

객체를 key로 쓰려면 `equals()`와 `hashCode()`가 올바르게 구현되어야 한다.

```java
class UserKey {
    private final Long userId;

    UserKey(Long userId) {
        this.userId = userId;
    }
}

Map<UserKey, String> map = new HashMap<>();

map.put(new UserKey(1L), "ACTIVE");

String status = map.get(new UserKey(1L)); // equals/hashCode가 없으면 null 가능
```

실무에서는 객체 key가 꼭 필요하지 않다면 `Long`, `String`, enum처럼 동등성 기준이 명확한 값을 key로 쓰는 편이 안전하다.

key로 쓰는 값은 저장 후 바뀌면 안 된다. hash 값이 바뀌면 기존 bucket에서 찾지 못할 수 있다.

## 중복 key 처리

`Collectors.toMap()`은 중복 key가 생기면 기본적으로 예외가 발생한다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

merge 전략은 반드시 의도를 설명할 수 있어야 한다. “나중 값”이 최신이라는 보장이 없다면 정렬 기준이나 비교 기준을 먼저 정해야 한다.

## 자주 나는 실수

- key 객체의 `equals/hashCode`를 재정의하지 않는다.
- mutable 객체를 key로 사용하고 저장 후 값을 변경한다.
- 중복 key 가능성이 있는데 `toMap()` merge 전략을 지정하지 않는다.
- 순서가 필요한데 `HashMap`을 사용한다.
- 여러 스레드가 동시에 수정하는데 일반 `HashMap`을 사용한다.
- 작은 데이터까지 무조건 `Map`으로 바꿔 가독성을 떨어뜨린다.

## 핵심 요약

`HashMap`은 `hashCode()`로 위치를 찾고 `equals()`로 같은 key인지 확인한다. 그래서 key의 동등성 기준이 정확해야 한다.

실무에서는 반복적인 목록 조회를 줄이고 응답을 조립할 때 자주 사용한다. 순서가 필요하면 `LinkedHashMap`, 정렬이 필요하면 `TreeMap`, 동시 수정이 필요하면 `ConcurrentHashMap`을 고려한다.

중복 key, mutable key, 객체 key의 `equals/hashCode`는 코드 리뷰에서 반드시 확인해야 한다.

## 꼬리 질문

> [!question]- `HashMap`에서 `equals()`와 `hashCode()`가 모두 중요한 이유는?
> `hashCode()`로 bucket을 찾고 `equals()`로 같은 key인지 판단하기 때문입니다. 둘의 기준이 맞지 않으면 저장한 값을 다시 찾지 못할 수 있습니다.

> [!question]- `HashMap`은 입력 순서를 보장하는가?
> 보장하지 않습니다. 입력 순서가 필요하면 `LinkedHashMap`, 정렬 순서가 필요하면 `TreeMap`을 사용합니다.

> [!question]- `Collectors.toMap()`에서 중복 key가 생기면?
> merge 전략이 없으면 `IllegalStateException`이 발생합니다. 세 번째 인자로 merge function을 지정해야 합니다.

> [!question]- 언제 `ConcurrentHashMap`을 고려하는가?
> 여러 스레드가 같은 Map을 동시에 읽고 쓸 수 있을 때 고려합니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
