---
title: Collection Selection
description: Java List, Set, Map 선택 기준과 실무 사용 패턴
---

# Collection Selection

## 한 줄 정의

Java 컬렉션 선택은 데이터를 순서대로 다룰지, 중복을 제거할지, key로 빠르게 찾을지에 따라 `List`, `Set`, `Map` 중 적절한 구조를 고르는 일이다.

## 실무에서 왜 중요한가

실무 코드는 데이터를 가져오는 것보다 가져온 데이터를 가공하고 조립하는 일이 많다.

컬렉션을 잘못 고르면 다음 문제가 생긴다.

- `List`를 반복 순회해서 응답 조립 시간이 늘어난다.
- 중복 제거가 필요한데 `List`로 직접 처리하다가 누락된다.
- 순서가 중요한데 `HashSet`, `HashMap`을 사용해서 응답 순서가 흔들린다.
- key 조회가 필요한데 매번 `stream().filter()`를 사용한다.
- 정렬 기준이 필요한데 데이터 구조와 정렬 위치가 불명확해진다.

3년차 백엔드 개발자에게 중요한 것은 컬렉션 API를 많이 아는 것보다, “이 데이터는 어떤 방식으로 다시 사용될 것인가”를 보고 구조를 고르는 감각이다.

## 기본 선택 기준

| 필요 | 우선 고려 |
|---|---|
| 순서대로 보여줘야 한다 | `List` |
| 중복을 제거해야 한다 | `Set` |
| id나 code로 빠르게 찾아야 한다 | `Map` |
| 입력 순서를 유지해야 한다 | `ArrayList`, `LinkedHashSet`, `LinkedHashMap` |
| 정렬된 상태가 필요하다 | 정렬된 `List`, `TreeSet`, `TreeMap` |
| 여러 스레드가 동시에 수정한다 | concurrent collection 또는 동기화 검토 |

## List를 쓰는 경우

`List`는 순서가 있고 중복을 허용한다.

실무에서 자주 쓰는 경우는 다음과 같다.

- API 응답 목록
- DB 조회 결과
- 정렬된 데이터
- 페이지네이션 결과
- 순서가 의미 있는 처리 대상

```java
List<OrderResponse> responses = orders.stream()
    .map(OrderResponse::from)
    .toList();
```

`List`는 읽기 쉽고 자연스럽지만, 특정 값을 반복해서 찾아야 하면 비용이 커질 수 있다.

```java
User user = users.stream()
    .filter(it -> it.getId().equals(order.getUserId()))
    .findFirst()
    .orElseThrow();
```

이런 조회가 반복되면 `Map`으로 바꾸는 것을 검토한다.

## Set을 쓰는 경우

`Set`은 중복을 허용하지 않는다.

실무에서 자주 쓰는 경우는 다음과 같다.

- 요청에 중복 id가 있는지 제거할 때
- 이미 처리한 항목을 기록할 때
- 권한, 역할, 태그처럼 중복이 의미 없는 값을 다룰 때
- 두 집합의 차이, 교집합을 구할 때

```java
Set<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .collect(Collectors.toSet());
```

주의할 점은 `HashSet`은 순서를 보장하지 않는다는 것이다. 응답 순서가 중요하면 `LinkedHashSet`이나 정렬된 `List`를 고려한다.

## Map을 쓰는 경우

`Map`은 key로 value를 찾는다.

실무에서 자주 쓰는 경우는 다음과 같다.

- id 기준으로 엔티티를 빠르게 찾을 때
- code 기준으로 설정값을 찾을 때
- 그룹별 데이터를 묶을 때
- 여러 목록을 하나의 응답으로 조립할 때
- 카운트나 합계를 집계할 때

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

User user = userMap.get(order.getUserId());
```

`Map`을 만들 때는 key 중복 가능성을 반드시 확인해야 한다.

```java
Map<Long, Order> orderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getId,
        order -> order
    ));
```

같은 key가 두 번 나오면 예외가 발생한다. 중복 가능성이 있으면 merge 전략을 명시한다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

## 실무 패턴: 응답 조립

주문 목록과 사용자 목록을 조립한다고 가정한다.

나쁜 방향은 주문마다 사용자 목록을 다시 찾는 것이다.

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

데이터가 작을 때는 문제 없어 보이지만, 목록이 커지면 반복 횟수가 빠르게 늘어난다.

먼저 `Map`으로 바꾸면 의도가 명확해지고 조회 비용도 줄어든다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

List<OrderResponse> responses = orders.stream()
    .map(order -> OrderResponse.of(order, userMap.get(order.getUserId())))
    .toList();
```

이 패턴은 JPA N+1을 줄인 뒤, 메모리에서 데이터를 조립할 때도 자주 쓰인다.

## 자주 나는 실수

- 데이터가 작다는 이유로 이중 반복을 방치한다.
- 순서가 필요한 응답에 `HashSet`이나 `HashMap`의 순서를 기대한다.
- 중복 key 가능성을 확인하지 않고 `Collectors.toMap()`을 사용한다.
- 객체를 `Set`에 넣으면서 `equals/hashCode` 기준을 확인하지 않는다.
- `Map`으로 바꾸면 무조건 좋은 줄 알고 오히려 코드를 복잡하게 만든다.
- mutable collection을 외부에 그대로 반환해서 호출자가 수정하게 둔다.

## 판단 기준

| 질문 | 선택 힌트 |
|---|---|
| 이 데이터를 순서대로 보여줘야 하는가? | `List` |
| 중복이 있으면 안 되는가? | `Set` |
| 특정 id로 여러 번 찾아야 하는가? | `Map` |
| 입력 순서가 결과에 영향을 주는가? | `LinkedHashSet`, `LinkedHashMap`, 정렬된 `List` |
| key가 중복될 수 있는가? | `Map<K, List<V>>` 또는 merge 전략 |
| 동시 수정 가능성이 있는가? | 일반 collection 사용을 피하거나 동기화 검토 |

## 확인 방법

- 코드 리뷰에서 nested loop나 반복적인 `stream().filter()`를 찾는다.
- 응답 순서가 요구사항에 있는지 확인한다.
- 중복 제거 기준이 primitive 값인지 객체 동등성인지 확인한다.
- `toMap()` 사용 시 중복 key가 발생할 수 있는지 확인한다.
- 데이터 크기가 커질 때 반복 횟수가 어떻게 늘어나는지 계산한다.

## 면접 답변 1분 버전

Java 컬렉션은 데이터를 어떻게 다시 사용할지에 따라 선택합니다. 순서가 중요하고 중복을 허용하는 목록이면 `List`, 중복 제거가 목적이면 `Set`, id나 code로 빠르게 찾아야 하면 `Map`을 우선 고려합니다. 실무에서는 DB에서 조회한 목록을 응답으로 조립할 때 `List`를 매번 순회하면 성능이 나빠질 수 있어서, 반복 조회가 있으면 `Map`으로 변환해 key 기반 조회를 사용합니다. 반대로 데이터가 작고 한 번만 순회한다면 `Map`으로 바꾸는 것이 오히려 복잡할 수 있습니다. 또 `HashSet`과 `HashMap`은 순서를 보장하지 않고, 객체를 key나 Set 요소로 쓸 때는 `equals/hashCode` 기준이 중요합니다. 그래서 컬렉션 선택은 성능뿐 아니라 순서, 중복, 동등성, 동시성 요구사항을 함께 보고 결정해야 합니다.

## 꼬리 질문

- `List`, `Set`, `Map`은 각각 어떤 상황에서 선택하는가?
- `List.contains()`를 반복해서 쓰면 어떤 문제가 생길 수 있는가?
- `HashSet`은 중복을 어떤 기준으로 판단하는가?
- `Collectors.toMap()`에서 중복 key가 생기면 어떻게 처리할 수 있는가?
- 응답 순서가 중요할 때 어떤 컬렉션을 고려해야 하는가?

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[hashmap]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/jpa/jpa|jpa]]
