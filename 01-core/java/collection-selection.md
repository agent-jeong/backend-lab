---
title: 컬렉션 선택 기준 (List, Set, Map)
description: List, Set, Map을 언제 고르고, 응답을 조립할 때 반복 조회를 Map으로 바꾸는 방법
tags: [concept, java]
---

# 컬렉션 선택 기준 (List, Set, Map)

`List`, `Set`, `Map` 중 무엇을 쓸지는 데이터를 순서대로 다룰지, 중복을 없앨지, key로 빨리 찾을지에 따라 정한다. 고를 때는 "이 데이터를 나중에 어떻게 다시 쓸까"를 먼저 생각한다.

백엔드 코드는 DB에서 가져온 데이터를 응답 DTO로 조립하고, 중복을 빼고, id로 다시 찾는 일이 많다. 예를 들어 주문 목록에 사용자 이름을 붙여 내려준다면, 주문마다 사용자 목록을 처음부터 훑을지 id로 바로 찾을지가 컬렉션 선택에 달렸다. 잘못 고르면 반복 조회가 늘고, 응답 순서가 실행할 때마다 바뀌고, 중복 key나 객체 비교 기준 때문에 버그가 난다.

## 무엇을 고르나

| 필요 | 먼저 볼 것 |
|---|---|
| 순서대로 보여줘야 함 | `List` |
| 중복을 없애야 함 | `Set` |
| id/code로 빨리 찾아야 함 | `Map` |
| 입력 순서를 유지해야 함 | `ArrayList`, `LinkedHashSet`, `LinkedHashMap` |
| 정렬된 상태가 필요함 | 정렬된 `List`, `TreeSet`, `TreeMap` |
| 여러 스레드가 동시에 수정함 | concurrent collection 또는 동기화 |

## List

순서가 있고 중복을 허용한다. API 응답 목록, DB 조회 결과, 페이지 조회 결과, 정렬된 데이터, 순서대로 처리해야 하는 대상에 쓴다.

```java
List<OrderResponse> responses = orders.stream()
    .map(OrderResponse::from)
    .toList();
```

반복 조회를 조심한다. 반복문 안에서 계속 `stream().filter()`로 찾으면 데이터가 많아질수록 느려진다.

## Set

중복을 허용하지 않는다. 요청 id의 중복을 걸러 낼 때, 이미 처리한 항목을 기억할 때, 권한·역할·태그처럼 중복이 있어도 쓸모없는 값을 담을 때, 차집합·교집합을 구할 때 쓴다.

```java
Set<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .collect(Collectors.toSet());
```

`HashSet`은 순서를 지키지 않는다. 응답 순서가 중요하면 `LinkedHashSet`이나 정렬된 `List`를 쓴다.

## Map

key로 value를 찾는다. id로 엔티티를 찾을 때, code로 설정값을 찾을 때, 여러 목록을 하나의 응답으로 조립할 때, 그룹별로 묶을 때, 개수나 합계를 셀 때 쓴다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

User user = userMap.get(order.getUserId());
```

`toMap()`은 같은 key가 두 번 나오면 기본적으로 예외를 던진다. key가 겹칠 수 있으면 merge 함수를 넘긴다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

이때 왜 새 값을 남기는지가 코드에 드러나거나, 미리 정렬해 둬서 설명이 돼야 한다.

## 응답을 조립할 때 반복 조회는 Map으로

주문마다 사용자 목록을 처음부터 다시 훑으면 느려진다.

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

이런 반복 조회가 보이면 먼저 `Map`으로 바꾼다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

List<OrderResponse> responses = orders.stream()
    .map(order -> OrderResponse.of(order, userMap.get(order.getUserId())))
    .toList();
```

JPA N+1을 줄이고 나서 메모리에서 데이터를 조립할 때 자주 쓰는 방식이다. 반대로 데이터가 적고 한 번만 훑는다면 `List` 그대로 두는 편이 읽기 쉽다.

## 자주 깨지는 곳

- 데이터가 적다고 이중 반복문을 그냥 두면, 데이터가 늘어나는 만큼 그대로 느려진다.
- `HashSet`이나 `HashMap`에 순서를 기대하면, 응답 순서가 실행할 때마다 달라진다.
- 중복 key를 확인하지 않고 `Collectors.toMap()`을 쓰면, 운영 데이터에서 처음 key가 겹치는 날 예외가 난다.
- 객체를 `Set`에 넣으면서 `equals/hashCode` 기준을 확인하지 않으면, 중복이 생각대로 걸러지지 않는다.
- `Map`이 무조건 낫다고 보고 아무 데나 쓰면, 필요 없는 곳까지 코드만 복잡해진다.

## 한 번에 설명하기

> 순서가 중요하면 List, 중복을 없애야 하면 Set, key로 여러 번 찾아야 하면 Map을 먼저 봅니다.
>
> 응답을 조립하다가 `stream().filter()`가 반복문 안에 보이면 Map으로 바꾸고, 데이터가 적고 한 번만 훑으면 List 그대로 둡니다.
>
> 속도만 보는 게 아니라 순서가 필요한지, 중복을 어떻게 판단하는지, key가 겹칠 수 있는지, 여러 스레드가 동시에 고치는지까지 보고 고릅니다.

## 꼬리 질문

> [!question]- `List`, `Set`, `Map`은 각각 언제 고르나?
> 순서가 있고 중복이 있어도 되면 `List`, 중복을 없애는 게 목적이면 `Set`, key로 빨리 찾아야 하면 `Map`을 고릅니다.

> [!question]- 반복문 안의 `stream().filter()`가 왜 문제인가?
> 목록을 돌면서 또 다른 목록을 처음부터 훑으니 반복 횟수가 곱으로 늘어납니다. 이런 반복 조회가 보이면 `Map`으로 바꿔 key로 바로 찾는 걸 검토합니다.

> [!question]- `HashSet`은 무엇으로 중복을 판단하나?
> `hashCode()`로 bucket을 찾고, 그 안에서 `equals()`로 같은 객체인지 확인합니다.

> [!question]- `Collectors.toMap()`에서 key가 겹치면?
> merge 함수를 안 넘겼으면 `IllegalStateException`이 납니다. 세 번째 인자로 merge 함수를 넘겨야 합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>ID로 반복 조회해야 하는 데이터를 List로 계속 filter하는 코드의 개선 방향은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="조회 기준이 key라면 Map으로 한 번 인덱싱해 O(1)에 가깝게 찾는 것이 일반적이다." aria-pressed="false">A. Map으로 변환해 key 기반 조회로 바꾼다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="정렬은 조회 비용 문제의 직접적인 해결책이 아니다." aria-pressed="false">B. List를 매번 정렬한 뒤 filter한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="parallelStream은 구조적 비용을 해결하지 못하고 오히려 오버헤드를 만들 수 있다." aria-pressed="false">C. parallelStream으로 filter를 병렬화한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>HashSet의 중복 판단은 equals와 hashCode에 의존한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="HashSet은 안에서 HashMap을 쓰므로 hashCode와 equals 계약을 그대로 따른다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="참조 주소만으로 중복을 판단하지 않는다. equals/hashCode 구현이 기준이 된다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Collectors.toMap()에서 중복 key가 생길 수 있는 경우 가장 안전한 대응은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="중복을 무시하면 어떤 값이 남는지 의도가 불명확해진다." aria-pressed="false">A. 예외가 나지 않도록 아무 값이나 남긴다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="중복이 정상인지 오류인지 먼저 판단하고, 필요하면 merge function으로 명시한다." aria-pressed="false">B. 중복 정책을 정하고 merge function 또는 사전 검증을 둔다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Set 변환은 key 충돌 정책을 명확히 설명하지 못한다." aria-pressed="false">C. 무조건 Set으로 바꾼다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21: Collections Framework Overview](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/doc-files/coll-overview.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[hashmap]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/jpa/jpa|jpa]]
