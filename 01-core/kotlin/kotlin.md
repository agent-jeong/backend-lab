---
title: Kotlin
description: Kotlin 백엔드 실무 필수 개념 학습 인덱스
comments: false
---

# Kotlin

## 운영 방식

- 이 문서는 Kotlin Core 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/kotlin/` 아래 개념별 문서로 나눈다.
- Java, Spring, JPA와 연결되는 실무 주제만 우선 정리한다.
- 문법 나열보다 null 안정성, 불변성, Java interop, coroutine의 한계를 중심으로 정리한다.

## 학습 산출물

- 다룰 Kotlin 실무 개념 하나를 고른다.
- Java와 비교했을 때 어떤 문제가 줄어드는지 먼저 쓴다.
- Spring/JPA/Jackson에서 생기는 주의점을 함께 남긴다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[kotlin-why-backend|Kotlin을 백엔드에서 사용하는 이유]]
2. [[kotlin-null-safety|Null Safety]]
3. [[kotlin-data-class-and-immutability|Data Class와 불변성]]
4. [[kotlin-collection-and-scope-functions|Collection과 Scope Functions]]
5. [[kotlin-java-interop|Java Interop]]
6. [[kotlin-coroutines-basics|Coroutine 기본]]

## 핵심 질문

- Kotlin을 Java 백엔드에 도입하면 어떤 문제가 줄어드는가?
- Kotlin null safety는 런타임 NPE를 완전히 없애는가?
- `data class`는 DTO에는 적합하지만 JPA Entity에는 왜 주의가 필요한가?
- `val`과 immutable collection은 같은 의미인가?
- scope function을 남용하면 왜 가독성이 나빠지는가?
- Java API와 섞일 때 platform type은 어떤 위험을 만드는가?
- coroutine은 thread를 대체하는가, 아니면 다른 추상화인가?
- Spring MVC/JPA 기반 서비스에서 coroutine을 쓸 때 어떤 한계가 있는가?

## 실무 관점

- Kotlin의 장점은 짧은 문법보다 null 안정성, 불변 데이터 모델, 표현력 있는 컬렉션 처리에 있다.
- Java와 함께 쓰는 프로젝트에서는 interop 경계의 nullability와 annotation 처리가 중요하다.
- Spring/JPA에서는 Kotlin의 final class, 기본 생성자, `data class` 자동 메서드가 프레임워크 요구사항과 충돌할 수 있다.
- Coroutine은 I/O 대기 작업을 효율적으로 표현하는 도구지만, blocking API와 섞이면 기대한 효과를 얻기 어렵다.

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
