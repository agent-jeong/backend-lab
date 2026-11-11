---
title: Testcontainers
description: 실제 DB나 Redis를 Docker로 띄워 운영에 가까운 통합 테스트를 하는 방법과 비용
tags: [concept, testing]
---

# Testcontainers

Testcontainers는 테스트를 돌리는 동안 DB, Redis, 메시지 브로커 같은 의존성을 Docker container로 띄워 주는 도구다. 운영과 같은 종류의 인프라를 놓고 통합 테스트를 할 수 있다.

인메모리 DB는 운영 DB와 SQL 문법, lock, transaction 동작이 다르다. 로컬에 띄워 둔 공유 DB는 테스트끼리 서로 간섭하고 개발자 환경마다 결과가 달라진다. 실제 Redis 동작, DB 제약, migration을 테스트에서 확인하지 않으면 운영에서만 실패하는 코드가 나온다. Testcontainers는 이 차이를 줄이고, 그 대가로 테스트가 느려지고 CI 설정이 늘어난다.

## 어디에 맞나

| 대상 | Testcontainers 적합도 |
|---|---|
| DB dialect, migration | 높음 |
| Redis TTL, command 동작 | 높음 |
| 단순 계산 로직 | 낮음 |
| 외부 SaaS API | mock server가 더 적합할 수 있음 |

DB dialect, migration, lock, transaction을 확인할 때 특히 쓸모 있다. 모든 테스트에 쓸 필요는 없다.

## 자주 깨지는 곳

- 모든 테스트를 Testcontainers로 만들면, 테스트가 느려져서 자주 돌리지 않게 된다.
- container를 띄우는 시간을 따져 보지 않으면, 테스트 클래스마다 container를 새로 띄우느라 시간이 쌓인다.
- 데이터를 어떻게 지울지 정하지 않고 container를 같이 쓰면, 테스트끼리 간섭한다. 데이터 격리와 container 재사용 방법은 함께 정한다.
- CI에서 Docker를 쓸 수 있는지 확인하지 않으면, 로컬에서만 돌고 CI에서 깨진다.

## 점검할 것

- 운영 DB와 같은 major version을 쓰는지 확인한다.
- 테스트 시작 때 migration이 적용되는지 확인한다.
- CI에서 매번 깨지지 않고 도는지 확인한다.

## 한 번에 설명하기

> Testcontainers는 실제 DB나 Redis를 container로 띄워서 운영에 가까운 통합 테스트를 하게 해 주는 도구입니다.
>
> 인메모리 DB와 운영 DB는 문법, lock, 트랜잭션 동작이 달라서 거기서 생기는 오류를 테스트에서 놓칩니다. 그래서 DB dialect, migration, lock을 확인할 때 씁니다.
>
> 대신 느리고 CI 비용이 들어서 단순 로직에는 쓰지 않고, 데이터 격리와 container 재사용 방법을 같이 정합니다.

## 꼬리 질문

- 인메모리 DB 테스트의 한계는?
- Testcontainers는 어떤 테스트에 맞나?
- CI에서 Testcontainers를 쓸 때 무엇을 확인하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Testcontainers for Java](https://java.testcontainers.org/)
- [Spring Boot: Testcontainers](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)

## 관련 문서

- [[02-practical-backend/testing/testing|testing]]
- [[unit-vs-integration-test]]
- [[01-core/database/database|database]]
