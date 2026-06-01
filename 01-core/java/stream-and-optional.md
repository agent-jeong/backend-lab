---
title: Stream And Optional
description: Java Stream과 Optional의 실무 사용 패턴과 남용 사례
---

# Stream And Optional

## 한 줄 정의

Stream은 컬렉션 데이터를 선언적으로 변환하고 집계하는 파이프라인이고, Optional은 값이 없을 수 있는 상황을 명시적으로 표현하는 컨테이너다.

## 실무에서 왜 중요한가

Stream과 Optional은 Java 8 이후 가장 많이 쓰이는 기능이지만, 남용하면 오히려 코드 품질이 떨어진다.

- Stream을 과도하게 체이닝해서 디버깅이 어려워진다.
- `Optional`을 필드나 파라미터에 사용해서 의도와 다르게 복잡해진다.
- `Optional.get()`을 검사 없이 호출해서 `NoSuchElementException`이 발생한다.
- Stream 안에서 외부 상태를 변경해서 동시성 문제가 생긴다.
- 단순 for문이면 충분한 로직을 Stream으로 바꿔서 가독성이 나빠진다.

## Stream 실무 패턴

### 적절한 사용

```java
// 주문 목록에서 특정 상태의 주문 금액 합계
long totalAmount = orders.stream()
    .filter(order -> order.getStatus() == OrderStatus.COMPLETED)
    .mapToLong(Order::getAmount)
    .sum();
```

```java
// Entity -> DTO 변환
List<UserResponse> responses = users.stream()
    .map(UserResponse::from)
    .toList();
```

필터링, 변환, 집계처럼 데이터 흐름이 명확한 경우에 Stream이 읽기 좋다.

### 남용 사례

```java
// Stream 안에서 외부 상태 변경 - 위험
List<String> results = new ArrayList<>();
items.stream()
    .filter(item -> item.isValid())
    .forEach(item -> results.add(item.getName())); // side effect
```

`forEach` 안에서 외부 리스트를 변경하는 것은 Stream의 의도에 맞지 않고, parallelStream 사용 시 동시성 문제가 생긴다.

```java
// 올바른 방식
List<String> results = items.stream()
    .filter(Item::isValid)
    .map(Item::getName)
    .toList();
```

### Stream을 쓰지 않는 것이 나은 경우

- 단순 for문으로 충분한 한두 줄 로직
- 반복 중 인덱스가 필요한 경우
- 중간에 break나 continue가 필요한 경우
- 예외 처리가 복잡한 경우
- Stream 체이닝이 5단계 이상으로 길어지는 경우

## Optional 실무 패턴

### 적절한 사용

```java
// 메서드 반환 타입으로 사용
public Optional<User> findByEmail(String email) {
    return userRepository.findByEmail(email);
}

// 호출부에서 처리
User user = userService.findByEmail(email)
    .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
```

### 잘못된 사용

```java
// 필드로 사용 - 금지
public class User {
    private Optional<String> nickname; // 직렬화 문제, 불필요한 복잡성
}

// 파라미터로 사용 - 금지
public void updateUser(Optional<String> nickname) { // 호출부가 불편
}

// get()을 검사 없이 호출
Optional<User> user = findById(id);
user.get(); // NoSuchElementException 가능
```

### Optional 처리 메서드 선택

| 메서드 | 사용 시점 |
|---|---|
| `orElseThrow()` | 값이 없으면 예외를 던져야 할 때 |
| `orElse(기본값)` | 기본값이 항상 준비되어 있을 때 |
| `orElseGet(() -> ...)` | 기본값 생성 비용이 클 때 (lazy) |
| `ifPresent(consumer)` | 값이 있을 때만 처리하고 없으면 무시할 때 |
| `map()` / `flatMap()` | 값을 변환할 때 |

주의: `orElse()`는 값이 있어도 인자가 항상 실행된다. 비용이 큰 연산은 `orElseGet()`을 써야 한다.

```java
// orElse - createDefault()가 항상 실행됨
User user = findById(id).orElse(createDefault());

// orElseGet - 값이 없을 때만 실행됨
User user = findById(id).orElseGet(() -> createDefault());
```

## 자주 나는 실수

- Stream에서 외부 상태를 변경한다.
- `Optional.get()`을 검사 없이 호출한다.
- `Optional`을 필드, 파라미터, 컬렉션 원소로 사용한다.
- `orElse()`와 `orElseGet()`의 차이를 모르고 사용한다.
- 단순 null 체크를 `Optional`로 감싸서 코드만 늘린다.
- Stream 체이닝이 길어져서 어디서 문제가 생기는지 추적이 어렵다.
- `parallelStream()`을 성능 개선 목적으로 무분별하게 사용한다.

## 면접 답변 1분 버전

Stream은 컬렉션 데이터를 선언적으로 필터링, 변환, 집계하는 파이프라인입니다. 가독성이 좋지만, 외부 상태를 변경하는 side effect를 넣으면 안 되고, 단순 로직에서는 for문이 나을 수 있습니다. Optional은 메서드 반환 타입에서 값이 없을 수 있음을 명시적으로 표현할 때 사용합니다. 필드나 파라미터에는 사용하지 않고, `get()` 대신 `orElseThrow()`나 `orElseGet()`을 사용하는 것이 안전합니다. 주의할 점으로 `orElse()`는 값이 있어도 인자가 항상 실행되므로, 비용이 큰 연산은 `orElseGet()`을 써야 합니다.

## 꼬리 질문

- Stream에서 side effect가 문제가 되는 구체적인 상황은?
- `orElse()`와 `orElseGet()`의 차이를 코드로 설명할 수 있는가?
- `parallelStream()`은 언제 성능이 나빠지는가?
- Optional을 필드로 사용하면 안 되는 이유는?
- Stream의 lazy evaluation은 어떻게 동작하는가?

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[02-practical-backend/performance/performance|performance]]