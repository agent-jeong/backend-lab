---
title: Kotlin Data Class와 불변성
description: data class를 어디에 쓰고 어디에 쓰지 말지, val과 List가 실제로 무엇을 막아 주는지
tags: [concept, kotlin]
---

# Kotlin Data Class와 불변성

`data class`는 값을 실어 나르는 객체를 짧게 만드는 Kotlin 문법이다. 불변성은 만든 뒤에 객체 상태가 바뀌지 않게 막는 설계 원칙이다. 상태가 안 바뀌면 코드를 읽을 때 값이 어디서 바뀌었는지 찾아다닐 필요가 없다.

백엔드에는 request, response, command, event처럼 값만 나르는 객체가 많아서 `data class`가 잘 맞는다. 문제는 그 밖에서 쓸 때다. JPA Entity에 쓰면 자동으로 생기는 메서드가 사고를 내고, `val`이나 `List`를 불변이라고 착각하면 여러 곳이 같이 쓰는 주문 목록이 모르는 새 바뀐다. default value를 넣으면 요청에서 값이 빠졌는지 Jackson도 validation도 알아채지 못한다.

## data class를 쓰는 곳

DTO나 command처럼 값을 넘기는 게 목적인 객체에 쓴다.

```kotlin
data class OrderResponse(
    val orderId: Long,
    val status: String,
    val totalPrice: Long
)
```

`equals`, `hashCode`, `toString`, `copy`, `componentN`이 자동으로 생긴다. 값 객체에는 편한 일이지만, Entity처럼 식별자가 있고 저장, 조회, 수정을 거치며 오래 사는 객체에서는 바로 이 메서드들이 문제를 만든다.

## JPA Entity에는 쓰지 않는다

```kotlin
data class Order(
    val id: Long?,
    val status: String
)
```

- class와 method가 기본으로 final이라 JPA가 proxy를 만들 수 없다.
- `equals/hashCode`가 생성자의 모든 프로퍼티를 비교하도록 만들어진다.
- 양방향 연관관계가 `toString`에 들어가면 순환 참조가 생길 수 있다.
- `toString`, `equals`, `hashCode`가 지연 로딩 필드를 건드려 의도하지 않은 조회가 나갈 수 있다.

Entity는 일반 class로 만들고, data class는 DTO에만 쓴다.

## val과 불변성

`val`은 변수에 다른 값을 다시 넣는 것만 막는다.

```kotlin
val items: MutableList<String> = mutableListOf()
items.add("order") // 가능
```

가리키는 객체가 mutable이면 그 안의 내용은 바뀐다. Kotlin의 `List`도 읽기 전용 인터페이스일 뿐이라, 실제 객체가 `MutableList`라면 다른 쪽에서 내용을 바꿀 수 있다. 정말 안 바뀌게 하려면 mutable 타입을 밖으로 내보내지 말고, 필요하면 복사본을 넘긴다(방어적 복사).

```kotlin
class Cart(
    items: List<String>
) {
    private val _items = items.toMutableList()
    val items: List<String>
        get() = _items.toList()
}
```

## 어디에 무엇을 쓰나

| 상황 | 선택 |
|---|---|
| API request/response | data class |
| service command/query | data class |
| domain value object | data class 가능, 불변성은 확인 |
| JPA Entity | 일반 class |
| 외부에 노출하는 collection | 읽기 전용 타입 + 방어적 복사 검토 |

## 자주 깨지는 곳

- DTO와 Entity를 모두 `data class`로 만들면, Entity 쪽에서 proxy, equals/hashCode, 지연 로딩 문제가 한꺼번에 생긴다.
- `val`이면 완전히 불변이라고 믿으면, `val` 프로퍼티가 가리키는 mutable collection의 내용이 바뀌는 걸 놓친다.
- `copy()`를 deep copy로 알고 쓰면, 안쪽의 mutable 객체는 원본과 같이 쓰고 있어서 한쪽을 바꾸면 다른 쪽도 바뀐다. `copy()` 뒤에 안쪽 객체를 바꿔 보고 원본이 변하는지 테스트해 본다.
- mutable collection을 그대로 밖에 내주면, 받은 쪽이 내부 상태를 바꾼다.
- 필수 입력에 default value를 넣으면, 값이 안 왔는데도 기본값으로 정상 처리된다.

## 한 번에 설명하기

> `data class`는 DTO, command, event처럼 값을 넘기는 게 목적인 객체에 씁니다. JPA Entity는 식별자, proxy, 지연 로딩, 생명주기 문제가 얽혀서 일반 class로 만듭니다.
>
> `val`은 다시 대입하는 것만 막고 안쪽 내용이 바뀌는 건 못 막습니다. `List`도 읽기 전용 인터페이스일 뿐입니다.
>
> 그래서 정말 안 바뀌어야 하는 상태라면 mutable 객체를 밖으로 내보내지 않고, 복사본을 넘깁니다.

## 꼬리 질문

> [!question]- Kotlin data class는 어떤 상황에 적합한가?
> API DTO, command, event처럼 값을 넘기는 게 목적이고, 필드 값으로 `equals/hashCode/toString/copy`를 자동으로 만들어도 어색하지 않은 객체에 씁니다.

> [!question]- JPA Entity에 data class를 쓰면 왜 위험한가?
> 문제가 한꺼번에 겹칩니다. class가 final이라 proxy를 못 만들고, equals/hashCode가 모든 필드를 비교하고, toString이 지연 로딩 필드를 건드려 쿼리가 나갑니다.

> [!question]- `val`이면 불변 객체인가?
> 아닙니다. `val`은 다른 객체를 다시 넣는 것만 막습니다. 가리키는 객체가 mutable이면 그 안의 상태는 바뀝니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>data class가 특히 적합한 백엔드 용도는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="값 중심의 DTO, command, response처럼 동등성과 표현이 값 기준이어야 하는 모델에 적합하다." aria-pressed="false">A. DTO, command, response 같은 값 객체</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JPA Entity는 프록시, 지연 로딩, 변경 감지 때문에 data class와 충돌할 수 있다." aria-pressed="false">B. 모든 JPA Entity</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="스레드 풀 자체를 data class로 표현하는 것이 목적은 아니다." aria-pressed="false">C. ExecutorService 구현체</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>val 프로퍼티만 사용하면 객체 내부 상태까지 항상 완전한 불변이 된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="val은 참조 재할당을 막을 뿐, 참조 대상이 MutableList라면 내부 변경은 가능하다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="완전한 불변을 원하면 참조 대상의 mutable 여부까지 함께 관리해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA Entity에 data class를 피하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="data class가 생성하는 equals/hashCode/toString/copy와 final 성격이 JPA 프록시·연관관계와 충돌할 수 있다." aria-pressed="false">A. 자동 생성 메서드와 final 성격이 JPA 모델과 충돌할 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="data class에도 메서드를 정의할 수 있다." aria-pressed="false">B. data class는 메서드를 가질 수 없기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문제는 SQL 생성 여부가 아니라 엔티티 생명주기와 프록시다." aria-pressed="false">C. data class는 SQL을 절대 생성하지 못하기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kotlin: Data classes](https://kotlinlang.org/docs/data-classes.html)
- [Kotlin: No-arg compiler plugin (JPA)](https://kotlinlang.org/docs/no-arg-plugin.html)

## 관련 문서

- [[kotlin]]
- [[kotlin-null-safety]]
- [[01-core/java/class-interface-enum-record|class-interface-enum-record]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
