---
title: Redis를 사용하는 이유
description: Redis에 무엇을 두고 무엇을 두지 않는지, 쓸 때 조심할 점
tags: [concept, redis]
---

# Redis를 사용하는 이유

Redis는 데이터를 메모리에 두는 key-value 저장소다. 읽고 쓰는 게 빠르고 key마다 만료 시간을 걸 수 있어서, 캐시나 세션, 락, 카운터처럼 원본이 따로 있거나 잠깐만 필요한 데이터를 두는 데 많이 쓴다.

Redis를 "빠른 DB"로 생각하면 주문이나 잔액 같은 데이터까지 넣게 되고, 메모리가 차서 key가 지워지거나 서버가 죽으면 되살릴 곳이 없다. 그래서 도입할 때는 속도보다 먼저 "이 데이터가 Redis에서 사라지면 DB나 기본값으로 다시 만들 수 있나"를 묻는다.

## 동작

1. 애플리케이션이 key로 Redis에 값을 조회하거나 저장한다.
2. Redis는 데이터 대부분을 메모리에서 처리해서 응답이 빠르다.
3. key에 TTL을 걸면 시간이 지난 뒤 자동으로 만료된다.
4. 메모리가 모자라면 설정한 eviction policy에 따라 일부 key를 지운다.
5. Redis가 느려지거나 죽으면 Redis를 호출하는 애플리케이션 경로도 같이 느려진다.

```java
String key = "product:summary:" + productId;

ProductSummary cached = redisTemplate.opsForValue().get(key);
if (cached != null) {
    return cached;
}

ProductSummary summary = productRepository.findSummary(productId);
redisTemplate.opsForValue().set(key, summary, Duration.ofMinutes(10));
return summary;
```

이 코드에서 원본은 DB이고, Redis는 읽기를 빠르게 할 뿐이다. 그러니 Redis 조회가 실패하면 DB를 읽어서 응답할 수 있어야 한다.

## 대표 사용처

| 사용처 | 예시 | 조심할 점 |
|---|---|---|
| 캐시 | 상품 상세, 설정값, 집계 결과 | 원본 DB와 값이 달라질 수 있다 |
| 세션 저장소 | 로그인 세션, 인증 상태 | Redis가 죽으면 사용자가 로그아웃되거나 인증에 실패한다 |
| 분산 락 | 중복 처리 방지, 단일 작업 실행 | 락 만료 시간과 작업 시간이 어긋나면 동시 실행된다 |
| 카운터 | 조회수, rate limit | 숫자가 정확히 남아야 하면 DB에 옮겨 적는 방법을 따로 정해야 한다 |
| Pub/Sub | 서버 간 간단한 이벤트 전달 | 메시지가 유실될 수 있다 |
| Sorted Set | 랭킹, 우선순위 목록 | 점수를 언제 갱신하고 어떻게 조회할지를 함께 정해야 한다 |

## 쓸지 말지

| 상황 | 판단 | 이유 |
|---|---|---|
| 자주 읽고 잘 안 바뀌는 데이터 | 쓴다 | 캐시로 DB 부하와 응답 시간을 줄인다 |
| 꼭 최신이어야 하는 결제/재고 원본 데이터 | 안 쓴다 | 원본은 트랜잭션으로 정합성을 지켜 주는 DB에 둔다 |
| 짧은 시간 중복 요청을 막아야 함 | 조건부 | TTL을 건 key나 분산 락으로 막을 수 있지만, Redis가 실패할 때 어떻게 할지 정해 둬야 한다 |
| 대용량 검색/분석 | 안 쓴다 | 검색 엔진이나 분석 저장소가 더 맞다 |
| 장애 때 없어도 되는 보조 데이터 | 쓴다 | fallback이나 재계산으로 버틸 수 있으면 Redis가 죽어도 서비스는 돈다 |

메모리에 두니 빠르지만 그만큼 메모리 값이 비싸고, 복잡한 조회나 여러 테이블을 묶는 트랜잭션에는 맞지 않는다. 대신 TTL과 여러 자료구조가 있어서, 서버 여러 대가 함께 보는 짧은 상태를 다루기는 편하다.

## 자주 깨지는 곳

- 주문이나 잔액 같은 데이터를 Redis에만 두면, eviction이나 장애로 사라졌을 때 되살릴 원본이 없다.
- TTL을 걸지 않으면 안 쓰는 데이터가 계속 쌓이고, 메모리가 차면 OOM이 나거나 eviction으로 엉뚱한 데이터가 지워진다.
- key 이름 규칙이 없으면 장애 때 어떤 key가 문제인지, 어디까지 지워야 하는지 알기 어렵다.
- Redis timeout을 길게 잡으면, Redis가 멈췄을 때 애플리케이션 스레드가 응답을 기다리다 다 묶인다. Redis timeout은 API timeout보다 충분히 짧게 둔다.
- 캐시, 세션, 분산 락, 랭킹, rate limit을 Redis 하나에 섞어 두면, 그 Redis가 죽을 때 이 기능이 전부 같이 멈춘다.
- hit ratio만 보면 옛 값이 나가는 것, eviction, timeout, fallback 실패를 놓친다.

## 운영에서 볼 것

- 테스트: Redis가 죽거나, timeout이 나거나, 느리게 응답할 때 서비스가 어떻게 되는지 확인한다. connection pool이 바닥날 때도 본다.
- 로그: Redis timeout, connection pool 고갈, fallback이 실행됐는지를 남긴다.
- 메트릭: hit ratio, latency, memory usage, evicted keys, expired keys, connected clients를 본다. hit ratio 옆에는 DB QPS를 같이 둔다.
- 주기 점검: key prefix별 개수, TTL 분포, big key, hot key를 본다.

## 한 번에 설명하기

> Redis는 메모리에 데이터를 둬서 빠르지만, 저는 무엇을 Redis에 둘지부터 정합니다. 캐시, 세션, 분산 락, 카운터처럼 사라져도 DB나 기본값으로 다시 만들 수 있는 것만 두고, 원본 데이터는 DB에 둡니다.
>
> 도입할 때는 TTL, key 이름, 메모리 사용량, Redis가 죽었을 때 어디로 돌릴지를 같이 정합니다.
>
> 빠르다는 이유로 조회를 전부 Redis로 옮기면, DB와 값이 어긋나는 곳이 늘고 운영할 것도 많아집니다.

## 꼬리 질문

- Redis를 DB 대신 사용하면 어떤 문제가 생기나?
- Redis와 RDB의 역할 차이를 어떻게 설명하나?
- 캐시 데이터가 오래돼도 되는 기준은 어떻게 정하나?
- Redis 장애 시 계속 동작해야 하는 기능과 실패해도 되는 기능은 어떻게 나누나?
- Redis를 쓰면 항상 성능이 좋아지나?
- Redis에 저장하면 안 되는 데이터는?
- Redis latency가 갑자기 오르면 어떤 지표부터 볼 것인가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: Develop with Redis](https://redis.io/docs/latest/develop/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
