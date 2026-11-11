---
title: Stream과 Optional 활용 기준
description: Stream과 Optional을 어디에 쓰면 읽기 좋아지고, 어디에 쓰면 오히려 나빠지는지
tags: [concept, java]
---

# Stream과 Optional 활용 기준

Stream은 컬렉션을 "무엇을 거르고, 무엇으로 바꾸고, 어떻게 모을지"만 적어서 처리하는 방식이다. Optional은 "이 메서드는 값을 못 돌려줄 수도 있다"는 걸 반환 타입에 드러내는 상자다. 둘 다 Java 8부터 가장 많이 쓰는 기능이지만, 아무 데나 쓰면 코드가 오히려 나빠진다.

흔히 겪는 문제는 이렇다. Stream을 길게 이어 붙여 디버깅이 어려워진다. `Optional`을 필드나 파라미터에 써서 쓸데없이 복잡해진다. `Optional.get()`을 검사 없이 불러 `NoSuchElementException`이 난다. Stream 안에서 외부 상태를 바꿔 동시성 문제가 생긴다. for문이면 충분한 로직을 Stream으로 바꿔 더 읽기 어려워진다.

## Stream

거르고, 바꾸고, 합치는 흐름이 분명할 때 Stream이 읽기 좋다. 완료된 주문의 금액 합계를 구하는 코드가 그렇다.

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

### 안에서 외부 상태를 바꾸지 않는다

```java
// Stream 안에서 외부 상태 변경 - 위험
List<String> results = new ArrayList<>();
items.stream()
    .filter(item -> item.isValid())
    .forEach(item -> results.add(item.getName())); // side effect
```

`forEach` 안에서 바깥 리스트를 고치는 건 Stream을 쓰는 방식이 아니다. parallelStream으로 바꾸면 여러 스레드가 같은 리스트에 동시에 넣게 되어 결과가 깨진다. 결과는 Stream이 돌려주는 값으로 받는다.

```java
// 올바른 방식
List<String> results = items.stream()
    .filter(Item::isValid)
    .map(Item::getName)
    .toList();
```

### for문이 나은 경우

- 한두 줄짜리 단순 로직
- 반복 중 인덱스가 필요할 때
- 중간에 break나 continue가 필요할 때
- 예외 처리가 복잡할 때
- 체이닝이 5단계 이상으로 길어질 때

## Optional

메서드 반환 타입에 쓰고, 값이 없을 때 어떻게 할지는 호출하는 쪽에서 정한다.

```java
// 메서드 반환 타입으로 사용
public Optional<User> findByEmail(String email) {
    return userRepository.findByEmail(email);
}

// 호출부에서 처리
User user = userService.findByEmail(email)
    .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
```

필드나 파라미터에는 쓰지 않고, 값이 있는지 확인하지 않은 채 `get()`을 부르지 않는다.

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

### 어떤 메서드로 꺼내나

| 메서드 | 쓰는 때 |
|---|---|
| `orElseThrow()` | 값이 없으면 예외를 던져야 할 때 |
| `orElse(기본값)` | 기본값이 이미 준비되어 있을 때 |
| `orElseGet(() -> ...)` | 기본값 생성 비용이 클 때 (lazy) |
| `ifPresent(consumer)` | 값이 있을 때만 처리하고 없으면 무시할 때 |
| `map()` / `flatMap()` | 값을 변환할 때 |

`orElse()`에 넘긴 식은 값이 있어도 항상 실행된다. 기본값을 만드는 데 비용이 크면 `orElseGet()`으로 넘긴다.

```java
// orElse - createDefault()가 항상 실행됨
User user = findById(id).orElse(createDefault());

// orElseGet - 값이 없을 때만 실행됨
User user = findById(id).orElseGet(() -> createDefault());
```

## 자주 깨지는 곳

- Stream 안에서 바깥 상태를 바꾸면, parallelStream으로 바꾸는 순간 결과가 깨진다.
- `Optional.get()`을 확인 없이 부르면, 값이 없을 때 `NoSuchElementException`이 난다.
- `Optional`을 필드, 파라미터, 컬렉션 원소로 쓰면, 직렬화 문제가 생기고 호출하는 쪽 코드만 복잡해진다.
- `orElse()`와 `orElseGet()`을 구분하지 않으면, 값이 있는데도 비싼 기본값을 매번 만든다.
- 단순한 null 체크를 `Optional`로 감싸면, 코드만 길어진다.
- 메서드를 너무 길게 이어 붙이면, 어느 단계에서 문제가 났는지 찾기 어렵다.
- `parallelStream()`을 빨라지겠거니 하고 아무 데나 쓰면, 데이터가 적거나 공유 pool이 붐빌 때 오히려 느려진다.

## 한 번에 설명하기

> Stream은 거르고, 바꾸고, 합치는 흐름이 분명할 때 씁니다. 다만 안에서 바깥 상태를 바꾸지 않고, 단순한 로직이나 중간에 break가 필요한 곳은 for문으로 둡니다.
>
> Optional은 반환 타입에서 값이 없을 수 있다는 걸 드러낼 때만 쓰고, 필드나 파라미터에는 쓰지 않습니다.
>
> 꺼낼 때는 get() 대신 orElseThrow()나 orElseGet()을 씁니다. orElse()는 값이 있어도 인자로 넘긴 식이 실행되기 때문입니다.

## 꼬리 질문

> [!question]- Stream에서 side effect가 문제가 되는 건 어떤 때인가?
> `forEach` 안에서 바깥 리스트를 고치다가 `parallelStream`으로 바꾸면, 여러 스레드가 같은 리스트를 동시에 건드리게 됩니다. `map()`이나 `collect()`로 결과를 돌려받는 쪽이 안전합니다.

> [!question]- `orElse()`와 `orElseGet()`은 코드로 보면 뭐가 다른가?
> `orElse(createDefault())`는 값이 있어도 `createDefault()`를 항상 실행합니다. `orElseGet(() -> createDefault())`는 값이 없을 때만 실행합니다. 기본값을 만드는 데 비용이 크면 `orElseGet()`을 씁니다.

> [!question]- `parallelStream()`은 언제 오히려 느려지나?
> 데이터가 적을 때, I/O 작업이 섞여 있을 때, 공유 ForkJoinPool을 다른 작업과 나눠 쓰느라 서로 기다릴 때 오히려 느려질 수 있습니다.

> [!question]- Optional을 필드로 쓰면 안 되는 이유는?
> `Optional`은 `Serializable`이 아니라서 직렬화할 때 문제가 생깁니다. 그리고 필드마다 한 번씩 감싸면 메모리도 더 쓰고 코드도 복잡해집니다.

> [!question]- Stream의 lazy evaluation은 어떻게 동작하나?
> `filter()`, `map()` 같은 중간 연산은 부르는 순간 실행되지 않습니다. `collect()`, `toList()` 같은 최종 연산을 부를 때 앞의 단계가 한꺼번에 실행됩니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>orElse()와 orElseGet()의 핵심 차이는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="orElse는 값 존재 여부와 관계없이 인자를 먼저 평가하고, orElseGet은 필요할 때 Supplier를 실행한다." aria-pressed="false">A. 기본값 계산 시점이 다르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 Optional 값을 꺼내는 API다. 차이는 반환 타입이 아니다." aria-pressed="false">B. 반환 타입이 완전히 다르다.</button>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: java.util.stream](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html)
- [Java SE 21 API: Optional](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[02-practical-backend/performance/performance|performance]]