---
title: Transactional Test
description: 테스트 트랜잭션과 실제 트랜잭션 동작 차이를 이해하는 기준
---

# Transactional Test

Transactional Test는 테스트 메서드를 트랜잭션으로 감싸고, 끝나면 rollback해서 DB 상태를 정리하는 방식이다.

정리가 쉬운 대신 운영 트랜잭션과 다르게 동작한다. 테스트는 commit하지 않으니 commit 이후의 동작은 검증되지 않는다. JPA 1차 캐시 때문에 DB를 검증한다고 착각하기도 쉽다. 그래서 편해서 붙이지 말고, 검증하려는 동작의 실제 트랜잭션 경계를 보고 붙인다.

## 상황별 주의점

| 상황 | 주의점 |
|---|---|
| Repository query 검증 | flush/clear 후 조회한다 |
| after commit 이벤트 | 실제 commit이 발생하는 테스트가 필요하다 |
| 비동기 처리 | 테스트 트랜잭션과 별도 스레드 경계를 고려한다 |
| DB 제약 검증 | flush 시점에 예외가 나는지 확인한다 |

비동기, 이벤트, after commit hook은 테스트 트랜잭션 안에서 운영과 다르게 동작한다. 다른 스레드는 테스트 트랜잭션에 참여하지 않는다.

## 자주 깨지는 곳

- **저장한 뒤 같은 영속성 컨텍스트에서 다시 읽고 DB 검증이라고 생각한다.** 1차 캐시에서 읽은 값이라 DB에 무엇이 들어갔는지는 모른다.
- **commit 이후 이벤트를 rollback 테스트에서 검증한다.** commit이 없으니 이벤트도 안 일어난다.
- **unique 제약 예외가 끝까지 안 나는 이유를 놓친다.** 제약 위반은 flush 시점에 드러나는데, rollback 테스트는 flush 없이 끝날 수 있다.
- **모든 통합 테스트에 `@Transactional`을 붙인다.** 운영 흐름과 다른 것을 검증하게 된다.

## 점검할 것

- `flush`와 `clear` 후 실제 DB 조회 결과를 본다.
- commit 이후 동작은 별도 테스트에서 실제로 commit되게 구성한다.
- 제약 조건 검증은 예외가 나는 시점을 확인한다.

## 면접에서 말하기

> `@Transactional` 테스트는 rollback으로 DB 정리를 쉽게 해 주지만 실제 운영 트랜잭션과 차이를 만듭니다. JPA 1차 캐시에서 읽으면 DB를 검증한 게 아니어서 저는 flush/clear 후 다시 조회하고, DB 제약은 flush 시점에 예외가 나는지 봅니다. after commit 이벤트나 비동기 처리는 rollback 테스트에서 놓치기 쉬워 실제로 commit되는 테스트를 따로 둡니다.

## 꼬리 질문

- `@Transactional` 테스트가 운영 동작과 달라지는 경우는?
- 왜 flush/clear가 필요한가?
- after commit 이벤트는 어떻게 테스트하나?

## 관련 문서

- [[testing]]
- [[transaction-and-flush]]
- [[spring-transaction]]
