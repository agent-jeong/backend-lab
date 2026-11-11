---
title: 리플렉션과 애노테이션 동작 원리
description: Spring, JPA, Jackson이 안에서 쓰는 Reflection과 Annotation이 어떻게 동작하고 언제 막히는지
tags: [concept, java]
---

# 리플렉션과 애노테이션 동작 원리

Reflection은 프로그램이 실행되는 중에 클래스의 메서드와 필드 목록을 읽고, 필요하면 그 메서드를 호출하거나 필드 값을 바꾸는 기능이다. Annotation은 코드에 표시를 붙여 두고, 프레임워크가 그 표시를 보고 동작하게 하는 문법이다. annotation은 혼자서는 아무것도 하지 않는다. 그 표시를 읽고 처리하는 코드가 있어야 동작한다.

Spring, JPA, Jackson이 알아서 해 주는 일은 대부분 이 둘로 돌아간다. 원리를 알면 이런 질문에 답할 수 있다.

- Spring은 `@Component`, `@Service`, `@Autowired`를 어떻게 찾아 Bean으로 등록하나?
- JPA는 Entity 필드를 어떻게 읽고 프록시를 만드나?
- Jackson은 왜 기본 생성자나 getter, record 생성자를 요구하나?
- annotation을 붙였는데 아무 일도 안 일어나는 건 왜인가? (retention이 RUNTIME이 아닐 때)
- reflection 코드는 왜 컴파일러가 검사해 주지 못하고 느린가?

## Annotation

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface TraceLog {
}
```

정해야 할 설정은 `@Target`과 `@Retention` 두 가지다.

| 설정 | 의미 |
|---|---|
| `@Target` | annotation을 붙일 수 있는 위치 |
| `@Retention` | annotation 정보를 언제까지 남길지. 아래 세 값 중 하나 |
| └ `SOURCE` | 컴파일하면 사라진다(`@Override` 등) |
| └ `CLASS` | class 파일에는 남지만 실행 중 reflection으로는 읽지 못한다. 지정하지 않으면 이 값이다 |
| └ `RUNTIME` | 실행 중 reflection으로 읽을 수 있다 |

Spring처럼 실행 중에 annotation을 읽어서 동작하게 하려면 보통 `RetentionPolicy.RUNTIME`이어야 한다.

## Reflection

실행 중에 클래스 정보를 읽는다. 아래는 `@TraceLog`가 붙은 메서드를 찾는 코드다.

```java
Class<?> clazz = UserService.class;

for (Method method : clazz.getDeclaredMethods()) {
    if (method.isAnnotationPresent(TraceLog.class)) {
        System.out.println(method.getName());
    }
}
```

private 필드나 메서드에 접근 제한을 무시하고 들어갈 수도 있다.

```java
Field field = User.class.getDeclaredField("name");
field.setAccessible(true);
Object value = field.get(user);
```

객체가 숨겨 둔 필드를 건드리고, 이름이 틀려도 실행해 봐야 알 수 있는 기능이다. 그래서 일반 비즈니스 코드에서는 직접 쓰지 않는다.

## 프레임워크는 어디에 쓰나

| 프레임워크 | 사용 예 |
|---|---|
| Spring | classpath scanning, Bean 등록, AOP proxy, dependency injection |
| JPA | Entity field 접근, 기본 생성자, proxy 생성 |
| Jackson | JSON field 매핑, constructor/property 탐색 |
| Validation | `@NotNull`, `@Size` 같은 제약 조건 탐색 |

Spring은 정해진 annotation이 붙은 클래스를 찾아 BeanDefinition을 만들고, 실행 중에 객체를 생성해 컨테이너에 등록한다.

JPA는 Entity를 프록시로 감싸거나, 필드 값을 읽어서 무엇이 바뀌었는지 확인한다. 그래서 Entity에는 기본 생성자가 있어야 하고, 상속할 수 있는 class여야 하고, 프레임워크가 접근할 수 있는 접근 제어자를 써야 한다.

## 언제 쓰나

| 상황 | 판단 |
|---|---|
| Spring/JPA/Jackson 동작 원리 설명 | Reflection + Annotation 기반으로 설명 |
| 반복적인 횡단 관심사 | Annotation + AOP 검토 |
| 일반 비즈니스 로직 | Reflection을 직접 쓰지 않는다 |
| 런타임 annotation 처리 | `RetentionPolicy.RUNTIME` 필요 |
| 성능 민감 경로 | reflection 호출 비용과 캐싱 검토 |

## 자주 깨지는 곳

- 직접 만든 annotation에 `@Retention(RUNTIME)`을 빠뜨리면, 실행 중에 읽히지 않아서 아무 일도 일어나지 않는다.
- reflection으로 private 필드를 직접 바꾸면, 객체가 지키던 규칙이 깨진다. 예를 들어 음수가 될 수 없던 재고 수량이 음수가 된다.
- annotation만 붙이면 동작한다고 생각하면 틀린다. 처리하는 코드나 프레임워크 설정이 없으면 그냥 표시일 뿐이다.
- reflection으로 이름을 문자열로 넘기면, 오타나 메서드 시그니처 변경을 컴파일러가 못 잡아서 실행 중에야 예외가 난다.
- final class나 record를 JPA Entity로 쓰면, 상속할 수 없어서 프록시를 만들지 못한다. Jackson은 record는 지원하지만, 기본 생성자도 `@JsonCreator`도 없고 `-parameters`로 컴파일해 파라미터 이름을 남기지도 않은 class는 역직렬화하지 못한다.

## 코드 리뷰에서 볼 것

- 실행 중에 읽어야 하는 annotation이라면 `@Retention`이 RUNTIME인지 본다.
- 프레임워크가 요구하는 생성자, 접근 제어자, final 여부를 본다.
- reflection을 쓰는 곳은 테스트를 돌려서 실행 중 오류를 미리 잡는다.
- 자주 호출되는 곳에서 reflection으로 읽은 정보를 매번 다시 읽지 않고 캐시해 두는지 본다.

## 한 번에 설명하기

> Reflection은 실행 중에 클래스의 메서드와 필드 정보를 읽거나 호출하는 기능이고, Annotation은 프레임워크가 읽을 표시를 코드에 붙이는 방식입니다. Spring, JPA, Jackson은 annotation을 찾아 읽은 뒤 reflection으로 객체를 만들고, 필드에 접근하고, 메서드를 호출합니다.
>
> annotation이 스스로 동작하는 게 아니라 그걸 읽는 코드가 있어야 하고, 실행 중에 읽으려면 RetentionPolicy.RUNTIME이어야 합니다.
>
> reflection은 컴파일러가 검사해 주지 못하고, 객체가 숨긴 필드를 건드리고, 일반 호출보다 느립니다. 그래서 비즈니스 코드에서는 직접 쓰지 않습니다.

## 꼬리 질문

> [!question]- Reflection이 뭔가?
> 실행 중에 클래스, 메서드, 필드 정보를 읽고, 필요하면 필드에 접근하거나 메서드를 호출할 수 있게 해 주는 기능입니다.

> [!question]- Annotation은 붙이기만 하면 동작하나?
> 아닙니다. Annotation은 표시일 뿐이고, 그걸 읽고 처리하는 프레임워크나 코드가 있어야 뭔가 일어납니다.

> [!question]- `RetentionPolicy.RUNTIME`은 왜 필요한가?
> 실행 중에 reflection으로 annotation을 읽으려면, annotation 정보가 실행 시점까지 남아 있어야 하기 때문입니다.

> [!question]- Reflection의 단점은?
> 컴파일러가 검사해 주지 못해서 실행해 봐야 오류를 압니다. 객체가 숨겨 둔 필드를 건드릴 수 있고, 일반 메서드 호출보다 비용도 큽니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Annotation을 붙였는데 런타임 프레임워크가 읽지 못하는 대표적인 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="RetentionPolicy가 RUNTIME이 아니면 런타임 리플렉션으로 조회할 수 없다." aria-pressed="false">A. RetentionPolicy가 RUNTIME이 아닐 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="애노테이션은 클래스에만 붙는 것이 아니다. Target 설정에 따라 다르다." aria-pressed="false">B. 애노테이션은 메서드에 붙일 수 없기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="패키지명이 길다고 런타임 조회가 불가능해지는 것은 아니다." aria-pressed="false">C. 패키지 이름이 너무 길기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Annotation은 붙이는 것만으로 동작하고, 이를 읽고 처리하는 코드가 없어도 기능이 실행된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="애노테이션은 메타데이터이며, 리플렉션/컴파일러/APT/프레임워크 같은 처리 주체가 있어야 의미가 생긴다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="붙이는 것과 동작시키는 것은 다르다. 처리 로직이 필요하다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Reflection을 쓸 때 실무에서 주의할 점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="컴파일 타임 안전성이 약해지고 성능/접근 제어/리팩터링 추적 문제가 생길 수 있다." aria-pressed="false">A. 타입 안전성과 성능, 리팩터링 안정성을 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Reflection이 항상 직접 호출보다 빠른 것은 아니다." aria-pressed="false">B. 직접 메서드 호출보다 항상 빠르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Reflection은 private 멤버 접근도 가능하게 만들 수 있어 오히려 캡슐화 주의가 필요하다." aria-pressed="false">C. 접근 제어와 전혀 관련이 없다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: java.lang.reflect](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/package-summary.html)
- [JLS 21: Annotations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html#jls-9.6)

## 관련 문서

- [[01-core/java/java|java]]
- [[class-interface-enum-record]]
- [[serialization-and-jackson]]
- [[01-core/spring/ioc-and-di|ioc-and-di]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
