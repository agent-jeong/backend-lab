---
title: Kotlin null 안전성
description: Kotlin이 null을 타입으로 막는 방식과, 그래도 NPE가 나는 곳
tags: [concept, kotlin]
---

# Kotlin null 안전성

Kotlin은 null이 될 수 있는 타입과 될 수 없는 타입을 나눠 두고, null 체크를 빠뜨리면 컴파일 에러를 낸다. NPE를 없애 주는 게 아니라 줄여 준다.

백엔드에서 null은 요청값, DB 조회 결과, 외부 API 응답, 설정값 어디서나 나온다. Kotlin을 써도 Java API가 돌려준 platform type, 여기저기 붙인 `!!`, JPA Entity에서 나중에 채워지는 필드에서는 여전히 NPE가 난다. Jackson이 JSON을 객체로 만들 때를 생각해 nullable과 default value를 따로 정해야 하고, null과 빈 문자열과 빈 컬렉션이 같은 뜻인지 다른 뜻인지 헷갈리기도 한다.

## 기본 개념

Kotlin은 타입 뒤에 `?`가 붙어야 null을 담을 수 있다.

```kotlin
val name: String = "kim"
val nickname: String? = null
```

nullable 값은 바로 쓸 수 없다.

```kotlin
val length = nickname.length // compile error
```

안전 호출(`?.`)이나 null일 때 할 일을 적어 줘야 쓸 수 있다.

```kotlin
val length = nickname?.length ?: 0
```

## 값마다 어떻게 받나

| 상황 | 권장 |
|---|---|
| 요청 필수값 | non-null 타입 + validation |
| 요청 선택값 | nullable 타입 |
| 조회 결과 없음 | nullable 또는 명시적 예외 |
| 목록 없음 | null보다 empty list 우선 |
| 외부 API 불확실한 값 | nullable DTO로 받고 검증 후 내부 모델 변환 |

밖에서 들어오는 입력과 안쪽 도메인 모델은 null 허용 여부를 따로 정한다.

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

요청 DTO는 값이 빠져서 올 수 있으니 nullable로 두고, 검증을 통과한 뒤 만드는 내부 command는 non-null로 둔다.

## `!!`는 NPE를 직접 던진다

`!!`는 값이 null이면 바로 NPE를 던진다.

```kotlin
val length = nickname!!.length
```

`!!`가 늘수록 Kotlin이 null을 막아 주는 이점이 사라진다. 정말 null일 수 없는 상황이라면, 무엇이 왜 없는지 알 수 있는 예외를 직접 던지는 편이 낫다.

```kotlin
val user = userRepository.findByIdOrNull(id)
    ?: throw UserNotFoundException(id)
```

## 자주 깨지는 곳

- 컴파일 오류를 빨리 없애려고 `!!`를 붙이면, 오류가 실행 중 NPE로 미뤄질 뿐이다. 코드 리뷰에서 `!!`가 어디 왜 붙었는지 본다.
- Java API가 돌려준 값을 non-null로 믿고 쓰면, platform type이라 컴파일러가 막지 않아 실행 중에 NPE가 난다.
- nullable 필드를 여러 계층으로 그대로 넘기면, 계층마다 null 체크가 반복된다. request DTO와 내부 command, domain 모델의 null 허용 여부를 따로 정한다.
- 빈 컬렉션이면 될 자리에 nullable collection을 쓰면, 부르는 쪽마다 null 처리가 붙는다.
- 검증하기 전의 request DTO를 domain 객체처럼 쓰면, 빠진 값이 도메인 안까지 들어온다. 테스트에서는 필드가 아예 없는 경우, null인 경우, 빈 문자열인 경우를 나눠서 본다.

## 한 번에 설명하기

> Kotlin은 null이 될 수 있는지를 타입에 적게 해서, null 체크를 빠뜨리면 컴파일할 때 잡아 줍니다. 그래도 NPE가 완전히 없어지지는 않고, Java에서 받은 platform type이나 `!!`, JPA나 Jackson과 맞물리는 곳에서는 여전히 납니다.
>
> 저는 밖에서 들어오는 요청 DTO는 nullable로 받고, 검증한 뒤 안쪽 모델은 non-null로 바꿉니다.
>
> 빈 목록은 null 대신 empty list로 돌려줘서 부르는 쪽 코드를 단순하게 둡니다.

## 꼬리 질문

> [!question]- Kotlin의 nullable 타입과 non-null 타입 차이는?
> `String`에는 null을 못 넣고, `String?`에는 넣을 수 있습니다. nullable 값은 안전 호출을 쓰거나 null일 때 어떻게 할지 적어 줘야 쓸 수 있습니다.

> [!question]- `!!`는 왜 위험한가?
> null이면 그 자리에서 NPE를 던져서, Kotlin이 null을 막아 주는 걸 스스로 꺼 버리는 셈입니다. 그래서 무엇이 없는지 알려 주는 예외를 직접 던지거나, `?:`로 기본값을 주는 쪽을 먼저 씁니다.

> [!question]- Kotlin을 써도 NPE가 발생할 수 있는 경우는?
> Java에서 받은 platform type 값, `!!`, 초기화하기 전에 필드를 읽는 경우, 그리고 reflection으로 객체를 만드는 Jackson이나 JPA와 맞물리는 곳에서 납니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Kotlin의 nullable 타입과 non-null 타입 차이로 맞는 설명은?</p>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kotlin: Null safety](https://kotlinlang.org/docs/null-safety.html)

## 관련 문서

- [[01-core/kotlin/kotlin|kotlin]]
- [[kotlin-java-interop]]
- [[kotlin-data-class-and-immutability]]
- [[01-core/java/primitive-and-reference-types|primitive-and-reference-types]]
