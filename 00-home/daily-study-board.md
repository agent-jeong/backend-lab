---
title: Daily Study Board
description: 실무 중심 백엔드 CS 학습 보드
---

# Daily Study Board

## 사용 방법

- 이미 아는 주제라도 면접 답변과 실무 체크리스트가 없으면 다시 정리한다.
- 완료한 주제의 연결 문서에 작은 개선을 남긴다.
- 실제 회사 정보는 쓰지 않고 공개 가능한 예시만 사용한다.

## 학습 주제

### Java 기초

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [[primitive-and-reference-types]] | `==`, `equals()`, wrapper null 실수 정리 | primitive type과 reference type의 차이는? |
| [[equals-and-hashcode]] | 객체 동등성 기준과 hash 컬렉션 문제 정리 | equals와 hashCode를 왜 함께 재정의하나? |
| [[collection-selection]] | List, Set, Map 선택 기준 정리 | 컬렉션은 어떤 기준으로 선택하나? |
| [[hashmap]] | List 반복 조회를 Map 조회로 바꾸는 기준 | HashMap은 언제 성능이 나빠질 수 있나? |
| [java](../01-core/java/java.md) JVM / GC | OOM, GC pause 확인 방법 | GC가 지연 시간에 영향을 주는 경우는? |

### Spring / JPA

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [spring](../01-core/spring/spring.md) DI / Bean | Bean 생성, 주입, scope 흐름 | DI는 왜 필요한가? |
| [spring](../01-core/spring/spring.md) AOP / Proxy | 프록시가 적용되지 않는 경우 | `@Transactional`이 안 먹는 경우는? |
| [jpa](../01-core/jpa/jpa.md) 영속성 컨텍스트 | 1차 캐시, dirty checking, flush | 영속성 컨텍스트의 장점과 주의점은? |
| [jpa](../01-core/jpa/jpa.md) N+1 | 쿼리 수 확인과 fetch 전략 | N+1은 왜 발생하고 어떻게 줄이나? |

### Database / Transaction

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [database](../01-core/database/database.md) Index | 선택도, 복합 인덱스 순서 | 복합 인덱스 컬럼 순서는 어떻게 정하나? |
| [database](../01-core/database/database.md) 실행 계획 | full scan, range scan, join 확인 | 실행 계획에서 무엇을 보나? |
| [transaction](../02-practical-backend/transaction/transaction.md) Isolation / Lock | 정합성 문제와 락 경합 정리 | 격리 수준은 어떤 문제를 막나? |

### 실무 백엔드

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [concurrency](../02-practical-backend/concurrency/concurrency.md) Race Condition | 동시에 들어온 요청 재현 방법 | 동시성 문제를 어떻게 재현하나? |
| [idempotency](../02-practical-backend/idempotency/idempotency.md) Retry / Key | 중복 요청 방지 흐름 | 멱등성은 어떻게 보장하나? |
| [performance](../02-practical-backend/performance/performance.md) Latency / Throughput | 병목 측정 순서 | 성능 문제를 어떤 순서로 분석하나? |
| [redis](../01-core/redis/redis.md) Cache Aside / TTL | 캐시 정합성 체크리스트 | 캐시는 어떤 문제를 만들 수 있나? |

### 인프라 / 운영

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [network](../01-core/network/network.md) Timeout / Retry | timeout, retry, circuit breaker 판단 | retry는 왜 위험할 수 있나? |
| [os](../01-core/os/os.md) Resource | CPU, memory, disk, network 병목 구분 | 서버 리소스 병목을 어떻게 확인하나? |
| [testing](../02-practical-backend/testing/testing.md) Unit / Integration | 테스트 범위 선택 기준 | 단위 테스트와 통합 테스트를 어떻게 나누나? |
| [observability](../02-practical-backend/observability/observability.md) Log / Metric / Trace | 장애 분석 순서 | 로그, 메트릭, 트레이스는 각각 무엇을 보나? |
| [ci-cd](../02-practical-backend/ci-cd/ci-cd.md) Rollback | 배포 실패 대응 절차 | 배포 실패 시 어떻게 되돌리나? |

### 사례 정리

| 주제 | 산출물 | 면접 질문 |
|---|---|---|
| [case-studies](../03-case-studies/case-studies.md) | 하나의 사례를 문제-원인-해결로 정리 | 프로젝트 경험을 어떻게 기술적으로 설명하나? |

## 학습 체크리스트

- 문제 상황을 먼저 썼는가?
- 원인을 확인하는 방법을 썼는가?
- 해결책의 한계나 부작용을 썼는가?
- 핵심 요약으로 줄였는가?
- 관련 문서 링크를 1개 이상 연결했는가?
