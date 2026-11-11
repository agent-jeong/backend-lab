---
title: Redis 장애 대응과 fallback
description: Redis가 느려지거나 죽었을 때 서비스까지 같이 멈추지 않게 하는 방법
tags: [concept, redis]
---

# Redis 장애 대응과 fallback

Redis에 timeout이 나거나, 연결이 끊기거나, 응답이 느려질 때 애플리케이션이 어떻게 할지를 미리 정해 두는 일이다. 정해 두지 않으면 Redis 하나의 문제가 서비스 전체 장애가 된다.

"캐시니까 죽어도 괜찮다"고 생각하기 쉽지만 실제로는 그렇지 않다. Redis가 느려지면 API 스레드가 Redis 응답을 기다리다 다 묶이고, 캐시 miss가 DB로 몰리면 DB까지 넘어간다. 그래서 Redis가 잘 돌 때보다, 느리거나 죽었을 때 애플리케이션이 어떻게 망가지는지를 먼저 본다.

## 장애 유형별 대응

| 장애 유형 | 증상 | 대응 |
|---|---|---|
| 연결 실패 | Redis connection error 증가 | 짧은 timeout, fallback, circuit breaker |
| 지연 증가 | Redis latency 상승, API 응답 지연 | slow command 확인, hot key/big key 점검, timeout 제한 |
| 메모리 부족 | evicted keys 증가, OOM 위험 | TTL 점검, maxmemory policy 확인, big key 정리 |
| connection pool 고갈 | Redis client 대기 증가 | pool 크기, timeout, 호출량, blocking command 점검 |
| 캐시 전체 만료 | DB QPS 급증 | TTL jitter, warm-up, mutex, 사전 갱신 |

## 기능별 실패 정책

캐시는 원본 DB가 있으니 DB로 돌리면 되지만, 세션이나 락, rate limit처럼 Redis에만 상태가 있는 기능은 장애 때 어떻게 할지 따로 정해야 한다.

| 기능 | 장애 시 정책 | 이유 |
|---|---|---|
| 상품/게시글 조회 캐시 | DB fallback 또는 짧은 기본 응답 | 원본 DB가 있고, 옛 값이 잠깐 보여도 되는 경우가 많다 |
| 설정 캐시 | 로컬에 있는 마지막 값 사용 | 설정 조회 실패가 요청 전체 실패로 번지지 않는다 |
| 세션 저장소 | 인증 실패 또는 재로그인 유도 | 인증 상태를 임의로 통과시키면 보안 문제가 된다 |
| 분산 락 | 작업 중단 또는 DB 제약으로 보완 | 락 실패를 무시하면 중복 처리가 생긴다 |
| rate limit | 보수적으로 제한하거나 임시 허용 | 막으면 사용자가 불편하고, 열면 보안이나 비용 위험이 생긴다. 둘 중 하나를 고른다 |

## 자주 깨지는 곳

- Redis timeout을 API timeout만큼 길게 두면, Redis가 멈췄을 때 API 스레드가 그 시간 동안 묶여 결국 바닥난다.
- 장애 때 모든 요청을 DB로 보내면, fallback 요청이 몰려 DB까지 장애가 난다.
- hit ratio만 보고 Redis latency, timeout, fallback count를 안 보면 장애를 늦게 안다.
- Redis 장애를 warn이나 error 로그로 남기지 않으면 원인을 찾는 데 오래 걸린다.
- 세션, 락, 캐시를 한 Redis에 섞어 두면, 그 Redis가 죽을 때 세 기능이 다 멈춘다.
- fallback이 성공한다고 안심하면 놓치는 게 있다. 그동안 사용자 응답은 느려지고 DB 부하는 계속 오르고 있을 수 있다.

## 운영에서 볼 것

- 테스트: Redis 연결 차단, 지연 주입, 캐시 전체 삭제를 재현한다.
- 로그: timeout, connection error, fallback 실행, circuit breaker가 열렸는지를 남긴다.
- 메트릭: Redis latency, timeout count, pool usage, fallback count, DB QPS를 같이 본다.
- 점검: slowlog, big key, hot key, memory usage, evicted keys를 본다.

## 한 번에 설명하기

> Redis가 느리거나 죽었을 때 애플리케이션까지 같이 멈추지 않도록, 실패하면 어떻게 할지를 미리 정해 둡니다. Redis timeout은 API timeout보다 짧게 두고, connection pool과 circuit breaker로 Redis 문제가 API까지 번지지 않게 끊습니다.
>
> 캐시는 DB로 돌리되, 그 요청이 몰려 DB가 넘어가지 않게 양을 제한합니다. 세션, 락, rate limit은 기능마다 실패했을 때의 정책을 따로 정합니다.
>
> 확인할 때는 Redis 지표와 함께 API latency, DB QPS, fallback count를 봅니다.

## 꼬리 질문

- Redis가 3초 동안 응답하지 않으면 API 스레드는 어떻게 되나?
- Redis timeout은 왜 API timeout보다 짧아야 하나?
- Redis 장애 시 DB fallback을 무제한 허용하면 어떤 문제가 생기나?
- 세션 저장소 Redis가 장애 나면 사용자 영향을 어디까지 허용할 것인가?
- 캐시 fallback은 항상 좋은 선택인가?
- fallback이 정상 동작해도 장애로 봐야 하는 기준은?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: Redis replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)
- [Redis Docs: Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[timeout]]
- [[02-practical-backend/performance/performance|performance]]
