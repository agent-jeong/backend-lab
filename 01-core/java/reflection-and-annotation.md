---
title: 리플렉션과 애노테이션 동작 원리
description: Spring, JPA, Jackson의 기반이 되는 Reflection과 Annotation의 실무 이해
tags: [concept, java]
---

# 리플렉션과 애노테이션 동작 원리

Reflection은 런타임에 클래스, 메서드, 필드 정보를 조회하거나 호출하는 기능이고, Annotation은 코드에 메타데이터를 붙여 프레임워크가 그걸 보고 동작하게 하는 문법이다. annotation은 스스로 아무것도 하지 않는다. 그것을 읽고 처리하는 코드가 있어야 동작한다.

Spring, JPA, Jackson의 자동화는 대부분 이 둘 위에 서 있다. 원리를 모르면 이런 것들이 설명되지 않는다. Spring이 `@Component`, `@Service`, `@Autowired`를 어떻게 찾아 Bean으로 등록하는지, JPA가 Entity 필드를 어떻게 읽고 프록시를 만드는지, Jackson이 왜 기본 생성자나 getter, record constructor를 요구하는지, annotation을 붙였는데 runtime retention이 아니라서 동작하지 않는 이유, reflection 코드가 왜 컴파일 타임 검사와 성능에서 불리한지.

## Annotation

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface TraceLog {
}
```

볼 설정은 `@Target`과 `@Retention` 두 가지다.

| 설정 | 의미 |
|---|---|
| `@Target` | annotation을 붙일 수 있는 위치 |
| `@Retention` | annotation 정보가 유지되는 시점 |
| `SOURCE` | 컴파일 후 사라짐 |
| `CLASS` | class 파일에는 있지만 런타임 reflection에서 일반적으로 읽지 않음 |
| `RUNTIME` | 런타임 reflection으로 읽을 수 있음 |

Spring처럼 런타임에 annotation을 읽어 동작하려면 보통 `RetentionPolicy.RUNTIME`이어야 한다.

## Reflection

런타임에 클래스 정보를 조회한다.

```java
Class<?> clazz = UserService.class;

for (Method method : clazz.getDeclaredMethods()) {
    if (method.isAnnotationPresent(TraceLog.class)) {
        System.out.println(method.getName());
    }
}
```

필드나 메서드의 접근 제한을 우회할 수도 있다.

```java
Field field = User.class.getDeclaredField("name");
field.setAccessible(true);
Object value = field.get(user);
```

캡슐화를 깨고 오류를 런타임으로 미루는 기능이라, 일반 비즈니스 코드에서는 직접 쓰지 않는다.

## 프레임워크는 어디에 쓰나

| 프레임워크 | 사용 예 |
|---|---|
| Spring | classpath scanning, Bean 등록, AOP proxy, dependency injection |
| JPA | Entity field 접근, 기본 생성자, proxy 생성 |
| Jackson | JSON field 매핑, constructor/property 탐색 |
| Validation | `@NotNull`, `@Size` 같은 제약 조건 탐색 |

Spring은 특정 annotation이 붙은 클래스를 찾아 BeanDefinition을 만들고, 런타임에 객체를 생성해 컨테이너에 등록한다.

JPA는 Entity를 프록시로 감싸거나 필드 값을 읽어 변경 감지를 한다. 그래서 Entity에는 기본 생성자, 상속 가능한 class 구조, 프레임워크가 접근할 수 있는 접근 제어가 필요하다.

## 언제 쓰나

| 상황 | 판단 |
|---|---|
| Spring/JPA/Jackson 동작 원리 설명 | Reflection + Annotation 기반으로 설명 |
| 반복적인 횡단 관심사 | Annotation + AOP 검토 |
| 일반 비즈니스 로직 | Reflection을 직접 쓰지 않는다 |
| 런타임 annotation 처리 | `RetentionPolicy.RUNTIME` 필요 |
| 성능 민감 경로 | reflection 호출 비용과 캐싱 검토 |

## 자주 깨지는 곳

- **custom annotation에 `@Retention(RUNTIME)`을 빠뜨린다.** 런타임에 읽히지 않아 아무 일도 일어나지 않는다.
- **reflection으로 private field를 직접 바꾼다.** 객체가 지키던 불변식이 깨진다.
- **annotation만 붙이면 동작한다고 생각한다.** 처리하는 코드나 프레임워크 설정이 빠져 있으면 그냥 메타데이터다.
- **reflection 예외를 런타임에서야 발견한다.** 이름 오타나 시그니처 변경을 컴파일러가 잡아 주지 않는다.
- **record, final class, private constructor가 프레임워크 요구사항과 부딪힌다.** 프록시 생성이나 역직렬화가 실패한다.

## 확인하는 방법

- 런타임에 필요한 annotation인지 `@Retention`을 본다.
- 프레임워크가 요구하는 생성자, 접근 제어자, final 여부를 본다.
- reflection을 쓰는 곳은 테스트로 런타임 오류를 미리 잡는다.
- 반복 호출되는 reflection metadata는 캐싱하는지 본다.

## 면접에서 말하기

> Reflection은 런타임에 클래스와 멤버 정보를 조회하거나 호출하는 기능이고, Annotation은 프레임워크가 읽을 메타데이터를 코드에 붙이는 방식입니다. Spring, JPA, Jackson은 annotation을 스캔하고 reflection으로 객체 생성, 필드 접근, 메서드 호출을 합니다. annotation 자체가 동작하는 게 아니라 그걸 읽는 코드가 있어야 하고, 런타임에 읽으려면 RetentionPolicy.RUNTIME이 필요합니다. reflection은 컴파일 타임 검사가 약하고 캡슐화와 성능 비용이 있어서 비즈니스 코드에서는 직접 쓰지 않습니다.

## 꼬리 질문

> [!question]- Reflection이란 무엇인가?
> 런타임에 클래스, 메서드, 필드 정보를 조회하고 필요하면 접근하거나 호출할 수 있게 해주는 기능입니다.

> [!question]- Annotation은 붙이기만 하면 동작하는가?
> 아닙니다. Annotation은 메타데이터일 뿐이고, 이를 읽고 처리하는 프레임워크나 코드가 있어야 동작합니다.

> [!question]- `RetentionPolicy.RUNTIME`은 왜 중요한가?
> 런타임에 reflection으로 annotation을 읽어야 하는 경우 annotation 정보가 런타임까지 유지되어야 하기 때문입니다.

> [!question]- Reflection의 단점은 무엇인가?
> 컴파일 타임 안정성이 낮고, 캡슐화를 깰 수 있으며, 일반 메서드 호출보다 비용이 크고 런타임 오류 가능성이 있습니다.

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

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Java SE 21 API: java.lang.reflect](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/package-summary.html)
- [JLS 21: Annotations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html#jls-9.6)

## 관련 문서

- [[java]]
- [[class-interface-enum-record]]
- [[serialization-and-jackson]]
- [[01-core/spring/ioc-and-di|ioc-and-di]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
