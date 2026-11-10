---
title: 기본 타입과 참조 타입의 차이
description: Java primitive type과 reference type의 차이와 실무 주의점
tags: [concept, java]
---

# 기본 타입과 참조 타입의 차이

primitive type은 값 자체를 담는 기본 타입이고, reference type은 객체를 가리키는 참조값을 담는 타입이다.

이 차이를 놓치면 `==`, `equals()`, `null`, wrapper type, 컬렉션에서 버그가 난다. 실무에서 흔한 건 `String`이나 `Integer`·`Long`을 `==`로 비교하는 것, wrapper의 `null`을 잊어 `NullPointerException`이 나는 것, Request DTO에 primitive를 써서 값 누락과 기본값을 구분하지 못하는 것이다.

## 두 타입의 차이

| | primitive type | reference type |
|---|---|---|
| 예 | `int`, `long`, `double`, `char`, `boolean` | `String`, 배열, 클래스, 인터페이스, enum |
| 변수가 담는 것 | 실제 값 | 객체를 가리키는 참조값 |
| `null` | 될 수 없다 | 될 수 있다 |
| `==` | 값 비교 | 같은 객체인지 비교 |

```java
int a = 100;
int b = 100;

System.out.println(a == b); // true
```

```java
String a = new String("java");
String b = new String("java");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // true
```

문자열 내용은 `equals()`로 비교한다.

## Wrapper type

`Integer`, `Long`, `Boolean` 같은 wrapper type은 reference type이다. 그래서 `null`이 될 수 있고, 자동 unboxing 순간에 `NullPointerException`이 난다.

```java
Integer count = null;

if (count == 0) {
    // NullPointerException 발생 가능
}
```

값 비교도 `==`가 아니라 `Objects.equals()`로 한다. `==`는 참조 비교라서 같은 값이어도 false가 나올 수 있다.

```java
Integer a = 128;
Integer b = 128;

System.out.println(a == b); // false일 수 있음
System.out.println(Objects.equals(a, b)); // true
```

## 어떤 타입을 고르나

- 값이 늘 있어야 하면 primitive type을 먼저 쓴다.
- 값이 없을 수 있거나 DB `NULL`을 표현해야 하면 wrapper type을 쓴다.
- 객체 내용은 `equals()`, wrapper 값은 `Objects.equals()`로 비교한다.
- `equals()`를 부르는 쪽이 `null`일 수 있으면 상수나 null이 아닌 객체에서 호출한다.

```java
if ("ACTIVE".equals(status)) {
    // status가 null이어도 안전
}
```

## 면접에서 말하기

> primitive type은 값 자체를, reference type은 객체를 가리키는 참조를 다룹니다. primitive는 `null`이 될 수 없고 `==`로 값을 비교하지만, reference type의 `==`는 같은 객체인지를 보고 의미상 같은지는 `equals()`로 봅니다. 실무에서는 문자열이나 wrapper를 `==`로 비교하거나 wrapper의 `null`을 unboxing하다 NPE가 나는 경우가 많아서, 값이 없을 수 있는지로 타입을 고르고 비교는 `equals()`나 `Objects.equals()`로 합니다.

## 꼬리 질문

> [!question]- `int`와 `Integer`는 언제 각각 사용해야 하는가?
> 값이 반드시 있어야 하면 `int`, 값이 없을 수 있거나 DB NULL을 표현해야 하면 `Integer`를 사용합니다. 컬렉션의 제네릭 타입에는 `Integer`만 가능합니다.

> [!question]- `String` 비교에서 `==`가 아니라 `equals()`를 써야 하는 이유는 무엇인가?
> `==`는 같은 객체 참조인지 비교합니다. `new String("java")`처럼 생성하면 내용이 같아도 다른 객체이므로 `==`가 false를 반환합니다.

> [!question]- auto boxing과 auto unboxing은 어떤 문제를 만들 수 있는가?
> wrapper type이 null일 때 unboxing하면 `NullPointerException`이 발생합니다. 또한 반복문에서 불필요한 boxing이 반복되면 성능에 영향을 줄 수 있습니다.

> [!question]- Boolean과 boolean은 언제 구분해서 사용해야 하는가?
> 값이 반드시 true 또는 false라면 boolean을 사용합니다. 반면 true, false, 미정 처럼 세 가지 상태를 표현해야 하거나 DB NULL을 표현해야 한다면 Boolean을 사용합니다. 단, 조건문에서는 Boolean.TRUE.equals(value)처럼 비교하는 것이 안전합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>int 대신 Integer를 선택해야 하는 대표적인 경우는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="성능만 보면 primitive가 더 단순하고 boxing 비용도 없다." aria-pressed="false">A. 모든 숫자 연산에서 성능을 높이고 싶을 때</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="null로 값의 부재를 표현해야 하거나 제네릭/컬렉션에 담아야 할 때 wrapper가 필요하다." aria-pressed="false">B. null 가능성이나 컬렉션/제네릭 사용이 필요한 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="비교 연산을 위해 wrapper를 쓰면 오히려 == 비교 함정이 생길 수 있다." aria-pressed="false">C. == 비교를 더 안전하게 만들고 싶을 때</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Integer끼리는 값이 같으면 항상 == 비교가 true다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Integer 캐시는 일부 범위에만 적용된다. 값 비교는 equals를 사용해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="wrapper 객체의 ==는 참조 비교다. 캐시 범위를 벗어나면 같은 값이어도 false가 될 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Boolean wrapper를 사용할 때 기술 질문에서 자주 지적되는 위험은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Boolean은 null이 될 수 있어 auto-unboxing 시 NullPointerException이 발생할 수 있다." aria-pressed="false">A. null 값이 auto-unboxing되면 NPE가 날 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Boolean 자체가 동시성 안전성을 제공하지는 않는다." aria-pressed="false">B. Boolean은 멀티스레드에서 항상 race condition을 만든다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="값이 두 개뿐이라서가 아니라 null이 들어올 수 있어서 문제다." aria-pressed="false">C. true/false만 표현할 수 있어서 상태 표현이 불가능하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [JLS 21: Types, Values, and Variables](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html)
- [JLS 21: Boxing Conversion](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html#jls-5.1.7)

## 관련 문서

- [[01-core/java/java|java]]
