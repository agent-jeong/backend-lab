---
title: Generics And Type Erasure
description: Java 제네릭과 타입 소거의 실무 사용 기준과 한계
---

# Generics And Type Erasure

## 한 줄 정의

Generics는 컴파일 타임에 타입 안정성을 제공하는 문법이고, type erasure는 런타임에는 대부분의 제네릭 타입 정보가 제거되는 Java의 구현 방식이다.

## 실무에서 왜 중요한가

제네릭은 컬렉션과 API 설계에서 거의 항상 사용된다. 하지만 타입 소거를 모르면 다음 문제가 생긴다.

- raw type을 사용해서 런타임 `ClassCastException`이 발생한다.
- `List<String>`과 `List<Integer>`를 런타임에 구분할 수 있다고 오해한다.
- `List<Object>`와 `List<?>`의 차이를 몰라 API 파라미터를 잘못 설계한다.
- Jackson, JPA, Reflection에서 제네릭 타입 정보가 필요한 상황을 이해하지 못한다.
- wildcard를 남용해서 읽기와 쓰기 가능 여부가 불분명해진다.

## 기본 사용

제네릭을 사용하면 컴파일러가 타입 오류를 미리 잡는다.

```java
List<String> names = new ArrayList<>();
names.add("kim");

String first = names.get(0);
```

raw type을 사용하면 컴파일 타임 검사가 약해지고 런타임 오류가 생길 수 있다.

```java
List raw = new ArrayList();
raw.add("kim");
raw.add(1);

String name = (String) raw.get(1); // ClassCastException
```

실무 코드에서는 특별한 이유가 없으면 raw type을 사용하지 않는다.

## 타입 소거

Java 제네릭은 런타임에 타입 파라미터가 대부분 제거된다.

```java
List<String> names = List.of("a");
List<Integer> numbers = List.of(1);

System.out.println(names.getClass() == numbers.getClass()); // true
```

컴파일 후에는 둘 다 런타임에서 주로 `List`로 취급된다. 그래서 다음 코드는 사용할 수 없다.

```java
// 불가능
if (value instanceof List<String>) {
}
```

타입 소거 때문에 런타임에 제네릭 타입이 필요하면 `Class<T>`, `TypeReference<T>` 같은 보조 정보가 필요하다.

```java
List<UserResponse> users = objectMapper.readValue(
    json,
    new TypeReference<List<UserResponse>>() {}
);
```

## Wildcard 판단 기준

`List<Object>`와 `List<?>`는 다르다.

```java
void printAll(List<?> values) {
    for (Object value : values) {
        System.out.println(value);
    }
}
```

`List<?>`는 어떤 타입의 List든 받을 수 있지만, 타입을 알 수 없으므로 null 외에는 안전하게 추가할 수 없다.

```java
void addAny(List<Object> values) {
    values.add("a");
    values.add(1);
}
```

`List<Object>`는 Object를 담는 List만 받을 수 있다. `List<String>`은 `List<Object>`의 하위 타입이 아니다.

## PECS

Wildcard를 사용할 때는 PECS를 기준으로 판단한다.

| 상황 | 사용 | 의미 |
|---|---|---|
| 값을 읽기만 한다 | `? extends T` | Producer Extends |
| 값을 넣어야 한다 | `? super T` | Consumer Super |
| 읽고 쓰는 타입이 명확하다 | `T` | 구체 타입 유지 |

```java
void copy(List<? extends Number> source, List<? super Number> target) {
    for (Number number : source) {
        target.add(number);
    }
}
```

실무에서는 API가 복잡해지면 wildcard를 줄이고 명확한 DTO나 타입 파라미터를 사용하는 편이 낫다.

## 자주 나는 실수

- raw type을 사용한다.
- `List<String>`과 `List<Integer>`가 런타임에도 다른 타입이라고 생각한다.
- `List<Object>`가 모든 List를 받을 수 있다고 오해한다.
- wildcard를 과하게 사용해서 호출부가 이해하기 어려워진다.
- JSON 역직렬화에서 `List<User>` 타입 정보를 넘기지 않는다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| 컬렉션 타입이 명확하다 | `List<Order>`처럼 구체 타입 사용 |
| 읽기 전용 파라미터 | `List<? extends T>` 검토 |
| 값을 추가해야 하는 파라미터 | `List<? super T>` 검토 |
| JSON 역직렬화 | `TypeReference<T>` 사용 |
| 복잡한 public API | wildcard보다 명확한 타입 설계 우선 |

## 확인 방법

- IDE warning에서 raw type 사용을 확인한다.
- `ClassCastException`이 발생한 지점보다 컬렉션에 값이 들어간 지점을 확인한다.
- Jackson 역직렬화에서 nested generic 타입이 제대로 전달되는지 확인한다.
- API 파라미터가 읽기 전용인지 쓰기 가능한지 확인한다.

## 핵심 요약

Java Generics는 컴파일 타임 타입 안정성을 제공하지만 런타임에는 타입 소거가 적용됩니다.

그래서 `List<String>`과 `List<Integer>`는 런타임에 같은 `List` 클래스로 취급되고, `instanceof List<String>` 같은 검사는 할 수 없습니다.

raw type을 사용하면 컴파일러의 타입 검사를 우회해서 런타임 `ClassCastException`을 만들 수 있습니다.

`List<Object>`는 모든 List를 받는 타입이 아니며, 알 수 없는 타입의 List를 받으려면 `List<?>`를 사용해야 합니다.

Jackson처럼 런타임 타입 정보가 필요한 도구에서는 `TypeReference` 같은 방식으로 제네릭 타입 정보를 명시해야 합니다.

## 꼬리 질문

> [!question]- Java의 type erasure란 무엇인가?
> 컴파일 후 런타임에는 대부분의 제네릭 타입 파라미터 정보가 제거되는 방식입니다. 그래서 `List<String>`과 `List<Integer>`를 런타임에 직접 구분하기 어렵습니다.

> [!question]- `List<Object>`와 `List<?>`의 차이는 무엇인가?
> `List<Object>`는 Object를 담는 List만 받을 수 있고, `List<?>`는 어떤 타입의 List든 받을 수 있지만 값을 안전하게 추가하기 어렵습니다.

> [!question]- raw type을 쓰면 왜 위험한가?
> 컴파일 타임 타입 검사를 우회하기 때문에 잘못된 타입이 들어가도 컴파일이 되고, 나중에 꺼낼 때 `ClassCastException`이 발생할 수 있습니다.

> [!question]- PECS는 무엇인가?
> Producer는 `extends`, Consumer는 `super`를 사용한다는 wildcard 설계 기준입니다. 값을 읽기만 하면 `? extends T`, 값을 넣어야 하면 `? super T`를 고려합니다.

## 관련 문서

- [[java]]
- [[collection-selection]]
- [[serialization-and-jackson]]
- [[reflection-and-annotation]]
