---
title: Cache 적용
description: 캐시를 붙일 때 hit ratio와 함께 옛 값, 장애 전파까지 따져 보는 방법
tags: [concept, performance]
---

# Cache 적용

캐시는 같은 조회를 반복하지 않으려고 결과를 빠른 저장소에 담아 두는 방법이다. 붙일 때는 옛 값을 얼마나 보여 줄지, TTL, 장애 대응, stampede까지 같이 정해야 한다.

캐시를 붙인다고 늘 빨라지지는 않는다. 상품 정보를 캐시하면 DB 부하는 줄지만, 가격이 바뀐 뒤에도 잠깐 옛 가격이 보인다. miss가 한꺼번에 몰리면 DB가 넘어가고, Redis 장애가 API 장애로 번지면 캐시가 오히려 장애를 만든다. 자주 바뀌는 데이터는 캐시를 지우는 비용이 얻는 속도보다 클 때도 있다. 그래서 붙이기 전에 옛 값을 얼마나 오래 봐줄지와 언제 캐시를 지울지부터 정한다.

## 캐시를 거치는 흐름

1. 캐시할 데이터와 옛 값 허용 시간을 정한다.
2. cache aside 같은 패턴으로 먼저 캐시를 조회한다.
3. miss면 DB를 조회하고 캐시에 저장한다.
4. 원본 데이터가 바뀌면 캐시를 삭제하거나 갱신한다.
5. Redis가 죽으면 timeout, fallback, circuit breaker로 API까지 같이 죽지 않게 막는다.

```java
ProductSummary cached = cache.get(key);
if (cached != null) {
    return cached;
}

ProductSummary summary = productRepository.findSummary(productId);
cache.set(key, summary, Duration.ofMinutes(5));
return summary;
```

가장 단순한 cache aside 흐름이다. 실제로는 Redis timeout, 캐시 저장 실패, stampede, 원본이 바뀌었는데 캐시 삭제가 실패하는 경우까지 다뤄야 한다.

stampede가 걱정되는 key에는 TTL jitter, mutex/single-flight, stale-while-revalidate 같은 방어를 검토한다. 어느 쪽이든 miss 난 요청이 한꺼번에 DB로 몰리지 않게 하려는 것이다.

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

- TTL과 캐시를 지울 시점을 정하지 않으면, 옛 값이 언제까지 남을지 아무도 모른다.
- Redis timeout을 길게 잡으면, 캐시를 기다리다 API가 timeout 난다.
- hit ratio만 보면, 수치가 높아도 hot key, big key, Redis latency 때문에 API가 느린 걸 놓친다.
- 캐시 삭제 실패와 DB fallback 부하를 지켜보지 않으면, 옛 값이 남거나 DB가 버거워져도 늦게 안다.
- 모든 key에 같은 TTL을 주면, 한꺼번에 만료되어 DB로 요청이 몰린다.
- stampede를 막지 않으면, miss 난 요청이 전부 DB로 간다.
- 원본이 바뀔 때 캐시 값을 직접 덮어쓰면(set), 동시에 들어온 쓰기 두 건이 캐시에 반영되는 순서가 DB와 뒤바뀔 때 옛 값이 TTL까지 남는다. 그래서 보통은 DB commit 뒤에 캐시를 지운다.
- DB commit 전에 캐시를 지우면, 그 사이 들어온 조회가 commit 전 값을 다시 캐시에 채운다. commit 뒤에 지워도 같은 경합이 드물게 남으니 TTL을 안전망으로 둔다.

## 운영에서 볼 것

- cache cold와 cache warm 상태를 나눠 측정한다.
- cache hit/miss, Redis timeout, fallback, invalidation failure를 로그로 남긴다.
- hit ratio, Redis latency, DB QPS, evicted keys, hot key를 본다.
- Redis timeout이나 장애가 났을 때 API가 fallback으로 넘어가는지 장애 실험으로 확인한다.
- cache cold 상태에서 miss가 몰릴 때 DB QPS와 latency가 버티는지 부하 테스트로 확인한다.

## 한 번에 설명하기

> 캐시는 같은 조회를 덜 하게 해 주지만, 그 대가로 옛 값을 보여 주는 시간이 생깁니다.
>
> 그래서 붙이기 전에 옛 값을 얼마나 봐줄지와 언제 캐시를 지울지부터 정합니다. 붙인 뒤에는 hit ratio만 보지 않고 Redis latency, timeout, DB fallback, eviction을 같이 봅니다.
>
> Redis 장애가 API 장애로 번지지 않게 timeout과 fallback을 두고, miss가 몰려 DB가 넘어가는 stampede는 TTL jitter와 single-flight로 줄입니다.

## 꼬리 질문

- 어떤 데이터가 캐시에 적합한가?
- cache hit ratio가 높아도 API가 느릴 수 있는 이유는 무엇인가?
- Redis 장애가 발생하면 API는 어떻게 동작해야 하는가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Cache Abstraction](https://docs.spring.io/spring-framework/reference/integration/cache.html)
- [Redis Docs: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[01-core/redis/cache-aside-and-ttl|cache-aside-and-ttl]]
- [[01-core/redis/redis-failure-and-fallback|redis-failure-and-fallback]]
- [[01-core/redis/redis-monitoring|redis-monitoring]]
