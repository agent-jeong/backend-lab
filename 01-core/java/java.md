---
title: Java
description: Java Core 학습 인덱스
comments: false
---

# Java

## 운영 방식

- 이 문서는 Java Core 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/java/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 한 줄 정의, 동작 원리, 실무 주의점, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. Java 언어 기본기
   - [[primitive-and-reference-types]]
   - [[class-interface-enum-record]]
   - [[equals-and-hashcode]]
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
   - [[02-practical-backend/concurrency/concurrency|동시성 문제]]

## 핵심 질문

- Java를 실무에서 왜 사용하는가?
- Java 언어 기능은 어떤 문제를 줄이기 위해 발전해 왔는가?
- 제네릭은 컴파일 타임 타입 안정성을 어떻게 제공하고, 타입 소거는 어떤 한계를 만드는가?
- JVM은 Java 코드를 어떻게 실행하는가?
- Reflection과 Annotation은 Spring, JPA, Jackson에서 어떻게 사용되는가?
- Java Memory Model에서 visibility, atomicity, happens-before는 왜 중요한가?
- Thread pool과 ExecutorService는 왜 직접 Thread 생성보다 실무에 적합한가?
- GC는 언제 성능 문제가 되는가?
- 이 주제의 핵심 동작 원리는 무엇인가?
- 실무에서 자주 발생하는 문제는 무엇인가?
- 어떤 상황에서 주의해야 하는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- Java는 문법보다 JVM, 메모리, 컬렉션, 동시성 이해가 실무 품질에 더 큰 영향을 준다.
- 버전별 기능은 단순 암기보다 "어떤 코드를 더 안전하고 읽기 쉽게 만드는가"로 정리한다.
- 제네릭, Reflection, Annotation은 Spring/JPA/Jackson 같은 프레임워크 동작 원리를 이해하는 기반이다.
- Java 동시성은 `Thread` API보다 실행 모델, 공유 상태, visibility, pool 관리 기준을 중심으로 이해한다.
- GC는 대부분 기본 설정으로 충분하지만, 지연 시간, 처리량, 메모리 사용량 문제가 생기면 원리를 알아야 분석할 수 있다.
- Spring, JPA, 동시성, 성능 문제는 Java Core 이해 부족에서 시작되는 경우가 많다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
- [[04-interview/interview-questions|interview-questions]]
