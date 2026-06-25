---
title: Kotlin Null Safety
description: Kotlin nullable 타입과 Java interop에서 발생하는 null 처리 기준
---

# Kotlin Null Safety

## 한 줄 정의

Kotlin null safety는 null이 가능한 타입과 불가능한 타입을 타입 시스템에서 구분해 null 처리 누락을 컴파일 타임에 줄이는 기능이다.

## 실무에서 왜 중요한가

백엔드 서비스에서 null은 요청값, DB 조회 결과, 외부 API 응답, 설정값에서 자주 발생한다. Kotlin을 사용해도 다음 상황은 계속 주의해야 한다.

- Java API가 반환한 platform type에서 NPE가 발생한다.
- `!!`를 남용해서 Kotlin 코드에서도 NPE가 발생한다.
- JPA Entity의 지연 초기화 필드와 non-null 타입이 충돌한다.
- Jackson 역직렬화를 위해 nullable/default value 설계가 필요하다.
- null과 빈 문자열, 빈 컬렉션의 의미가 섞인다.

## 기본 개념

Kotlin은 타입 뒤에 `?`가 붙어야 null을 담을 수 있다.

```kotlin
val name: String = "kim"
val nickname: String? = null
```

nullable 값은 바로 사용할 수 없다.

```kotlin
val length = nickname.length // compile error
```

안전 호출이나 명시적 처리가 필요하다.

```kotlin
val length = nickname?.length ?: 0
```

## 실무 처리 방식

| 상황 | 권장 |
|---|---|
| 요청 필수값 | non-null 타입 + validation |
| 요청 선택값 | nullable 타입 |
| 조회 결과 없음 | nullable 또는 명시적 예외 |
| 목록 없음 | null보다 empty list 우선 |
| 외부 API 불확실한 값 | nullable DTO로 받고 검증 후 내부 모델 변환 |

외부 입력과 내부 도메인 모델의 nullability를 분리하는 것이 좋다.

```kotlin
data class CreateUserRequest(
    val name: String?,
    val email: String?
)

data class CreateUserCommand(
    val name: String,
    val email: String
)
```

요청 DTO에서는 입력 불완전성을 표현하고, 검증 후 내부 command는 non-null로 만드는 식이다.

## `!!` 사용 주의

`!!`는 null이면 즉시 NPE를 던진다.

```kotlin
val length = nickname!!.length
```

실무에서는 `!!`가 많아지면 Kotlin null safety의 장점이 사라진다. 정말 불가능한 상태라면 예외 메시지를 명확히 남기는 편이 낫다.

```kotlin
val user = userRepository.findByIdOrNull(id)
    ?: throw UserNotFoundException(id)
```

## 자주 나는 실수

- `!!`로 컴파일 오류를 빠르게 없앤다.
- Java API 반환값을 non-null이라고 단정한다.
- nullable field를 그대로 여러 계층으로 전파한다.
- 빈 컬렉션이면 충분한데 nullable collection을 사용한다.
- validation 전 request DTO를 domain 객체처럼 사용한다.

## 확인 방법

- 코드 리뷰에서 `!!` 사용 위치와 이유를 확인한다.
- Java API 호출부의 반환값 null 가능성을 확인한다.
- request DTO와 내부 command/domain 모델의 nullability가 분리되어 있는지 확인한다.
- 테스트에서 누락 필드, null 필드, 빈 문자열을 구분해 검증한다.

## 핵심 요약

Kotlin null safety는 null 가능성을 타입으로 표현해 null 처리 누락을 줄인다.

하지만 Java interop의 platform type, `!!` 남용, JPA/Jackson 경계에서는 여전히 NPE가 발생할 수 있다.

외부 입력 DTO는 nullable로 받을 수 있지만, 검증 후 내부 모델은 non-null로 바꾸는 것이 안전하다.

빈 목록은 null보다 empty list로 표현하는 편이 호출부를 단순하게 만든다.

면접에서는 Kotlin이 NPE를 완전히 제거하는 것이 아니라 컴파일 타임에 null 위험을 줄인다고 설명하는 것이 정확하다.

## 꼬리 질문

> [!question]- Kotlin의 nullable 타입과 non-null 타입 차이는?
> `String`은 null을 담을 수 없고, `String?`은 null을 담을 수 있습니다. nullable 값은 안전 호출이나 null 처리를 거쳐야 사용할 수 있습니다.

> [!question]- `!!`는 왜 위험한가?
> null이면 런타임에 NPE를 던지므로 Kotlin null safety의 장점을 우회합니다. 명시적 예외나 안전한 변환을 우선 고려해야 합니다.

> [!question]- Kotlin을 써도 NPE가 발생할 수 있는 경우는?
> Java interop의 platform type, `!!`, 초기화 전 접근, reflection/Jackson/JPA 경계에서 발생할 수 있습니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin의 nullable 타입과 non-null 타입 차이로 가장 적절한 설명은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="String?은 null 가능성을 타입에 포함하고, String은 컴파일러가 null 대입을 제한한다." aria-pressed="false">A. null 가능성을 타입 시스템에 명시하느냐의 차이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="non-null 타입도 Java 경계나 lateinit 등에서 런타임 NPE 가능성이 완전히 사라지는 것은 아니다." aria-pressed="false">B. non-null 타입은 어떤 상황에서도 NPE가 절대 발생하지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="nullable 타입은 null만 담는 타입이 아니라 값 또는 null을 담을 수 있는 타입이다." aria-pressed="false">C. nullable 타입은 null 값만 담을 수 있다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>!!는 컴파일러에게 null이 아니라고 단언하는 것이므로, 잘못 쓰면 NPE가 발생할 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="!!는 null 검사를 우회하고 null이면 런타임 예외를 발생시킨다. 경계에서 제한적으로 사용해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="!!는 안전 호출이 아니라 강제 단언이다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin 코드에서도 NPE가 발생할 수 있는 대표적인 경우는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Java platform type, !!, lateinit 미초기화, 프레임워크 리플렉션 경계에서 NPE가 발생할 수 있다." aria-pressed="false">A. Java platform type이나 !!를 잘못 다룬 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Kotlin의 non-null 문법만으로 모든 런타임 경계가 안전해지지는 않는다." aria-pressed="false">B. Kotlin 파일 안에서는 NPE가 원천적으로 불가능하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="val은 재할당을 막을 뿐 참조 대상의 null 경계 전체를 제거하지 않는다." aria-pressed="false">C. val을 쓰면 모든 NPE가 사라진다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[kotlin]]
- [[kotlin-java-interop]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/primitive-and-reference-types|primitive-and-reference-types]]
