---
title: Redis 장애 대응과 fallback
description: Redis 장애가 서비스 장애로 전파되지 않게 설계하는 기준
---

# Redis 장애 대응과 fallback

## 한 줄 정의

Redis 장애 대응은 Redis timeout, 연결 실패, 지연 증가가 애플리케이션 전체 장애로 번지지 않도록 실패 정책을 정하는 것이다.

## 실무에서 왜 문제 되는가

- Redis가 느려지면 애플리케이션 스레드가 Redis 응답을 기다리며 같이 고갈될 수 있다.
- 캐시 장애가 DB fallback으로 몰리면 DB 부하가 급증해 2차 장애가 날 수 있다.
- 세션, 락, rate limit처럼 Redis 의존도가 높은 기능은 fallback이 단순하지 않다.
- Redis 장애를 "캐시니까 괜찮다"로 보면 timeout, connection pool, 장애 전파를 놓치기 쉽다.

## 장애 유형별 대응

| 장애 유형 | 증상 | 대응 |
|---|---|---|
| 연결 실패 | Redis connection error 증가 | 짧은 timeout, fallback, circuit breaker |
| 지연 증가 | Redis latency 상승, API 응답 지연 | slow command 확인, hot key/big key 점검, timeout 제한 |
| 메모리 부족 | evicted keys 증가, OOM 위험 | TTL 점검, maxmemory policy 확인, big key 정리 |
| connection pool 고갈 | Redis client 대기 증가 | pool 크기, timeout, 호출량, blocking command 점검 |
| 캐시 전체 만료 | DB QPS 급증 | TTL jitter, warm-up, mutex, 사전 갱신 |

## 실무 판단 기준

| 기능 | 장애 시 정책 | 이유 |
|---|---|---|
| 상품/게시글 조회 캐시 | DB fallback 또는 짧은 기본 응답 | 원본 DB가 있고 stale data 허용 가능성이 있다 |
| 설정 캐시 | 로컬 마지막 값 사용 | 설정 조회 실패가 요청 전체 실패로 번지지 않게 한다 |
| 세션 저장소 | 인증 실패 또는 재로그인 유도 | 인증 상태를 임의로 통과시키면 보안 문제가 된다 |
| 분산 락 | 작업 중단 또는 DB 제약으로 보완 | 락 실패를 무시하면 중복 처리가 생긴다 |
| rate limit | 보수적으로 제한 또는 임시 허용 | 보안/비용 위험과 사용자 영향 사이에서 정해야 한다 |

## 자주 나는 실수

- Redis timeout을 API timeout과 비슷하게 길게 둔다.
- Redis 장애 시 모든 요청을 DB로 보내 DB까지 장애로 만든다.
- 캐시 hit ratio만 보고 Redis latency, timeout, fallback count를 보지 않는다.
- Redis 장애 로그를 warn/error로 남기지 않아 장애 원인 파악이 늦어진다.
- 세션, 락, 캐시를 같은 Redis에 섞어 장애 영향 범위를 키운다.
- fallback 성공만 보고 사용자 응답 지연과 DB 부하 증가를 같이 보지 않는다.

## 확인 방법

- 테스트: Redis 연결 차단, 지연 주입, 전체 캐시 삭제 상황을 재현한다.
- 로그: timeout, connection error, fallback 실행, circuit breaker open 여부를 남긴다.
- 메트릭: Redis latency, timeout count, pool usage, fallback count, DB QPS를 함께 본다.
- 운영 점검: slowlog, big key, hot key, memory usage, evicted keys를 확인한다.

## 핵심 요약

Redis 장애 대응의 핵심은 Redis가 빠를 때가 아니라 느리거나 죽었을 때 애플리케이션이 어떻게 망가지는지 보는 것이다. 캐시는 DB fallback이 가능하지만, fallback이 몰리면 DB 장애가 될 수 있다. 세션, 분산 락, rate limit처럼 Redis 의존도가 높은 기능은 실패 정책을 따로 정해야 한다. timeout은 짧게 두고 connection pool과 circuit breaker로 장애 전파를 제한한다. Redis 지표만 보지 말고 API latency, DB QPS, fallback count를 함께 봐야 한다.

## 꼬리 질문

- Redis가 3초 동안 응답하지 않으면 API 스레드는 어떻게 되는가?
- Redis timeout은 왜 API timeout보다 짧아야 하는가?
- Redis 장애 시 DB fallback을 무제한 허용하면 어떤 문제가 생기는가?
- 세션 저장소 Redis가 장애 나면 어떤 사용자 영향을 허용할 것인가?
- 캐시 fallback은 항상 좋은 선택인가?
- fallback이 정상 동작해도 장애로 봐야 하는 기준은 무엇인가?

## 관련 문서

- [[redis]]
- [[cache-aside-and-ttl]]
- [[timeout]]
- [[performance]]
