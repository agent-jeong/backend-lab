---
title: Kotlin과 Java 함께 쓰기
description: Kotlin과 Java를 함께 사용할 때 nullability, annotation, 예외, 빌드 경계에서 주의할 점
---

# Kotlin과 Java 함께 쓰기

Kotlin과 Java는 같은 JVM에서 서로를 호출한다. 문제는 그 경계에서 Kotlin의 안전장치가 약해진다는 점이다.

Kotlin 백엔드는 거의 항상 Java 라이브러리, Spring, JPA, Jackson과 같이 돈다. 그래서 Java가 돌려준 null을 Kotlin이 non-null로 믿거나, Java 쪽에서 Kotlin default parameter를 못 쓰거나, checked exception이 강제되지 않아 실패 처리를 놓치는 일이 생긴다. Kotlin class가 기본 final이라 Spring/JPA proxy와 부딪히는 것도 이 경계 문제다.

## Platform Type

Kotlin이 nullability를 확정할 수 없는 Java 타입은 platform type으로 보인다.

```java
public User findUser(Long id) {
    return null;
}
```

Kotlin에서는 `User!`로 취급되어 nullable로도, non-null로도 쓸 수 있다. 컴파일러가 막아 주지 않는다는 뜻이다.

```kotlin
val user = javaUserRepository.findUser(id)
println(user.name) // 런타임 NPE 가능
```

Java API 경계에서는 null을 명시적으로 막는다.

```kotlin
val user = javaUserRepository.findUser(id)
    ?: throw UserNotFoundException(id)
```

## Java에서 Kotlin 호출

Kotlin의 default parameter는 Java에서는 보이지 않는다. Java 쪽은 모든 인자를 넘겨야 한다.

```kotlin
class MailSender {
    fun send(to: String, retry: Int = 3) {
    }
}
```

Java에서도 편하게 불러야 하면 `@JvmOverloads`로 overload를 만든다.

```kotlin
class MailSender {
    @JvmOverloads
    fun send(to: String, retry: Int = 3) {
    }
}
```

companion object 함수를 Java static처럼 노출하려면 `@JvmStatic`을 붙인다.

```kotlin
class TokenUtils {
    companion object {
        @JvmStatic
        fun parse(token: String): Long = token.toLong()
    }
}
```

## Spring/JPA와의 경계

Kotlin class는 기본이 final이다. Spring AOP나 JPA가 상속 기반 proxy를 쓰면 open class가 필요하다.

보통 Gradle plugin으로 처리한다.

```kotlin
plugins {
    kotlin("plugin.spring")
    kotlin("plugin.jpa")
}
```

두 플러그인은 하는 일이 다르다.

| 플러그인 | 하는 일 | 하지 않는 일 |
|---|---|---|
| `plugin.spring` | `@Component`, `@Transactional`, `@Async` 등이 붙은 클래스를 `open`으로 만든다 | `@Entity`는 열지 않는다 |
| `plugin.jpa` | `@Entity`, `@Embeddable`, `@MappedSuperclass`에 no-arg 생성자를 만든다 | `open` 처리는 하지 않는다 |

그래서 Entity는 기본 설정만으로는 final로 남고, Hibernate가 지연 로딩 프록시를 만들지 못해 `@ManyToOne(fetch = LAZY)`가 사실상 즉시 로딩처럼 동작할 수 있다. Entity에는 `allOpen`을 따로 건다.

```kotlin
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}
```

Entity를 `data class`로 만드는 문제는 플러그인으로 해결되지 않는다. [[kotlin-data-class-and-immutability]] 참고.

## 상황별로 정리하면

| 상황 | 할 일 |
|---|---|
| Java API 호출 | null 가능성 방어 |
| Java에서도 호출할 Kotlin API | `@JvmOverloads`, `@JvmStatic` 검토 |
| Spring AOP 대상 | kotlin spring plugin 확인 |
| JPA Entity | kotlin jpa plugin + 일반 class 설계 |
| 외부 라이브러리 예외 | Kotlin에서도 명시적 try-catch 기준 마련 |

## 자주 깨지는 곳

- **Java API 반환값을 non-null로 단정한다.** platform type이라 컴파일은 되고 런타임에 NPE가 난다. platform type 경고와 null 처리 방식을 경계마다 본다.
- **default parameter만 믿고 overload를 만들지 않는다.** Java 호출부가 모든 인자를 넘겨야 한다.
- **Java checked exception 처리를 놓친다.** Kotlin이 강제하지 않으니 실패가 그대로 올라간다.
- **`kotlin("plugin.spring")`, `kotlin("plugin.jpa")` 없이 proxy 문제를 만난다.** proxy가 필요한 class가 final로 남는다. Entity는 no-arg 생성자와 open 처리가 둘 다 적용됐는지 따로 확인한다.
- **Java와 Kotlin DTO의 nullability annotation이 어긋난다.** 한쪽에서는 필수, 다른 쪽에서는 선택이 된다.

## 면접에서 말하기

> Kotlin은 Java와 잘 섞이지만 그 경계에서는 Kotlin의 null 안전성이 약해집니다. Java 반환 타입은 nullability를 모르는 platform type이라 Kotlin에서도 NPE가 날 수 있어서, 저는 Java API를 부르는 자리에서 null을 명시적으로 막습니다. Spring/JPA에서는 Kotlin class가 기본 final이고 no-arg 생성자가 없어서 plugin.spring, plugin.jpa가 필요하고, Entity에는 allOpen을 따로 겁니다.

## 꼬리 질문

> [!question]- Kotlin platform type이란 무엇인가?
> Java에서 온 타입처럼 null 가능성을 Kotlin 컴파일러가 확정할 수 없는 타입입니다. 명시적으로 처리하지 않으면 런타임 NPE가 납니다.

> [!question]- Kotlin class가 기본 final인 것이 Spring/JPA에서 왜 문제가 되는가?
> Spring AOP나 JPA proxy가 상속 기반으로 동작할 때 final class를 상속할 수 없기 때문입니다.

> [!question]- Kotlin에서 Java checked exception은 어떻게 다뤄지는가?
> Kotlin은 checked exception 처리를 강제하지 않습니다. 그래서 Java API 호출 실패를 어떻게 처리할지 설계와 코드 리뷰에서 기준을 정해 둡니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin platform type이 위험한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Java에서 온 타입은 nullability 정보가 불명확해 Kotlin 컴파일러가 null 안전성을 충분히 보장하지 못한다." aria-pressed="false">A. Java 타입의 nullability가 불명확할 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="platform type이 Java 호출 자체를 막지는 않는다." aria-pressed="false">B. Java 메서드를 호출할 수 없게 만든다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="성능 최적화가 아니라 nullability 경계 문제다." aria-pressed="false">C. 모든 호출을 reflection으로 바꾼다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Kotlin class는 기본적으로 final이므로 Spring AOP나 JPA 프록시와 충돌할 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="프록시 생성에는 상속/오버라이드가 필요한 경우가 있어 open 처리나 compiler plugin 설정이 필요할 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="클래스가 기본으로 final이라 Spring/JPA 프록시와 부딪힌다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin에서 Java checked exception을 다룰 때 주의할 점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Kotlin은 checked exception 처리를 강제하지 않으므로 Java 호출부의 실패 계약을 문서와 테스트로 명확히 해야 한다." aria-pressed="false">A. 컴파일러 강제가 없으므로 실패 계약을 명시적으로 관리한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="checked exception이 사라지는 것이 아니라 강제 처리 규칙이 다르다." aria-pressed="false">B. Java checked exception은 Kotlin에서 절대 발생하지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 예외를 삼키는 것은 장애를 숨기는 위험한 방식이다." aria-pressed="false">C. 모든 Java 예외를 빈 catch로 처리한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[kotlin]]
- [[kotlin-null-safety]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/reflection-and-annotation|reflection-and-annotation]]
- [[01-core/spring/aop|aop]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
