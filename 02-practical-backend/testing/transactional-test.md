---
title: Transactional Test
description: 테스트 트랜잭션과 실제 트랜잭션 동작 차이를 이해하는 기준
---

# Transactional Test

## 한 줄 정의

Transactional Test는 테스트 메서드를 트랜잭션으로 감싸고 종료 시 rollback해 DB 상태를 정리하는 방식이다.

## 실무에서 왜 문제 되는가

- 테스트 트랜잭션 때문에 실제 commit 이후 동작을 놓칠 수 있다.
- 영속성 컨텍스트 1차 캐시 때문에 DB에 반영된 상태를 확인하지 못할 수 있다.
- 비동기, 이벤트, after commit hook은 테스트 트랜잭션 안에서 다르게 동작할 수 있다.
- rollback 편의성 때문에 실제 운영 흐름과 다른 검증을 할 수 있다.

## 실무 판단 기준

| 상황 | 주의점 |
|---|---|
| Repository query 검증 | flush/clear 후 조회한다 |
| after commit 이벤트 | 실제 commit이 발생하는 테스트가 필요하다 |
| 비동기 처리 | 테스트 트랜잭션과 별도 스레드 경계를 고려한다 |
| DB 제약 검증 | flush 시점에 예외가 나는지 확인한다 |

## 자주 나는 실수

- 저장 후 같은 영속성 컨텍스트에서 다시 읽고 DB 검증이라고 생각한다.
- commit 이후 발생하는 이벤트를 rollback 테스트에서 검증한다.
- unique 제약 예외가 테스트 끝까지 발생하지 않는 이유를 놓친다.
- 모든 통합 테스트에 무조건 `@Transactional`을 붙인다.

## 확인 방법

- `flush`와 `clear` 후 실제 DB 조회 결과를 확인한다.
- commit 이후 동작은 별도 테스트에서 명시적으로 commit되게 구성한다.
- 제약 조건 검증은 예외 발생 시점을 확인한다.

## 핵심 요약

Transactional Test는 DB 정리를 쉽게 하지만 실제 운영 트랜잭션과 차이를 만든다.

JPA 1차 캐시 때문에 DB 상태를 검증한다고 착각할 수 있다.

DB 제약은 flush 시점에 드러날 수 있다.

after commit 이벤트와 비동기는 rollback 테스트에서 놓치기 쉽다.

편의성보다 검증하려는 동작의 실제 경계를 기준으로 사용해야 한다.

## 꼬리 질문

- `@Transactional` 테스트가 실제 운영 동작과 달라지는 경우는 무엇인가?
- 왜 flush/clear가 필요한가?
- after commit 이벤트는 어떻게 테스트할 것인가?

## 관련 문서

- [[testing]]
- [[transaction-and-flush]]
- [[spring-transaction]]
