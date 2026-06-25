---
title: Stream과 Optional 활용 기준
description: Java Stream과 Optional의 실무 사용 패턴과 남용 사례
---

# Stream과 Optional 활용 기준

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

## 핵심 요약

Stream은 컬렉션 데이터를 선언적으로 필터링, 변환, 집계하는 파이프라인입니다.
가독성이 좋지만, 외부 상태를 변경하는 side effect를 넣으면 안 되고, 단순 로직에서는 for문이 나을 수 있습니다.

Optional은 메서드 반환 타입에서 값이 없을 수 있음을 명시적으로 표현할 때 사용합니다.
필드나 파라미터에는 사용하지 않고, `get()` 대신 `orElseThrow()`나 `orElseGet()`을 사용하는 것이 안전합니다.

주의할 점으로 `orElse()`는 값이 있어도 인자가 항상 실행되므로, 비용이 큰 연산은 `orElseGet()`을 써야 합니다.

## 꼬리 질문

> [!question]- Stream에서 side effect가 문제가 되는 구체적인 상황은?
> `forEach` 안에서 외부 리스트를 수정하면 `parallelStream` 사용 시 동시성 문제가 생깁니다. `map()`이나 `collect()`로 결과를 반환하는 것이 안전합니다.

> [!question]- `orElse()`와 `orElseGet()`의 차이를 코드로 설명할 수 있는가?
> `orElse(createDefault())`는 값이 있어도 `createDefault()`가 항상 실행됩니다. `orElseGet(() -> createDefault())`는 값이 없을 때만 실행됩니다. 비용이 큰 연산은 `orElseGet()`을 써야 합니다.

> [!question]- `parallelStream()`은 언제 성능이 나빠지는가?
> 데이터가 적거나, I/O 작업이 섞여 있거나, 공유 ForkJoinPool에서 다른 작업과 경합할 때 오히려 느려질 수 있습니다.

> [!question]- Optional을 필드로 사용하면 안 되는 이유는?
> `Optional`은 `Serializable`하지 않아 직렬화 문제가 생기고, 필드마다 wrapping하면 메모리 오버헤드와 코드 복잡성이 늘어납니다.

> [!question]- Stream의 lazy evaluation은 어떻게 동작하는가?
> `filter()`, `map()` 같은 중간 연산은 즉시 실행되지 않고, `collect()`, `toList()` 같은 최종 연산이 호출될 때 파이프라인 전체가 실행됩니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>orElse()와 orElseGet()의 핵심 차이는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="orElse는 값 존재 여부와 관계없이 인자를 먼저 평가하고, orElseGet은 필요할 때 Supplier를 실행한다." aria-pressed="false">A. 기본값 계산 시점이 다르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 Optional 값을 꺼내는 API이며 반환 타입 차이가 핵심은 아니다." aria-pressed="false">B. 반환 타입이 완전히 다르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="orElseGet도 null을 무조건 막아주지는 않는다." aria-pressed="false">C. orElseGet은 null을 절대 반환할 수 없다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Optional을 Entity 필드나 DTO 필드 타입으로 쓰는 것은 일반적으로 권장된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Optional은 반환 타입에서 부재 가능성을 표현하는 용도에 가깝고 필드에는 직렬화/ORM 호환 문제가 생길 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="필드 타입보다는 메서드 반환 타입에서 제한적으로 쓰는 것이 일반적이다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>parallelStream()이 오히려 느려질 수 있는 대표적인 경우는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="작업이 작거나 blocking I/O가 섞이면 분할/병합과 공용 풀 경쟁 비용이 이득보다 클 수 있다." aria-pressed="false">A. 작은 작업이거나 blocking I/O가 섞인 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="CPU 바운드 대량 작업은 조건이 맞으면 이점이 있을 수 있다." aria-pressed="false">B. 독립적인 CPU 연산이 충분히 큰 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="순수 함수 기반 처리 자체가 문제는 아니다." aria-pressed="false">C. 부작용 없는 map 연산만 있는 경우</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[02-practical-backend/performance/performance|performance]]