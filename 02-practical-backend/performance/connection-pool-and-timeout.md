---
title: Connection Pool과 Timeout
description: pool 고갈과 timeout이 API 지연과 장애 전파로 이어지는 흐름
---

# Connection Pool과 Timeout

## 한 줄 정의

Connection pool은 외부 자원 연결을 재사용하는 장치이고, timeout은 대기와 호출 시간을 제한해 장애 전파를 막는 안전장치다.

## 실무에서 왜 문제 되는가

- DB, Redis, HTTP client pool이 고갈되면 실제 호출 전 대기 시간이 늘어난다.
- pool wait과 query time을 구분하지 않으면 원인을 잘못 판단한다.
- timeout이 너무 길면 장애 의존성을 오래 기다리며 thread와 connection을 점유한다.
- timeout이 너무 짧으면 정상 요청도 실패할 수 있다.
- retry가 timeout과 결합되면 부하를 더 키울 수 있다.

## 동작 원리

1. 애플리케이션이 DB나 외부 API 호출을 시도한다.
2. pool에서 connection을 빌린다.
3. pool이 비어 있으면 대기한다.
4. connection을 얻은 뒤 실제 호출을 수행한다.
5. pool 대기, connect, read, 전체 요청 timeout 중 하나가 초과되면 실패한다.

## 실무 판단 기준

| 증상 | 확인할 지표 | 판단 |
|---|---|---|
| DB query는 빠른데 API 느림 | pool wait time | connection pool 고갈 가능 |
| timeout 급증 | dependency p99, retry count | 외부 의존성 지연 가능 |
| thread 급증 | active thread, blocked thread | blocking 대기 증가 |
| DB CPU 낮고 pool full | connection usage, transaction duration | 커넥션을 오래 잡는 코드 확인 |
| retry 후 더 느림 | retry count, traffic amplification | retry 폭증 확인 |
| 인스턴스 수 증가 후 DB 장애 | total pool size, DB max connections | 전체 커넥션 합이 DB 한계를 넘을 수 있다 |

## 자주 나는 실수

- pool 크기를 늘리면 항상 해결된다고 생각한다.
- timeout을 무한대 또는 매우 길게 둔다.
- connect timeout과 read timeout을 구분하지 않는다.
- retry를 넣으면서 timeout budget을 계산하지 않는다.
- 트랜잭션 안에서 외부 API를 호출해 DB connection을 오래 점유한다.
- 인스턴스별 pool 크기만 보고 전체 서비스의 총 DB connection 수를 계산하지 않는다.
- pool acquire timeout을 너무 길게 둬 요청 대기열이 계속 쌓이게 만든다.

## 확인 방법

- 테스트: 외부 의존성을 지연시켜 pool wait과 timeout을 재현한다.
- 로그: pool wait time, execution time, timeout type을 분리해 남긴다.
- 메트릭: active/idle connection, pending acquire, timeout count, retry count를 본다.
- 용량 확인: 인스턴스 수 × 인스턴스별 pool max가 DB max connection과 운영 여유분 안에 있는지 확인한다.
- thread dump: 많은 스레드가 DB/HTTP/Redis 대기 중인지 확인한다.

## 장점과 한계

| 설정 | 장점 | 한계 |
|---|---|---|
| pool | connection 생성 비용을 줄인다 | 고갈되면 대기열이 된다 |
| timeout | 장애 전파를 제한한다 | 너무 짧으면 정상 요청도 실패한다 |
| retry | 일시 장애를 흡수한다 | 멱등성 없이는 중복 처리와 부하 증폭을 만든다 |
| circuit breaker | 연쇄 장애를 줄인다 | 임계값 설정과 fallback 설계가 필요하다 |

## 짧은 예제

```text
API timeout budget: 1s
- DB pool wait: 100ms
- query timeout: 300ms
- external API read timeout: 500ms
- serialization and margin: 100ms
```

각 dependency timeout의 합이 API 전체 timeout보다 커지면, 사용자는 이미 timeout됐는데 서버는 계속 작업하는 상황이 생길 수 있다.

## 핵심 요약

Connection pool 고갈은 실제 DB나 외부 API 호출 전 대기 시간으로 나타난다.

성능 분석에서는 pool wait time과 execution time을 구분해야 한다.

timeout은 장애 의존성을 오래 기다리지 않게 하는 안전장치다.

retry는 timeout, 멱등성, backoff, 최대 횟수와 함께 설계해야 한다.

pool 크기를 늘리기 전에 connection을 오래 잡는 트랜잭션, 외부 호출, 느린 쿼리를 먼저 확인한다.

pool 크기는 애플리케이션 인스턴스 수와 DB max connection을 함께 보고 정해야 한다.

## 꼬리 질문

- DB query time은 짧은데 API가 느릴 수 있는 이유는 무엇인가?
- connect timeout과 read timeout은 어떻게 다른가?
- pool 크기를 늘리는 것이 항상 해결책이 아닌 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/network/timeout|timeout]]
- [[01-core/network/retry|retry]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
