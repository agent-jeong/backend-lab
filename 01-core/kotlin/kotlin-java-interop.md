---
title: Kotlin과 Java 함께 쓰기
description: Kotlin과 Java가 서로 부를 때 null, 기본 인자, 예외, final class에서 생기는 문제
tags: [concept, kotlin]
---

# Kotlin과 Java 함께 쓰기

Kotlin과 Java는 같은 JVM에서 서로를 부른다. 그런데 서로 넘나드는 자리에서는 Kotlin이 걸어 둔 안전장치가 약해진다.

Kotlin 백엔드는 거의 늘 Java 라이브러리, Spring, JPA, Jackson과 같이 돈다. 그래서 Java가 돌려준 null을 Kotlin이 non-null로 믿고 쓰다가 NPE가 나고, Java 쪽에서는 Kotlin의 default parameter를 못 써서 인자를 전부 넘겨야 한다. checked exception을 Kotlin이 강제하지 않으니 실패 처리를 빠뜨리기도 한다. Kotlin class가 기본으로 final이라 Spring과 JPA의 proxy와 부딪히는 것도 같은 종류의 문제다.

## Platform Type

Java 타입은 null이 올 수 있는지 Kotlin이 알 수 없어서 platform type으로 보인다.

```java
public User findUser(Long id) {
    return null;
}
```

Kotlin에서는 `User!`로 취급되어 nullable로도, non-null로도 쓸 수 있다. 어느 쪽으로 쓰든 컴파일러가 막지 않는다.

```kotlin
val user = javaUserRepository.findUser(id)
println(user.name) // 런타임 NPE 가능
```

Java API를 부르는 자리에서는 null이 오면 어떻게 할지 직접 적는다.

```kotlin
val user = javaUserRepository.findUser(id)
    ?: throw UserNotFoundException(id)
```

## Java에서 Kotlin 호출

Kotlin의 default parameter는 Java에서는 보이지 않는다. Java에서 부를 때는 인자를 모두 넘겨야 한다.

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

Kotlin class는 기본이 final이다. Spring AOP나 JPA는 클래스를 상속해서 proxy를 만들기 때문에 open class가 필요하다.

보통 Gradle plugin으로 푼다.

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
| `plugin.jpa` | `@Entity`, `@Embeddable`, `@MappedSuperclass`에 no-arg 생성자를 만든다. Kotlin 2.3.20부터는 이 클래스들을 `open`으로도 만든다 | Kotlin 2.3.20 전에는 `open` 처리를 하지 않는다 |

`plugin.jpa`가 Entity를 여는지는 Kotlin 버전에 달렸다. Kotlin 2.3.20부터는 `plugin.jpa`가 JPA 프리셋을 켠 all-open 플러그인까지 같이 적용해서 따로 설정할 게 없다. 그 전 버전에서는 no-arg만 적용돼서, 두 플러그인만 켜 두면 Entity가 final로 남는다. 그러면 Hibernate가 지연 로딩 프록시를 만들지 못해 `@ManyToOne(fetch = LAZY)`가 즉시 로딩처럼 돈다. Kotlin 2.3.20 전이라면 Entity에 `allOpen`을 따로 건다.

```kotlin
allOpen {
    annotation("jakarta.persistence.Entity")
    annotation("jakarta.persistence.MappedSuperclass")
    annotation("jakarta.persistence.Embeddable")
}
```

Entity를 `data class`로 만들면, 플러그인을 켜도 data class가 모든 프로퍼티로 만드는 `equals`·`hashCode`·`toString`은 그대로 남는다. 그래서 Kotlin 문서도 Entity는 일반 class로 만들라고 한다. 자세한 내용은 [[kotlin-data-class-and-immutability]]에 있다.

## 상황별로 할 일

| 상황 | 할 일 |
|---|---|
| Java API 호출 | null 가능성 방어 |
| Java에서도 호출할 Kotlin API | `@JvmOverloads`, `@JvmStatic` 검토 |
| Spring AOP 대상 | kotlin spring plugin 확인 |
| JPA Entity | kotlin jpa plugin + 일반 class 설계 |
| 외부 라이브러리 예외 | Kotlin에서도 명시적 try-catch 기준 마련 |

## 자주 깨지는 곳

- Java API가 돌려준 값을 non-null로 믿고 쓰면, platform type이라 컴파일은 되고 실행 중에 NPE가 난다. Java를 부르는 자리마다 platform type 경고와 null 처리를 본다.
- default parameter만 믿고 overload를 만들지 않으면, Java에서 부르는 쪽이 인자를 전부 넘겨야 한다.
- Java checked exception을 Kotlin이 강제하지 않는다고 그냥 두면, 실패가 아무 처리 없이 그대로 위로 올라간다.
- `kotlin("plugin.spring")` 없이 쓰면 Spring Bean class가 final로 남아, Spring AOP 대상 Bean은 기동할 때 CGLIB 오류가 난다. `kotlin("plugin.jpa")`는 Kotlin 2.3.20 전에는 Entity에 no-arg 생성자만 만들고 class를 열지 않는다. 그 버전에서 Entity를 지연 로딩 프록시로 쓰려면 `allOpen`에 `jakarta.persistence.Entity` 같은 어노테이션을 따로 등록한다. 2.3.20부터는 `plugin.jpa`가 Entity도 연다.
- Java DTO와 Kotlin DTO의 nullability annotation이 어긋나면, 같은 필드가 한쪽에서는 필수, 다른 쪽에서는 선택이 된다.

## 한 번에 설명하기

> Kotlin은 Java와 잘 섞이지만, 서로 넘나드는 자리에서는 Kotlin의 null 안전성이 약해집니다. Java가 돌려주는 값은 null이 올지 모르는 platform type이라 Kotlin에서도 NPE가 날 수 있습니다. 그래서 저는 Java API를 부르는 자리에서 null을 직접 막습니다.
>
> Spring과 JPA에서는 Kotlin class가 기본 final이고 no-arg 생성자가 없어서 plugin.spring과 plugin.jpa를 켭니다. Kotlin 2.3.20 전 버전이라면 plugin.jpa가 Entity를 열지 않으니 allOpen을 따로 겁니다.

## 꼬리 질문

> [!question]- Kotlin platform type이란 무엇인가?
> Java에서 온 타입처럼, null이 올 수 있는지 Kotlin 컴파일러가 알 수 없는 타입입니다. null 처리를 직접 해 두지 않으면 실행 중에 NPE가 납니다.

> [!question]- Kotlin class가 기본 final인 것이 Spring/JPA에서 왜 문제가 되는가?
> Spring AOP나 JPA는 클래스를 상속해서 proxy를 만드는데, final class는 상속할 수 없어서입니다.

> [!question]- Kotlin에서 Java checked exception은 어떻게 다뤄지는가?
> Kotlin은 checked exception을 잡으라고 강제하지 않습니다. 그래서 Java API 호출이 실패했을 때 어떻게 처리할지는 팀이 설계와 코드 리뷰에서 기준을 정해 둬야 합니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kotlin: Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html)
- [Kotlin: All-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html)
- [Kotlin: Kotlin-jpa compiler plugin](https://kotlinlang.org/docs/kotlin-jpa-plugin.html): Entity는 data class가 아닌 일반 class로
- [What's new in Kotlin 2.3.20: Improved JPA support](https://kotlinlang.org/docs/whatsnew2320.html): `plugin.jpa`가 all-open을 같이 적용

## 관련 문서

- [[01-core/kotlin/kotlin|kotlin]]
- [[kotlin-null-safety]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/reflection-and-annotation|reflection-and-annotation]]
- [[01-core/spring/aop|aop]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
