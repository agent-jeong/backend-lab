---
title: Spring
description: Spring 핵심 개념과 실무 학습 인덱스
comments: false
---

# Spring

## 운영 방식

- 이 문서는 Spring 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/spring/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 동작 원리, 실무 주의점, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-spring|Spring을 사용하는 이유]]
2. [[ioc-and-di|IoC와 DI]]
3. [[bean-lifecycle-and-scope|Bean 생명주기와 Scope]]
4. [[aop|AOP]]
5. [[spring-mvc-request-flow|Spring MVC 요청 흐름]]
6. [[validation-and-exception-handling|Validation과 예외 처리]]
7. [[transaction-integration|Transaction 연동]]
8. [[configuration-and-profile|Configuration과 Profile]]

## 핵심 질문

- Spring을 실무에서 왜 사용하는가?
- Spring은 객체 생성과 의존성 관리를 어떻게 해결하는가?
- Spring Bean은 언제 생성되고 어떻게 주입되는가?
- AOP는 어떤 문제를 해결하기 위해 사용하는가?
- @Transactional은 어떤 원리로 동작하고 언제 실패하는가?
- Spring MVC에서 요청은 어떤 순서로 처리되는가?
- 검증과 예외 처리는 어떤 계층에서 해야 하는가?
- Profile과 설정 관리를 어떻게 분리하는가?

## 실무 관점

- Spring은 프레임워크 사용법보다 객체 설계, 의존성 관리, 트랜잭션 경계 이해가 중요하다.
- annotation의 의미를 외우기보다 어떤 시점에 어떤 객체가 관여하는지 설명할 수 있어야 한다.
- 실무 문제는 대부분 Bean 주입, 프록시, 트랜잭션, 예외 처리 경계에서 발생한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
