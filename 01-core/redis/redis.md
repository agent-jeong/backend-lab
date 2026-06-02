---
title: Redis
description: Redis 캐시 전략과 장애 대응 학습 인덱스
comments: false
---

# Redis

## 운영 방식

- 이 문서는 Redis 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/redis/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 캐시 전략, 정합성 문제, 장애 상황, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

## 학습 순서

1. [[why-redis|Redis를 사용하는 이유]]
2. [[cache-aside-and-ttl|Cache Aside와 TTL]]
3. [[redis-failure-and-fallback|Redis 장애 대응과 fallback]]
4. [[redis-distributed-lock|Redis 분산 락]]
5. [[redis-data-structures|Redis 자료구조]]
6. [[redis-key-and-memory|Key 설계와 메모리 관리]]
7. [[redis-monitoring|운영 모니터링]]

## 핵심 질문

- Redis를 실무에서 왜 사용하는가?
- Redis는 빠른 DB가 아니라 캐시, 세션, 락, 카운터 같은 보조 상태 처리 도구라는 점을 어떻게 설명할 수 있는가?
- 캐시는 어떤 문제를 해결하고 어떤 정합성 문제를 만드는가?
- Cache Aside에서 cache hit, cache miss, DB fallback 흐름은 어떻게 이어지는가?
- TTL은 어떻게 정해야 하는가?
- 캐시 무효화는 왜 어렵고, stale data 허용 시간은 어떻게 정하는가?
- DB 변경 후 캐시 삭제가 실패하면 어떤 문제가 생기는가?
- Redis 장애 시 timeout, fallback, circuit breaker는 어떻게 설계해야 하는가?
- Redis 분산 락의 원자적 획득, TTL, 안전한 해제는 어떻게 보장하는가?
- Redis 분산 락과 DB 정합성 보장은 어떤 차이가 있는가?
- String, Hash, Set, Sorted Set, Stream/Pub/Sub은 각각 어떤 실무 문제에 적합한가?
- hot key, big key, memory eviction, connection pool 고갈은 어떻게 확인하는가?

## 실무 관점

- Redis는 빠른 저장소가 아니라 캐시, 세션, 분산 제어 같은 특정 문제를 해결하기 위한 도구다.
- 캐시는 성능을 높이지만 데이터 정합성, 만료 정책, 장애 대응 복잡도를 만든다.
- Redis 의존 경로는 장애 시 fallback 가능 여부를 반드시 확인해야 한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
