---
title: Mastery Map
description: 백엔드 엔지니어링 학습 주제와 목표 숙련도 지도
---

# Mastery Map

## 운영 방식

“개념 이해”가 아니라 “실무에서 어떻게 판단할지”를 남기는 것이 목표다.

| 활동 | 목표 | 산출물 |
|---|---|---|
| 개념 학습 | 한 개념을 실무 문제와 연결 | 개념 문서 1개 보강 |
| 면접 압축 | 면접 질문으로 압축 | [interview-questions](../04-interview/interview-questions.md) 답변 1개 |
| 사례 정리 | 사례로 재구성 | [case-studies](../03-case-studies/case-studies.md) 항목 1개 보강 |
| 레벨 점검 | 부족한 영역 재배치 | 현재 레벨 업데이트 |

## 숙련도 기준

| 단계 | 기준 |
|---|---|
| L0 | 들어본 적만 있음 |
| L1 | 한 줄 정의 가능 |
| L2 | 동작 순서와 내부 원리 설명 가능 |
| L3 | 실무 문제, 장애 양상, 해결책 설명 가능 |
| L4 | 프로젝트 경험 또는 일반화된 사례와 연결해 면접 답변 가능 |
| L5 | 트레이드오프와 대안을 비교해 설명 가능 |

## Core

| 영역 | 먼저 공부할 주제 | 실무 연결 질문 | 목표 | 연결 문서 |
|---|---|---|---:|---|
| Java | primitive/reference, collection, JVM, GC | 타입/메모리/컬렉션 선택이 어떤 버그와 성능 문제를 만드는가? | L4 | [java](../01-core/java/java.md) |
| Kotlin | null safety, data class, interop, coroutine | Java/Spring/JPA 경계에서 어떤 장점과 한계가 생기는가? | L3 | [kotlin](../01-core/kotlin/kotlin.md), [java](../01-core/java/java.md) |
| Spring | DI, Bean, AOP, MVC, Transaction | 요청 하나가 어떤 객체와 프록시를 지나 처리되는가? | L5 | [spring](../01-core/spring/spring.md), [transaction](../02-practical-backend/transaction/transaction.md) |
| JPA | 영속성 컨텍스트, flush, fetch 전략, N+1 | 쿼리 수와 트랜잭션 경계를 어떻게 확인하는가? | L5 | [jpa](../01-core/jpa/jpa.md), [performance](../02-practical-backend/performance/performance.md) |
| Database | index, execution plan, lock, isolation | 느린 쿼리와 정합성 문제를 어떤 순서로 좁히는가? | L5 | [database](../01-core/database/database.md), [transaction](../02-practical-backend/transaction/transaction.md) |
| Redis | TTL, cache aside, invalidation, 장애 대응 | 캐시가 정합성과 장애 전파에 어떤 비용을 만드는가? | L4 | [redis](../01-core/redis/redis.md) |
| Network | HTTP, DNS, TCP, timeout, retry | 외부 API 장애를 어느 구간부터 의심하는가? | L4 | [network](../01-core/network/network.md) |
| OS | process/thread, memory, I/O, resource monitoring | 애플리케이션 문제가 서버 리소스 병목인지 어떻게 구분하는가? | L4 | [os](../01-core/os/os.md) |

## Practical Backend

| 영역 | 먼저 공부할 주제 | 실무 연결 질문 | 목표 | 연결 문서 |
|---|---|---|---:|---|
| Transaction | ACID, isolation, lock, external API boundary | 정합성과 락 경합 사이에서 어디에 경계를 둘 것인가? | L5 | [transaction](../02-practical-backend/transaction/transaction.md) |
| Concurrency | race condition, lock, unique constraint | 같은 요청이 동시에 들어오면 어떤 데이터가 깨지는가? | L5 | [concurrency](../02-practical-backend/concurrency/concurrency.md) |
| Idempotency | retry, idempotency key, state transition | 중복 요청과 재처리가 결과를 바꾸지 않게 하려면? | L5 | [idempotency](../02-practical-backend/idempotency/idempotency.md) |
| Performance | latency, throughput, DB, cache, load test | 병목을 측정하고 개선 전후를 어떻게 증명하는가? | L5 | [performance](../02-practical-backend/performance/performance.md) |
| Observability | log, metric, trace, alert | 장애가 나기 전에 어떤 신호를 남길 것인가? | L4 | [observability](../02-practical-backend/observability/observability.md) |
| Architecture | layer, dependency, module, transaction boundary | 변경이 잦은 요구사항을 어느 책임에 둘 것인가? | L4 | [architecture](../02-practical-backend/architecture/architecture.md) |
| Batch | scheduling, chunk, retry, monitoring | 실패한 배치를 어디서부터 다시 처리할 수 있는가? | L4 | [batch-processing](../02-practical-backend/batch/batch-processing.md) |
| Security | authn/authz, token, CORS, injection, logging | 권한 누락과 민감 정보 노출을 어디서 막는가? | L4 | [security](../02-practical-backend/security/security.md) |
| Testing | unit, integration, fixture, test container | 어떤 위험을 어떤 테스트로 막을 것인가? | L4 | [testing](../02-practical-backend/testing/testing.md) |
| CI/CD | pipeline, rollback, config, secret, GitOps | 배포 실패를 어떻게 빠르게 되돌릴 것인가? | L4 | [ci-cd](../02-practical-backend/ci-cd/ci-cd.md) |

## 운영 방법

- 현재 레벨은 매주 한 번만 업데이트한다.
- 한 번에 L5를 목표로 하지 않는다. L2까지는 원리, L3부터는 실무 문제, L4부터는 면접 답변을 남긴다.
- L3 이상 문서에는 반드시 실패 사례, 검증 방법, 한계가 있어야 한다.
- 실제 회사 정보는 쓰지 않고 `order`, `payment`, `user`, `example-service` 같은 일반 이름만 사용한다.
