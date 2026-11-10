---
title: Testing
description: 변경 위험을 줄이는 테스트 전략 학습 인덱스
comments: false
---

# Testing

> 학습 인덱스다. 상세 내용은 `02-practical-backend/testing/` 아래 개념 문서에 둔다.
> 개념 문서는 테스트 목적, 범위, 격리, 유지보수 비용을 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. 테스트가 필요한 이유
2. [[unit-vs-integration-test|Unit Test와 Integration Test]]
3. [[mock-stub-fake|Mock과 Stub]]
4. [[test-fixture|Test Fixture]]
5. [[transactional-test|Transactional Test]]
6. [[testcontainers|Testcontainers]]
7. E2E Test

## 핵심 질문

- 어떤 로직은 단위 테스트로, 어떤 로직은 통합 테스트로 검증해야 하는가?
- mock을 많이 쓰면 테스트가 통과해도 운영에서 깨지는 이유는 무엇인가?
- 테스트에 `@Transactional`을 붙이면 무엇을 검증하지 못하게 되는가?
- H2 대신 Testcontainers로 실제 DB를 띄우는 이유와 비용은 무엇인가?
- 테스트가 서로의 데이터에 영향을 받아 순서에 따라 깨질 때 어떻게 격리하는가?

## 기준

- 테스트는 버그가 없음을 증명하지 못한다. 변경했을 때 무엇이 깨졌는지 빨리 알려 주는 장치다.
- 범위가 넓은 테스트일수록 믿을 만해지지만, 느려지고 유지보수 비용이 커진다.
- 면접에서는 어떤 로직을 왜 단위/통합 테스트로 나눴는지 말한다.

## 관련 문서

- [[02-practical-backend/concurrency/concurrency-test|concurrency-test]]
- [[02-practical-backend/transaction/spring-transaction|spring-transaction]]
- [[03-case-studies/case-studies|case-studies]]
- [[04-interview/interview-questions|technical-questions]]
