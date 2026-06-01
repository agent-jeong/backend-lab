---
title: HashMap
description: Java HashMap의 동작 원리와 실무 사용 기준
---

# HashMap

## 한 줄 정의

`HashMap`은 key의 `hashCode()`로 저장 위치를 찾고, `equals()`로 같은 key인지 확인해서 값을 저장하고 조회하는 `Map` 구현체다.

## 실무에서 왜 중요한가

백엔드 개발에서 `HashMap`은 단순 자료구조가 아니라 데이터를 빠르게 찾고 조립하기 위한 기본 도구다.

자주 쓰이는 상황은 다음과 같다.

- DB에서 조회한 목록을 `id` 기준으로 빠르게 찾을 때
- 여러 API 응답이나 엔티티 목록을 하나의 응답 DTO로 조립할 때
- 중복 데이터를 제거하거나 집계할 때
- `List` 이중 반복을 줄여 응답 시간을 개선할 때
- JPA 연관 데이터 조회 후 메모리에서 매핑할 때

예를 들어 사용자 목록과 주문 목록을 조립할 때 매번 `users` 리스트를 순회하면 데이터가 많아질수록 느려진다.

```java
for (Order order : orders) {
    User user = users.stream()
        .filter(it -> it.getId().equals(order.getUserId()))
        .findFirst()
        .orElseThrow();
}
```

이 방식은 주문 수와 사용자 수가 늘수록 반복 횟수가 크게 증가한다.

`HashMap`으로 먼저 바꾸면 key로 바로 찾을 수 있다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

for (Order order : orders) {
    User user = userMap.get(order.getUserId());
}
```

## 동작 원리

`HashMap`은 내부적으로 배열과 연결 구조를 함께 사용한다.

1. key를 넣으면 key의 `hashCode()`를 호출한다.
2. hash 값을 이용해 내부 배열의 index를 계산한다.
3. 같은 index에 이미 값이 있으면 `equals()`로 같은 key인지 확인한다.
4. 같은 key면 값을 덮어쓴다.
5. 다른 key면 같은 bucket 안에 함께 저장한다.
6. 데이터가 많아져 임계값을 넘으면 내부 배열 크기를 늘리고 다시 배치한다.

핵심은 `hashCode()`가 “어느 bucket에 둘지”를 정하고, `equals()`가 “정말 같은 key인지”를 판단한다는 점이다.

## 성능 감각

일반적인 `get`, `put`은 평균적으로 빠르다. 하지만 항상 빠른 것은 아니다.

| 상황 | 영향 |
|---|---|
| hash가 고르게 분포됨 | 조회와 저장이 빠르다 |
| 여러 key가 같은 bucket에 몰림 | 같은 bucket 안에서 추가 비교가 필요하다 |
| `equals/hashCode` 구현이 잘못됨 | 값을 찾지 못하거나 중복 key처럼 동작하지 않는다 |
| 너무 많은 데이터가 들어감 | resize 비용과 메모리 사용량이 커진다 |
| 여러 스레드가 동시에 수정함 | 데이터 정합성이 깨질 수 있다 |

실무에서는 `HashMap` 자체를 튜닝하기보다, 적절한 key 선택과 `equals/hashCode` 구현이 더 중요하다.

## equals와 hashCode가 중요한 이유

객체를 key로 쓸 때는 `equals()`와 `hashCode()`를 함께 봐야 한다.

```java
class UserKey {
    private final Long userId;

    UserKey(Long userId) {
        this.userId = userId;
    }
}
```

이 클래스가 `equals()`와 `hashCode()`를 재정의하지 않으면, `userId`가 같아도 서로 다른 key로 취급될 수 있다.

```java
Map<UserKey, String> map = new HashMap<>();

map.put(new UserKey(1L), "ACTIVE");

String status = map.get(new UserKey(1L)); // 기대와 달리 null 가능
```

실무에서는 객체 key가 꼭 필요하지 않다면 `Long`, `String`, enum처럼 동등성 기준이 명확한 값을 key로 쓰는 편이 안전하다.

## 자주 나는 실수

- `List`에서 매번 `stream().filter()`로 찾을 수 있는데 굳이 `Map`이 필요한지 판단하지 않는다.
- key로 쓰는 객체의 `equals/hashCode`를 재정의하지 않는다.
- mutable 객체를 key로 사용하고, 저장 후 key 필드를 변경한다.
- 중복 key 가능성이 있는데 `Collectors.toMap()`의 merge 전략을 지정하지 않는다.
- 순서가 필요한데 `HashMap`을 사용한다.
- 여러 스레드가 동시에 수정하는데 일반 `HashMap`을 사용한다.

## 실무 판단 기준

| 상황 | 선택 |
|---|---|
| key로 빠르게 찾아야 한다 | `HashMap` |
| 입력 순서를 유지해야 한다 | `LinkedHashMap` |
| key 정렬이 필요하다 | `TreeMap` |
| 여러 스레드가 동시에 읽고 쓴다 | `ConcurrentHashMap` |
| key가 enum이다 | `EnumMap` |
| 데이터 수가 매우 작고 한 번만 순회한다 | `List` 유지도 가능 |

`HashMap`은 조회 성능을 위해 자주 쓰지만, 모든 코드를 `Map`으로 바꾸는 것이 좋은 것은 아니다. 데이터가 작고 로직이 단순하면 `List`가 더 읽기 쉽다.

## 확인 방법

- 코드 리뷰에서 이중 반복이나 반복적인 `stream().filter()`가 있는지 본다.
- 같은 key로 조회했는데 `null`이 나오면 `equals/hashCode`를 확인한다.
- 중복 key 가능성이 있으면 `Collectors.toMap()`에서 merge function을 명시한다.
- 동시 수정 가능성이 있으면 `HashMap` 대신 `ConcurrentHashMap`이나 외부 동기화를 검토한다.
- 응답 시간이 느리면 DB 쿼리 수, 반복문 구조, 데이터 크기를 함께 확인한다.

## 짧은 예제

중복 key가 있을 수 있는 데이터를 `Map`으로 바꿀 때는 merge 전략을 정해야 한다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

위 코드는 같은 `userId`의 주문이 여러 개 있으면 나중 주문으로 덮어쓴다. 실제 코드에서는 “최신” 기준이 생성일인지, 상태인지, 정렬된 입력인지 명확히 해야 한다.

## 핵심 요약

`HashMap`은 key-value 형태로 데이터를 저장하고, key의 `hashCode()`로 내부 배열의 위치를 찾은 뒤 `equals()`로 같은 key인지 확인하는 자료구조입니다.

평균적으로 `get`과 `put`이 빠르기 때문에 실무에서는 DB에서 조회한 목록을 id 기준으로 매핑하거나, API 응답을 조립할 때 이중 반복을 줄이는 데 자주 사용합니다.
다만 객체를 key로 사용할 때 `equals()`와 `hashCode()`가 올바르게 구현되어 있지 않으면 같은 값인데도 조회가 안 되거나 중복 저장처럼 동작할 수 있습니다.

순서가 필요하면 `LinkedHashMap`, 정렬이 필요하면 `TreeMap`, 동시 수정이 필요하면 `ConcurrentHashMap`을 고려해야 합니다.
그래서 실무에서는 단순히 HashMap이 빠르다고 외우기보다 key의 동등성 기준, 데이터 크기, 순서 요구사항, 동시성 여부를 함께 보고 선택합니다.

## 꼬리 질문

> [!question]- `HashMap`에서 `equals()`와 `hashCode()`를 함께 재정의해야 하는 이유는 무엇인가?
> `hashCode()`로 bucket 위치를 정하고 `equals()`로 같은 key인지 판단합니다. 하나만 재정의하면 저장은 되지만 조회가 안 되는 문제가 생깁니다.

> [!question]- `HashMap`과 `ConcurrentHashMap`은 언제 구분해서 써야 하는가?
> 단일 스레드나 읽기 전용이면 `HashMap`, 여러 스레드가 동시에 읽고 쓰면 `ConcurrentHashMap`을 사용합니다.

> [!question]- `Collectors.toMap()`에서 중복 key가 생기면 어떻게 되는가?
> merge 전략이 없으면 `IllegalStateException`이 발생합니다. `(old, new) -> new` 같은 merge function을 세 번째 인자로 지정해야 합니다.

> [!question]- `HashMap`은 입력 순서를 보장하는가?
> 보장하지 않습니다. 입력 순서가 필요하면 `LinkedHashMap`, 정렬된 순서가 필요하면 `TreeMap`을 사용합니다.

> [!question]- 객체를 `HashMap`의 key로 사용할 때 어떤 점을 조심해야 하는가?
> `equals()`와 `hashCode()`를 반드시 재정의해야 하고, key로 쓰는 필드는 변경 불가능해야 합니다. 가능하면 `Long`, `String`, enum을 key로 쓰는 것이 안전합니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[primitive-and-reference-types]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
