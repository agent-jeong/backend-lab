---
title: Kotlin
description: Kotlin 노트 목록과 읽는 순서
tags: [kotlin]
comments: false
---

# Kotlin

Kotlin을 Spring과 JPA로 만든 백엔드에서 쓸 때 부딪히는 주제만 다룬다. Java로 쓸 때보다 무엇이 줄어드는지, 그리고 Spring, JPA, Jackson과 맞물리는 곳에서 무엇이 깨지는지를 본다.

## 읽는 순서

1. [[kotlin-why-backend|Kotlin을 백엔드에서 사용하는 이유]]
2. [[kotlin-null-safety|Null Safety]]
3. [[kotlin-data-class-and-immutability|Data Class와 불변성]]
4. [[kotlin-collection-and-scope-functions|Collection과 Scope Functions]]
5. [[kotlin-java-interop|Java Interop]]
6. [[kotlin-coroutines-basics|Coroutine 기본]]

## 먼저 답해 볼 질문

- Kotlin을 Java 백엔드에 도입하면 어떤 문제가 줄어드는가?
- Kotlin null safety는 런타임 NPE를 완전히 없애는가?
- `data class`는 DTO에는 잘 맞는데 JPA Entity에는 왜 조심해서 써야 하는가?
- `val`과 immutable collection은 같은 말인가?
- scope function을 너무 많이 쓰면 왜 읽기 어려워지는가?
- Java API와 섞일 때 platform type은 어떤 위험을 만드는가?
- coroutine은 thread를 대신하는가, 아니면 다른 층의 개념인가?
- Spring MVC와 JPA로 만든 서비스에서 coroutine을 쓰면 어디서 막히는가?

## 실무에서 보는 것

- Kotlin이 좋은 건 문법이 짧아서보다, null을 타입으로 막고, 데이터 모델을 불변으로 두기 쉽고, 컬렉션 처리가 읽기 쉬워서다.
- Java와 섞인 프로젝트에서 NPE는 대부분 Java 코드에서 값을 받아 오는 자리(platform type)에서 난다.
- Spring과 JPA에서는 Kotlin의 final class, 기본 생성자 없음, `data class`가 만드는 메서드가 프레임워크가 기대하는 것과 부딪힌다.
- Coroutine은 I/O를 기다리는 작업을 적은 스레드로 돌리게 해 주지만, blocking API와 섞이면 그 이점이 사라진다.

## 관련 문서

- [[01-core/java/java|java]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
