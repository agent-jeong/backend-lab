---
title: HashMap 내부 동작과 충돌 처리
description: Java HashMap의 동작 원리와 실무 사용 기준
tags: [concept, java]
---

# HashMap 내부 동작과 충돌 처리

`HashMap`은 key의 `hashCode()`로 저장 위치를 찾고, `equals()`로 같은 key인지 확인해 값을 넣고 꺼내는 `Map` 구현체다. 그래서 key의 동등성 기준이 틀리면 넣은 값을 다시 못 찾는다.

백엔드에서는 DB 조회 결과를 id로 매핑하고, 여러 목록을 한 응답으로 조립하고, 반복적인 `List` 조회를 줄일 때 늘 쓴다. key의 동등성 기준, 중복 key, 순서, 동시성 요구를 놓치면 조회 실패나 데이터 정합성 문제가 생긴다.

## 동작

1. `hashCode()`로 bucket 위치를 찾는다.
2. 같은 bucket 안에서 `equals()`로 같은 key인지 확인한다.

같은 key면 값을 덮어쓰고, 다른 key면 같은 bucket에 함께 둔다. 데이터가 많아지면 내부 배열을 늘리고 다시 배치한다.

### 충돌 처리와 리사이즈 (Java 8+)

| 항목 | 기본 동작 |
|---|---|
| bucket 위치 | `(n - 1) & (h ^ (h >>> 16))`. 상위 비트를 섞어 하위 비트만 쓰는 인덱스 계산의 쏠림을 줄인다 |
| 충돌 | 같은 bucket에 연결 리스트로 붙인다 |
| treeify | 한 bucket이 8개를 넘고 배열 크기가 64 이상이면 Red-Black Tree로 바꾼다 (64 미만이면 트리 대신 리사이즈) |
| 리사이즈 | 기본 용량 16, load factor 0.75. 원소 수가 `용량 × 0.75`를 넘으면 배열을 2배로 늘리고 재배치한다 |

이 표가 실무에서 뜻하는 것:

- `hashCode()`가 늘 같은 값을 돌려주면 모든 key가 한 bucket에 몰린다. 트리화가 최악을 줄여 주지만(key가 `Comparable`이면 O(log n)), 정상적인 O(1)보다는 확실히 느리다.
- 크기를 아는 대량 적재는 초기 용량을 잡아 리사이즈를 피한다. Java 19+는 `HashMap.newHashMap(expectedSize)`가 load factor 계산을 대신해 준다.
- 여러 스레드가 동시에 `put`하면 값이 유실된다. 이때는 `ConcurrentHashMap`을 쓴다.

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

주문 목록을 응답으로 만들면서 사용자 목록을 매번 훑으면 비용이 커진다.

```java
for (Order order : orders) {
    User user = users.stream()
        .filter(it -> it.getId().equals(order.getUserId()))
        .findFirst()
        .orElseThrow();
}
```

먼저 `HashMap`으로 바꾸면 id로 바로 찾는다.

```java
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, user -> user));

for (Order order : orders) {
    User user = userMap.get(order.getUserId());
}
```

반복 조회가 있을 때 효과가 크다. 데이터가 작고 한 번만 훑는다면 `Map` 변환이 오히려 코드만 복잡하게 만든다.

## key 설계

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

String status = map.get(new UserKey(1L)); // equals/hashCode가 없으면 null 가능
```

객체 key가 꼭 필요하지 않으면 `Long`, `String`, enum처럼 동등성 기준이 분명한 값을 key로 쓰는 편이 안전하다.

key로 쓰는 값은 저장 후 바뀌면 안 된다. hash 값이 바뀌면 기존 bucket에서 찾지 못한다.

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

merge 함수는 의도를 설명할 수 있어야 한다. "나중 값"이 최신이라는 보장이 없다면 정렬 기준이나 비교 기준부터 정한다.

## 자주 깨지는 곳

- **key 객체의 `equals/hashCode`를 재정의하지 않는다.** 같은 값으로 만든 새 key로는 못 찾는다.
- **mutable 객체를 key로 쓰고 저장 후 값을 바꾼다.** 엉뚱한 bucket을 뒤져 조회가 실패한다.
- **중복 key가 가능한데 `toMap()` merge 함수를 넘기지 않는다.** 데이터가 겹치는 순간 예외가 난다.
- **순서가 필요한데 `HashMap`을 쓴다.** 응답 순서가 보장되지 않는다.
- **여러 스레드가 동시에 수정하는데 일반 `HashMap`을 쓴다.** 값이 유실된다.
- **작은 데이터까지 무조건 `Map`으로 바꾼다.** 얻는 것 없이 읽기만 어려워진다.

## 면접에서 말하기

> HashMap은 hashCode로 bucket을 찾고 equals로 같은 key인지 확인합니다. 그래서 key의 동등성 기준이 정확해야 하고, 저장 후 key 값이 바뀌면 안 됩니다. 실무에서는 응답 조립에서 반복적인 목록 조회를 줄일 때 많이 쓰고, 순서가 필요하면 LinkedHashMap, 정렬이 필요하면 TreeMap, 동시 수정이 있으면 ConcurrentHashMap을 씁니다. 코드 리뷰에서는 중복 key, mutable key, 객체 key의 equals/hashCode를 꼭 확인합니다.

## 꼬리 질문

> [!question]- `HashMap`에서 `equals()`와 `hashCode()`가 모두 중요한 이유는?
> `hashCode()`로 bucket을 찾고 `equals()`로 같은 key인지 판단하기 때문입니다. 둘의 기준이 맞지 않으면 저장한 값을 다시 찾지 못할 수 있습니다.

> [!question]- `HashMap`은 입력 순서를 보장하는가?
> 보장하지 않습니다. 입력 순서가 필요하면 `LinkedHashMap`, 정렬 순서가 필요하면 `TreeMap`을 사용합니다.

> [!question]- `Collectors.toMap()`에서 중복 key가 생기면?
> merge 전략이 없으면 `IllegalStateException`이 발생합니다. 세 번째 인자로 merge function을 지정해야 합니다.

> [!question]- 언제 `ConcurrentHashMap`을 고려하는가?
> 여러 스레드가 같은 Map을 동시에 읽고 쓸 수 있을 때 고려합니다.

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

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Java SE 21 API: HashMap](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
