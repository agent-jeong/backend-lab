---
title: Cache 적용
description: 캐시로 성능을 개선할 때 hit ratio, 정합성, 장애 전파를 함께 보는 기준
---

# Cache 적용

## 한 줄 정의

캐시 적용은 반복 조회 비용을 줄이기 위해 빠른 저장소에 결과를 저장하는 방법이지만, 정합성, TTL, 장애 대응, stampede를 함께 설계해야 한다.

## 실무에서 왜 문제 되는가

- 캐시는 DB 부하를 줄일 수 있지만 stale data를 만들 수 있다.
- cache miss가 한 번에 몰리면 DB 부하가 급증한다.
- Redis 장애가 API 장애로 전파되면 캐시가 오히려 장애 원인이 된다.
- hit ratio만 높아도 hot key, big key, Redis latency 때문에 API가 느릴 수 있다.
- 변경이 잦은 데이터는 캐시 무효화 비용이 성능 이득보다 클 수 있다.

## 동작 원리

1. 캐시할 데이터와 stale 허용 시간을 정한다.
2. cache aside 같은 패턴으로 먼저 캐시를 조회한다.
3. miss이면 DB를 조회하고 캐시에 저장한다.
4. 원본 데이터 변경 시 캐시 삭제 또는 갱신을 수행한다.
5. Redis 장애 시 timeout, fallback, circuit breaker로 API 장애 전파를 줄인다.

## 실무 판단 기준

| 상황 | 캐시 적합도 | 이유 |
|---|---|---|
| 읽기 많고 변경 적음 | 높음 | hit ratio를 기대할 수 있다 |
| 최신성 매우 중요 | 낮음 | stale data 허용이 어렵다 |
| 계산 비용 높음 | 검토 | 결과 캐시로 CPU/DB 비용을 줄일 수 있다 |
| hot key 집중 | 주의 | Redis 단일 key 병목이 될 수 있다 |
| miss 폭증 가능 | 주의 | cache stampede 방어가 필요하다 |
| 만료 시간이 같은 key 많음 | TTL jitter 적용 | 동시에 만료되어 DB 부하가 몰리는 것을 줄인다 |

## 자주 나는 실수

- 캐시를 붙이면 항상 빨라진다고 생각한다.
- TTL과 무효화 정책을 정하지 않는다.
- Redis timeout을 길게 잡아 API timeout을 만든다.
- cache hit ratio만 보고 장애 가능성을 놓친다.
- 캐시 삭제 실패와 DB fallback 부하를 모니터링하지 않는다.
- 모든 key에 같은 TTL을 적용해 동시에 대량 만료되게 만든다.
- stampede 방어 없이 miss 요청이 모두 DB로 향하게 둔다.

## 확인 방법

- 테스트: cache cold, cache warm 상태를 분리해 측정한다.
- 로그: cache hit/miss, Redis timeout, fallback, invalidation failure를 남긴다.
- 메트릭: hit ratio, Redis latency, DB QPS, evicted keys, hot key를 본다.
- 장애 실험: Redis timeout 또는 장애 시 API가 fallback하는지 확인한다.
- 부하 테스트: cache cold 상태에서 miss가 몰릴 때 DB QPS와 latency가 버티는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 반복 조회 지연을 줄인다 | stale data와 무효화 문제가 생긴다 |
| DB 부하를 낮출 수 있다 | miss 폭증 시 DB 장애로 전파될 수 있다 |
| 비용 큰 계산 결과를 재사용한다 | Redis 운영과 모니터링이 필요하다 |

## 짧은 예제

```java
ProductSummary cached = cache.get(key);
if (cached != null) {
    return cached;
}

ProductSummary summary = productRepository.findSummary(productId);
cache.set(key, summary, Duration.ofMinutes(5));
return summary;
```

이 코드는 단순 cache aside 흐름이다. 실무에서는 Redis timeout, 캐시 저장 실패, stampede, 원본 변경 시 삭제 실패를 함께 고려해야 한다.

stampede 위험이 있는 key는 TTL jitter, mutex/single-flight, stale-while-revalidate 같은 방어를 검토한다. 핵심은 miss 요청이 모두 동시에 DB로 향하지 않게 하는 것이다.

## 핵심 요약

캐시는 반복 조회 비용을 줄이는 성능 도구지만 정합성 비용을 만든다.

캐시 적용 전 stale data 허용 시간과 무효화 기준을 정해야 한다.

cache hit ratio만 보지 말고 Redis latency, timeout, DB fallback, eviction을 함께 봐야 한다.

Redis 장애가 API 장애로 전파되지 않도록 timeout과 fallback을 설계한다.

캐시 miss가 몰리는 cache stampede는 DB 장애로 이어질 수 있다.

TTL jitter와 single-flight 같은 방어로 대량 만료와 동시 miss를 완화할 수 있다.

## 꼬리 질문

- 어떤 데이터가 캐시에 적합한가?
- cache hit ratio가 높아도 API가 느릴 수 있는 이유는 무엇인가?
- Redis 장애가 발생하면 API는 어떻게 동작해야 하는가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/redis/cache-aside-and-ttl|cache-aside-and-ttl]]
- [[01-core/redis/redis-failure-and-fallback|redis-failure-and-fallback]]
- [[01-core/redis/redis-monitoring|redis-monitoring]]
