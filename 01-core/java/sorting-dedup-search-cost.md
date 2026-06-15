---
title: 정렬·중복 제거·탐색의 시간 복잡도
description: Java 컬렉션의 정렬, 중복 제거, 탐색 비용과 실무 판단
---

# 정렬·중복 제거·탐색의 시간 복잡도

## 한 줄 정의

컬렉션에서 정렬, 중복 제거, 탐색은 자주 사용되는 연산이며, 데이터 구조와 크기에 따라 비용이 크게 달라진다.

## 실무에서 왜 중요한가

데이터가 수십 건일 때는 어떤 방식이든 차이가 없다. 하지만 수천~수만 건이 되면 잘못된 선택이 응답 시간에 직접 영향을 준다.

- `List.contains()`를 반복 호출해서 O(n^2)이 되는 것을 모른다.
- 정렬 기준이 여러 개인데 `Comparator` 조합을 모르고 수동으로 비교한다.
- 중복 제거 시 `equals/hashCode`를 재정의하지 않아서 제거가 안 된다.
- DB에서 정렬해야 할 것을 애플리케이션에서 정렬해서 메모리를 낭비한다.
- `TreeSet`으로 정렬과 중복 제거를 동시에 하려다 `Comparable` 미구현으로 `ClassCastException`이 발생한다.

## 탐색 비용

### 자료구조별 탐색 시간 복잡도

| 연산 | ArrayList | HashSet | HashMap | TreeSet/TreeMap |
|---|---|---|---|---|
| 포함 여부 확인 | O(n) | O(1) 평균 | O(1) 평균 | O(log n) |
| 인덱스 접근 | O(1) | 불가 | 불가 | 불가 |
| key로 value 조회 | 불가 | 불가 | O(1) 평균 | O(log n) |

### List.contains()의 함정

```java
// 주문마다 처리 완료 목록에서 확인 - O(orders * processed)
List<Long> processedIds = getProcessedIds(); // 수만 건

for (Order order : orders) {
    if (processedIds.contains(order.getId())) { // 매번 O(n) 순회
        skip(order);
    }
}
```

`processedIds`가 1만 건이고 `orders`가 1만 건이면 최악 1억 번 비교한다.

```java
// Set으로 변환하면 O(orders) - 각 contains가 O(1)
Set<Long> processedIdSet = new HashSet<>(processedIds);

for (Order order : orders) {
    if (processedIdSet.contains(order.getId())) { // O(1)
        skip(order);
    }
}
```

**판단 기준**: `contains()`를 반복문 안에서 호출하면 `Set`으로 변환을 검토한다.

### List에서 반복 조회 vs Map 변환

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

### 기본 정렬

```java
// 자연 순서 (Comparable 구현 필요)
List<String> names = new ArrayList<>(List.of("kim", "lee", "park"));
Collections.sort(names); // 또는 names.sort(null)

// Comparator로 기준 지정
List<Order> orders = getOrders();
orders.sort(Comparator.comparing(Order::getCreatedAt));
```

### 다중 기준 정렬

```java
// 상태 우선, 같으면 생성일 최신순
orders.sort(
    Comparator.comparing(Order::getStatus)
        .thenComparing(Order::getCreatedAt, Comparator.reverseOrder())
);
```

`thenComparing()`으로 체이닝하면 if-else 분기 없이 다중 정렬을 표현할 수 있다.

### null 안전 정렬

```java
// null이 포함될 수 있는 필드 정렬
orders.sort(
    Comparator.comparing(
        Order::getCompletedAt,
        Comparator.nullsLast(Comparator.naturalOrder())
    )
);
```

`nullsFirst()` / `nullsLast()`를 사용하지 않으면 null이 있을 때 `NullPointerException`이 발생한다.

### DB 정렬 vs 애플리케이션 정렬

| 기준 | DB 정렬 | 애플리케이션 정렬 |
|---|---|---|
| 데이터 양이 많다 | 인덱스 활용 가능, 효율적 | 전체를 메모리에 올려야 해서 비효율 |
| 정렬 기준이 DB 컬럼이다 | ORDER BY 사용 | 불필요한 전체 조회 |
| 정렬 기준이 가공된 값이다 | 어려움 | 적합 |
| 페이지네이션과 함께 | ORDER BY + LIMIT | 전체 조회 후 잘라야 해서 비효율 |
| 여러 API의 결과를 합쳐서 정렬 | 불가능 | 적합 |

**원칙**: 정렬 기준이 DB 컬럼이고 데이터가 크면 DB에서 정렬한다. 애플리케이션 정렬은 이미 메모리에 있는 소규모 데이터에서 사용한다.

## 중복 제거

### 단순 값 중복 제거

```java
// primitive/wrapper 타입은 바로 가능
List<Long> ids = List.of(1L, 2L, 2L, 3L, 3L);
List<Long> uniqueIds = ids.stream().distinct().toList();
// [1, 2, 3]
```

### 객체 중복 제거

`distinct()`는 `equals()`를 기준으로 동작한다. `equals/hashCode`를 재정의하지 않으면 참조 비교가 되어 중복이 제거되지 않는다.

```java
// equals/hashCode가 없으면 모든 객체가 다르다고 판단
List<User> users = List.of(new User(1L, "kim"), new User(1L, "kim"));
users.stream().distinct().toList(); // 2건 그대로
```

해결 방법:

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

// 방법 3: 순서를 유지하면서 특정 필드 기준 중복 제거
List<User> unique = users.stream()
    .collect(Collectors.collectingAndThen(
        Collectors.toCollection(() -> new TreeSet<>(Comparator.comparing(User::getId))),
        ArrayList::new
    ));
```

### Set을 이용한 중복 제거

```java
// HashSet: 순서 보장 X, O(1) 삽입/조회
Set<Long> uniqueIds = new HashSet<>(idList);

// LinkedHashSet: 입력 순서 유지, O(1) 삽입/조회
Set<Long> uniqueIds = new LinkedHashSet<>(idList);

// TreeSet: 정렬된 순서 유지, O(log n) 삽입/조회
Set<Long> sortedUniqueIds = new TreeSet<>(idList);
```

### TreeSet 주의점

`TreeSet`은 `Comparable`을 기준으로 동등성을 판단한다. `equals()`가 아니라 `compareTo()`가 0을 반환하면 같은 원소로 취급한다.

```java
// Comparable을 구현하지 않은 객체를 넣으면 ClassCastException
Set<User> users = new TreeSet<>();
users.add(new User(1L, "kim")); // ClassCastException

// Comparator를 제공해야 한다
Set<User> users = new TreeSet<>(Comparator.comparing(User::getId));
```

## 시간 복잡도 정리

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

## 자주 나는 실수

- 반복문 안에서 `List.contains()`를 호출해서 O(n^2)이 되는 것을 모른다.
- `distinct()`가 `equals()`를 기준으로 동작하는 것을 모르고 객체 중복 제거가 안 된다.
- `Comparator`에서 null을 처리하지 않아 `NullPointerException`이 발생한다.
- DB에서 정렬할 수 있는데 전체를 조회해서 애플리케이션에서 정렬한다.
- `TreeSet`에 `Comparable`을 구현하지 않은 객체를 넣어 `ClassCastException`이 발생한다.
- 정렬 기준이 여러 개인데 `Comparator` 체이닝을 모르고 if-else로 비교한다.
- `LinkedHashSet`과 `HashSet`의 순서 보장 차이를 모르고 순서가 달라진다.

## 실무 판단 기준

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

## 핵심 요약

컬렉션 연산에서 가장 중요한 것은 탐색 비용입니다.
`List.contains()`는 O(n)이라서 반복문 안에서 호출하면 O(n^2)이 됩니다.
이 경우 `Set`으로 변환하면 각 탐색이 O(1)이 되어 전체가 O(n)으로 줄어듭니다.

정렬은 `Comparator.comparing()`과 `thenComparing()`으로 다중 기준을 체이닝할 수 있고, null이 있으면 `nullsLast()`를 사용해야 합니다.

중복 제거에서 `distinct()`는 `equals()` 기준이므로 객체에 `equals/hashCode`가 없으면 동작하지 않습니다.

실무에서는 정렬 기준이 DB 컬럼이면 ORDER BY를 쓰는 것이 효율적이고, 애플리케이션 정렬은 이미 메모리에 있는 소규모 데이터에 적합합니다.

## 꼬리 질문

> [!question]- `List.contains()`와 `Set.contains()`의 시간 복잡도 차이는?
> `List.contains()`는 O(n)으로 처음부터 순회하고, `HashSet.contains()`는 O(1) 평균으로 hash 기반 조회합니다.

> [!question]- `distinct()`가 동작하지 않는 경우는 언제인가?
> 객체에 `equals()`와 `hashCode()`를 재정의하지 않으면 참조 비교가 되어 같은 값의 다른 인스턴스가 중복 제거되지 않습니다.

> [!question]- 다중 정렬 기준을 `Comparator`로 어떻게 표현하는가?
> `Comparator.comparing(Order::getStatus).thenComparing(Order::getCreatedAt, Comparator.reverseOrder())`처럼 `thenComparing()`으로 체이닝합니다.

> [!question]- DB 정렬과 애플리케이션 정렬은 언제 각각 적합한가?
> 정렬 기준이 DB 컬럼이고 데이터가 크면 ORDER BY가 효율적입니다. 여러 API 결과를 합치거나 가공된 값 기준이면 애플리케이션 정렬을 사용합니다.

> [!question]- `TreeSet`의 동등성 판단 기준은 `equals()`인가 `compareTo()`인가?
> `compareTo()`입니다. `compareTo()`가 0을 반환하면 같은 원소로 취급하므로, `equals()`와 일관되지 않으면 예상과 다르게 동작할 수 있습니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[hashmap]]
- [[equals-and-hashcode]]
- [[02-practical-backend/performance/performance|performance]]