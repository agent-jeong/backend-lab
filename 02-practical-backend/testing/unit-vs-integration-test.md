---
title: Unit Test와 Integration Test
description: 테스트 범위와 신뢰도, 속도, 유지보수 비용을 나누는 기준
---

# Unit Test와 Integration Test

## 한 줄 정의

Unit Test는 작은 단위의 로직을 빠르게 검증하고, Integration Test는 여러 구성요소가 실제로 함께 동작하는지 검증한다.

## 실무에서 왜 문제 되는가

- 모든 테스트를 통합 테스트로 만들면 느리고 원인 파악이 어렵다.
- 모든 테스트를 단위 테스트로만 만들면 설정, DB, 트랜잭션, 직렬화 문제를 놓친다.
- 테스트 범위가 목적과 맞지 않으면 실패해도 무엇이 깨졌는지 알기 어렵다.
- mock이 과하면 실제 동작과 다른 테스트가 된다.

## 실무 판단 기준

| 대상 | 적절한 테스트 |
|---|---|
| 계산, 정책, 상태 전이 | Unit Test |
| Repository query, DB 제약 | Integration Test |
| Controller validation, serialization | Slice 또는 Integration Test |
| 트랜잭션, lock, 동시성 | Integration Test |
| 외부 API 실패 대응 | Mock server 또는 contract test |

## 자주 나는 실수

- Spring context가 없어도 되는 테스트에 `@SpringBootTest`를 사용한다.
- DB query를 mock으로만 검증한다.
- 단위 테스트에서 구현 세부 메서드 호출 여부만 검증한다.
- 통합 테스트 실패 원인을 파악할 로그와 fixture가 없다.

## 확인 방법

- 테스트가 실패했을 때 원인을 좁힐 수 있는 범위인지 확인한다.
- 단위 테스트는 빠르게 자주 실행되는지 본다.
- 통합 테스트는 실제 위험(DB, transaction, serialization)을 검증하는지 본다.

## 핵심 요약

단위 테스트는 빠른 피드백과 로직 검증에 적합하다.

통합 테스트는 실제 구성요소 사이의 연결과 설정 문제를 잡는다.

테스트 범위가 넓을수록 신뢰도는 높아질 수 있지만 속도와 디버깅 비용도 커진다.

DB와 트랜잭션이 핵심인 코드는 mock만으로 충분하지 않다.

테스트는 목적에 맞는 최소 범위로 작성하는 것이 유지보수에 유리하다.

## 꼬리 질문

- 단위 테스트와 통합 테스트는 무엇이 다른가?
- 어떤 로직은 단위 테스트로 충분하고 어떤 로직은 통합 테스트가 필요한가?
- `@SpringBootTest`를 남용하면 어떤 문제가 생기는가?

## 관련 문서

- [[testing]]
- [[mock-stub-fake]]
- [[testcontainers]]
