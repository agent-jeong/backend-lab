---
title: 용어집
description: 이 블로그에 자주 나오는 백엔드 용어와, 그 용어를 다룬 글
comments: false
---

# 용어집

## Java / JVM

- **Primitive Type**: 값을 그대로 담는 타입. `int`, `long`, `boolean` 같은 것이다. `null`이 될 수 없다. 지역 변수면 스택에, 객체 필드면 객체와 함께 힙에 있다. → [[primitive-and-reference-types]]
- **Reference Type**: 객체의 주소를 담는 타입. 객체는 힙에 만들어지고, `==`는 주소 비교, `equals()`는 값 비교다. → [[primitive-and-reference-types]]
- **Boxing / Unboxing**: primitive와 wrapper 사이를 자동으로 바꿔 주는 것. `null`을 unboxing하면 `NullPointerException`이 난다. → [[primitive-and-reference-types]]
- **equals / hashCode**: 두 객체를 같다고 볼지 정하는 메서드. `hashCode`가 다르면 `HashMap`이 같은 키로 보지 않는다. → [[equals-and-hashcode]]
- **GC (Garbage Collection)**: 쓰지 않는 객체를 JVM이 자동으로 회수하는 것. STW(Stop-The-World) 동안에는 요청 처리가 멈추기 때문에 응답 시간이 바로 늘어난다. → [[gc-and-tuning]]
- **OOM (OutOfMemoryError)**: 힙 메모리가 모자랄 때 나는 에러. 흔한 원인은 메모리 누수, 한 번에 너무 많이 읽는 조회, 크기 제한 없는 캐시다. → [[memory-leak-and-oom]]
- **Thread Safety**: 여러 스레드가 동시에 건드려도 데이터가 깨지지 않는 상태. `synchronized`, `Atomic`, 불변 객체 같은 방법으로 지킨다. → [[java-concurrency-basics]]

## Spring

- **DI (Dependency Injection)**: 필요한 객체를 직접 만들지 않고 밖에서 넣어 받는 방식. 테스트할 때 가짜로 바꾸거나 구현을 교체하기 쉬워진다. → [[ioc-and-di]]
- **Bean**: Spring 컨테이너가 만들고 관리하는 객체. 기본 scope는 singleton이다. → [[bean-lifecycle-and-scope]]
- **AOP (Aspect-Oriented Programming)**: 로깅, 트랜잭션처럼 여러 곳에 공통으로 들어가는 코드(횡단 관심사)를 비즈니스 로직에서 떼어 내는 방법. Spring AOP는 프록시로 동작한다. → [[aop]]
- **Proxy**: Spring이 Bean을 감싸서 트랜잭션 같은 부가 기능을 끼워 넣는 객체. 같은 클래스 안에서 호출하면 프록시를 거치지 않아 `@Transactional`이 적용되지 않는다(기본 프록시 모드 기준, AspectJ 모드는 예외). → [[aop]]

## JPA / Database

- **Persistence Context**: JPA가 엔티티를 담아 두고 관리하는 공간이고, 1차 캐시로도 쓰인다. 같은 트랜잭션 안에서 같은 ID를 다시 조회하면 DB에 가지 않는다. → [[persistence-context]]
- **Dirty Checking**: 영속 상태 엔티티의 값이 바뀌면 JPA가 알아채고 flush 때 UPDATE를 날리는 것. → [[dirty-checking]]
- **N+1**: 연관 엔티티를 한 건씩 조회해 쿼리 수가 1 + N으로 불어나는 문제. fetch join이나 batch size로 줄인다. → [[n-plus-one-and-fetch-join]]
- **Fetch Join**: JPQL에서 연관 엔티티를 JOIN 쿼리 한 번으로 같이 가져오는 방법. → [[n-plus-one-and-fetch-join]]
- **Index**: 컬럼 값을 정렬된 자료구조로 따로 들고 있어서 검색을 빠르게 해 주는 DB 구조. 대신 쓰기가 느려지고, 선택도가 낮은 컬럼에서는 효과가 없다. → [[db-index]]
- **Full Scan**: 인덱스를 타지 않고 테이블 전체를 읽는 방식. 데이터가 적으면 오히려 더 빠를 때도 있다. → [[execution-plan]]
- **Execution Plan**: DB가 쿼리를 어떤 순서로, 어떤 방법으로 처리할지 정한 계획. `EXPLAIN`으로 확인한다. → [[execution-plan]]

## Transaction / Concurrency

- **Transaction**: 하나로 묶은 여러 작업. 전부 반영되거나 전부 롤백된다. → [[acid-and-isolation]]
- **ACID**: Atomicity, Consistency, Isolation, Durability. 트랜잭션이 지켜야 하는 네 가지 속성. → [[acid-and-isolation]]
- **Isolation Level**: 동시에 도는 트랜잭션끼리 서로의 데이터를 얼마나 보게 할지 정하는 수준. 기본값은 DB마다 다르다(MySQL InnoDB는 REPEATABLE READ, PostgreSQL은 READ COMMITTED). 수준을 올리면 정합성은 높아지지만 동시성은 떨어진다. → [[acid-and-isolation]]
- **Lock**: 여러 요청이 같은 데이터를 동시에 건드리지 못하게 막는 장치. 비관적 락은 DB에서 행을 잠그고, 낙관적 락은 버전을 비교해 충돌을 잡는다. → [[lock-and-deadlock]]
- **Deadlock**: 둘 이상의 트랜잭션이 서로가 잡은 Lock을 기다리며 영원히 멈춘 상태. → [[lock-and-deadlock]]
- **Race Condition**: 두 요청이 같은 데이터를 동시에 읽고 쓸 때 결과가 실행 순서에 따라 달라지는 문제. → [[race-condition-and-critical-section]]
- **MVCC**: 데이터의 옛 버전을 남겨 두고, 읽는 쪽은 락 없이 자기 시점의 버전을 보게 하는 방식. 그래서 일반 SELECT와 UPDATE가 서로를 기다리지 않는다. → [[transaction-and-isolation]]
- **Outbox**: DB 변경과 "보낼 이벤트" 기록을 같은 트랜잭션에 저장하고, 발행은 따로 하는 패턴. 이벤트 유실은 막지만 중복은 생길 수 있다. → [[compensation-and-outbox]]

## Idempotency / Reliability

- **Idempotency (멱등성)**: 같은 요청을 여러 번 보내도 한 번 보낸 것과 결과가 같은 성질. 결제, 주문처럼 부작용이 있는 API에는 꼭 필요하다. → [[why-idempotency]]
- **Idempotency Key**: 같은 요청이 다시 왔는지 알아보려고 클라이언트가 함께 보내는 고유 키. → [[idempotency-key]]
- **Retry**: 실패한 요청을 다시 보내는 패턴. 멱등하지 않은 API에 retry하면 중복 처리가 생긴다. → [[duplicate-request-and-retry]]
- **Circuit Breaker**: 외부 호출이 계속 실패하면 한동안 호출을 아예 막아서, 장애가 내 서비스로 번지지 않게 하는 패턴. → [[circuit-breaker]]

## Cache / Redis

- **Cache Aside**: 캐시에 없으면 DB에서 읽고 캐시에 넣어 두는 방식. 가장 흔하게 쓰는 캐시 패턴이다. → [[cache-aside-and-ttl]]
- **TTL (Time To Live)**: 캐시 데이터의 만료 시간. TTL이 없으면 바뀌기 전 데이터가 계속 나간다. → [[cache-aside-and-ttl]]
- **Cache Stampede**: TTL이 만료되는 순간 많은 요청이 한꺼번에 DB를 조회해 부하가 치솟는 현상. → [[cache-aside-and-ttl]]
- **Distributed Lock**: 서버 여러 대가 같은 자원을 동시에 건드리지 못하게 막는 락. Redis 기반의 Redisson을 많이 쓴다. → [[redis-distributed-lock]]

## Network

- **Timeout**: 응답을 기다리는 최대 시간. connection timeout과 read timeout을 나눠서 잡는다. → [[timeout]]
- **DNS**: 도메인을 IP 주소로 바꿔 주는 시스템. 결과가 TTL 동안 캐시되기 때문에 IP를 바꿔도 바로 반영되지 않을 수 있다. → [[dns]]
- **TLS**: 통신을 암호화하는 프로토콜. HTTPS는 HTTP + TLS다. → [[tls]]
- **CORS**: 브라우저의 동일 출처 정책을 서버가 허락한 출처에 한해 풀어 주는 장치. 서버가 응답 헤더로 허용할 출처를 알린다. → [[cors]]
- **Load Balancer**: 들어온 트래픽을 여러 서버에 나눠 보내는 장치. L4는 TCP, L7은 HTTP 수준에서 분배한다. → [[load-balancer]]

## Observability / Operations

- **Observability (관측 가능성)**: 로그, 메트릭, 트레이스를 보고 시스템 안에서 무슨 일이 일어나는지 알아낼 수 있는 정도. → [[why-observability]]
- **TraceId**: 요청 하나가 여러 서비스를 거칠 때, 그 흐름을 처음부터 끝까지 따라가려고 붙이는 고유 ID. → [[trace-id-and-correlation-id]]
- **SLO (Service Level Objective)**: 서비스가 지키기로 정한 품질 목표. "p99 latency 200ms 이내" 같은 식으로 정한다. → [[alert-and-slo]]
- **Latency**: 요청부터 응답까지 걸리는 시간. 실무에서는 평균보다 p95, p99를 본다. → [[latency-and-throughput]]
- **p95 / p99**: 요청 100개를 빠른 순으로 줄 세웠을 때 95번째, 99번째의 응답 시간. 가장 느린 5%, 1%가 어디서 시작하는지 보여 준다. 평균에 가려지는 느린 요청을 드러낸다. → [[latency-and-throughput]]
- **Throughput**: 정해진 시간 동안 처리하는 요청 수. TPS(Transactions Per Second)로 측정한다. → [[latency-and-throughput]]

## CI/CD / Deployment

- **CI (Continuous Integration)**: 코드가 바뀔 때마다 자동으로 빌드하고 테스트하는 파이프라인. → [[ci-vs-cd]]
- **CD (Continuous Deployment)**: 테스트를 통과한 코드를 운영 환경까지 자동으로 배포하는 과정. → [[ci-vs-cd]]
- **Rollback**: 배포 뒤 문제가 생기면 이전 버전으로 되돌리는 절차. → [[rollback-strategy]]
- **GitOps**: 인프라와 배포 설정을 Git에 두고, Git에 적힌 상태를 유일한 기준(Single Source of Truth)으로 삼아 관리하는 방식. → [[gitops]]

## Kubernetes

- **Pod**: Kubernetes가 배포하고 노드에 올리는 가장 작은 단위. 컨테이너 하나 이상이 IP와 포트를 같이 쓴다. 언제든 다시 만들어지고, 그때 IP가 바뀐다. → [[pod-and-container]]
- **Service**: 계속 바뀌는 Pod들 앞에 고정된 이름과 주소를 주는 리소스. label이 맞는 준비된 Pod로만 요청을 보낸다. → [[deployment-service-ingress]]
- **Readiness / Liveness Probe**: readiness는 요청을 받아도 되는지, liveness는 재시작해야 하는지 묻는 검사. 실패했을 때 일어나는 일이 다르다. → [[readiness-and-liveness-probe]]
- **kubeconfig**: `kubectl`이 어느 클러스터에 누구로 접속할지 적어 둔 파일. clusters, users, contexts로 되어 있다. → [[cluster-access-and-kubeconfig]]
