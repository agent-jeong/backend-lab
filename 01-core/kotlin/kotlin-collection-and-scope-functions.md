---
title: Kotlin Collection과 Scope Functions
description: Kotlin 컬렉션 처리와 scope function의 실무 사용 기준
---

# Kotlin Collection과 Scope Functions

## 한 줄 정의

Kotlin collection 함수와 scope function은 데이터를 변환하고 객체 초기화나 null 처리를 간결하게 표현하는 도구다.

## 실무에서 왜 중요한가

Kotlin은 컬렉션 처리와 객체 조립 코드가 짧다. 하지만 남용하면 다음 문제가 생긴다.

- `map`, `filter`, `groupBy` 체인이 길어져 디버깅이 어렵다.
- `also`, `apply`, `let`, `run`을 섞어 `it`과 `this`가 헷갈린다.
- 큰 컬렉션에서 중간 컬렉션을 많이 만들어 메모리 사용량이 늘어난다.
- Java Stream과 Kotlin collection의 eager/lazy 차이를 모르고 성능을 오해한다.
- scope function 안에서 side effect를 숨긴다.

## Collection 처리

Kotlin collection 함수는 기본적으로 eager evaluation이다.

```kotlin
val userIds = orders
    .filter { it.status == OrderStatus.PAID }
    .map { it.userId }
    .distinct()
```

각 단계가 새 컬렉션을 만들 수 있다. 데이터가 크거나 체인이 길면 `Sequence`를 검토한다.

```kotlin
val userIds = orders.asSequence()
    .filter { it.status == OrderStatus.PAID }
    .map { it.userId }
    .distinct()
    .toList()
```

단, 작은 목록이나 단순 변환에서는 일반 collection 함수가 더 읽기 쉽다.

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

Java의 `stream().collect(toMap())`보다 간결하지만, key 중복 가능성은 여전히 확인해야 한다.

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

scope function은 짧은 블록에서만 읽기 좋다. 중첩되면 일반 변수로 풀어 쓰는 편이 낫다.

## 자주 나는 실수

- `let`, `also`, `apply`를 중첩해서 현재 객체가 무엇인지 헷갈리게 만든다.
- `also` 안에 중요한 비즈니스 로직을 숨긴다.
- 큰 컬렉션에서 eager collection chain을 과하게 사용한다.
- `groupBy`로 큰 map/list를 만들고 메모리 사용량을 고려하지 않는다.
- `associateBy`에서 중복 key가 생기는 상황을 확인하지 않는다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| 단순 목록 변환 | collection 함수 |
| 큰 데이터 연속 변환 | `Sequence` 검토 |
| null이면 변환 | `let` |
| 객체 초기 설정 | `apply` |
| 로깅 같은 부가 작업 | `also` |
| 복잡한 비즈니스 로직 | scope function보다 명시적 변수 |

## 확인 방법

- scope function 중첩이 2단계 이상이면 풀어 쓰는 것을 검토한다.
- 컬렉션 크기가 커질 수 있으면 중간 컬렉션 생성 비용을 확인한다.
- `associateBy`, `groupBy`의 key 중복과 메모리 사용량을 확인한다.
- 변환 과정에 side effect가 섞여 있는지 확인한다.

## 핵심 요약

Kotlin collection 함수는 데이터 변환과 조립을 간결하게 만든다.

하지만 기본 collection chain은 eager evaluation이라 큰 데이터에서는 중간 컬렉션 비용을 고려해야 한다.

scope function은 null 처리, 객체 설정, 부가 작업을 간결하게 만들지만 중첩하면 가독성이 급격히 떨어진다.

`let`, `also`, `apply`의 반환값과 컨텍스트 객체 차이를 알고 사용해야 한다.

실무에서는 짧고 명확한 변환에는 Kotlin 스타일을 쓰고, 복잡한 로직은 명시적 변수와 함수로 분리하는 것이 좋다.

## 꼬리 질문

> [!question]- Kotlin collection 함수와 Sequence의 차이는?
> 일반 collection 함수는 기본적으로 eager하게 각 단계에서 컬렉션을 만들 수 있고, Sequence는 lazy하게 처리해 큰 데이터 연속 변환에서 중간 비용을 줄일 수 있습니다.

> [!question]- `let`, `also`, `apply`의 차이는?
> `let`은 lambda 결과를 반환하고 `it`을 사용합니다. `also`는 원본 객체를 반환하고 `it`을 사용합니다. `apply`는 원본 객체를 반환하고 `this`를 사용합니다.

> [!question]- scope function을 남용하면 왜 문제가 되는가?
> 중첩될수록 현재 객체와 반환값이 불명확해져 중요한 비즈니스 로직을 읽기 어려워집니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Collection 함수와 Sequence의 실무적 차이로 가장 적절한 것은?</p>
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
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 기본적으로 수신 객체를 반환한다. 반환 타입 차이가 핵심은 아니다." aria-pressed="false">B. 하나는 항상 Boolean을 반환한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="둘 다 scope function이며 coroutine 전용 기능이 아니다." aria-pressed="false">C. apply는 coroutine에서만 사용할 수 있다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[kotlin]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/collection-selection|collection-selection]]
- [[01-core/java/stream-and-optional|stream-and-optional]]
