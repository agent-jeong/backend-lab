---
title: Collection Selection
description: Java List, Set, Map 선택 기준과 실무 사용 패턴
---

# Collection Selection

## 한 줄 정의

Java 컬렉션 선택은 데이터를 순서대로 다룰지, 중복을 제거할지, key로 빠르게 찾을지에 따라 `List`, `Set`, `Map` 중 적절한 구조를 고르는 일이다.

## 실무에서 왜 중요한가

백엔드 코드는 DB에서 가져온 데이터를 응답 DTO로 조립하고, 중복을 제거하고, id 기준으로 다시 찾는 일이 많다.

컬렉션을 잘못 고르면 반복 조회가 늘어나고, 응답 순서가 흔들리며, 중복 key나 객체 동등성 문제로 버그가 생긴다.

## 한눈에 보는 선택 기준

| 필요 | 우선 고려 |
|---|---|
| 순서대로 보여줘야 함 | `List` |
| 중복을 제거해야 함 | `Set` |
| id/code로 빠르게 찾아야 함 | `Map` |
| 입력 순서를 유지해야 함 | `ArrayList`, `LinkedHashSet`, `LinkedHashMap` |
| 정렬된 상태가 필요함 | 정렬된 `List`, `TreeSet`, `TreeMap` |
| 여러 스레드가 동시에 수정함 | concurrent collection 또는 동기화 |

핵심 질문은 “이 데이터를 나중에 어떻게 다시 사용할 것인가?”이다.

## List

`List`는 순서가 있고 중복을 허용한다.

적합한 곳:

- API 응답 목록
- DB 조회 결과
- 페이지네이션 결과
- 정렬된 데이터
- 순서가 의미 있는 처리 대상

```java
List<OrderResponse> responses = orders.stream()
    .map(OrderResponse::from)
    .toList();
```

주의할 점은 반복 조회다. 반복문 안에서 계속 `stream().filter()`로 찾으면 데이터가 커질수록 비용이 커진다.

## Set

`Set`은 중복을 허용하지 않는다.

적합한 곳:

- 요청 id 중복 제거
- 이미 처리한 항목 기록
- 권한, 역할, 태그처럼 중복이 의미 없는 값
- 차집합, 교집합 계산

```java
Set<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .collect(Collectors.toSet());
```

`HashSet`은 순서를 보장하지 않는다. 응답 순서가 중요하면 `LinkedHashSet`이나 정렬된 `List`를 고려한다.

## Map

`Map`은 key로 value를 찾는다.

적합한 곳:

- id 기준으로 엔티티 조회
- code 기준 설정값 조회
- 여러 목록을 하나의 응답으로 조립
- 그룹별 데이터 묶기
- 카운트나 합계 집계

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

User user = userMap.get(order.getUserId());
```

`toMap()`은 key 중복 가능성을 확인해야 한다. 같은 key가 두 번 나오면 기본적으로 예외가 발생한다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

merge 전략은 “왜 새 값을 선택하는지”가 코드나 사전 정렬로 설명되어야 한다.

## 실무 패턴: 응답 조립

주문마다 사용자 목록을 다시 순회하면 비용이 커진다.

```java
List<OrderResponse> responses = orders.stream()
    .map(order -> {
        User user = users.stream()
            .filter(it -> it.getId().equals(order.getUserId()))
            .findFirst()
            .orElseThrow();

        return OrderResponse.of(order, user);
    })
    .toList();
```

반복 조회가 있으면 먼저 `Map`으로 바꾼다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

List<OrderResponse> responses = orders.stream()
    .map(order -> OrderResponse.of(order, userMap.get(order.getUserId())))
    .toList();
```

이 패턴은 JPA N+1을 줄인 뒤, 메모리에서 데이터를 조립할 때 자주 사용한다.

## 자주 나는 실수

- 데이터가 작다는 이유로 이중 반복을 계속 방치한다.
- 순서가 필요한 응답에 `HashSet`이나 `HashMap` 순서를 기대한다.
- 중복 key 가능성을 확인하지 않고 `Collectors.toMap()`을 사용한다.
- 객체를 `Set`에 넣으면서 `equals/hashCode` 기준을 확인하지 않는다.
- `Map`으로 바꾸면 무조건 좋은 줄 알고 코드를 불필요하게 복잡하게 만든다.

## 핵심 요약

순서가 중요하면 `List`, 중복 제거가 필요하면 `Set`, key로 반복 조회해야 하면 `Map`을 우선 고려한다.

실무에서는 응답 조립 과정에서 반복적인 `stream().filter()`가 보이면 `Map` 변환을 검토한다. 반대로 데이터가 작고 한 번만 순회한다면 `List`가 더 읽기 쉽다.

컬렉션 선택은 성능뿐 아니라 순서, 중복, 동등성, key 중복 가능성, 동시성 요구사항을 함께 보고 결정한다.

## 꼬리 질문

> [!question]- `List`, `Set`, `Map`은 각각 언제 선택하는가?
> 순서가 있고 중복을 허용하면 `List`, 중복 제거가 목적이면 `Set`, key로 빠르게 찾아야 하면 `Map`을 선택합니다.

> [!question]- 반복적인 `stream().filter()`가 문제 되는 이유는?
> 목록 안에서 다시 목록을 찾으면 반복 횟수가 커집니다. 반복 조회가 있으면 `Map`으로 바꿔 key 기반 조회를 고려합니다.

> [!question]- `HashSet`은 중복을 어떤 기준으로 판단하는가?
> `hashCode()`로 bucket을 찾고 `equals()`로 같은 객체인지 확인합니다.

> [!question]- `Collectors.toMap()`에서 중복 key가 생기면?
> merge 전략이 없으면 `IllegalStateException`이 발생합니다. 세 번째 인자로 merge function을 지정해야 합니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[hashmap]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/jpa/jpa|jpa]]
