---
title: Kotlin Collection과 Scope Functions
description: Kotlin 컬렉션 함수와 Sequence, scope function을 언제 쓰고 언제 풀어 쓸지
tags: [concept, kotlin]
---

# Kotlin Collection과 Scope Functions

Kotlin의 collection 함수와 scope function을 쓰면 데이터 변환, 객체 초기화, null 처리를 몇 줄로 짧게 쓸 수 있다.

그런데 짧게 쓸 수 있어서 오히려 탈이 난다. 주문 목록에 `map`, `filter`, `groupBy`를 길게 이어 붙이면 어디서 값이 틀어졌는지 디버깅하기 어렵다. `also`, `apply`, `let`, `run`이 섞이면 `it`과 `this`가 무엇을 가리키는지 헷갈린다. 컬렉션 함수는 기본이 eager라서, 큰 컬렉션에서는 단계마다 생기는 중간 컬렉션이 메모리를 먹는다.

## Collection 처리

collection 함수는 기본이 eager evaluation이라 호출하는 즉시 계산한다. Java Stream이 lazy인 것과 다르다.

```kotlin
val userIds = orders
    .filter { it.status == OrderStatus.PAID }
    .map { it.userId }
    .distinct()
```

단계마다 새 컬렉션이 생긴다. 데이터가 크거나 체인이 길면 `Sequence`를 쓴다.

```kotlin
val userIds = orders.asSequence()
    .filter { it.status == OrderStatus.PAID }
    .map { it.userId }
    .distinct()
    .toList()
```

작은 목록이나 단순 변환이면 일반 collection 함수가 더 읽기 쉽다.

## 자주 쓰는 패턴

| 목적 | 함수 |
|---|---|
| 변환 | `map` |
| 조건 필터 | `filter` |
| null 제거와 변환 | `mapNotNull` |
| key 기준 변환 | `associateBy` |
| 그룹핑 | `groupBy` |
| 합계/집계 | `sumOf`, `fold` |

```kotlin
val userMap = users.associateBy { it.id }

val responses = orders.map { order ->
    OrderResponse.of(order, userMap[order.userId])
}
```

Java의 `stream().collect(toMap())`보다 짧다. 다만 key가 겹칠 수 있는지는 여전히 직접 확인해야 한다.

## Scope Functions

| 함수 | 반환 | 컨텍스트 | 주 사용처 |
|---|---|---|---|
| `let` | lambda 결과 | `it` | null 처리, 변환 |
| `also` | 원본 객체 | `it` | 로깅, 부가 작업 |
| `apply` | 원본 객체 | `this` | 객체 설정 |
| `run` | lambda 결과 | `this` | 객체 기반 계산 |
| `with` | lambda 결과 | `this` | 이미 있는 객체 사용 |

```kotlin
val result = user
    ?.let { UserResponse.from(it) }
    ?: UserResponse.empty()
```

scope function은 블록이 짧을 때만 읽기 좋다. 중첩되면 일반 변수로 풀어 쓴다.

## 무엇을 쓸까

| 상황 | 선택 |
|---|---|
| 단순 목록 변환 | collection 함수 |
| 큰 데이터 연속 변환 | `Sequence` |
| null이면 변환 | `let` |
| 객체 초기 설정 | `apply` |
| 로깅 같은 부가 작업 | `also` |
| 복잡한 비즈니스 로직 | scope function 대신 명시적 변수와 함수 |

## 자주 깨지는 곳

- `let`, `also`, `apply`를 중첩하면, 지금 `it`과 `this`가 무엇인지 헷갈린다. 2단계 이상이면 풀어 쓴다.
- `also` 안에 비즈니스 로직을 넣으면, 로깅처럼 보이는 블록이 실제로는 상태를 바꾼다. 변환 중간에 side effect가 섞였는지 본다.
- 큰 컬렉션에 eager 체인을 길게 걸면, 단계마다 중간 컬렉션이 생겨 메모리를 먹는다.
- `groupBy`로 큰 map이나 list를 만들면, 메모리 사용량이 데이터 크기만큼 늘어난다.
- `associateBy`를 쓰면서 key가 겹치는지 확인하지 않으면, 겹친 key의 앞쪽 데이터가 아무 경고 없이 사라진다.

## 한 번에 설명하기

> Kotlin collection 함수는 기본이 eager라서 체인 단계마다 중간 컬렉션이 생깁니다. 그래서 큰 데이터를 여러 번 변환할 때는 `Sequence`를 씁니다.
>
> scope function은 함수마다 돌려주는 값과 블록 안에서 객체를 부르는 이름이 다릅니다. `let`은 lambda 결과를 돌려주고 `it`으로 부르고, `also`는 원본을 돌려주고 `it`으로, `apply`는 원본을 돌려주고 `this`로 부릅니다.
>
> 저는 짧고 뻔한 변환에만 쓰고, 중첩되거나 비즈니스 로직이 들어가면 변수와 함수로 풀어 씁니다.

## 꼬리 질문

> [!question]- Kotlin collection 함수와 Sequence의 차이는?
> 일반 collection 함수는 eager라서 단계마다 컬렉션을 새로 만듭니다. Sequence는 lazy라서 원소 하나씩 끝까지 흘려보내기 때문에, 큰 데이터를 여러 번 변환할 때 중간 컬렉션 비용이 줄어듭니다.

> [!question]- `let`, `also`, `apply`의 차이는?
> `let`은 lambda 결과를 돌려주고 블록 안에서 객체를 `it`으로 부릅니다. `also`는 원본 객체를 돌려주고 `it`으로 부릅니다. `apply`는 원본 객체를 돌려주고 `this`로 부릅니다. 그래서 변환은 `let`, 로깅은 `also`, 객체 설정은 `apply`에 씁니다.

> [!question]- scope function을 남용하면 왜 문제가 되는가?
> 겹겹이 쌓일수록 지금 블록의 객체가 무엇이고 무엇을 돌려주는지가 흐려져서, 정작 봐야 할 비즈니스 로직이 안 읽힙니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Collection 함수와 Sequence의 실무 차이로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Collection은 중간 결과를 만들 수 있고, Sequence는 지연 평가로 긴 체인이나 대량 데이터에서 이점이 있을 수 있다." aria-pressed="false">A. Sequence는 지연 평가로 중간 컬렉션 생성을 줄일 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Sequence가 항상 빠른 것은 아니다. 작은 데이터에서는 오버헤드가 더 클 수 있다." aria-pressed="false">B. Sequence는 모든 경우 Collection보다 빠르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 컬렉션 처리에 쓰이며 DB 쿼리를 자동 최적화하지 않는다." aria-pressed="false">C. Sequence를 쓰면 DB 인덱스가 자동 생성된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>scope function을 중첩해서 많이 쓰면 this/it의 의미가 흐려져 가독성이 나빠질 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="let/apply/also/run/with는 의도를 드러낼 때 유용하지만 중첩하면 수신 객체 추적이 어려워진다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="scope function은 가독성을 높일 수도 있지만 남용하면 반대로 읽기 어려워진다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>also와 apply의 차이를 설명할 때 핵심 기준은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="apply는 수신 객체를 this로 다루며 객체 설정에, also는 it으로 다루며 부가 작업에 자주 쓴다." aria-pressed="false">A. 수신 객체 접근 방식과 의도</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 수신 객체를 반환한다. 차이는 반환 타입이 아니다." aria-pressed="false">B. 하나는 항상 Boolean을 반환한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 scope function이며 coroutine 전용 기능이 아니다." aria-pressed="false">C. apply는 coroutine에서만 사용할 수 있다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kotlin: Scope functions](https://kotlinlang.org/docs/scope-functions.html)
- [Kotlin: Sequences](https://kotlinlang.org/docs/sequences.html)

## 관련 문서

- [[01-core/kotlin/kotlin|kotlin]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/collection-selection|collection-selection]]
- [[01-core/java/stream-and-optional|stream-and-optional]]
