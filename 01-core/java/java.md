---
title: Java
description: 타입, 컬렉션, JVM, 동시성, GC를 어떤 순서로 읽으면 되는지 모아 둔 목록
tags: [java]
comments: false
---

# Java

타입과 컬렉션, JVM 메모리와 GC, 동시성 기초를 다룬다. 문법 자체보다, 어떤 선택이 어떤 버그나 성능 문제로 이어지는지를 주로 적었다.

## 읽는 순서

1. Java 언어 기본기
   - [[primitive-and-reference-types]]
   - [[class-interface-enum-record]]
   - [[equals-and-hashcode]]
   - [[string-and-intern]]
   - [[exception-handling]]
   - [[generics-and-type-erasure]]
2. Java 컬렉션
   - [[collection-selection]]
   - [[hashmap]]
   - [[sorting-dedup-search-cost]]
3. Java 버전별 주요 변화
   - [[stream-and-optional]]
   - [[java-version-features]]
4. 프레임워크가 쓰는 Reflection
   - [[reflection-and-annotation]]
5. JVM 기본 구조
   - [[jvm-memory-structure]]
6. Java 동시성 기본
   - [[java-concurrency-basics]]
   - [[java-memory-model]]
7. GC
   - [[gc-and-tuning]]
8. 실무 연결
   - [[memory-leak-and-oom]]
   - [[serialization-and-jackson]]
   - [[concurrency|동시성 문제]]

## 먼저 답해 볼 질문

- Java를 실무에서 왜 쓰는가?
- Java 언어 기능은 어떤 문제를 줄이려고 바뀌어 왔는가?
- 제네릭은 컴파일할 때 타입을 어떻게 검사해 주고, 타입 소거 때문에 무엇을 못 하게 되는가?
- JVM은 Java 코드를 어떻게 실행하는가?
- Spring, JPA, Jackson은 Reflection과 Annotation을 어디에 쓰는가?
- Java Memory Model에서 visibility, atomicity, happens-before를 왜 알아야 하는가?
- Thread를 직접 만들지 않고 thread pool과 ExecutorService를 쓰는 이유는?
- GC는 언제 성능 문제가 되는가?

## 실무에서 보는 것

- 실무에서 코드 품질은 문법보다 JVM, 메모리, 컬렉션, 동시성을 얼마나 아는지에서 갈린다. Spring, JPA, 성능 문제도 따라 내려가면 결국 여기서 만난다.
- 버전별 기능은 외우기보다 "어떤 코드를 더 안전하고 읽기 쉽게 만드는가"로 정리한다.
- 제네릭, Reflection, Annotation을 알면 Spring, JPA, Jackson이 안에서 어떻게 돌아가는지 보인다.
- 동시성은 `Thread` API보다 실행 모델, 공유 상태, visibility, pool을 어떻게 관리하는지를 먼저 본다.
- GC는 대부분 기본 설정으로 충분하다. 다만 응답이 늦어지거나 처리량이 떨어지거나 메모리를 많이 쓰기 시작하면, 원리를 알아야 원인을 찾을 수 있다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[04-design-cases/interview-questions|technical-questions]]
