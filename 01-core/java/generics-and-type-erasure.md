---
title: Generics And Type Erasure
description: Java 제네릭과 타입 소거의 실무 사용 기준과 한계
---

# Generics And Type Erasure

## 한 줄 정의

Generics는 컴파일 타임에 타입 안정성을 제공하는 문법이고, type erasure는 런타임에 대부분의 제네릭 타입 정보가 제거되는 Java의 구현 방식이다.

## 실무에서 왜 중요한가

백엔드에서는 컬렉션, DTO, API 응답, Repository, JSON 역직렬화에서 제네릭을 계속 사용한다.

제네릭을 잘못 이해하면 raw type 때문에 `ClassCastException`이 발생하고, `List<Object>`와 `List<?>`를 혼동하며, Jackson에서 `List<UserResponse>` 같은 타입을 제대로 복원하지 못한다.

## 한눈에 보는 판단 기준

| 상황 | 권장 |
|---|---|
| 컬렉션 타입이 명확함 | `List<Order>`처럼 구체 타입 사용 |
| 타입을 모르는 목록을 읽기만 함 | `List<?>` 또는 `List<? extends T>` |
| 값을 추가해야 함 | 구체 타입 또는 `? super T` 검토 |
| JSON을 generic 타입으로 역직렬화 | `TypeReference<T>` 사용 |
| public API가 너무 복잡해짐 | wildcard보다 명확한 DTO/타입 설계 우선 |

## 기본 사용

제네릭을 쓰면 잘못된 타입을 컴파일 단계에서 막을 수 있다.

```java
List<String> names = new ArrayList<>();
names.add("kim");

String first = names.get(0);
```

raw type은 타입 검사를 우회하므로 실무 코드에서 피한다.

```java
List raw = new ArrayList();
raw.add("kim");
raw.add(1);

String name = (String) raw.get(1); // ClassCastException
```

## Type Erasure

Java 제네릭 타입 정보는 런타임에 대부분 사라진다.

```java
List<String> names = List.of("a");
List<Integer> numbers = List.of(1);

System.out.println(names.getClass() == numbers.getClass()); // true
```

그래서 아래 코드는 사용할 수 없다.

```java
if (value instanceof List<String>) { // 컴파일 불가
}
```

런타임에 제네릭 타입 정보가 필요한 도구에는 별도 타입 정보를 넘겨야 한다.

```java
List<UserResponse> users = objectMapper.readValue(
    json,
    new TypeReference<List<UserResponse>>() {}
);
```

Jackson, reflection 기반 라이브러리, 일부 프레임워크 코드는 이 한계를 자주 만난다.

## `List<Object>` vs `List<?>`

`List<Object>`는 모든 List를 받는 타입이 아니다. Object를 담는 List만 받는다.

```java
void addAny(List<Object> values) {
    values.add("a");
    values.add(1);
}
```

`List<?>`는 어떤 타입의 List든 받을 수 있지만, 타입을 모르기 때문에 값을 안전하게 추가하기 어렵다.

```java
void printAll(List<?> values) {
    for (Object value : values) {
        System.out.println(value);
    }
}
```

읽기만 하면 `List<?>`가 유용하고, 넣어야 하면 더 구체적인 타입이 필요하다.

## PECS

Wildcard를 사용할 때는 PECS를 기억한다.

| 상황 | 사용 |
|---|---|
| 값을 꺼내 읽는 producer | `? extends T` |
| 값을 넣는 consumer | `? super T` |
| 읽기와 쓰기 모두 타입이 명확함 | `T` |

```java
void copy(List<? extends Number> source, List<? super Number> target) {
    for (Number number : source) {
        target.add(number);
    }
}
```

다만 wildcard가 많아지면 API가 읽기 어려워진다. 실무에서는 복잡한 wildcard보다 명확한 DTO나 타입 파라미터가 더 나은 경우가 많다.

## 자주 나는 실수

- raw type을 사용한다.
- `List<String>`과 `List<Integer>`가 런타임에도 다른 타입이라고 생각한다.
- `List<Object>`가 모든 List를 받을 수 있다고 오해한다.
- JSON 역직렬화에서 `TypeReference`를 빠뜨린다.
- wildcard를 남용해서 읽기와 쓰기 가능 여부가 불분명해진다.

## 핵심 요약

Generics는 컴파일 타임 타입 안정성을 높이지만, 런타임에는 type erasure 때문에 대부분의 타입 파라미터가 사라진다.

raw type은 피하고, 컬렉션은 가능한 구체 타입으로 선언한다. 타입을 모르는 값을 읽기만 한다면 `List<?>`, 런타임 generic 타입 정보가 필요하면 `TypeReference` 같은 보조 정보를 사용한다.

Wildcard는 PECS 기준으로 판단하되, public API가 복잡해지면 더 명확한 타입 설계를 우선한다.

## 꼬리 질문

> [!question]- Java의 type erasure란 무엇인가?
> 컴파일 후 런타임에는 대부분의 제네릭 타입 파라미터 정보가 제거되는 방식입니다. 그래서 `List<String>`과 `List<Integer>`를 런타임에 직접 구분하기 어렵습니다.

> [!question]- raw type이 위험한 이유는?
> 컴파일 타임 타입 검사를 우회해서 잘못된 타입이 들어가도 컴파일되고, 나중에 꺼낼 때 `ClassCastException`이 발생할 수 있습니다.

> [!question]- `List<Object>`와 `List<?>`의 차이는?
> `List<Object>`는 Object를 담는 List이고, `List<?>`는 어떤 타입의 List든 받을 수 있지만 값을 안전하게 추가하기 어렵습니다.

> [!question]- PECS는 무엇인가?
> Producer는 `extends`, Consumer는 `super`를 사용한다는 기준입니다. 읽기만 하면 `? extends T`, 넣어야 하면 `? super T`를 고려합니다.

## 관련 문서

- [[java]]
- [[collection-selection]]
- [[serialization-and-jackson]]
- [[reflection-and-annotation]]
