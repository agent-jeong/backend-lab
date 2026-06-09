---
title: Glossary
description: 백엔드 실무에서 반드시 알아야 하는 핵심 용어 정리
---

# Glossary

## Java / JVM

- **Primitive Type**: 값 자체를 저장하는 타입. `int`, `long`, `boolean` 등. 스택에 저장되며 `null`을 가질 수 없다.
- **Reference Type**: 객체의 주소를 저장하는 타입. 힙에 할당되며 `==`는 주소 비교, `equals()`는 값 비교다.
- **Boxing / Unboxing**: primitive ↔ wrapper 자동 변환. `null` unboxing 시 `NullPointerException` 발생.
- **equals / hashCode**: 객체 동등성 판단 기준. `hashCode`가 다르면 `HashMap`에서 같은 키로 인식하지 못한다.
- **GC (Garbage Collection)**: 사용하지 않는 객체를 자동 회수하는 JVM 메커니즘. STW(Stop-The-World) 시간이 지연 시간에 직접 영향을 준다.
- **OOM (OutOfMemoryError)**: 힙 메모리가 부족할 때 발생하는 에러. 메모리 누수, 대량 조회, 캐시 미제한이 주요 원인이다.
- **Thread Safety**: 여러 스레드가 동시에 접근해도 데이터가 깨지지 않는 상태. `synchronized`, `Atomic`, 불변 객체 등으로 보장한다.

## Spring

- **DI (Dependency Injection)**: 객체가 의존하는 다른 객체를 직접 생성하지 않고 외부에서 주입받는 방식. 테스트와 교체가 쉬워진다.
- **Bean**: Spring 컨테이너가 생성하고 관리하는 객체. 기본 scope는 singleton이다.
- **AOP (Aspect-Oriented Programming)**: 횡단 관심사(로깅, 트랜잭션 등)를 비즈니스 로직과 분리하는 기법. Spring은 프록시 기반으로 동작한다.
- **Proxy**: Spring이 Bean을 감싸 부가 기능을 끼워넣는 래퍼 객체. 같은 클래스 내부 호출에서는 프록시를 타지 않아 `@Transactional`이 무시될 수 있다.

## JPA / Database

- **Persistence Context**: 엔티티를 관리하는 1차 캐시. 같은 트랜잭션 내에서 동일 ID 조회는 DB를 거치지 않는다.
- **Dirty Checking**: 영속 상태 엔티티의 변경을 자동 감지해 flush 시점에 UPDATE를 실행하는 메커니즘.
- **N+1**: 연관 엔티티를 건건이 조회하면서 쿼리 수가 1 + N으로 폭발하는 문제. fetch join 또는 batch size로 해결한다.
- **Fetch Join**: JPQL에서 연관 엔티티를 한 번의 JOIN 쿼리로 함께 로딩하는 방법.
- **Index**: 특정 컬럼 값을 정렬된 자료구조로 유지해 검색 속도를 높이는 DB 구조. 쓰기 비용이 증가하고 선택도가 낮으면 효과가 없다.
- **Full Scan**: 인덱스를 사용하지 않고 테이블 전체를 읽는 방식. 소량 데이터에서는 오히려 더 빠를 수 있다.
- **Execution Plan**: DB가 쿼리를 어떤 순서와 방법으로 처리할지 보여주는 계획. `EXPLAIN`으로 확인한다.

## Transaction / Concurrency

- **Transaction**: 하나의 작업 단위로 묶인 연산 집합. 전부 성공하거나 전부 롤백된다.
- **ACID**: Atomicity, Consistency, Isolation, Durability. 트랜잭션이 보장해야 하는 네 가지 속성.
- **Isolation Level**: 동시 트랜잭션 간 데이터 간섭 수준. READ COMMITTED가 실무 기본이며, 수준을 올리면 정합성은 높아지지만 동시성이 떨어진다.
- **Lock**: 동시 접근을 제어하는 메커니즘. 비관적 락은 DB 레벨에서 행을 잠그고, 낙관적 락은 버전 비교로 충돌을 감지한다.
- **Deadlock**: 둘 이상의 트랜잭션이 서로가 잡은 Lock을 기다리며 영원히 멈추는 상태.
- **Race Condition**: 두 요청이 같은 데이터를 동시에 읽고 쓸 때 결과가 실행 순서에 따라 달라지는 문제.

## Idempotency / Reliability

- **Idempotency (멱등성)**: 같은 요청을 여러 번 보내도 결과가 변하지 않는 성질. 결제, 주문 등 부작용이 있는 API에서 필수다.
- **Idempotency Key**: 중복 요청을 식별하기 위해 클라이언트가 보내는 고유 키.
- **Retry**: 실패한 요청을 재시도하는 패턴. 멱등하지 않은 API에 retry하면 중복 처리가 발생한다.
- **Circuit Breaker**: 외부 호출 실패가 반복되면 일정 시간 요청을 차단해 장애 전파를 막는 패턴.

## Cache / Redis

- **Cache Aside**: 캐시에 없으면 DB에서 읽고 캐시에 저장하는 전략. 가장 일반적인 캐시 패턴이다.
- **TTL (Time To Live)**: 캐시 데이터의 만료 시간. TTL이 없으면 오래된 데이터가 계속 서빙된다.
- **Cache Stampede**: TTL 만료 시 다수 요청이 동시에 DB를 조회하며 부하가 급증하는 현상.
- **Distributed Lock**: 분산 환경에서 여러 인스턴스의 동시 접근을 제어하기 위한 락. Redis의 Redisson이 대표적이다.

## Network

- **Timeout**: 응답을 기다리는 최대 시간. connection timeout과 read timeout을 구분해야 한다.
- **DNS**: 도메인을 IP 주소로 변환하는 시스템. TTL 캐시 때문에 IP 변경이 즉시 반영되지 않을 수 있다.
- **TLS**: 통신을 암호화하는 프로토콜. HTTPS는 HTTP + TLS다.
- **CORS**: 브라우저가 다른 출처의 요청을 차단하는 보안 정책. 서버에서 허용 출처를 명시해야 한다.
- **Load Balancer**: 트래픽을 여러 서버에 분산하는 장치. L4는 TCP, L7은 HTTP 수준에서 분배한다.

## Observability / Operations

- **Observability (관측 가능성)**: 로그, 메트릭, 트레이스 세 축으로 시스템 내부 상태를 파악하는 능력.
- **TraceId**: 하나의 요청이 여러 서비스를 거칠 때 전체 흐름을 추적하기 위한 고유 ID.
- **SLO (Service Level Objective)**: 서비스 품질 목표. 예: "p99 latency 200ms 이내".
- **Latency**: 요청부터 응답까지 걸리는 시간. 평균보다 p95, p99가 실무에서 더 중요하다.
- **Throughput**: 단위 시간당 처리하는 요청 수. TPS(Transactions Per Second)로 측정한다.

## CI/CD / Deployment

- **CI (Continuous Integration)**: 코드 변경을 자동으로 빌드하고 테스트하는 파이프라인.
- **CD (Continuous Deployment)**: 테스트를 통과한 코드를 자동으로 운영 환경에 배포하는 프로세스.
- **Rollback**: 배포 후 문제 발생 시 이전 버전으로 되돌리는 절차.
- **GitOps**: Git을 단일 진실 공급원(Single Source of Truth)으로 두고 인프라와 배포를 관리하는 방식.