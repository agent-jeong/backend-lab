---
title: Testcontainers
description: 실제 인프라에 가까운 통합 테스트 환경을 코드로 구성하는 기준
---

# Testcontainers

## 한 줄 정의

Testcontainers는 테스트 실행 중 Docker container로 DB, Redis, 메시지 브로커 같은 의존성을 띄워 실제 환경에 가까운 통합 테스트를 가능하게 하는 도구다.

## 실무에서 왜 문제 되는가

- 인메모리 DB는 운영 DB와 SQL 문법, lock, transaction 동작이 다를 수 있다.
- 로컬 공유 DB를 쓰면 테스트 간 간섭과 환경 의존성이 생긴다.
- 실제 Redis, DB 제약, migration을 검증하지 않으면 운영에서만 실패할 수 있다.
- container 기반 테스트는 느리고 CI 설정이 필요하다.

## 실무 판단 기준

| 대상 | Testcontainers 적합도 |
|---|---|
| DB dialect, migration | 높음 |
| Redis TTL, command 동작 | 높음 |
| 단순 계산 로직 | 낮음 |
| 외부 SaaS API | mock server가 더 적합할 수 있음 |

## 자주 나는 실수

- 모든 테스트를 Testcontainers로 만들어 느리게 만든다.
- container 초기화 비용을 고려하지 않는다.
- 테스트 데이터 정리 전략 없이 공유 container를 사용한다.
- CI 환경에서 Docker 사용 가능 여부를 확인하지 않는다.

## 확인 방법

- 운영 DB와 같은 major version을 사용하는지 확인한다.
- migration이 테스트 시작 시 적용되는지 확인한다.
- CI에서 안정적으로 실행되는지 확인한다.

## 핵심 요약

Testcontainers는 실제 인프라에 가까운 통합 테스트를 제공한다.

DB dialect, migration, lock, transaction 검증에 특히 유용하다.

인메모리 DB와 운영 DB 차이로 생기는 오류를 줄일 수 있다.

속도와 CI 환경 비용이 있으므로 모든 테스트에 적용할 필요는 없다.

테스트 데이터 격리와 container 재사용 전략을 함께 정해야 한다.

## 꼬리 질문

- 인메모리 DB 테스트의 한계는 무엇인가?
- Testcontainers는 어떤 테스트에 적합한가?
- CI에서 Testcontainers를 사용할 때 무엇을 확인해야 하는가?

## 관련 문서

- [[testing]]
- [[unit-vs-integration-test]]
- [[database]]
