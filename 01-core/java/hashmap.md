---
title: HashMap 내부 동작과 충돌 처리
description: HashMap이 hashCode와 equals로 값을 찾는 방식, 충돌과 리사이즈, 실무에서 key를 고르는 기준
tags: [concept, java]
---

# HashMap 내부 동작과 충돌 처리

`HashMap`은 key의 `hashCode()`로 어느 칸(bucket)에 둘지 정하고, 그 칸 안에서 `equals()`로 같은 key인지 확인해서 값을 넣고 꺼낸다. 그래서 key를 같다고 보는 기준이 틀리면 넣은 값을 다시 못 찾는다.

백엔드에서는 DB에서 읽은 목록을 id로 묶고, 여러 목록을 한 응답으로 조립하고, `List`를 반복해서 뒤지는 코드를 줄일 때 늘 쓴다. key 비교 기준, 중복 key, 순서, 여러 스레드가 동시에 쓰는지를 놓치면 값을 못 찾거나 데이터가 어긋난다.

## 동작

1. `hashCode()`로 bucket 위치를 찾는다.
2. 같은 bucket 안에서 `equals()`로 같은 key인지 확인한다.

같은 key면 값을 덮어쓰고, 다른 key면 같은 bucket에 함께 둔다. 데이터가 많아지면 내부 배열을 늘리고 원소를 다시 배치한다.

### 충돌 처리와 리사이즈 (Java 8+)

| 항목 | 기본 동작 |
|---|---|
| bucket 위치 | `(n - 1) & (h ^ (h >>> 16))`. 상위 비트를 섞어 하위 비트만 쓰는 인덱스 계산의 쏠림을 줄인다 |
| 충돌 | 같은 bucket에 연결 리스트로 붙인다 |
| treeify | 한 bucket이 8개를 넘고 배열 크기가 64 이상이면 Red-Black Tree로 바꾼다 (64 미만이면 트리 대신 리사이즈) |
| 리사이즈 | 기본 용량 16, load factor 0.75. 원소 수가 `용량 × 0.75`를 넘으면 배열을 2배로 늘리고 재배치한다 |

실무에서는 이렇게 이어진다.

- `hashCode()`가 늘 같은 값을 돌려주면 모든 key가 한 bucket에 몰린다. 트리로 바뀌면서 최악은 면하지만(key가 `Comparable`이면 O(log n)), 정상적인 O(1)보다는 확실히 느리다.
- 몇 건을 넣을지 알고 대량으로 넣을 때는 초기 용량을 잡아 리사이즈를 피한다. Java 19부터는 `HashMap.newHashMap(expectedSize)`가 load factor를 고려한 용량을 대신 계산해 준다.
- 여러 스레드가 동시에 `put`하면 값이 사라진다. 이때는 `ConcurrentHashMap`을 쓴다.

## 어떤 Map을 고르나

| 상황 | 선택 |
|---|---|
| key로 빨리 찾아야 함 | `HashMap` |
| 입력 순서를 유지해야 함 | `LinkedHashMap` |
| key 정렬이 필요함 | `TreeMap` |
| 여러 스레드가 동시에 읽고 씀 | `ConcurrentHashMap` |
| key가 enum임 | `EnumMap` |
| 데이터가 작고 한 번만 훑음 | `List` 그대로 둬도 된다 |

## List를 Map으로 바꾸기

주문 목록을 응답으로 만들면서 주문마다 사용자 목록을 처음부터 훑으면 느려진다.

```java
for (Order order : orders) {
    User user = users.stream()
        .filter(it -> it.getId().equals(order.getUserId()))
        .findFirst()
        .orElseThrow();
}
```

사용자 목록을 먼저 `HashMap`으로 바꿔 두면 id로 바로 찾는다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

for (Order order : orders) {
    User user = userMap.get(order.getUserId());
}
```

여러 번 찾을 때 효과가 크다. 데이터가 적고 한 번만 훑는다면 `Map`으로 바꾸는 코드만 늘어난다.

## key 정하기

객체를 key로 쓰려면 `equals()`와 `hashCode()`가 제대로 구현돼 있어야 한다.

```java
class UserKey {
    private final Long userId;

    UserKey(Long userId) {
        this.userId = userId;
    }
}

Map<UserKey, String> map = new HashMap<>();

map.put(new UserKey(1L), "ACTIVE");

String status = map.get(new UserKey(1L)); // equals/hashCode가 없으면 null
```

꼭 객체 key가 필요한 게 아니라면 `Long`, `String`, enum처럼 비교 기준이 정해진 값을 key로 쓰는 편이 안전하다.

key로 쓴 값은 넣은 뒤에 바뀌면 안 된다. hash 값이 바뀌면 원래 들어 있던 bucket에서 못 찾는다.

## 중복 key

`Collectors.toMap()`은 key가 겹치면 기본적으로 예외를 던진다.

```java
Map<Long, Order> latestOrderMap = orders.stream()
    .collect(Collectors.toMap(
        Order::getUserId,
        order -> order,
        (oldOrder, newOrder) -> newOrder
    ));
```

merge 함수가 왜 그 값을 남기는지 설명할 수 있어야 한다. 나중에 나온 값이 최신이라는 보장이 없다면 정렬 기준이나 비교 기준부터 정한다.

## 자주 깨지는 곳

- key 객체의 `equals/hashCode`를 재정의하지 않으면, 같은 값으로 새로 만든 key로는 못 찾는다.
- 바뀔 수 있는 객체를 key로 쓰고 넣은 뒤 값을 바꾸면, 엉뚱한 bucket을 뒤져서 못 찾는다.
- key가 겹칠 수 있는데 `toMap()`에 merge 함수를 안 넘기면, 데이터가 겹치는 순간 예외가 난다.
- 순서가 필요한데 `HashMap`을 쓰면, 응답 순서가 보장되지 않는다.
- 여러 스레드가 동시에 고치는데 일반 `HashMap`을 쓰면, 값이 사라진다.
- 작은 데이터까지 무조건 `Map`으로 바꾸면, 얻는 것 없이 읽기만 어려워진다.

## 한 번에 설명하기

> HashMap은 hashCode로 bucket을 찾고, equals로 같은 key인지 확인합니다. 그래서 key를 같다고 보는 기준이 정확해야 하고, 넣은 뒤에 key 값이 바뀌면 안 됩니다.
>
> 실무에서는 응답을 조립하면서 목록을 반복해서 뒤지는 코드를 줄일 때 많이 씁니다. 순서가 필요하면 LinkedHashMap, 정렬이 필요하면 TreeMap, 여러 스레드가 동시에 고치면 ConcurrentHashMap을 씁니다.
>
> 코드 리뷰에서는 중복 key, 바뀔 수 있는 key, 객체 key의 equals/hashCode를 꼭 확인합니다.

## 꼬리 질문

> [!question]- `HashMap`에서 `equals()`와 `hashCode()`가 둘 다 중요한 이유는?
> `hashCode()`로 bucket을 찾고 `equals()`로 같은 key인지 판단하기 때문입니다. 두 기준이 서로 안 맞으면 넣은 값을 다시 못 찾을 수 있습니다.

> [!question]- `HashMap`은 넣은 순서를 지키나?
> 안 지킵니다. 넣은 순서가 필요하면 `LinkedHashMap`, 정렬 순서가 필요하면 `TreeMap`을 씁니다.

> [!question]- `Collectors.toMap()`에서 key가 겹치면?
> merge 함수를 안 넘겼으면 `IllegalStateException`이 납니다. 세 번째 인자로 merge 함수를 넘겨야 합니다.

> [!question]- `ConcurrentHashMap`은 언제 쓰나?
> 여러 스레드가 같은 Map을 동시에 읽고 쓸 수 있을 때 씁니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>HashMap 조회에서 hashCode와 equals가 함께 필요한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="hashCode로 후보 버킷을 찾고 equals로 실제 같은 key인지 확인한다." aria-pressed="false">A. hashCode는 위치 후보, equals는 동등성 확인에 쓰인다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="hashCode만 같아도 서로 다른 객체일 수 있다." aria-pressed="false">B. hashCode가 같으면 equals 확인 없이 같은 key다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="equals만 사용하면 버킷 탐색 이점이 사라진다." aria-pressed="false">C. equals만 쓰고 hashCode는 사용하지 않는다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>HashMap은 입력 순서를 보장하므로 API 응답 순서를 유지하는 데 적합하다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="순서가 필요하면 LinkedHashMap이나 정렬된 구조를 명시적으로 선택해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="HashMap은 입력 순서를 보장하지 않는다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>멀티스레드에서 공유 Map을 갱신해야 한다면 먼저 고려할 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="HashMap은 동시 갱신 안전성을 보장하지 않는다." aria-pressed="false">A. HashMap을 그대로 쓰고 volatile만 붙인다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="동시 접근 패턴에 따라 ConcurrentHashMap이나 외부 동기화를 선택해야 한다." aria-pressed="false">B. ConcurrentHashMap 또는 명시적 동기화 전략을 검토한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="final은 참조 재할당을 막을 뿐 내부 상태 변경의 동시성을 보장하지 않는다." aria-pressed="false">C. Map 변수를 final로 선언하면 충분하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: HashMap](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
