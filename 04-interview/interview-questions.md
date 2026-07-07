---
title: Technical Questions
description: 기술 질문과 개념 노트 연결
comments: false
---

# Technical Questions

## 운영 방식

- 질문을 외우지 않는다.
- 질문마다 핵심 답변, 실무 예시, 주의점을 함께 정리한다.
- 프로젝트 경험과 연결할 수 있는 질문은 반드시 연결한다.
- 가능하면 개념 문서와 연결해 답변 근거를 남긴다.
- 질문은 "정의"보다 "왜", "언제 문제 되는지", "어떻게 판단하는지"를 중심으로 정리한다.

## 답변 구조

기술 답변은 아래 순서로 짧게 말한다.

1. 한 줄 정의
2. 동작 원리 또는 처리 흐름
3. 실무에서 문제가 되는 상황
4. 해결 방법과 한계
5. 내가 확인할 지표, 로그, 테스트

## 연습 방식

| 단계 | 할 일 | 완료 기준 |
|---|---|---|
| 1 | 학습한 개념에서 질문 하나를 고른다 | 질문이 왜 중요한지 설명 가능 |
| 2 | 1분 답변을 쓴다 | 정의, 원리, 실무 예시 포함 |
| 3 | 꼬리 질문 2개를 만든다 | 한계나 대안 질문 포함 |
| 4 | 관련 문서 링크를 붙인다 | 근거 문서로 이동 가능 |

## Java

- primitive type과 reference type의 차이는 무엇인가? [[primitive-and-reference-types]]
- equals와 hashCode를 함께 재정의해야 하는 이유는 무엇인가? [[equals-and-hashcode]]
- List, Set, Map은 각각 어떤 상황에서 선택하나요? [[collection-selection]]
- Java 버전별 차이는 무엇인가?
- HashMap은 내부적으로 어떻게 동작하고 언제 성능이 나빠질 수 있나요? [[hashmap]]
- String을 리터럴로 할당하는 것과 new로 할당하는 것의 차이는? [[string-and-intern]]
- String의 intern() 메서드는 무엇이고 언제 유용한가? [[string-and-intern]]
- GC는 어떻게 안 쓰는 객체를 찾아내는가? (Reachability Analysis) [[gc-and-tuning]]
- GC 같은 런타임을 직접 만든다면 안 쓰는 객체를 어떻게 찾을 것인가? [[gc-and-tuning]]
- GC가 애플리케이션 지연 시간에 영향을 주는 경우를 어떻게 확인하나요?

## Spring

- Spring을 왜 사용하나요?
- DI는 왜 필요한가요?
- @Transactional은 어떻게 동작하나요?
- @Transactional이 동작하지 않는 경우와 원인은? [[transactional-pitfalls]]
- Spring AOP가 적용되지 않는 대표적인 경우는 무엇인가요?
- Filter, Interceptor, AOP의 차이와 선택 기준은? [[filter-interceptor-aop]]
- @Async에서 트랜잭션이 동작하는가? ThreadLocal과의 관계는? [[threadlocal-and-async-transaction]]
- 스레드 풀에서 ThreadLocal 누수가 발생하는 이유와 대응은? [[threadlocal-and-async-transaction]]
- Controller, Service, Repository 책임을 어떻게 나누나요?

## JPA

- JPA를 왜 사용하나요?
- N+1은 왜 발생하나요?
- 영속성 컨텍스트는 어떤 이점을 주고 어떤 혼란을 만들 수 있나요?
- flush는 언제 발생하고 성능이나 정합성에 어떤 영향을 주나요?
- OSIV란 무엇이고 왜 끄는가? [[osiv]]

## Database

- B-Tree는 어떤 자료구조이고 왜 DB 인덱스에 사용하는가? [[db-index]]
- B-Tree와 B+ Tree의 차이는 무엇인가? [[db-index]]
- 인덱스는 어떤 기술인지 정의를 설명해주세요 [[db-index]]
- 복합 인덱스 컬럼 순서는 어떻게 정하나요? [[db-index]]
- 정규화(1NF~3NF)란 무엇이고 반정규화는 언제 하는가? [[normalization-and-denormalization]]
- Replication과 Sharding의 차이와 도입 시점은? [[replication-and-sharding]]
- 실행 계획에서 무엇을 확인하나요? (EXPLAIN) [[execution-plan]]
- 작업이 느릴 때 어디가 느린지 탐지하고 성능을 개선하는 방법은? [[bottleneck-analysis]]
- 트랜잭션 격리 수준은 어떤 문제를 막기 위한 것인가요?
- Deadlock이 발생하면 어떤 순서로 원인을 좁히나요?

## Redis

- Redis 캐싱 적용 시 정합성 문제를 어떻게 다루나요?
- Cache Aside 패턴의 장점과 한계는 무엇인가요?
- Redis 장애가 나도 서비스가 계속 동작해야 한다면 어떻게 설계하나요?

## Security

- 인증과 인가는 어떤 차이가 있나요? [[authentication-and-authorization]]
- Session과 Token 방식은 어떤 기준으로 선택하나요? [[session-and-token]]
- 권한 검증은 Controller와 Service 중 어디에 두나요? [[authorization-check-location]]
- 비밀번호를 안전하게 저장하려면 무엇을 고려해야 하나요? [[password-storage]]
- CSRF는 어떤 조건에서 문제가 되고 어떻게 막나요? [[csrf]]
- SQL Injection은 ORM을 써도 발생할 수 있나요? [[sql-injection]]
- 로그에 민감 정보가 남지 않게 하려면 무엇을 확인해야 하나요? [[sensitive-data-logging]]

## Concurrency

- 멱등성은 어떻게 보장하나요?
- 낙관적 락과 비관적 락은 언제 각각 선택하나요?
- 동시성 버그를 테스트로 어떻게 재현하나요?

## Batch

- Kubernetes CronJob을 왜 사용하나요?
- 실패한 배치를 재처리 가능하게 만들려면 무엇을 기록해야 하나요?
- Chunk 크기는 어떤 기준으로 정하나요? [[chunk-processing]]
- 배치 중복 실행은 어떻게 막나요? [[duplicate-execution-prevention]]
- 배치 성공 여부는 어떤 지표로 판단하나요? [[batch-monitoring]]

## Architecture

- 계층을 나누는 기준은 무엇인가요? [[layered-architecture]]
- Controller, Service, Repository 책임은 어떻게 나누나요? [[service-responsibility]]
- DTO와 Entity를 분리하는 이유는 무엇인가요? [[dto-vs-entity]]
- 의존성 방향이 깨지면 어떤 문제가 생기나요? [[dependency-direction]]
- 모듈 경계는 어떤 기준으로 정하나요? [[module-boundary]]

## Testing

- Unit Test와 Integration Test는 어떻게 나누나요? [[unit-vs-integration-test]]
- Mock과 Stub은 무엇이 다른가요? [[mock-stub-fake]]
- Test Fixture가 복잡해지면 어떤 문제가 생기나요? [[test-fixture]]
- `@Transactional` 테스트의 주의점은 무엇인가요? [[transactional-test]]
- Testcontainers는 언제 사용하는 것이 적절한가요? [[testcontainers]]

## Kubernetes

- Deployment, Service, Ingress는 각각 어떤 문제를 해결하나요? [[deployment-service-ingress]]
- Pod가 Running인데 요청이 실패하면 무엇을 확인하나요? [[deployment-service-ingress]]
- Rolling Update 중 순간 장애를 줄이려면 어떤 설정을 확인해야 하나요? [[deployment-service-ingress]]
- Readiness Probe와 Liveness Probe는 어떻게 다른가요? [[readiness-and-liveness-probe]]
- ConfigMap과 Secret은 어떤 기준으로 나누나요? [[configmap-and-secret]]
- Resource request와 limit은 어떤 장애와 연결되나요? [[resource-request-and-limit]]
- CronJob 중복 실행은 어떻게 막나요? [[cronjob]]
- Pod가 재시작된 원인은 어떻게 확인하나요? [[kubernetes-logging-and-metrics]]

## CI/CD

- GitOps의 장점은 무엇인가요?
- 배포 실패 시 롤백 전략을 어떻게 설계하나요?
- CI와 CD는 무엇이 다른가요? [[ci-vs-cd]]
- Build Pipeline에서 어떤 단계를 검증해야 하나요? [[build-pipeline]]
- 배포 전략은 어떤 기준으로 선택하나요? [[deployment-strategy]]
- Rollback이 어려운 배포는 어떤 경우인가요? [[rollback-strategy]]
- Config와 Secret은 어떻게 관리해야 하나요? [[config-and-secret-management]]

## Observability

- 장애가 발생하면 어떤 순서로 원인을 좁히나요?
- traceId는 왜 필요한가요?
- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하나요?
