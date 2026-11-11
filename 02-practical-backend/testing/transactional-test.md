---
title: 테스트와 @Transactional
description: 테스트에 @Transactional을 붙였을 때 운영 트랜잭션과 무엇이 달라지는지
tags: [concept, testing]
---

# 테스트와 @Transactional

테스트 메서드에 `@Transactional`을 붙이면 테스트 전체가 트랜잭션 하나로 감싸지고, 끝나면 rollback돼서 DB가 원래대로 돌아간다.

정리하기는 편하지만 운영 트랜잭션과 다르게 움직인다. 테스트는 commit하지 않으니 commit 이후에 일어나는 일은 확인되지 않는다. 주문을 저장하고 다시 읽었을 때 JPA 1차 캐시에서 값이 나와서 DB를 확인했다고 착각하기도 쉽다. 그래서 편하다고 붙이지 말고, 확인하려는 동작이 실제로 어떤 트랜잭션 안에서 도는지 보고 붙인다.

## 상황별 주의점

| 상황 | 주의점 |
|---|---|
| Repository query 검증 | flush/clear 후 조회한다 |
| after commit 이벤트 | 실제 commit이 발생하는 테스트가 필요하다 |
| 비동기 처리 | 테스트 트랜잭션과 별도 스레드 경계를 고려한다 |
| DB 제약 검증 | flush 시점에 예외가 나는지 확인한다 |

비동기 처리, 이벤트, after commit hook은 테스트 트랜잭션 안에서 운영과 다르게 동작한다. 다른 스레드는 테스트 트랜잭션에 참여하지 않는다.

## 자주 깨지는 곳

- 저장한 뒤 같은 영속성 컨텍스트에서 다시 읽고 DB를 확인했다고 여기면 틀린다. 1차 캐시에서 읽은 값이라 DB에 무엇이 들어갔는지는 모른다.
- commit 이후 이벤트를 rollback 테스트에서 확인하려 하면, commit이 없으니 이벤트도 일어나지 않는다.
- unique 제약 예외가 끝까지 안 나는 이유를 놓치기 쉽다. 제약 위반은 flush할 때 드러나는데, rollback 테스트는 flush 없이 끝날 수 있다.
- 모든 통합 테스트에 `@Transactional`을 붙이면, 운영 흐름과 다른 것을 확인하게 된다.

## 점검할 것

- `flush`와 `clear` 후 실제 DB 조회 결과를 본다.
- commit 이후 동작은 별도 테스트에서 실제로 commit되게 구성한다.
- 제약 조건 검증은 예외가 나는 시점을 확인한다.

## 한 번에 설명하기

> `@Transactional` 테스트는 rollback으로 DB를 쉽게 정리해 주지만, 실제 운영 트랜잭션과는 다르게 동작합니다.
>
> JPA 1차 캐시에서 읽으면 DB를 확인한 게 아니라서 flush/clear 후 다시 조회하고, DB 제약은 flush할 때 예외가 나는지 봅니다.
>
> after commit 이벤트나 비동기 처리는 rollback 테스트에서 놓치기 쉬워서, 실제로 commit되는 테스트를 따로 둡니다.

## 꼬리 질문

- `@Transactional` 테스트가 운영 동작과 달라지는 경우는?
- 왜 flush/clear가 필요한가?
- after commit 이벤트는 어떻게 테스트하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Transaction Management in Tests](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/tx.html)

## 관련 문서

- [[testing]]
- [[transaction-and-flush]]
- [[spring-transaction]]
