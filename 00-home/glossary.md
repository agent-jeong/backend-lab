---
title: 용어집
description: 백엔드 실무에서 자주 쓰는 용어 정리
comments: false
---

# 용어집

## Java / JVM

- **Primitive Type**: 값 자체를 저장하는 타입. `int`, `long`, `boolean` 등. `null`이 될 수 없다. 지역 변수면 스택에, 객체 필드면 객체와 함께 힙에 있다. → [[primitive-and-reference-types]]
- **Reference Type**: 객체의 주소를 저장하는 타입. 힙에 할당되며 `==`는 주소 비교, `equals()`는 값 비교다. → [[primitive-and-reference-types]]
- **Boxing / Unboxing**: primitive ↔ wrapper 자동 변환. `null`을 unboxing하면 `NullPointerException`이 난다. → [[primitive-and-reference-types]]
- **equals / hashCode**: 객체 동등성 판단 기준. `hashCode`가 다르면 `HashMap`이 같은 키로 보지 않는다. → [[equals-and-hashcode]]
- **GC (Garbage Collection)**: 쓰지 않는 객체를 JVM이 자동으로 회수하는 것. STW(Stop-The-World) 동안 요청 처리가 멈춰 지연 시간에 바로 영향을 준다. → [[gc-and-tuning]]
- **OOM (OutOfMemoryError)**: 힙 메모리가 모자랄 때 나는 에러. 주된 원인은 메모리 누수, 대량 조회, 크기 제한 없는 캐시다. → [[memory-leak-and-oom]]
- **Thread Safety**: 여러 스레드가 동시에 접근해도 데이터가 깨지지 않는 상태. `synchronized`, `Atomic`, 불변 객체 등으로 지킨다. → [[java-concurrency-basics]]

## Spring

- **DI (Dependency Injection)**: 필요한 객체를 직접 만들지 않고 밖에서 주입받는 방식. 테스트와 교체가 쉬워진다. → [[ioc-and-di]]
- **Bean**: Spring 컨테이너가 만들고 관리하는 객체. 기본 scope는 singleton이다. → [[bean-lifecycle-and-scope]]
- **AOP (Aspect-Oriented Programming)**: 로깅, 트랜잭션 같은 횡단 관심사를 비즈니스 로직에서 떼어 내는 기법. Spring AOP는 프록시로 동작한다. → [[aop]]
- **Proxy**: Spring이 Bean을 감싸 부가 기능을 끼워 넣는 래퍼 객체. 같은 클래스 안에서 호출하면 프록시를 거치지 않아 `@Transactional`이 적용되지 않는다(기본 프록시 모드 기준, AspectJ 모드는 예외). → [[aop]]

## JPA / Database

- **Persistence Context**: 엔티티를 관리하는 1차 캐시. 같은 트랜잭션 안에서 같은 ID를 다시 조회하면 DB에 가지 않는다. → [[persistence-context]]
- **Dirty Checking**: 영속 상태 엔티티의 변경을 자동으로 감지해 flush 때 UPDATE를 실행하는 것. → [[dirty-checking]]
- **N+1**: 연관 엔티티를 한 건씩 조회해 쿼리 수가 1 + N으로 불어나는 문제. fetch join이나 batch size로 줄인다. → [[n-plus-one-and-fetch-join]]
- **Fetch Join**: JPQL에서 연관 엔티티를 한 번의 JOIN 쿼리로 함께 로딩하는 방법. → [[n-plus-one-and-fetch-join]]
- **Index**: 특정 컬럼 값을 정렬된 자료구조로 유지해 검색을 빠르게 하는 DB 구조. 쓰기 비용이 늘고, 선택도가 낮으면 효과가 없다. → [[db-index]]
- **Full Scan**: 인덱스를 사용하지 않고 테이블 전체를 읽는 방식. 데이터가 적으면 오히려 더 빠를 때도 있다. → [[execution-plan]]
- **Execution Plan**: DB가 쿼리를 어떤 순서와 방법으로 처리할지 보여 주는 계획. `EXPLAIN`으로 확인한다. → [[execution-plan]]

## Transaction / Concurrency

- **Transaction**: 하나의 작업 단위로 묶인 연산들. 전부 성공하거나 전부 롤백된다. → [[acid-and-isolation]]
- **ACID**: Atomicity, Consistency, Isolation, Durability. 트랜잭션이 지켜야 하는 네 가지 속성. → [[acid-and-isolation]]
- **Isolation Level**: 동시에 도는 트랜잭션끼리 서로의 데이터를 얼마나 보게 할지 정하는 수준. 실무 기본은 READ COMMITTED이고, 수준을 올리면 정합성은 높아지지만 동시성은 떨어진다. → [[acid-and-isolation]]
- **Lock**: 동시 접근을 제어하는 장치. 비관적 락은 DB에서 행을 잠그고, 낙관적 락은 버전을 비교해 충돌을 잡는다. → [[lock-and-deadlock]]
- **Deadlock**: 둘 이상의 트랜잭션이 서로가 잡은 Lock을 기다리며 영원히 멈춘 상태. → [[lock-and-deadlock]]
- **Race Condition**: 두 요청이 같은 데이터를 동시에 읽고 쓸 때 결과가 실행 순서에 따라 달라지는 문제. → [[race-condition-and-critical-section]]

## Idempotency / Reliability

- **Idempotency (멱등성)**: 같은 요청을 여러 번 보내도 결과가 바뀌지 않는 성질. 결제, 주문처럼 부작용이 있는 API에는 꼭 필요하다. → [[why-idempotency]]
- **Idempotency Key**: 중복 요청을 식별하기 위해 클라이언트가 보내는 고유 키. → [[idempotency-key]]
- **Retry**: 실패한 요청을 다시 보내는 패턴. 멱등하지 않은 API에 retry하면 중복 처리가 생긴다. → [[duplicate-request-and-retry]]
- **Circuit Breaker**: 외부 호출 실패가 반복되면 일정 시간 요청을 차단해 장애 전파를 막는 패턴. → [[retry]]

## Cache / Redis

- **Cache Aside**: 캐시에 없으면 DB에서 읽고 캐시에 넣는 전략. 가장 흔한 캐시 패턴이다. → [[cache-aside-and-ttl]]
- **TTL (Time To Live)**: 캐시 데이터의 만료 시간. TTL이 없으면 오래된 데이터가 계속 서빙된다. → [[cache-aside-and-ttl]]
- **Cache Stampede**: TTL이 만료되는 순간 많은 요청이 한꺼번에 DB를 조회해 부하가 치솟는 현상. → [[cache-aside-and-ttl]]
- **Distributed Lock**: 여러 인스턴스의 동시 접근을 막는 락. Redis의 Redisson이 대표적이다. → [[redis-distributed-lock]]

## Network

- **Timeout**: 응답을 기다리는 최대 시간. connection timeout과 read timeout을 나눠서 잡는다. → [[timeout]]
- **DNS**: 도메인을 IP 주소로 변환하는 시스템. TTL 동안 캐시되기 때문에 IP를 바꿔도 바로 반영되지 않을 수 있다. → [[dns]]
- **TLS**: 통신을 암호화하는 프로토콜. HTTPS는 HTTP + TLS다. → [[tls]]
- **CORS**: 브라우저의 동일 출처 정책을 서버가 허락한 출처에 한해 풀어 주는 장치. 서버가 응답 헤더로 허용할 출처를 알린다. → [[cors]]
- **Load Balancer**: 트래픽을 여러 서버에 분산하는 장치. L4는 TCP, L7은 HTTP 수준에서 분배한다. → [[load-balancer]]

## Observability / Operations

- **Observability (관측 가능성)**: 로그, 메트릭, 트레이스로 시스템 내부 상태를 파악하는 능력. → [[why-observability]]
- **TraceId**: 하나의 요청이 여러 서비스를 거칠 때 전체 흐름을 추적하기 위한 고유 ID. → [[trace-id-and-correlation-id]]
- **SLO (Service Level Objective)**: 서비스 품질 목표. 예: "p99 latency 200ms 이내". → [[alert-and-slo]]
- **Latency**: 요청부터 응답까지 걸리는 시간. 실무에서는 평균보다 p95, p99를 본다. → [[latency-and-throughput]]
- **Throughput**: 단위 시간당 처리하는 요청 수. TPS(Transactions Per Second)로 측정한다. → [[latency-and-throughput]]

## CI/CD / Deployment

- **CI (Continuous Integration)**: 코드가 바뀔 때마다 자동으로 빌드하고 테스트하는 파이프라인. → [[ci-vs-cd]]
- **CD (Continuous Deployment)**: 테스트를 통과한 코드를 자동으로 운영 환경에 배포하는 프로세스. → [[ci-vs-cd]]
- **Rollback**: 배포 뒤 문제가 생기면 이전 버전으로 되돌리는 절차. → [[rollback-strategy]]
- **GitOps**: Git을 단일 진실 공급원(Single Source of Truth)으로 두고 인프라와 배포를 관리하는 방식. → [[gitops]]