---
title: Unit Test와 Integration Test
description: 테스트 범위와 신뢰도, 속도, 유지보수 비용을 나누는 기준
tags: [concept, testing]
---

# Unit Test와 Integration Test

Unit Test는 작은 단위의 로직을 빠르게 검증한다. Integration Test는 여러 구성요소가 실제로 같이 동작하는지 검증한다.

어느 한쪽만으로는 부족하다. 전부 통합 테스트로 만들면 느리고, 실패해도 어디가 깨졌는지 찾기 어렵다. 전부 단위 테스트로 만들면 설정, DB, 트랜잭션, 직렬화 문제를 놓친다. 범위는 테스트 목적에 맞는 최소한으로 잡는다.

## 무엇을 어떤 테스트로

| 대상 | 맞는 테스트 |
|---|---|
| 계산, 정책, 상태 전이 | Unit Test |
| Repository query, DB 제약 | Integration Test |
| Controller validation, serialization | Slice 또는 Integration Test |
| 트랜잭션, lock, 동시성 | Integration Test |
| 외부 API 실패 대응 | Mock server 또는 contract test |

범위가 넓을수록 믿을 만해지지만 속도와 디버깅 비용도 같이 커진다. DB와 트랜잭션이 핵심인 코드는 mock만으로는 부족하다.

## 자주 깨지는 곳

- **Spring context가 필요 없는 테스트에 `@SpringBootTest`를 쓴다.** 느려지고 실패 원인이 넓어진다.
- **DB query를 mock으로만 검증한다.** 쿼리가 실제로 맞는지는 모른다. mock이 과하면 실제와 다른 테스트가 된다.
- **단위 테스트에서 구현 세부 메서드 호출 여부만 검증한다.** 결과가 맞는지는 검증하지 않는다.
- **통합 테스트 실패 원인을 좁힐 로그와 fixture가 없다.** 깨졌다는 것만 알고 왜 깨졌는지 모른다.

## 점검할 것

- 테스트가 실패했을 때 원인을 좁힐 수 있는 범위인지 본다.
- 단위 테스트가 빨라서 자주 돌릴 수 있는지 본다.
- 통합 테스트가 실제 위험(DB, transaction, serialization)을 검증하는지 본다.

## 면접에서 말하기

> 단위 테스트는 빠른 피드백과 로직 검증에, 통합 테스트는 구성요소 사이의 연결과 설정 문제를 잡는 데 씁니다. 저는 계산이나 상태 전이는 단위 테스트로, 쿼리, DB 제약, 트랜잭션, lock은 실제 DB를 쓰는 통합 테스트로 나눕니다. 범위가 넓을수록 느리고 디버깅이 어려워지니, 목적에 맞는 가장 작은 범위로 씁니다.

## 꼬리 질문

- 단위 테스트와 통합 테스트는 무엇이 다른가?
- 어떤 로직은 단위 테스트로 충분하고 어떤 로직은 통합 테스트가 필요한가?
- `@SpringBootTest`를 남용하면 어떤 문제가 생기나?

## 관련 문서

- [[testing]]
- [[mock-stub-fake]]
- [[testcontainers]]
