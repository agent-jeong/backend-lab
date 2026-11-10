---
title: 제네릭과 타입 소거
description: Java 제네릭과 타입 소거의 실무 사용 기준과 한계
tags: [concept, java]
---

# 제네릭과 타입 소거

Generics는 컴파일 타임에 타입을 검사해 주는 문법이고, type erasure는 런타임에 제네릭 타입 정보 대부분을 지우는 Java의 구현 방식이다. 컴파일러가 막아 주는 것과 런타임에 남는 것이 다르다는 점이 실무 문제의 출발점이다.

컬렉션, DTO, API 응답, Repository, JSON 역직렬화에서 제네릭은 계속 나온다. 잘못 이해하면 raw type 때문에 `ClassCastException`이 나고, `List<Object>`와 `List<?>`를 헷갈리고, Jackson이 `List<UserResponse>` 같은 타입을 제대로 복원하지 못한다.

## 상황별로 어떻게 쓰나

| 상황 | 권장 |
|---|---|
| 컬렉션 타입이 명확함 | `List<Order>`처럼 구체 타입 사용 |
| 타입을 모르는 목록을 읽기만 함 | `List<?>` 또는 `List<? extends T>` |
| 값을 추가해야 함 | 구체 타입 또는 `? super T` 검토 |
| JSON을 generic 타입으로 역직렬화 | `TypeReference<T>` 사용 |
| public API가 너무 복잡해짐 | wildcard보다 명확한 DTO/타입 설계 우선 |

## 기본 사용

제네릭을 쓰면 잘못된 타입이 컴파일 단계에서 막힌다.

```java
List<String> names = new ArrayList<>();
names.add("kim");

String first = names.get(0);
```

raw type은 타입 검사를 건너뛰므로 실무 코드에서 쓰지 않는다. 잘못된 타입이 들어가도 컴파일되고, 꺼낼 때 터진다.

```java
List raw = new ArrayList();
raw.add("kim");
raw.add(1);

String name = (String) raw.get(1); // ClassCastException
```

## Type Erasure

제네릭 타입 정보는 런타임에 대부분 사라진다.

```java
List<String> names = List.of("a");
List<Integer> numbers = List.of(1);

System.out.println(names.getClass() == numbers.getClass()); // true
```

그래서 아래 코드는 쓸 수 없다.

```java
if (value instanceof List<String>) { // 컴파일 불가
}
```

런타임에 제네릭 타입이 필요한 도구에는 타입 정보를 따로 넘긴다.

```java
List<UserResponse> users = objectMapper.readValue(
    json,
    new TypeReference<List<UserResponse>>() {}
);
```

Jackson, reflection 기반 라이브러리, 일부 프레임워크 코드가 이 한계를 자주 만난다.

## `List<Object>`와 `List<?>`

`List<Object>`는 모든 List를 받는 타입이 아니다. Object를 담는 List만 받는다.

```java
void addAny(List<Object> values) {
    values.add("a");
    values.add(1);
}
```

`List<?>`는 어떤 타입의 List든 받지만, 원소 타입을 모르니 값을 안전하게 넣기 어렵다.

```java
void printAll(List<?> values) {
    for (Object value : values) {
        System.out.println(value);
    }
}
```

읽기만 하면 `List<?>`, 넣어야 하면 더 구체적인 타입을 쓴다.

## PECS

Wildcard는 PECS(Producer Extends, Consumer Super)로 고른다.

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

wildcard가 많아지면 API를 읽기 어려워진다. 실무에서는 복잡한 wildcard보다 명확한 DTO나 타입 파라미터가 나은 경우가 많다.

## 자주 깨지는 곳

- **raw type을 쓴다.** 타입 검사가 꺼져 `ClassCastException`이 꺼내는 쪽에서 난다.
- **`List<String>`과 `List<Integer>`가 런타임에도 다른 타입이라고 생각한다.** 런타임에는 둘 다 그냥 `List`다.
- **`List<Object>`가 모든 List를 받는다고 오해한다.** `List<String>`을 넘기면 컴파일 에러다.
- **JSON 역직렬화에서 `TypeReference`를 빠뜨린다.** 원소가 DTO가 아니라 Map으로 들어온다.
- **wildcard를 남발한다.** 어디서 읽고 어디에 쓸 수 있는지가 흐려진다.

## 면접에서 말하기

> 제네릭은 컴파일 타임에 타입을 검사해 주지만, 런타임에는 type erasure 때문에 타입 파라미터 대부분이 사라집니다. 그래서 raw type은 쓰지 않고 컬렉션은 되도록 구체 타입으로 선언합니다. 타입을 모르는 값을 읽기만 할 때는 `List<?>`, 런타임에 제네릭 타입이 필요한 JSON 역직렬화에는 `TypeReference`를 씁니다. wildcard는 PECS로 고르되, public API가 복잡해지면 타입 설계를 먼저 다시 봅니다.

## 꼬리 질문

> [!question]- Java의 type erasure란 무엇인가?
> 컴파일 후 런타임에는 대부분의 제네릭 타입 파라미터 정보가 제거되는 방식입니다. 그래서 `List<String>`과 `List<Integer>`를 런타임에 직접 구분하기 어렵습니다.

> [!question]- raw type이 위험한 이유는?
> 컴파일 타임 타입 검사를 우회해서 잘못된 타입이 들어가도 컴파일되고, 나중에 꺼낼 때 `ClassCastException`이 발생할 수 있습니다.

> [!question]- `List<Object>`와 `List<?>`의 차이는?
> `List<Object>`는 Object를 담는 List이고, `List<?>`는 어떤 타입의 List든 받을 수 있지만 값을 안전하게 추가하기 어렵습니다.

> [!question]- PECS는 무엇인가?
> Producer는 `extends`, Consumer는 `super`를 사용한다는 기준입니다. 읽기만 하면 `? extends T`, 넣어야 하면 `? super T`를 고려합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Java의 type erasure가 의미하는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="제네릭 타입 정보는 주로 컴파일 타임 검증에 쓰이고 런타임에는 원시 타입에 가깝게 동작한다." aria-pressed="false">A. 제네릭 타입 정보가 런타임에 대부분 제거된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="제네릭은 런타임 객체를 자동으로 복제하지 않는다." aria-pressed="false">B. 제네릭 컬렉션은 타입마다 별도 클래스로 생성된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="성능 최적화가 목적이라기보다 하위 호환성과 타입 검증 모델의 결과다." aria-pressed="false">C. 모든 캐스팅 비용을 완전히 제거한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>List&lt;Object&gt;는 List&lt;String&gt;을 받을 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="List&lt;Object&gt;에 Integer를 추가할 수 있으므로 List&lt;String&gt;을 대입하면 타입 안전성이 깨진다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="제네릭은 불공변이다. 읽기 중심의 알 수 없는 타입은 List&lt;?&gt;를 사용한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>PECS에서 값을 꺼내 읽는 생산자 컬렉션에 적합한 선언은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Producer Extends 원칙에 따라 읽기 중심이면 ? extends T가 적합하다." aria-pressed="false">A. ? extends T</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="? super T는 값을 넣는 소비자에 적합하다." aria-pressed="false">B. ? super T</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="raw type은 타입 검사를 약화시켜 ClassCastException 위험을 뒤로 미룬다." aria-pressed="false">C. raw type</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [JLS 21: Type Erasure](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.6)

## 관련 문서

- [[java]]
- [[collection-selection]]
- [[serialization-and-jackson]]
- [[reflection-and-annotation]]
