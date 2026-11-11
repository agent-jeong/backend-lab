---
title: Spring
description: Spring 노트 목록과 읽는 순서
tags: [spring]
comments: false
---

# Spring

IoC와 DI, 빈 생명주기, AOP와 프록시, MVC 요청 흐름, 트랜잭션을 다룬다. 요청 하나가 들어와서 어떤 객체와 프록시를 지나 처리되는지를 따라가며 읽으면 된다.

## 읽는 순서

컨테이너 → 웹 요청 → 트랜잭션 → 설정 순서다. 글 대부분은 Spring Boot 3.x 기준이고, Boot 4에서 이름이 바뀐 곳은 글 안에 적었다.

1. [[why-spring|Spring을 사용하는 이유]]
2. [[ioc-and-di|IoC 컨테이너와 의존성 주입]]
3. [[bean-lifecycle-and-scope|Bean 생명주기와 Scope]]
4. [[aop|AOP 동작 원리와 프록시 제약]]
5. [[spring-mvc-request-flow|Spring MVC 요청 처리 흐름]]
6. [[filter-interceptor-aop|Filter vs Interceptor vs AOP]]
7. [[validation-and-exception-handling|요청 검증과 예외 처리]]
8. [[transaction-integration|@Transactional 동작 원리와 롤백]]
9. [[transactional-pitfalls|@Transactional 동작 실패 케이스]]
10. [[threadlocal-and-async-transaction|@Async와 ThreadLocal 함정]]
11. [[configuration-and-profile|설정 관리와 Profile 분리]]
12. [[spring-boot-auto-configuration|Spring Boot 자동 설정]]

## 먼저 답해 볼 질문

- Spring을 실무에서 왜 사용하는가?
- Spring은 객체 생성과 의존성 관리를 어떻게 해결하는가?
- Spring Bean은 언제 생성되고 어떻게 주입되는가?
- AOP는 어떤 문제를 풀려고 쓰는가?
- @Transactional은 어떤 원리로 동작하고 언제 실패하는가?
- Spring MVC에서 요청은 어떤 순서로 처리되는가?
- 검증과 예외 처리는 어떤 계층에서 해야 하는가?
- Profile과 설정 관리를 어떻게 분리하는가?

## 실무에서 보는 것

- annotation 이름을 외우기보다, 언제 어떤 객체가 끼어드는지를 말할 수 있게 공부한다. 끼어드는 쪽은 대개 프록시, 컨테이너, DispatcherServlet이다.
- 실무 장애는 대부분 Bean 주입, 프록시, 트랜잭션, 예외 처리의 경계에서 난다. 같은 클래스 안에서 호출한 `@Transactional` 메서드가 프록시를 거치지 않아 트랜잭션이 안 걸리는 게 대표적이다.

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: `AFTER_COMMIT` 비동기와 `REQUIRES_NEW`
- [[inherited-access-system-incidents|이어받은 출입 시스템의 장애 추적]]: `@Scheduled` 단일 스레드, `parallelStream`과 `@Transactional`

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
