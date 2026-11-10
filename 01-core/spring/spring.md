---
title: Spring
description: Spring 핵심 개념과 실무 학습 인덱스
comments: false
---

# Spring

> 학습 인덱스다. 상세 내용은 `01-core/spring/` 아래 개념 문서에 둔다.
> 초점: 동작 원리, 실무 주의점. 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓰고, 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[why-spring|Spring을 사용하는 이유]]
2. [[ioc-and-di|IoC와 DI]]
3. [[bean-lifecycle-and-scope|Bean 생명주기와 Scope]]
4. [[aop|AOP]]
5. [[spring-mvc-request-flow|Spring MVC 요청 흐름]]
6. [[validation-and-exception-handling|Validation과 예외 처리]]
7. [[filter-interceptor-aop|Filter, Interceptor, AOP]]
8. [[transaction-integration|Transaction 연동]]
9. [[transactional-pitfalls|@Transactional 주의점]]
10. [[threadlocal-and-async-transaction|ThreadLocal과 비동기 트랜잭션]]
11. [[configuration-and-profile|Configuration과 Profile]]

## 핵심 질문

- Spring을 실무에서 왜 사용하는가?
- Spring은 객체 생성과 의존성 관리를 어떻게 해결하는가?
- Spring Bean은 언제 생성되고 어떻게 주입되는가?
- AOP는 어떤 문제를 해결하기 위해 사용하는가?
- @Transactional은 어떤 원리로 동작하고 언제 실패하는가?
- Spring MVC에서 요청은 어떤 순서로 처리되는가?
- 검증과 예외 처리는 어떤 계층에서 해야 하는가?
- Profile과 설정 관리를 어떻게 분리하는가?

## 공부할 때 기준

- annotation 이름보다 "언제, 어떤 객체(프록시, 컨테이너, DispatcherServlet)가 끼어드는가"를 설명할 수 있게 공부한다.
- 실무 장애는 대부분 Bean 주입, 프록시, 트랜잭션, 예외 처리의 경계에서 난다. 같은 클래스 안에서 호출한 `@Transactional` 메서드가 프록시를 거치지 않아 트랜잭션이 안 걸리는 게 대표적이다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview-cases/interview-questions|technical-questions]]
