---
title: Cache 적용
description: 캐시로 성능을 개선할 때 hit ratio, 정합성, 장애 전파를 함께 보는 기준
tags: [concept, performance]
---

# Cache 적용

캐시는 반복 조회 비용을 줄이려고 빠른 저장소에 결과를 저장하는 방법이다. 대신 정합성, TTL, 장애 대응, stampede를 같이 설계해야 한다.

캐시를 붙인다고 항상 빨라지지는 않는다. DB 부하를 줄이는 대신 옛 값을 보여 주는 시간이 생기고, miss가 한꺼번에 몰리면 DB가 넘어가고, Redis 장애가 API 장애로 번지면 캐시가 오히려 장애 원인이 된다. 변경이 잦은 데이터는 무효화 비용이 성능 이득보다 클 수 있다. 그래서 적용 전에 옛 값을 얼마나 오래 허용할지와 무효화 기준부터 정한다.

## 동작

1. 캐시할 데이터와 옛 값 허용 시간을 정한다.
2. cache aside 같은 패턴으로 먼저 캐시를 조회한다.
3. miss면 DB를 조회하고 캐시에 저장한다.
4. 원본 데이터가 바뀌면 캐시를 삭제하거나 갱신한다.
5. Redis 장애 시 timeout, fallback, circuit breaker로 API 장애 전파를 줄인다.

```java
ProductSummary cached = cache.get(key);
if (cached != null) {
    return cached;
}

ProductSummary summary = productRepository.findSummary(productId);
cache.set(key, summary, Duration.ofMinutes(5));
return summary;
```

단순 cache aside 흐름이다. 실제로는 Redis timeout, 캐시 저장 실패, stampede, 원본 변경 시 삭제 실패까지 같이 다뤄야 한다.

stampede 위험이 있는 key는 TTL jitter, mutex/single-flight, stale-while-revalidate 같은 방어를 검토한다. 목표는 miss 요청이 모두 동시에 DB로 가지 않게 하는 것이다.

## 어떤 데이터에 맞나

| 상황 | 캐시 적합도 | 이유 |
|---|---|---|
| 읽기 많고 변경 적음 | 높음 | hit ratio를 기대할 수 있다 |
| 최신성이 매우 중요 | 낮음 | 옛 값 허용이 어렵다 |
| 계산 비용 높음 | 검토 | 결과 캐시로 CPU/DB 비용을 줄일 수 있다 |
| hot key 집중 | 주의 | Redis 단일 key 병목이 될 수 있다 |
| miss 폭증 가능 | 주의 | cache stampede 방어가 필요하다 |
| 만료 시간이 같은 key 많음 | TTL jitter 적용 | 동시에 만료되어 DB 부하가 몰리는 것을 줄인다 |

## 자주 깨지는 곳

- **TTL과 무효화 정책을 정하지 않는다.**
- **Redis timeout을 길게 잡는다.** 캐시 대기가 API timeout이 된다.
- **hit ratio만 본다.** 높아도 hot key, big key, Redis latency 때문에 API가 느릴 수 있다.
- **캐시 삭제 실패와 DB fallback 부하를 모니터링하지 않는다.**
- **모든 key에 같은 TTL을 준다.** 동시에 대량 만료된다.
- **stampede 방어 없이 둔다.** miss 요청이 전부 DB로 간다.
- **원본 변경 시 캐시 값을 직접 덮어쓴다(set).** 동시 쓰기 두 건의 캐시 반영 순서가 DB와 뒤바뀌면 옛 값이 TTL까지 남는다. 보통은 DB commit 후 캐시를 삭제한다.
- **DB commit 전에 캐시를 삭제한다.** 그 사이 들어온 조회가 commit 전 값을 다시 캐시에 채운다. commit 후 삭제해도 같은 경합이 드물게 남으므로 TTL을 안전망으로 둔다.

## 운영에서 볼 것

- cache cold와 cache warm 상태를 나눠 측정한다.
- cache hit/miss, Redis timeout, fallback, invalidation failure를 로그로 남긴다.
- hit ratio, Redis latency, DB QPS, evicted keys, hot key를 본다.
- Redis timeout이나 장애 시 API가 fallback하는지 장애 실험으로 확인한다.
- cache cold 상태에서 miss가 몰릴 때 DB QPS와 latency가 버티는지 부하 테스트로 확인한다.

## 면접에서 말하기

> 캐시는 반복 조회 비용을 줄이는 대신 정합성 비용을 만드는 도구입니다. 저는 적용 전에 옛 값을 얼마나 허용할지와 무효화 기준을 먼저 정하고, hit ratio만이 아니라 Redis latency, timeout, DB fallback, eviction을 같이 봅니다. Redis 장애가 API 장애로 번지지 않게 timeout과 fallback을 두고, miss가 몰려 DB가 넘어가는 stampede는 TTL jitter와 single-flight로 완화합니다.

## 꼬리 질문

- 어떤 데이터가 캐시에 적합한가?
- cache hit ratio가 높아도 API가 느릴 수 있는 이유는 무엇인가?
- Redis 장애가 발생하면 API는 어떻게 동작해야 하는가?

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/redis/cache-aside-and-ttl|cache-aside-and-ttl]]
- [[01-core/redis/redis-failure-and-fallback|redis-failure-and-fallback]]
- [[01-core/redis/redis-monitoring|redis-monitoring]]
