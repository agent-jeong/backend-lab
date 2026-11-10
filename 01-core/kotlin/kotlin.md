---
title: Kotlin
description: Kotlin 백엔드 실무 필수 개념 학습 인덱스
comments: false
---

# Kotlin

> 학습 인덱스다. 상세 내용은 `01-core/kotlin/` 아래 개념 문서에 둔다.
> 문법 나열은 하지 않는다. Java, Spring, JPA와 맞닿는 주제만 고르고, 각 문서는 "Java 대비 무엇이 줄어드는가 → Spring/JPA/Jackson에서 무엇이 깨지는가" 순으로 쓴다.

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

## 실무에서 보는 것

- Kotlin의 장점은 짧은 문법보다 null 안정성, 불변 데이터 모델, 읽기 쉬운 컬렉션 처리에 있다.
- Java와 섞인 프로젝트에서 NPE는 대부분 interop 경계(platform type)에서 난다.
- Spring/JPA에서는 Kotlin의 final class, 기본 생성자, `data class` 자동 메서드가 프레임워크 요구사항과 부딪힌다.
- Coroutine은 I/O 대기를 적은 스레드로 표현하는 도구지만, blocking API와 섞이면 그 이점이 사라진다.

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/performance|performance]]
- [[04-interview-cases/interview-questions|technical-questions]]
