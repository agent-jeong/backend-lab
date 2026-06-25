---
title: 기본 타입과 참조 타입의 차이
description: Java primitive type과 reference type의 차이와 실무 주의점
---

# 기본 타입과 참조 타입의 차이

## 한 줄 정의

Java의 primitive type은 값 자체를 다루는 기본 타입이고, reference type은 객체에 접근하기 위한 참조값을 다루는 타입이다.

## 실무에서 왜 중요한가

두 타입의 차이를 모르면 `==`, `equals()`, `null`, wrapper type, 컬렉션 사용에서 버그가 자주 생긴다.

특히 실무에서는 다음 문제가 자주 발생한다.

- `String` 값을 `==`로 비교한다.
- `Integer`, `Long` 같은 wrapper type을 `==`로 비교한다. 
- wrapper type의 `null`을 고려하지 않아 `NullPointerException`이 발생한다. 
- Request DTO에서 primitive를 사용해 값 누락과 기본값을 구분하지 못한다.

## 핵심 개념

- primitive type은 `int`, `long`, `double`, `char`, `boolean` 같은 기본 타입이다.
- primitive 변수는 실제 값을 가진다.
- primitive type은 `null`이 될 수 없다.
- reference type은 `String`, 배열, 클래스, 인터페이스, enum 같은 객체 타입이다.
- reference 변수는 객체 자체가 아니라 객체를 가리키는 참조값을 가진다.
- reference type은 `null`이 될 수 있다.

## 비교 방식

primitive type에서 `==`는 값을 비교한다.

```java
int a = 100;
int b = 100;

System.out.println(a == b); // true
```

reference type에서 `==`는 같은 객체를 참조하는지 비교한다.

```java
String a = new String("java");
String b = new String("java");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // true
```

문자열 내용 비교는 `==`가 아니라 `equals()`를 사용한다.

## Wrapper Type 주의점

`Integer`, `Long`, `Boolean` 같은 wrapper type은 reference type이다.

따라서 wrapper type은 `null`이 될 수 있고, 자동 unboxing 과정에서 `NullPointerException`이 발생할 수 있다.

```java
Integer count = null;

if (count == 0) {
    // NullPointerException 발생 가능
}
```

또한 wrapper type은 reference type이므로 ==로 값 비교를 하면 안 되고, `Objects.equals()`를 사용하는 것이 안전하다.

```java
Integer a = 128;
Integer b = 128;

System.out.println(a == b); // false일 수 있음
System.out.println(Objects.equals(a, b)); // true
```

## 실무 판단 기준

- 값이 반드시 있어야 하면 primitive type을 우선 고려한다.
- 값이 없을 수 있거나 DB `NULL`을 표현해야 하면 wrapper type을 사용한다.
- 객체 내용 비교는 `equals()`를 사용한다.
- wrapper type의 값 비교는 `Objects.equals()`를 사용한다.
- `equals()` 호출 대상이 `null`일 수 있으면 상수나 안전한 객체에서 호출한다.

```java
if ("ACTIVE".equals(status)) {
    // status가 null이어도 안전
}
```

## 핵심 요약

Java의 primitive type은 값 자체를 다루는 기본 타입이고, reference type은 객체를 참조하는 타입입니다.
primitive type은 `null`이 될 수 없고 `==`로 값을 비교합니다.

반면 reference type은 `null`이 될 수 있으며, `==`는 같은 객체인지 비교하고 `equals()`는 객체의 의미상 동등성을 비교할 때 사용합니다.

실무에서는 문자열이나 wrapper type을 `==`로 비교하거나, wrapper type의 `null`을 고려하지 않아 `NullPointerException`이 나는 경우가 많기 때문에 타입 선택과 비교 방식을 명확히 구분해야 합니다.

## 꼬리 질문

> [!question]- `int`와 `Integer`는 언제 각각 사용해야 하는가?
> 값이 반드시 있어야 하면 `int`, 값이 없을 수 있거나 DB NULL을 표현해야 하면 `Integer`를 사용합니다. 컬렉션의 제네릭 타입에는 `Integer`만 가능합니다.

> [!question]- `String` 비교에서 `==`가 아니라 `equals()`를 써야 하는 이유는 무엇인가?
> `==`는 같은 객체 참조인지 비교합니다. `new String("java")`처럼 생성하면 내용이 같아도 다른 객체이므로 `==`가 false를 반환합니다.

> [!question]- auto boxing과 auto unboxing은 어떤 문제를 만들 수 있는가?
> wrapper type이 null일 때 unboxing하면 `NullPointerException`이 발생합니다. 또한 반복문에서 불필요한 boxing이 반복되면 성능에 영향을 줄 수 있습니다.

> [!question]- Boolean과 boolean은 언제 구분해서 사용해야 하는가?
> 값이 반드시 true 또는 false라면 boolean을 사용합니다. 반면 true, false, 미정 처럼 세 가지 상태를 표현해야 하거나 DB NULL을 표현해야 한다면 Boolean을 사용합니다. 단, 조건문에서는 Boolean.TRUE.equals(value)처럼 비교하는 것이 안전합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

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
    <p class="quiz-question"><span class="quiz-label">객관식</span>Boolean wrapper를 사용할 때 면접에서 자주 지적되는 위험은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Boolean은 null이 될 수 있어 auto-unboxing 시 NullPointerException이 발생할 수 있다." aria-pressed="false">A. null 값이 auto-unboxing되면 NPE가 날 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Boolean 자체가 동시성 안전성을 제공하지는 않는다." aria-pressed="false">B. Boolean은 멀티스레드에서 항상 race condition을 만든다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="값이 두 개뿐이라는 점이 문제가 아니라 null 가능성이 핵심이다." aria-pressed="false">C. true/false만 표현할 수 있어서 상태 표현이 불가능하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
