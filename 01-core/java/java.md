---
title: Java
description: Java Core 학습 인덱스
comments: false
---

# Java

Java Core 학습 인덱스다. 상세 내용은 `01-core/java/` 아래 개념 문서에 있다. 각 문서는 동작 원리와 실무에서 깨지는 곳을 중심으로 쓰고, 아직 공부하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

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
3. Java 버전별 핵심 변화
   - [[stream-and-optional]]
   - [[java-version-features]]
4. Reflection과 프레임워크 기반
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

## 핵심 질문

- Java를 실무에서 왜 쓰는가?
- Java 언어 기능은 어떤 문제를 줄이려고 발전해 왔는가?
- 제네릭은 컴파일 타임 타입 안정성을 어떻게 주고, 타입 소거는 어떤 한계를 만드는가?
- JVM은 Java 코드를 어떻게 실행하는가?
- Spring, JPA, Jackson은 Reflection과 Annotation을 어디에 쓰는가?
- Java Memory Model에서 visibility, atomicity, happens-before를 왜 알아야 하는가?
- Thread를 직접 만들지 않고 thread pool과 ExecutorService를 쓰는 이유는?
- GC는 언제 성능 문제가 되는가?

## 실무에서 보는 것

- 실무 품질은 문법보다 JVM, 메모리, 컬렉션, 동시성 이해에서 갈린다. Spring, JPA, 성능 문제도 결국 여기로 내려온다.
- 버전별 기능은 외우지 말고 "어떤 코드를 더 안전하고 읽기 쉽게 만드나"로 정리한다.
- 제네릭, Reflection, Annotation을 알아야 Spring, JPA, Jackson이 어떻게 동작하는지 보인다.
- 동시성은 `Thread` API보다 실행 모델, 공유 상태, visibility, pool 관리 기준을 먼저 본다.
- GC는 대부분 기본 설정으로 충분하다. 다만 지연 시간, 처리량, 메모리 사용량 문제가 생기면 원리를 알아야 분석이 된다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[04-interview-cases/interview-questions|technical-questions]]
