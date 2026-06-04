---
title: Kotlin Java Interop
description: Kotlin과 Java를 함께 사용할 때 nullability, annotation, 예외, 빌드 경계에서 주의할 점
---

# Kotlin Java Interop

## 한 줄 정의

Kotlin Java interop은 Kotlin 코드와 Java 코드가 같은 JVM 생태계에서 서로 호출될 수 있게 하는 기능과 그 경계에서 생기는 주의점이다.

## 실무에서 왜 중요한가

Kotlin 백엔드는 대부분 Java 라이브러리, Spring, JPA, Jackson과 함께 동작한다. interop을 모르면 다음 문제가 생긴다.

- Java 반환값이 null일 수 있는데 Kotlin에서 non-null처럼 사용한다.
- Java에서 Kotlin default parameter를 자연스럽게 호출하지 못한다.
- checked exception이 Kotlin에서 강제되지 않아 실패 처리를 놓친다.
- `@JvmStatic`, `@JvmOverloads`, `@JvmField` 사용 기준이 없다.
- Kotlin class가 기본 final이라 Spring/JPA proxy와 충돌한다.

## Platform Type

Java 타입은 Kotlin에서 nullability를 확정할 수 없으면 platform type으로 보인다.

```java
public User findUser(Long id) {
    return null;
}
```

Kotlin에서는 `User!`처럼 취급되어 nullable처럼도, non-null처럼도 사용할 수 있다.

```kotlin
val user = javaUserRepository.findUser(id)
println(user.name) // 런타임 NPE 가능
```

Java API 경계에서는 null 가능성을 명시적으로 방어하는 것이 안전하다.

```kotlin
val user = javaUserRepository.findUser(id)
    ?: throw UserNotFoundException(id)
```

## Java에서 Kotlin 호출

Kotlin의 default parameter는 Java에서 그대로 편하게 보이지 않는다.

```kotlin
class MailSender {
    fun send(to: String, retry: Int = 3) {
    }
}
```

Java 호출 편의가 필요하면 `@JvmOverloads`를 검토한다.

```kotlin
class MailSender {
    @JvmOverloads
    fun send(to: String, retry: Int = 3) {
    }
}
```

companion object를 Java static처럼 노출하려면 `@JvmStatic`을 사용할 수 있다.

```kotlin
class TokenUtils {
    companion object {
        @JvmStatic
        fun parse(token: String): Long = token.toLong()
    }
}
```

## Spring/JPA와의 경계

Kotlin class는 기본적으로 final이다. Spring AOP나 JPA proxy는 상속 기반 proxy를 사용할 때 open class가 필요할 수 있다.

실무에서는 Gradle plugin으로 처리하는 경우가 많다.

```kotlin
plugins {
    kotlin("plugin.spring")
    kotlin("plugin.jpa")
}
```

이 플러그인은 Spring annotation이나 JPA entity에 필요한 open/no-arg 처리를 도와준다. 그래도 Entity를 `data class`로 만드는 문제까지 자동으로 해결해주지는 않는다.

## 자주 나는 실수

- Java API 반환값을 non-null로 단정한다.
- Java 호출이 필요한 Kotlin 함수에 default parameter만 믿고 overload를 만들지 않는다.
- Kotlin에서 checked exception 처리를 놓친다.
- `kotlin("plugin.spring")`, `kotlin("plugin.jpa")` 설정 없이 proxy 문제를 만난다.
- Java와 Kotlin DTO의 nullability annotation을 맞추지 않는다.

## 실무 판단 기준

| 상황 | 권장 |
|---|---|
| Java API 호출 | null 가능성 방어 |
| Java에서도 호출할 Kotlin API | `@JvmOverloads`, `@JvmStatic` 검토 |
| Spring AOP 대상 | kotlin spring plugin 확인 |
| JPA Entity | kotlin jpa plugin + 일반 class 설계 |
| 외부 라이브러리 예외 | Kotlin에서도 명시적 try-catch 기준 마련 |

## 확인 방법

- Java API 경계에서 platform type 경고와 null 처리 방식을 확인한다.
- Spring proxy가 필요한 class가 final로 남아 있지 않은지 확인한다.
- JPA Entity에 no-arg 생성자와 open 처리가 적용되는지 확인한다.
- Java 호출부에서 Kotlin default parameter를 제대로 사용할 수 있는지 확인한다.

## 핵심 요약

Kotlin은 Java와 잘 섞이지만 interop 경계에서는 Kotlin의 안전성이 약해질 수 있다.

Java 반환 타입은 nullability를 알 수 없는 platform type이 될 수 있어 Kotlin에서도 NPE가 발생할 수 있다.

Java에서 Kotlin 코드를 호출해야 한다면 default parameter, companion object, property 노출 방식을 별도로 고려해야 한다.

Spring/JPA에서는 Kotlin class의 final 기본값과 no-arg 생성자 문제가 proxy와 Entity 생성에 영향을 줄 수 있다.

Kotlin 백엔드를 실무에서 안정적으로 쓰려면 Java interop 경계를 명시적으로 관리해야 한다.

## 꼬리 질문

> [!question]- Kotlin platform type이란 무엇인가?
> Java에서 온 타입처럼 null 가능성을 Kotlin 컴파일러가 확정할 수 없는 타입입니다. 안전하게 처리하지 않으면 런타임 NPE가 발생할 수 있습니다.

> [!question]- Kotlin class가 기본 final인 것이 Spring/JPA에서 왜 문제가 되는가?
> Spring AOP나 JPA proxy가 상속 기반으로 동작할 때 final class를 상속할 수 없기 때문입니다.

> [!question]- Kotlin에서 Java checked exception은 어떻게 다뤄지는가?
> Kotlin은 checked exception 처리를 강제하지 않습니다. 따라서 Java API 호출 실패를 명시적으로 처리할 기준을 코드 리뷰와 설계에서 잡아야 합니다.

## 관련 문서

- [[kotlin]]
- [[kotlin-null-safety]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/reflection-and-annotation|reflection-and-annotation]]
- [[01-core/spring/aop|aop]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
