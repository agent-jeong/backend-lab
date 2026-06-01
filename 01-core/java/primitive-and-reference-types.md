---
title: Primitive And Reference Types
description: Java primitive type과 reference type의 차이와 실무 주의점
---

# Primitive And Reference Types

## 한 줄 정의

Java의 primitive type은 값 자체를 다루는 기본 타입이고, reference type은 객체가 있는 위치를 참조하는 타입이다.

## 실무에서 왜 중요한가

두 타입의 차이를 모르면 `==`, `equals()`, `null`, wrapper type, 컬렉션 사용에서 버그가 자주 생긴다.

## 핵심 개념

- primitive type은 `int`, `long`, `boolean`, `double` 같은 기본 타입이다.
- reference type은 `String`, 배열, 클래스, 인터페이스, enum 같은 객체 타입이다.
- primitive 변수는 실제 값을 가진다.
- reference 변수는 객체 자체가 아니라 객체를 가리키는 참조값을 가진다.
- primitive type은 `null`이 될 수 없다.
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

```java
Integer count = null;

if (count == 0) {
    // NullPointerException 발생 가능
}
```

wrapper type은 자동 unboxing 과정에서 `NullPointerException`이 발생할 수 있다.

## 실무에서 자주 나는 문제

- `String` 값을 `==`로 비교한다.
- `Long`, `Integer` 값을 `==`로 비교한다.
- wrapper type이 `null`일 수 있는데 primitive처럼 사용한다.
- DTO, Entity 필드에서 `int`와 `Integer`의 의미 차이를 고려하지 않는다.

## 실무 판단 기준

- 값이 반드시 있어야 하면 primitive type을 우선 고려한다.
- 값이 없을 수 있거나 DB `NULL`을 표현해야 하면 wrapper type을 사용한다.
- 객체 내용 비교는 `equals()`를 사용한다.
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

## 관련 문서

- [[01-core/java/java|java]]
