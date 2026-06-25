---
title: Kotlin Data Class와 불변성
description: Kotlin data class, val, copy, 불변 컬렉션의 실무 사용 기준
---

# Kotlin Data Class와 불변성

## 한 줄 정의

Kotlin `data class`는 값 전달 객체를 간결하게 만들기 위한 문법이고, 불변성은 객체 상태 변경을 제한해 예측 가능한 코드를 만드는 설계 원칙이다.

## 실무에서 왜 중요한가

백엔드에서는 request, response, command, event 같은 값 전달 객체가 많다. Kotlin은 이를 간결하게 만들지만 다음 주의점이 있다.

- `data class`를 JPA Entity로 사용하면 자동 생성된 `equals`, `hashCode`, `toString`이 문제를 만들 수 있다.
- `val`은 재할당을 막지만 참조하는 객체 내부 변경까지 막지는 않는다.
- `List`는 읽기 전용 인터페이스이지 완전한 불변 컬렉션이 아니다.
- `copy()`는 얕은 복사라 nested mutable 객체는 공유될 수 있다.
- default value가 Jackson 역직렬화와 validation 의미를 흐릴 수 있다.

## data class 사용처

`data class`는 DTO나 command처럼 값 전달이 목적인 객체에 적합하다.

```kotlin
data class OrderResponse(
    val orderId: Long,
    val status: String,
    val totalPrice: Long
)
```

자동으로 다음 메서드가 생성된다.

- `equals`
- `hashCode`
- `toString`
- `copy`
- `componentN`

이 자동 생성이 장점이지만, Entity처럼 식별자와 생명주기가 있는 객체에는 위험할 수 있다.

## JPA Entity에 data class를 피하는 이유

```kotlin
data class Order(
    val id: Long?,
    val status: String
)
```

JPA Entity에 `data class`를 사용하면 다음 문제가 생길 수 있다.

- class와 method가 기본적으로 final이라 proxy 생성과 충돌한다.
- `equals/hashCode`가 모든 생성자 프로퍼티를 기준으로 만들어진다.
- 양방향 연관관계가 `toString`에 포함되면 순환 참조가 생길 수 있다.
- 지연 로딩 필드 접근이 의도치 않게 발생할 수 있다.

JPA Entity는 일반 class로 만들고, DTO는 data class로 분리하는 편이 안전하다.

## val과 불변성

`val`은 변수 재할당을 막는다.

```kotlin
val items: MutableList<String> = mutableListOf()
items.add("order") // 가능
```

하지만 참조하는 객체가 mutable이면 내부 상태 변경은 가능하다. 완전한 불변성을 원하면 mutable 타입을 외부로 노출하지 않아야 한다.

```kotlin
class Cart(
    items: List<String>
) {
    private val _items = items.toMutableList()
    val items: List<String>
        get() = _items.toList()
}
```

## 자주 나는 실수

- DTO와 Entity를 모두 `data class`로 만든다.
- `val`이면 객체가 완전히 불변이라고 생각한다.
- `copy()`가 deep copy라고 오해한다.
- mutable collection을 외부에 그대로 노출한다.
- default value로 필수 입력 누락을 숨긴다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| API request/response | data class |
| service command/query | data class |
| domain value object | data class 가능, 불변성 확인 |
| JPA Entity | 일반 class 우선 |
| 외부 노출 collection | 읽기 전용 타입 + 방어적 복사 검토 |

## 확인 방법

- JPA Entity가 `data class`인지 확인한다.
- `toString`, `equals`, `hashCode`가 lazy loading 필드를 건드리지 않는지 확인한다.
- `val` 프로퍼티가 mutable collection을 가리키는지 확인한다.
- `copy()` 후 nested 객체 변경이 원본에 영향을 주는지 테스트한다.

## 핵심 요약

Kotlin `data class`는 DTO, command, event처럼 값 전달이 목적인 객체에 적합하다.

JPA Entity는 식별자, proxy, lazy loading, 생명주기 문제가 있어 `data class`를 피하는 편이 안전하다.

`val`은 재할당을 막지만 객체 내부 변경까지 막지는 않는다.

Kotlin의 `List`는 읽기 전용 인터페이스일 뿐 완전한 불변 컬렉션을 보장하지 않는다.

불변성을 실무에서 얻으려면 mutable 상태를 외부에 노출하지 않고, 필요한 경우 방어적 복사를 사용해야 한다.

## 꼬리 질문

> [!question]- Kotlin data class는 어떤 상황에 적합한가?
> API DTO, command, event처럼 값 전달이 목적이고 자동 `equals/hashCode/toString/copy`가 자연스러운 객체에 적합합니다.

> [!question]- JPA Entity에 data class를 쓰면 왜 위험한가?
> final class, 모든 필드 기반 equals/hashCode, toString의 lazy loading 접근, proxy 생성 문제 때문에 위험할 수 있습니다.

> [!question]- `val`이면 불변 객체인가?
> 아닙니다. `val`은 참조 재할당만 막습니다. 참조 대상이 mutable이면 내부 상태는 변경될 수 있습니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

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
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA Entity에 data class를 피하는 이유로 가장 적절한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="data class가 생성하는 equals/hashCode/toString/copy와 final 성격이 JPA 프록시·연관관계와 충돌할 수 있다." aria-pressed="false">A. 자동 생성 메서드와 final 성격이 JPA 모델과 충돌할 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="data class에도 메서드를 정의할 수 있다." aria-pressed="false">B. data class는 메서드를 가질 수 없기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문제의 핵심은 SQL 생성 여부가 아니라 엔티티 생명주기와 프록시다." aria-pressed="false">C. data class는 SQL을 절대 생성하지 못하기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[kotlin]]
- [[kotlin-null-safety]]
- [[01-core/java/class-interface-enum-record|class-interface-enum-record]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
