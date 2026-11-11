---
title: Kotlin을 백엔드에서 사용하는 이유
description: Kotlin을 쓰면 Java 백엔드에서 어떤 문제가 줄고, 어디서 새로 조심해야 하는지
tags: [concept, kotlin]
---

# Kotlin을 백엔드에서 사용하는 이유

Kotlin은 JVM에서 돌고 Java 코드와 서로 불러 쓸 수 있는 언어다. null을 타입으로 막아 주고, 데이터 클래스를 짧게 쓰게 해 주고, 컬렉션을 함수형으로 다루고, coroutine을 쓸 수 있다.

문법이 짧아서 쓰는 언어는 아니다. 백엔드에서 Kotlin을 쓰면 이런 문제가 줄어든다.

- null 체크를 빠뜨려서 나는 `NullPointerException`
- DTO, request, response 객체마다 반복되는 코드
- 컬렉션을 변환하고 조건을 붙이는 장황한 코드

그리고 이런 바람을 채워 준다.

- Java 라이브러리와 Spring은 그대로 쓰면서 타입은 더 엄격하게 쓰고 싶다.
- 비동기 I/O 흐름을 callback보다 읽기 쉽게 쓰고 싶다.

## Java와 무엇이 다른가

| 주제 | Java | Kotlin |
|---|---|---|
| null | 모든 reference가 null 가능 | nullable/non-nullable 타입 구분 |
| DTO | class, record | data class |
| 불변 변수 | `final` | `val` |
| 컬렉션 처리 | Stream API | collection extension 함수 |
| checked exception | 있음 | 없음 |
| 비동기 | Future, CompletableFuture | coroutine |

Kotlin은 Java를 몰아낸다기보다, JVM 백엔드에서 Java의 불편한 부분을 덜어 주는 쪽에 가깝다.

## 상황별 득실

| 상황 | Kotlin 장점 | 주의점 |
|---|---|---|
| API DTO가 많다 | data class로 반복 코드 감소 | default value와 Jackson 설정 확인 |
| null 버그가 많다 | 타입으로 null 가능성 표현 | Java interop 경계에서는 platform type 주의 |
| JPA Entity 사용 | 코드가 짧아진다 | final class, data class, no-arg 문제 |
| 비동기 I/O | suspend 함수로 흐름 표현 | blocking API와 섞이면 효과 감소 |
| 기존 Java 프로젝트 | 점진 도입 가능 | 팀의 Kotlin 숙련도와 빌드 설정 필요 |

## 자주 깨지는 곳

- NPE가 완전히 사라진다고 믿으면, Java API가 돌려준 값에서 NPE를 맞는다. 그 값은 platform type이라 컴파일러가 막지 않는다. 받는 쪽에서 null이 올 수 있는지 확인한다.
- JPA Entity를 무심코 `data class`로 만들면, final class, 자동으로 생기는 메서드, 기본 생성자 문제가 한꺼번에 생긴다.
- `val`만 쓰면 완전히 불변이라고 믿으면, 가리키는 객체가 mutable일 때 내용이 바뀌는 걸 놓친다.
- coroutine을 쓰면 알아서 빨라진다고 믿고 blocking I/O를 그대로 부르면, 아무 효과가 없다.

## 한 번에 설명하기

> Kotlin은 Java 라이브러리와 Spring을 그대로 쓰면서 null 안정성, data class, 컬렉션 처리, coroutine을 쓸 수 있게 해 줍니다. 저는 문법이 짧은 것보다 타입으로 실수를 미리 막아 주는 점을 더 크게 봅니다.
>
> 다만 Java 코드와 섞이는 곳, JPA, Jackson, Spring 프록시와 맞물리는 곳에서는 Kotlin의 특징이 오히려 걸림돌이 됩니다.
>
> 그래서 도입할 때는 한 번에 바꾸기보다 DTO, 테스트, 새 모듈처럼 위험이 낮은 곳부터 씁니다.

## 꼬리 질문

> [!question]- Kotlin을 백엔드에서 사용하는 이유는 무엇인가?
> null 안정성, data class, 컬렉션 extension, coroutine 덕분에 Java로 쓸 때의 반복 코드가 줄고, 실행해 봐야 알던 오류 일부를 컴파일할 때 잡을 수 있어서입니다.

> [!question]- Kotlin을 쓰면 Java가 필요 없어지는가?
> 아닙니다. Kotlin은 대개 JVM 위에서 Java 라이브러리와 함께 쓰여서, Java, Spring, JPA가 어떻게 도는지는 여전히 알아야 합니다.

> [!question]- Kotlin 도입 시 가장 먼저 주의할 경계는?
> 넷을 먼저 봅니다. Java에서 받은 값의 platform type, JPA Entity를 어떻게 만들지, Jackson이 객체를 제대로 만들어 내는지, Spring 프록시가 실제로 걸리는지입니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin을 백엔드에 도입할 때 가장 먼저 관리해야 할 경계는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Java/Spring/JPA와 맞닿는 nullability, final class, proxy, checked exception 경계를 먼저 관리해야 한다." aria-pressed="false">A. Java/Spring/JPA와의 interop 경계</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문법이 간결해지는 것만으로 운영 리스크가 사라지지는 않는다." aria-pressed="false">B. 코드 라인 수가 줄어드는지 여부만 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Kotlin 도입 후에도 JVM과 Java 생태계 이해는 계속 필요하다." aria-pressed="false">C. Java 지식을 모두 제거해도 되는지 확인한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Kotlin을 사용하면 Java의 JVM, Spring, JPA 동작 원리를 몰라도 된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Kotlin 백엔드는 JVM과 Java 생태계 위에서 동작하므로 기존 동작 원리 이해가 여전히 필요하다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Kotlin은 Java를 대체하는 문법일 수 있지만 JVM/Spring/JPA 지식을 대체하지는 않는다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin의 장점을 백엔드 코드에서 가장 현실적으로 활용하는 방식은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="nullable 타입, data class, 표현식 문법으로 DTO와 비즈니스 로직의 의도가 코드에 드러난다." aria-pressed="false">A. null 가능성과 데이터 모델의 의도를 타입으로 드러낸다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Kotlin이 DB 쿼리를 자동 최적화하지는 않는다." aria-pressed="false">B. DB 인덱스 설계를 자동으로 대체한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 Java 라이브러리를 제거하는 것이 목적은 아니다." aria-pressed="false">C. Java 라이브러리를 전혀 쓰지 않는 방향으로 강제한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kotlin for server side](https://kotlinlang.org/docs/server-overview.html)
- [Spring Framework: Kotlin](https://docs.spring.io/spring-framework/reference/languages/kotlin.html)

## 관련 문서

- [[01-core/kotlin/kotlin|kotlin]]
- [[kotlin-null-safety]]
- [[kotlin-java-interop]]
- [[01-core/java/java|java]]
