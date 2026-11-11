---
title: 정렬·중복 제거·탐색의 시간 복잡도
description: 정렬, 중복 제거, 탐색이 자료구조마다 얼마나 드는지와 반복문 안에서 느려지는 경우
tags: [concept, java]
---

# 정렬·중복 제거·탐색의 시간 복잡도

정렬, 중복 제거, 탐색은 컬렉션으로 가장 자주 하는 일이다. 같은 일이라도 어떤 자료구조에 담았는지, 데이터가 몇 건인지에 따라 걸리는 시간이 크게 달라진다. 실무에서 가장 자주 문제가 되는 건 반복문 안에서 목록을 뒤지는 코드다.

수십 건일 때는 무엇을 써도 차이가 없다. 수천~수만 건이 되면 잘못 고른 자료구조가 바로 응답 시간에 드러난다. 흔히 보는 경우는 이렇다. 반복문 안의 `List.contains()`가 O(n^2)이 된다. 정렬 기준이 여럿인데 `Comparator`를 이어 붙이지 않고 손으로 비교한다. `equals/hashCode`가 없어서 중복이 안 빠진다. DB에서 정렬하면 될 걸 애플리케이션에서 정렬하느라 메모리를 쓴다. `Comparable`을 구현하지 않은 객체를 `TreeSet`에 넣어 `ClassCastException`이 난다.

## 탐색

| 연산 | ArrayList | HashSet | HashMap | TreeSet/TreeMap |
|---|---|---|---|---|
| 포함 여부 확인 | O(n) | O(1) 평균 | O(1) 평균 | O(log n) |
| 인덱스 접근 | O(1) | 불가 | 불가 | 불가 |
| key로 value 조회 | 불가 | 불가 | O(1) 평균 | O(log n) |

### 반복문 안의 List.contains()

```java
// 주문마다 처리 완료 목록에서 확인 - O(orders * processed)
List<Long> processedIds = getProcessedIds(); // 수만 건

for (Order order : orders) {
    if (processedIds.contains(order.getId())) { // 매번 O(n) 순회
        skip(order);
    }
}
```

`processedIds`가 1만 건, `orders`가 1만 건이면 최악의 경우 1억 번 비교한다.

```java
// Set으로 변환하면 O(orders) - 각 contains가 O(1)
Set<Long> processedIdSet = new HashSet<>(processedIds);

for (Order order : orders) {
    if (processedIdSet.contains(order.getId())) { // O(1)
        skip(order);
    }
}
```

반복문 안에서 `contains()`를 부르고 있으면 그 목록을 `Set`으로 바꾼다.

### 반복 조회는 Map으로

```java
// O(n * m) - 주문마다 사용자 목록을 순회
for (Order order : orders) {
    User user = users.stream()
        .filter(u -> u.getId().equals(order.getUserId()))
        .findFirst()
        .orElseThrow();
}

// O(n + m) - Map으로 변환 후 조회
Map<Long, User> userMap = users.stream()
    .collect(Collectors.toMap(User::getId, u -> u));

for (Order order : orders) {
    User user = userMap.get(order.getUserId()); // O(1)
}
```

## 정렬

```java
// 자연 순서 (Comparable 구현 필요)
List<String> names = new ArrayList<>(List.of("kim", "lee", "park"));
Collections.sort(names); // 또는 names.sort(null)

// Comparator로 기준 지정
List<Order> orders = getOrders();
orders.sort(Comparator.comparing(Order::getCreatedAt));
```

기준이 여럿이면 `thenComparing()`으로 이어 붙인다. if-else로 비교할 필요가 없다.

```java
// 상태 우선, 같으면 생성일 최신순
orders.sort(
    Comparator.comparing(Order::getStatus)
        .thenComparing(Order::getCreatedAt, Comparator.reverseOrder())
);
```

null이 들어올 수 있는 필드는 `nullsFirst()`나 `nullsLast()`로 감싼다. 그러지 않으면 null을 만나는 순간 `NullPointerException`이 난다.

```java
// null이 포함될 수 있는 필드 정렬
orders.sort(
    Comparator.comparing(
        Order::getCompletedAt,
        Comparator.nullsLast(Comparator.naturalOrder())
    )
);
```

### DB에서 정렬할까, 애플리케이션에서 할까

| 기준 | DB 정렬 | 애플리케이션 정렬 |
|---|---|---|
| 데이터 양이 많다 | 인덱스 활용 가능, 효율적 | 전체를 메모리에 올려야 해서 비효율 |
| 정렬 기준이 DB 컬럼이다 | ORDER BY 사용 | 불필요한 전체 조회 |
| 정렬 기준이 가공된 값이다 | 어려움 | 적합 |
| 페이지네이션과 함께 | ORDER BY + LIMIT | 전체 조회 후 잘라야 해서 비효율 |
| 여러 API의 결과를 합쳐서 정렬 | 불가능 | 적합 |

정렬 기준이 DB 컬럼이고 데이터가 많으면 DB에서 정렬한다. 애플리케이션에서 정렬하는 건 이미 메모리에 올라온 작은 데이터일 때다.

## 중복 제거

숫자나 문자열 같은 값은 바로 된다.

```java
// primitive/wrapper 타입은 바로 가능
List<Long> ids = List.of(1L, 2L, 2L, 3L, 3L);
List<Long> uniqueIds = ids.stream().distinct().toList();
// [1, 2, 3]
```

객체는 다르다. `distinct()`는 `equals()`로 같은지 보는데, `equals/hashCode`를 재정의하지 않으면 같은 객체인지만 비교하게 돼서 중복이 빠지지 않는다.

```java
// equals/hashCode가 없으면 모든 객체가 다르다고 판단
List<User> users = List.of(new User(1L, "kim"), new User(1L, "kim"));
users.stream().distinct().toList(); // 2건 그대로
```

```java
// 방법 1: equals/hashCode 재정의
// 방법 2: 특정 필드 기준으로 중복 제거
List<User> unique = users.stream()
    .collect(Collectors.toMap(
        User::getId,
        u -> u,
        (existing, replacement) -> existing
    ))
    .values()
    .stream()
    .toList();

// 방법 3: 특정 필드 기준 중복 제거 (결과는 원래 순서가 아니라 id 순으로 정렬된다)
List<User> unique = users.stream()
    .collect(Collectors.collectingAndThen(
        Collectors.toCollection(() -> new TreeSet<>(Comparator.comparing(User::getId))),
        ArrayList::new
    ));
```

### Set으로 중복 제거

```java
// HashSet: 순서 보장 X, O(1) 삽입/조회
Set<Long> uniqueIds = new HashSet<>(idList);

// LinkedHashSet: 입력 순서 유지, O(1) 삽입/조회
Set<Long> uniqueIds = new LinkedHashSet<>(idList);

// TreeSet: 정렬된 순서 유지, O(log n) 삽입/조회
Set<Long> sortedUniqueIds = new TreeSet<>(idList);
```

### TreeSet은 compareTo()로 같은지 본다

`TreeSet`은 `equals()`를 보지 않는다. `compareTo()`(또는 넘겨준 `Comparator`)가 0을 돌려주면 같은 원소로 친다.

```java
// Comparable을 구현하지 않은 객체를 넣으면 ClassCastException
Set<User> users = new TreeSet<>();
users.add(new User(1L, "kim")); // ClassCastException

// Comparator를 제공해야 한다
Set<User> users = new TreeSet<>(Comparator.comparing(User::getId));
```

## 시간 복잡도 한눈에

| 연산 | 방식 | 시간 복잡도 |
|---|---|---|
| 정렬 | `Collections.sort()` / `List.sort()` | O(n log n) |
| 중복 제거 | `stream().distinct()` | O(n) (hash 기반) |
| 중복 제거 | `new HashSet<>(list)` | O(n) |
| 중복 제거 | `new TreeSet<>(list)` | O(n log n) |
| 탐색 | `List.contains()` | O(n) |
| 탐색 | `Set.contains()` | O(1) 평균 / O(log n) TreeSet |
| 탐색 | `Map.get()` | O(1) 평균 / O(log n) TreeMap |
| 탐색 | `List` 반복문 안에서 `List.contains()` | O(n * m) |
| 탐색 | `List` 반복문 안에서 `Set.contains()` | O(n) |

## 상황별로 무엇을 쓰나

| 상황 | 권장 |
|---|---|
| 반복문 안에서 포함 여부 확인 | `List` → `Set` 변환 후 사용 |
| 반복문 안에서 key로 조회 | `List` → `Map` 변환 후 사용 |
| 정렬 기준이 DB 컬럼 | ORDER BY 사용 |
| 정렬 기준이 가공된 값 | `Comparator` 체이닝 |
| 중복 제거 (primitive) | `stream().distinct()` 또는 `Set` |
| 중복 제거 (객체, 특정 필드 기준) | `toMap()` merge 전략 |
| 정렬 + 중복 제거 동시 | `TreeSet` + `Comparator` |
| 순서 유지 + 중복 제거 | `LinkedHashSet` |

## 자주 깨지는 곳

- 반복문 안에서 `List.contains()`를 부르면, 데이터가 늘수록 O(n^2)으로 느려진다.
- `distinct()`가 `equals()`로 비교한다는 걸 모르면, 객체 중복이 그대로 남는다.
- `Comparator`에서 null을 처리하지 않으면, null 하나 때문에 정렬 전체가 `NullPointerException`으로 실패한다.
- DB에서 정렬할 수 있는데 전부 읽어 와서 애플리케이션에서 정렬하면, 메모리와 조회 시간을 버린다.
- `Comparable`을 구현하지 않은 객체를 `TreeSet`에 넣으면, `ClassCastException`이 난다.
- 정렬 기준이 여럿인데 if-else로 비교하면, `thenComparing()`으로 이어 붙이면 한 줄일 코드가 길어진다.
- 순서가 필요한데 `LinkedHashSet` 대신 `HashSet`을 쓰면, 결과 순서가 실행할 때마다 달라진다.

## 한 번에 설명하기

> 컬렉션 코드를 볼 때 저는 반복문 안에서 무언가를 찾고 있는지부터 봅니다. `List.contains()`는 O(n)이라 반복문 안에서 부르면 O(n^2)이 됩니다. 그 목록을 Set으로 바꾸면 한 번 찾는 데 O(1)이라 전체가 O(n)으로 줄어듭니다.
>
> 정렬은 `comparing()`과 `thenComparing()`으로 기준을 이어 붙이고, null이 있으면 `nullsLast()`를 씁니다.
>
> `distinct()`는 equals로 비교하니 객체라면 equals/hashCode가 있어야 합니다. 정렬 기준이 DB 컬럼이면 애플리케이션에서 하지 않고 ORDER BY로 처리합니다.

## 꼬리 질문

> [!question]- `List.contains()`와 `Set.contains()`는 시간 복잡도가 어떻게 다른가?
> `List.contains()`는 처음부터 하나씩 훑어서 O(n)입니다. `HashSet.contains()`는 hash로 바로 위치를 찾아서 평균 O(1)입니다.

> [!question]- `distinct()`가 중복을 못 거르는 건 언제인가?
> 객체에 `equals()`와 `hashCode()`를 재정의하지 않았을 때입니다. 그러면 같은 객체인지만 비교해서, 값이 같은 다른 인스턴스는 그대로 남습니다.

> [!question]- 정렬 기준이 여럿이면 `Comparator`로 어떻게 쓰나?
> `Comparator.comparing(Order::getStatus).thenComparing(Order::getCreatedAt, Comparator.reverseOrder())`처럼 `thenComparing()`으로 이어 붙입니다.

> [!question]- DB에서 정렬할 때와 애플리케이션에서 정렬할 때는 어떻게 나누나?
> 정렬 기준이 DB 컬럼이고 데이터가 많으면 ORDER BY가 낫습니다. 여러 API 결과를 합쳐야 하거나 계산해서 만든 값으로 정렬해야 하면 애플리케이션에서 정렬합니다.

> [!question]- `TreeSet`은 `equals()`와 `compareTo()` 중 무엇으로 같은지 보나?
> `compareTo()`입니다. `compareTo()`가 0을 돌려주면 같은 원소로 칩니다. 그래서 `compareTo()`와 `equals()`의 판단이 서로 다르면 생각과 다르게 동작할 수 있습니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>List.contains()를 대량 반복 호출하는 코드가 느릴 때 대표적인 개선은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="반복 membership check는 Set으로 바꿔 탐색 비용을 줄이는 것이 일반적이다." aria-pressed="false">A. 조회 대상 컬렉션을 Set으로 변환한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="출력은 성능 병목을 더 악화시킬 수 있다." aria-pressed="false">B. contains 호출마다 로그를 남긴다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="sleep은 처리량을 낮출 뿐 탐색 비용을 줄이지 않는다." aria-pressed="false">C. 호출 사이에 sleep을 추가한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Stream distinct()는 객체의 equals/hashCode 기준으로 중복을 판단한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="distinct가 기대와 다르게 동작하면 값 객체의 equals/hashCode 구현을 먼저 확인해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="객체 주소만이 아니라 equals/hashCode 기준이 사용된다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>DB 정렬과 애플리케이션 정렬은 무엇으로 고르나?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="페이징, 인덱스, 데이터 양을 고려하면 보통 DB에서 정렬하는 편이 안정적이다." aria-pressed="false">A. 페이징과 대량 데이터는 DB 정렬을 우선 검토한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 정렬을 애플리케이션으로 가져오면 메모리와 네트워크 비용이 커질 수 있다." aria-pressed="false">B. 데이터가 많을수록 항상 애플리케이션에서 정렬한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="정렬 기준이 항상 하나라는 가정은 현실적이지 않다." aria-pressed="false">C. 다중 정렬은 Java에서 불가능하므로 DB만 사용한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: List.sort](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/List.html)
- [Java SE 21 API: Collections](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[hashmap]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]