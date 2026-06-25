---
title: Kotlin을 백엔드에서 사용하는 이유
description: Kotlin이 Java 백엔드의 어떤 실무 문제를 줄이는지 정리
---

# Kotlin을 백엔드에서 사용하는 이유

## 한 줄 정의

Kotlin은 JVM 위에서 동작하면서 Java와 상호 운용되고, null 안정성, 간결한 데이터 모델, 함수형 컬렉션 처리, coroutine을 제공하는 언어다.

## 실무에서 왜 중요한가

Kotlin은 문법이 짧아서 쓰는 언어가 아니다. 백엔드 실무에서는 다음 문제를 줄이는 데 의미가 있다.

- null 처리 누락으로 발생하는 `NullPointerException`
- DTO, request, response 객체의 반복 코드
- 컬렉션 변환과 조건 조립의 장황한 코드
- Java 라이브러리와 Spring 생태계를 유지하면서 더 안전한 타입 표현을 쓰고 싶은 요구
- 비동기 I/O 흐름을 callback보다 읽기 쉽게 표현하고 싶은 요구

## Java와 비교한 핵심 차이

| 주제 | Java | Kotlin |
|---|---|---|
| null | 모든 reference가 null 가능 | nullable/non-nullable 타입 구분 |
| DTO | class, record | data class |
| 불변 변수 | `final` | `val` |
| 컬렉션 처리 | Stream API | collection extension 함수 |
| checked exception | 있음 | 없음 |
| 비동기 | Future, CompletableFuture | coroutine |

Kotlin은 Java를 대체한다기보다 JVM 백엔드에서 Java의 불편한 부분을 줄이는 선택지에 가깝다.

## 실무 판단 기준

| 상황 | Kotlin 장점 | 주의점 |
|---|---|---|
| API DTO가 많다 | data class로 반복 코드 감소 | default value와 Jackson 설정 확인 |
| null 버그가 많다 | 타입으로 null 가능성 표현 | Java interop 경계에서는 platform type 주의 |
| JPA Entity 사용 | 코드가 짧아질 수 있음 | final class, data class, no-arg 문제 |
| 비동기 I/O | suspend 함수로 흐름 표현 | blocking API와 섞이면 효과 감소 |
| 기존 Java 프로젝트 | 점진 도입 가능 | 팀의 Kotlin 숙련도와 빌드 설정 필요 |

## 자주 나는 실수

- Kotlin을 쓰면 NPE가 완전히 사라진다고 생각한다.
- JPA Entity를 무심코 `data class`로 만든다.
- `val`만 쓰면 객체가 완전히 불변이라고 생각한다.
- Java 라이브러리 반환값의 nullability를 확인하지 않는다.
- coroutine을 쓰면 자동으로 성능이 좋아진다고 생각한다.

## 확인 방법

- 코드 리뷰에서 nullable 타입과 non-null 타입 경계가 명확한지 확인한다.
- JPA Entity가 final class, data class, 기본 생성자 문제를 만들지 않는지 확인한다.
- Java API 호출부에서 platform type을 안전하게 처리하는지 확인한다.
- coroutine 사용부가 blocking I/O를 그대로 호출하지 않는지 확인한다.

## 핵심 요약

Kotlin은 JVM과 Java 생태계를 유지하면서 null 안정성, 간결한 DTO, 표현력 있는 컬렉션 처리, coroutine을 제공한다.

백엔드 실무에서 중요한 장점은 문법 축약보다 타입으로 오류 가능성을 줄이는 데 있다.

하지만 Java interop, JPA, Jackson, Spring proxy 같은 경계에서는 Kotlin의 언어 특성이 오히려 주의점을 만든다.

Kotlin을 도입할 때는 전체 전환보다 DTO, 테스트, 신규 모듈처럼 위험이 낮은 영역부터 시작하는 것이 현실적이다.

## 꼬리 질문

> [!question]- Kotlin을 백엔드에서 사용하는 이유는 무엇인가?
> null 안정성, data class, 컬렉션 extension, coroutine을 통해 Java 코드의 반복과 일부 런타임 오류 가능성을 줄일 수 있기 때문입니다.

> [!question]- Kotlin을 쓰면 Java가 필요 없어지는가?
> 아닙니다. Kotlin은 JVM 위에서 Java 생태계와 함께 쓰이는 경우가 많아서 Java, Spring, JPA 동작 원리를 여전히 알아야 합니다.

> [!question]- Kotlin 도입 시 가장 먼저 주의할 경계는?
> Java interop의 platform type, JPA Entity 설계, Jackson 역직렬화, Spring proxy 적용 여부를 먼저 확인해야 합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

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
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="nullable 타입, data class, 표현식 기반 문법으로 DTO와 비즈니스 로직의 의도를 명확히 하는 데 효과적이다." aria-pressed="false">A. null 가능성과 데이터 모델의 의도를 타입으로 드러낸다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Kotlin이 DB 쿼리를 자동 최적화하지는 않는다." aria-pressed="false">B. DB 인덱스 설계를 자동으로 대체한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 Java 라이브러리를 제거하는 것이 목적은 아니다." aria-pressed="false">C. Java 라이브러리를 전혀 쓰지 않는 방향으로 강제한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[kotlin]]
- [[kotlin-null-safety]]
- [[kotlin-java-interop]]
- [[01-core/java/java|java]]
