---
title: 컬렉션 선택 기준 (List, Set, Map)
description: Java List, Set, Map 선택 기준과 실무 사용 패턴
tags: [concept, java]
---

# 컬렉션 선택 기준 (List, Set, Map)

컬렉션은 데이터를 순서대로 다룰지, 중복을 없앨지, key로 빨리 찾을지에 따라 `List`, `Set`, `Map` 중에서 고른다. 기준은 "이 데이터를 나중에 어떻게 다시 쓸 것인가"다.

백엔드 코드는 DB에서 가져온 데이터를 응답 DTO로 조립하고, 중복을 빼고, id로 다시 찾는 일이 많다. 컬렉션을 잘못 고르면 반복 조회가 늘고, 응답 순서가 흔들리고, 중복 key나 객체 동등성 문제로 버그가 난다.

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

순서가 있고 중복을 허용한다. API 응답 목록, DB 조회 결과, 페이지네이션 결과, 정렬된 데이터, 순서에 의미가 있는 처리 대상에 쓴다.

```java
List<OrderResponse> responses = orders.stream()
    .map(OrderResponse::from)
    .toList();
```

반복 조회를 조심한다. 반복문 안에서 계속 `stream().filter()`로 찾으면 데이터가 커질수록 비용이 커진다.

## Set

중복을 허용하지 않는다. 요청 id 중복 제거, 이미 처리한 항목 기록, 권한·역할·태그처럼 중복이 의미 없는 값, 차집합·교집합 계산에 쓴다.

```java
Set<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .collect(Collectors.toSet());
```

`HashSet`은 순서를 보장하지 않는다. 응답 순서가 중요하면 `LinkedHashSet`이나 정렬된 `List`를 쓴다.

## Map

key로 value를 찾는다. id로 엔티티 찾기, code로 설정값 찾기, 여러 목록을 한 응답으로 조립하기, 그룹별로 묶기, 카운트·합계 집계에 쓴다.

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

이때 "왜 새 값을 고르는지"가 코드나 사전 정렬로 설명돼야 한다.

## 응답 조립: 반복 조회를 Map으로

주문마다 사용자 목록을 다시 훑으면 비용이 커진다.

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

반복 조회가 보이면 먼저 `Map`으로 바꾼다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

List<OrderResponse> responses = orders.stream()
    .map(order -> OrderResponse.of(order, userMap.get(order.getUserId())))
    .toList();
```

JPA N+1을 줄인 뒤 메모리에서 데이터를 조립할 때 자주 쓰는 패턴이다. 반대로 데이터가 작고 한 번만 훑는다면 `List` 그대로가 더 읽기 쉽다.

## 자주 깨지는 곳

- **데이터가 작다며 이중 반복을 방치한다.** 데이터가 늘면 그대로 비용이 된다.
- **`HashSet`·`HashMap`의 순서를 기대한다.** 응답 순서가 실행마다 달라진다.
- **중복 key를 확인하지 않고 `Collectors.toMap()`을 쓴다.** 운영 데이터에서 처음 겹칠 때 예외가 난다.
- **객체를 `Set`에 넣으면서 `equals/hashCode` 기준을 보지 않는다.** 중복 제거가 의도대로 되지 않는다.
- **`Map`이면 무조건 낫다고 본다.** 필요 없는 곳까지 코드만 복잡해진다.

## 면접에서 말하기

> 순서가 중요하면 List, 중복 제거가 필요하면 Set, key로 반복해서 찾아야 하면 Map을 먼저 봅니다. 응답을 조립하다 반복적인 `stream().filter()`가 보이면 Map으로 바꾸고, 데이터가 작고 한 번만 훑으면 List 그대로 둡니다. 성능만이 아니라 순서, 중복, 객체 동등성, key 중복 가능성, 동시 수정 여부까지 보고 고릅니다.

## 꼬리 질문

> [!question]- `List`, `Set`, `Map`은 각각 언제 선택하는가?
> 순서가 있고 중복을 허용하면 `List`, 중복 제거가 목적이면 `Set`, key로 빠르게 찾아야 하면 `Map`을 선택합니다.

> [!question]- 반복적인 `stream().filter()`가 문제 되는 이유는?
> 목록 안에서 다시 목록을 찾으면 반복 횟수가 커집니다. 반복 조회가 있으면 `Map`으로 바꿔 key 기반 조회를 고려합니다.

> [!question]- `HashSet`은 중복을 어떤 기준으로 판단하는가?
> `hashCode()`로 bucket을 찾고 `equals()`로 같은 객체인지 확인합니다.

> [!question]- `Collectors.toMap()`에서 중복 key가 생기면?
> merge 전략이 없으면 `IllegalStateException`이 발생합니다. 세 번째 인자로 merge function을 지정해야 합니다.

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

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[hashmap]]
- [[02-practical-backend/performance/performance|performance]]
- [[01-core/jpa/jpa|jpa]]
