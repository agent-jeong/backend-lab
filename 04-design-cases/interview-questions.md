---
title: 기술 질문
aliases:
  - 04-interview/interview-questions
  - 04-interview-cases/interview-questions
description: 자주 받는 기술 질문과, 답을 정리해 둔 개념 글 링크
tags: [design-case]
comments: false
---

# 기술 질문

## 이 목록을 쓰는 법

- 질문과 답을 외우려고 만든 목록이 아니다.
- 질문마다 짧은 답, 실무 예시, 어디서 깨지는지를 같이 정리한다.
- 직접 겪은 일과 이어지는 질문은 [[work-cases|내 실무 사례]]로 링크한다.
- 답의 근거는 개념 글 링크로 남긴다.
- 정의보다는 왜 그런지, 언제 문제가 되는지, 어떻게 판단하는지를 중심으로 정리한다.

## 답하는 순서

기술 질문에는 아래 순서로 짧게 답한다.

1. 무엇인지 한두 문장으로 말한다.
2. 어떻게 동작하는지, 어떤 흐름으로 처리되는지 말한다.
3. 실무에서 어떤 상황이 문제가 되는지 말한다.
4. 어떻게 해결하고, 그 방법에 어떤 한계가 있는지 말한다.
5. 내가 확인할 지표, 로그, 테스트를 말한다.

## 연습하는 법

| 단계 | 할 일 | 완료 기준 |
|---|---|---|
| 1 | 공부한 개념에서 질문 하나를 고른다 | 이 질문을 왜 받는지 설명할 수 있다 |
| 2 | 1분 안에 말할 답을 쓴다 | 정의, 원리, 실무 예시가 들어 있다 |
| 3 | 꼬리 질문 2개를 만든다 | 한계나 대안을 묻는 질문이 들어 있다 |
| 4 | 관련 글 링크를 붙인다 | 링크를 따라 근거 글로 갈 수 있다 |

## Java

- primitive type과 reference type의 차이는 무엇인가? [[primitive-and-reference-types]]
- equals와 hashCode를 함께 재정의해야 하는 이유는 무엇인가? [[equals-and-hashcode]]
- List, Set, Map은 각각 어떤 상황에서 선택하나요? [[collection-selection]]
- Java 버전별 차이는 무엇인가? [[java-version-features]]
- HashMap은 내부적으로 어떻게 동작하고 언제 성능이 나빠질 수 있나요? [[hashmap]]
- String을 리터럴로 할당하는 것과 new로 할당하는 것의 차이는? [[string-and-intern]]
- String의 intern() 메서드는 무엇이고 언제 유용한가? [[string-and-intern]]
- GC는 어떻게 안 쓰는 객체를 찾아내는가? (Reachability Analysis) [[gc-and-tuning]]
- GC 같은 런타임을 직접 만든다면 안 쓰는 객체를 어떻게 찾을 것인가? [[gc-and-tuning]]
- GC가 애플리케이션 지연 시간에 영향을 주는 경우를 어떻게 확인하나요? [[gc-and-tuning]]

## Spring

- Spring을 왜 사용하나요? [[why-spring]]
- DI는 왜 필요한가요? [[ioc-and-di]]
- @Transactional은 어떻게 동작하나요? [[transaction-integration]]
- @Transactional이 동작하지 않는 경우와 원인은? [[transactional-pitfalls]]
- Spring AOP가 적용되지 않는 대표적인 경우는 무엇인가요? [[aop]] [[transactional-pitfalls]]
- Filter, Interceptor, AOP의 차이와 선택 기준은? [[filter-interceptor-aop]]
- @Async에서 트랜잭션이 동작하는가? ThreadLocal과의 관계는? [[threadlocal-and-async-transaction]]
- 스레드 풀에서 ThreadLocal 누수가 발생하는 이유와 대응은? [[threadlocal-and-async-transaction]]
- Controller, Service, Repository 책임을 어떻게 나누나요? [[layered-architecture]] [[service-responsibility]]
- Boot 3로 올린 뒤 직접 만든 라이브러리의 자동 설정이 켜지지 않는다면 어디를 보나? [[spring-boot-auto-configuration]]
- 직접 등록한 `ObjectMapper` 때문에 날짜가 배열로 나간다면 원인은 무엇인가? [[spring-boot-auto-configuration]]
- 어떤 자동 설정이 켜졌는지 어떻게 확인하나? [[spring-boot-auto-configuration]]

## JPA

- JPA를 왜 사용하나요? [[why-jpa]]
- N+1은 왜 발생하나요? [[n-plus-one-and-fetch-join]]
- 영속성 컨텍스트는 어떤 이점을 주고 어떤 혼란을 만들 수 있나요? [[persistence-context]]
- flush는 언제 발생하고 성능이나 정합성에 어떤 영향을 주나요? [[transaction-and-flush]]
- OSIV란 무엇이고 왜 끄는가? [[osiv]]

## Database

- B-Tree는 어떤 자료구조이고 왜 DB 인덱스에 사용하는가? [[db-index]]
- B-Tree와 B+ Tree의 차이는 무엇인가? [[db-index]]
- 인덱스가 무엇인지 설명해 주세요. [[db-index]]
- 복합 인덱스 컬럼 순서는 어떻게 정하나요? [[db-index]]
- 정규화(1NF~3NF)란 무엇이고 반정규화는 언제 하는가? [[normalization-and-denormalization]]
- Replication과 Sharding의 차이와 도입 시점은? [[replication-and-sharding]]
- 실행 계획에서 무엇을 확인하나요? (EXPLAIN) [[execution-plan]]
- 작업이 느릴 때 어디가 느린지 탐지하고 성능을 개선하는 방법은? [[bottleneck-analysis]]
- 트랜잭션 격리 수준은 어떤 문제를 막기 위한 것인가요? [[transaction-and-isolation]]
- Deadlock이 발생하면 어떤 순서로 원인을 좁히나요? [[lock-and-deadlock]]
- CAP 정리를 "셋 중 둘을 고른다"로 설명하면 무엇이 틀렸나? [[nosql-and-cap]]
- consistent hashing은 노드를 늘릴 때 옮기는 데이터를 어떻게 줄이나? [[nosql-and-cap]]
- 데드락이 생기는 네 가지 조건 중, 실무에서는 무엇을 깨나? [[lock-and-deadlock]]

## Redis

- Redis 캐싱 적용 시 정합성 문제를 어떻게 다루나요? [[cache-aside-and-ttl]]
- Cache Aside 패턴의 장점과 한계는 무엇인가요? [[cache-aside-and-ttl]]
- Redis 장애가 나도 서비스가 계속 동작해야 한다면 어떻게 설계하나요? [[redis-failure-and-fallback]]

## Network

- 브라우저에 URL을 입력하면 응답을 받기까지 무슨 일이 일어나나? [[request-journey]]
- 사용자는 504를 받았는데 애플리케이션 로그에는 200이 찍혔다면 무슨 일인가? [[request-journey]]
- PUT과 PATCH는 어떻게 다르고, PATCH는 왜 멱등하지 않을 수 있나? [[rest-api-design]]
- offset 페이지네이션은 왜 뒤로 갈수록 느려지고, cursor는 어떻게 다른가? [[rest-api-design]]
- 서킷 브레이커의 CLOSED, OPEN, HALF_OPEN은 어떻게 바뀌나? [[circuit-breaker]]
- Retry와 서킷 브레이커는 어느 쪽을 바깥에 두나? [[circuit-breaker]]

## Performance

- 고정 윈도우 처리율 제한의 경계 문제는 무엇이고 어떻게 줄이나? [[rate-limiting]]
- 서버가 여러 대일 때 처리율 제한 카운터는 어디에 두나? [[rate-limiting]]

## Messaging

- 주문 완료 뒤 알림, 포인트, 정산을 동기 호출과 메시지 중 무엇으로 붙이나? [[message-queue-basics]]
- exactly-once를 지원하는 브로커를 쓰면 소비자 멱등성이 필요 없나? [[message-queue-basics]]
- 소비자를 늘렸는데 처리 속도가 그대로인 이유는? [[kafka-core-concepts]]
- offset을 처리 전과 처리 후 중 언제 커밋하나? 각각 무엇이 생기나? [[kafka-core-concepts]]
- `acks=all`이면 메시지를 절대 잃지 않나? [[kafka-core-concepts]]

## Security

- 인증과 인가는 어떤 차이가 있나요? [[authentication-and-authorization]]
- Session과 Token 방식은 어떤 기준으로 선택하나요? [[session-and-token]]
- 권한 검증은 Controller와 Service 중 어디에 두나요? [[authorization-check-location]]
- 비밀번호를 안전하게 저장하려면 무엇을 챙겨야 하나요? [[password-storage]]
- CSRF는 어떤 조건에서 문제가 되고 어떻게 막나요? [[csrf]]
- SQL Injection은 ORM을 써도 발생할 수 있나요? [[sql-injection]]
- 로그에 민감 정보가 남지 않게 하려면 무엇을 확인해야 하나요? [[sensitive-data-logging]]
- `permitAll`로 연 API에서 401이 나는 이유는? [[spring-security-flow]]
- 로그인하지 않은 요청이 401이 아니라 403으로 나가는 이유는? [[spring-security-flow]]
- OAuth와 OIDC는 무엇이 다르고, ID token에서 무엇을 검증하나? [[oauth2-and-oidc]]
- PKCE는 무엇을 막고, 서버 앱에도 필요한가? [[oauth2-and-oidc]]
- HttpOnly 쿠키를 쓰면 XSS가 막히나? [[xss]]
- XSS는 입력할 때 막나, 출력할 때 막나? [[xss]]

## Concurrency

- 멱등성은 어떻게 보장하나요? [[why-idempotency]] [[idempotency-key]]
- 낙관적 락과 비관적 락은 언제 각각 선택하나요? [[optimistic-lock]] [[pessimistic-lock]]
- 동시성 버그를 테스트로 어떻게 재현하나요? [[concurrency-test]]

## Batch

- Kubernetes CronJob을 왜 사용하나요? [[cronjob]]
- 실패한 배치를 재처리 가능하게 만들려면 무엇을 기록해야 하나요? [[batch-failure-state]] [[retryable-batch-design]]
- Chunk 크기는 어떤 기준으로 정하나요? [[chunk-processing]]
- 배치 중복 실행은 어떻게 막나요? [[duplicate-execution-prevention]]
- 배치 성공 여부는 어떤 지표로 판단하나요? [[batch-monitoring]]

## Architecture

- 계층을 나누는 기준은 무엇인가요? [[layered-architecture]]
- Controller, Service, Repository 책임은 어떻게 나누나요? [[service-responsibility]]
- DTO와 Entity를 분리하는 이유는 무엇인가요? [[dto-vs-entity]]
- 의존성 방향이 깨지면 어떤 문제가 생기나요? [[dependency-direction]]
- 모듈 경계는 어떤 기준으로 정하나요? [[module-boundary]]
- 결제 수단이 늘 때마다 if문이 늘어나는 코드를 어떻게 바꾸나? [[oop-design-principles]]
- 구현이 하나뿐인 Service에도 인터페이스를 만들어야 하나? [[oop-design-principles]]
- 마이크로서비스로 나누면 무엇이 비싸지나? [[monolith-and-msa]]
- 분산 모놀리스는 무엇이고 어떻게 알아보나? [[monolith-and-msa]]

## Testing

- Unit Test와 Integration Test는 어떻게 나누나요? [[unit-vs-integration-test]]
- Mock과 Stub은 무엇이 다른가요? [[mock-stub-fake]]
- Test Fixture가 복잡해지면 어떤 문제가 생기나요? [[test-fixture]]
- `@Transactional` 테스트의 주의점은 무엇인가요? [[transactional-test]]
- Testcontainers는 언제 쓰나요? [[testcontainers]]

## Kubernetes

- Deployment, Service, Ingress는 각각 어떤 문제를 해결하나요? [[deployment-service-ingress]]
- Pod가 Running인데 요청이 실패하면 무엇을 확인하나요? [[deployment-service-ingress]]
- Rolling Update 중 순간 장애를 줄이려면 어떤 설정을 확인해야 하나요? [[deployment-service-ingress]]
- Readiness Probe와 Liveness Probe는 어떻게 다른가요? [[readiness-and-liveness-probe]]
- ConfigMap과 Secret은 어떤 기준으로 나누나요? [[configmap-and-secret]]
- Resource request와 limit은 어떤 장애와 연결되나요? [[resource-request-and-limit]]
- CronJob 중복 실행은 어떻게 막나요? [[cronjob]]
- Pod가 재시작된 원인은 어떻게 확인하나요? [[kubernetes-logging-and-metrics]]
- 배포 중에 502가 몇 건씩 나는 이유와 대책은? [[graceful-shutdown]]
- terminationGracePeriodSeconds는 어떻게 정하나? [[graceful-shutdown]]

## CI/CD

- GitOps의 장점은 무엇인가요? [[gitops]]
- 배포 실패 시 롤백 전략을 어떻게 설계하나요? [[rollback-strategy]]
- CI와 CD는 무엇이 다른가요? [[ci-vs-cd]]
- Build Pipeline에서 어떤 단계를 검증해야 하나요? [[build-pipeline]]
- 배포 전략은 어떤 기준으로 선택하나요? [[deployment-strategy]]
- Rollback이 어려운 배포는 어떤 경우인가요? [[rollback-strategy]]
- Config와 Secret은 어떻게 관리해야 하나요? [[config-and-secret-management]]

## Observability

- 장애가 발생하면 어떤 순서로 원인을 좁히나요? [[incident-analysis-flow]]
- traceId는 왜 필요한가요? [[trace-id-and-correlation-id]]
- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하나요? [[why-observability]]
