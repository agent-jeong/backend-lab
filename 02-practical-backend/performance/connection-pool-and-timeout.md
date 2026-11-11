---
title: Connection Pool과 Timeout
description: pool이 바닥나고 timeout이 어긋날 때 API가 느려지고 장애가 번지는 과정
tags: [concept, performance]
---

# Connection Pool과 Timeout

Connection pool은 DB나 외부 서버와의 연결을 만들어 두고 돌려 쓰는 장치다. timeout은 기다리는 시간과 호출 시간에 상한을 둬서, 한 곳의 장애가 다른 곳까지 번지지 않게 막는다.

DB, Redis, HTTP client pool이 바닥나면 실제 호출을 하기도 전에 기다리는 시간이 늘어난다. 이 pool wait을 query time과 나눠 보지 않으면 원인을 엉뚱하게 짚는다. timeout이 너무 길면 이미 죽은 결제 API를 오래 기다리며 thread와 connection을 쥐고 있고, 너무 짧으면 멀쩡한 요청도 실패한다. 여기에 retry까지 붙으면 부하가 더 커진다.

## 연결을 빌려 쓰는 흐름

1. 애플리케이션이 DB나 외부 API 호출을 시도한다.
2. pool에서 connection을 빌린다.
3. pool이 비어 있으면 기다린다.
4. connection을 얻은 뒤 실제 호출을 한다.
5. pool 대기, connect, read, 전체 요청 timeout 중 하나를 넘으면 실패한다.

```text
API timeout budget: 1s
- DB pool wait: 100ms
- query timeout: 300ms
- external API read timeout: 500ms
- serialization and margin: 100ms
```

의존성마다 준 timeout을 더한 값이 API 전체 timeout보다 크면, 사용자는 이미 timeout을 받았는데 서버는 계속 일하고 있게 된다.

## 증상별 판단

| 증상 | 확인할 지표 | 판단 |
|---|---|---|
| DB query는 빠른데 API 느림 | pool wait time | connection pool 고갈 가능 |
| timeout 급증 | dependency p99, retry count | 외부 의존성 지연 가능 |
| thread 급증 | active thread, blocked thread | blocking 대기 증가 |
| DB CPU 낮고 pool full | connection usage, transaction duration | 커넥션을 오래 잡는 코드 확인 |
| retry 후 더 느림 | retry count, traffic amplification | retry 폭증 확인 |
| 인스턴스 수 증가 후 DB 장애 | total pool size, DB max connections | 전체 커넥션 합이 DB 한계를 넘을 수 있다 |

| 설정 | 장점 | 한계 |
|---|---|---|
| pool | connection 생성 비용을 줄인다 | 고갈되면 대기열이 된다 |
| timeout | 장애 전파를 제한한다 | 너무 짧으면 정상 요청도 실패한다 |
| retry | 일시 장애를 흡수한다 | 멱등성 없이는 중복 처리와 부하 증폭을 만든다 |
| circuit breaker | 연쇄 장애를 줄인다 | 임계값 설정과 fallback 설계가 필요하다 |

## 자주 깨지는 곳

- 커넥션을 오래 잡는 트랜잭션, 외부 호출, 느린 쿼리가 원인인데 pool 크기만 늘리면, 대기열만 길어진다.
- timeout을 아예 두지 않거나 아주 길게 두면, 응답 없는 의존성을 기다리느라 thread와 connection이 묶인다.
- connect timeout과 read timeout을 나누지 않으면, 연결이 안 되는 상황과 응답이 늦는 상황을 같은 값으로 다루게 된다.
- retry를 넣으면서 timeout budget을 계산하지 않으면, 재시도까지 더한 시간이 API timeout을 넘는다. retry는 timeout, 멱등성, backoff, 최대 횟수와 함께 정한다.
- 트랜잭션 안에서 외부 API를 부르면, 그 응답을 기다리는 동안 DB connection을 쥐고 있다.
- 인스턴스별 pool 크기만 보고 서비스 전체의 DB connection 수를 계산하지 않으면, 스케일 아웃할 때 DB가 넘어간다.
- pool acquire timeout을 너무 길게 두면, 요청 대기열이 계속 쌓인다.

## 운영에서 볼 것

- 외부 의존성을 지연시켜 pool wait과 timeout을 재현하는 테스트를 둔다.
- pool wait time, execution time, timeout 종류를 나눠 로그로 남긴다.
- active/idle connection, pending acquire, timeout count, retry count를 본다.
- 인스턴스 수 × 인스턴스별 pool max가 DB max connection과 운영 여유분 안에 있는지 확인한다.
- thread dump로 스레드 다수가 DB, HTTP, Redis를 기다리고 있는지 본다.

## 한 번에 설명하기

> Connection pool이 바닥나면 DB나 외부 API를 부르기 전에 기다리는 시간이 늘어납니다. 그래서 성능을 볼 때 pool wait time과 execution time을 나눠 봅니다.
>
> pool 크기를 늘리기 전에 커넥션을 오래 잡는 트랜잭션, 외부 호출, 느린 쿼리를 먼저 찾습니다. 크기는 인스턴스 수와 DB max connection을 같이 보고 정합니다.
>
> timeout은 장애 난 의존성을 오래 기다리지 않게 하는 장치입니다. retry는 timeout budget, 멱등성, backoff, 최대 횟수와 함께 정합니다.

## 꼬리 질문

- DB query time은 짧은데 API가 느릴 수 있는 이유는 무엇인가?
- connect timeout과 read timeout은 어떻게 다른가?
- pool 크기를 늘리는 것이 항상 해결책이 아닌 이유는 무엇인가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [Amazon Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/network/timeout|timeout]]
- [[01-core/network/retry|retry]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
