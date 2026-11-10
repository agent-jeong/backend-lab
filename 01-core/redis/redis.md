---
title: Redis
description: Redis 캐시 전략과 장애 대응 학습 인덱스
tags: [redis]
comments: false
---

# Redis

캐시 전략과 TTL, 자료구조, 분산 락, 장애 대응을 다룬다. 캐시가 정합성과 장애 전파에 만드는 비용이 중심이다.

## 읽는 순서

1. [[why-redis|Redis를 사용하는 이유]]
2. [[cache-aside-and-ttl|Cache Aside와 TTL]]
3. [[redis-failure-and-fallback|Redis 장애 대응과 fallback]]
4. [[redis-distributed-lock|Redis 분산 락]]
5. [[redis-data-structures|Redis 자료구조]]
6. [[redis-key-and-memory|Key 설계와 메모리 관리]]
7. [[redis-monitoring|운영 모니터링]]

## 핵심 질문

- Redis를 실무에서 왜 사용하는가?
- 캐시는 어떤 문제를 해결하고 어떤 정합성 문제를 만드는가?
- Cache Aside에서 cache hit, cache miss, DB fallback 흐름은 어떻게 이어지는가?
- TTL은 어떻게 정해야 하는가?
- 캐시 무효화는 왜 어렵고, stale data 허용 시간은 어떻게 정하는가?
- DB 변경 후 캐시 삭제가 실패하면 어떤 문제가 생기는가?
- Redis 장애 시 timeout, fallback, circuit breaker는 어떻게 설계하는가?
- Redis 분산 락의 원자적 획득, TTL, 안전한 해제는 어떻게 보장하는가?
- Redis 분산 락과 DB 정합성 보장은 어떤 차이가 있는가?
- String, Hash, Set, Sorted Set, Stream/Pub/Sub은 각각 어떤 실무 문제에 맞는가?
- hot key, big key, memory eviction, connection pool 고갈은 어떻게 확인하는가?

## 실무에서 보는 것

- Redis는 "빠른 DB"가 아니다. 캐시, 세션, 분산 락, 카운터처럼 잃어도 복구되는 보조 상태를 둔다.
- 캐시는 빨라지는 대신 정합성, 만료 정책, 장애 대응이라는 숙제를 만든다.
- Redis를 호출하는 경로마다 "Redis가 죽으면 DB로 가는가, 실패시키는가"를 정해 둔다.

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: Redis 분산 락이 막지 못하는 틈

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
