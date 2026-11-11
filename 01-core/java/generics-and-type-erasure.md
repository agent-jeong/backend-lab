---
title: 제네릭과 타입 소거
description: 제네릭이 컴파일할 때 막아 주는 것과, 실행할 때 타입 정보가 지워져서 생기는 문제
tags: [concept, java]
---

# 제네릭과 타입 소거

제네릭(generics)은 컴파일할 때 타입을 검사해 주는 문법이다. 그런데 Java는 컴파일이 끝나면 제네릭 타입 정보 대부분을 지운다. 이걸 타입 소거(type erasure)라고 한다. 실무에서 겪는 문제는 대부분 컴파일러가 막아 주는 것과 실행 중에 남아 있는 것이 서로 다르다는 데서 나온다.

컬렉션, DTO, API 응답, Repository, JSON 역직렬화 어디에나 제네릭이 나온다. 잘못 알면 raw type 때문에 `ClassCastException`이 나고, `List<Object>`와 `List<?>`를 헷갈리고, Jackson이 `List<UserResponse>`를 DTO 목록이 아니라 Map 목록으로 읽어 온다.

## 상황별로 어떻게 쓰나

| 상황 | 권장 |
|---|---|
| 컬렉션 타입이 명확함 | `List<Order>`처럼 구체 타입 사용 |
| 타입을 모르는 목록을 읽기만 함 | `List<?>` 또는 `List<? extends T>` |
| 값을 추가해야 함 | 구체 타입 또는 `? super T` 검토 |
| JSON을 generic 타입으로 역직렬화 | `TypeReference<T>` 사용 |
| public API가 너무 복잡해짐 | wildcard보다 명확한 DTO/타입 설계 우선 |

## 기본 사용

제네릭을 쓰면 다른 타입을 넣으려는 순간 컴파일 에러가 난다.

```java
List<String> names = new ArrayList<>();
names.add("kim");

String first = names.get(0);
```

raw type은 타입 검사를 건너뛰니 실무 코드에서는 쓰지 않는다. 다른 타입이 들어가도 컴파일되고, 꺼낼 때 터진다.

```java
List raw = new ArrayList();
raw.add("kim");
raw.add(1);

String name = (String) raw.get(1); // ClassCastException
```

## Type Erasure

제네릭 타입 정보는 실행할 때 대부분 사라진다.

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

실행 중에 제네릭 타입을 알아야 하는 도구에는 타입 정보를 따로 넘겨 준다.

```java
List<UserResponse> users = objectMapper.readValue(
    json,
    new TypeReference<List<UserResponse>>() {}
);
```

Jackson, reflection을 쓰는 라이브러리, 일부 프레임워크 코드가 이 한계에 자주 부딪힌다.

## `List<Object>`와 `List<?>`

`List<Object>`는 아무 List나 받는 타입이 아니다. Object를 담는 List만 받는다.

```java
void addAny(List<Object> values) {
    values.add("a");
    values.add(1);
}
```

`List<?>`는 어떤 타입의 List든 받지만, 원소 타입을 모르니 값을 안전하게 넣을 수 없다.

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

wildcard가 많아지면 메서드 시그니처를 읽기 어려워진다. 실무에서는 복잡한 wildcard보다 DTO나 타입 파라미터를 분명하게 정하는 편이 나은 경우가 많다.

## 자주 깨지는 곳

- raw type을 쓰면, 타입 검사가 꺼져서 `ClassCastException`이 꺼내는 쪽에서 난다.
- `List<String>`과 `List<Integer>`가 실행 중에도 다른 타입이라고 생각하면 틀린다. 실행 중에는 둘 다 그냥 `List`다.
- `List<Object>`가 아무 List나 받는다고 생각하고 `List<String>`을 넘기면, 컴파일 에러가 난다.
- JSON 역직렬화에서 `TypeReference`를 빠뜨리면, 원소가 DTO가 아니라 Map으로 들어온다.
- wildcard를 여기저기 쓰면, 어디서 읽고 어디에 넣을 수 있는지 알아보기 어려워진다.

## 한 번에 설명하기

> 제네릭은 컴파일할 때 타입을 검사해 주지만, 실행할 때는 type erasure 때문에 타입 파라미터 대부분이 사라집니다. 그래서 raw type은 쓰지 않고, 컬렉션은 되도록 구체 타입으로 선언합니다.
>
> 타입을 모르는 값을 읽기만 할 때는 `List<?>`를 쓰고, 실행 중에 제네릭 타입을 알아야 하는 JSON 역직렬화에는 `TypeReference`를 넘깁니다.
>
> wildcard는 PECS로 고르지만, public API가 복잡해지면 wildcard를 더 붙이기보다 타입 설계부터 다시 봅니다.

## 꼬리 질문

> [!question]- Java의 type erasure가 뭔가?
> 컴파일이 끝나면 제네릭 타입 파라미터 정보 대부분이 지워지는 방식입니다. 그래서 실행 중에는 `List<String>`과 `List<Integer>`를 직접 구분하기 어렵습니다.

> [!question]- raw type은 왜 위험한가?
> 컴파일할 때 타입 검사를 건너뛰어서, 다른 타입이 들어가도 컴파일이 됩니다. 그러다 나중에 꺼낼 때 `ClassCastException`이 날 수 있습니다.

> [!question]- `List<Object>`와 `List<?>`는 뭐가 다른가?
> `List<Object>`는 Object를 담는 List 하나만 받습니다. `List<?>`는 어떤 타입의 List든 받지만, 대신 값을 안전하게 넣기 어렵습니다.

> [!question]- PECS가 뭔가?
> 값을 꺼내 주는 쪽(Producer)은 `extends`, 값을 받는 쪽(Consumer)은 `super`를 쓴다는 기준입니다. 읽기만 하면 `? extends T`, 넣어야 하면 `? super T`를 검토합니다.

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

2026년 11월에 확인한 공식 문서다.

- [JLS 21: Type Erasure](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.6)

## 관련 문서

- [[01-core/java/java|java]]
- [[collection-selection]]
- [[serialization-and-jackson]]
- [[reflection-and-annotation]]
