---
title: 테스트
description: 변경 위험을 줄이는 테스트 전략 학습 인덱스
tags: [testing]
comments: false
---

# 테스트

단위·통합 테스트, Mock·Stub·Fake, 픽스처, Testcontainers, 트랜잭션 테스트를 다룬다. 어떤 위험을 어떤 테스트로 잡을지가 중심이다.

## 읽는 순서

1. [[unit-vs-integration-test|Unit Test와 Integration Test]]
2. [[mock-stub-fake|Mock, Stub, Fake]]
3. [[test-fixture|테스트 픽스처]]
4. [[transactional-test|테스트와 @Transactional]]
5. [[testcontainers|Testcontainers]]

## 먼저 답해 볼 질문

- 어떤 로직은 단위 테스트로, 어떤 로직은 통합 테스트로 검증해야 하는가?
- mock을 많이 쓰면 테스트가 통과해도 운영에서 깨지는 이유는 무엇인가?
- 테스트에 `@Transactional`을 붙이면 무엇을 검증하지 못하게 되는가?
- H2 대신 Testcontainers로 실제 DB를 띄우는 이유와 비용은 무엇인가?
- 테스트가 서로의 데이터에 영향을 받아 순서에 따라 깨질 때 어떻게 격리하는가?

## 실무에서 보는 것

- 테스트가 버그가 없다는 걸 증명해 주지는 않는다. 코드를 바꿨을 때 무엇이 깨졌는지 빨리 알려 줄 뿐이다.
- 범위가 넓은 테스트일수록 결과를 믿을 만하지만, 느려지고 고칠 일도 많아진다.
- 면접에서는 어떤 로직을 왜 단위 테스트로, 어떤 로직을 왜 통합 테스트로 나눴는지 말한다.

## 내 사례

- [[inherited-access-system-incidents|이어받은 출입 시스템의 장애 추적]]: 재현 테스트를 먼저 쓰고 변이로 테스트가 실제로 잡는지 확인

## 관련 문서

- [[02-practical-backend/concurrency/concurrency-test|concurrency-test]]
- [[02-practical-backend/transaction/spring-transaction|spring-transaction]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
