---
title: Cache Aside와 TTL
description: Redis 캐시를 붙일 때 TTL을 어떻게 잡고, 원본이 바뀌면 캐시를 어떻게 비우는지
tags: [concept, redis]
---

# Cache Aside와 TTL

Cache Aside는 애플리케이션이 캐시를 먼저 보고, 없으면 DB에서 읽어 캐시에 넣는 방식이다. TTL은 그렇게 넣은 값이 캐시에 남아 있는 최대 시간이다.

캐시를 붙이면 빨라지는 대신 DB와 다른 값이 보이는 시간이 생긴다. 상품 이름이 바뀌었는데 몇 분 동안 옛 이름이 보이는 식이다. 그래서 캐시를 설계할 때는 얼마나 빨라지는지보다 "옛 값을 얼마나 오래 보여 줘도 되나"를 먼저 정한다. TTL은 그 시간을 숫자로 적은 것이다.

## 동작

1. Redis에서 key를 조회한다.
2. 있으면(hit) 그 값을 돌려준다.
3. 없으면(miss) DB에서 읽고, TTL을 붙여 Redis에 저장한다.
4. 원본이 바뀌면 해당 key를 지운다.
5. TTL이 지나면 Redis가 key를 지우고, 다음 요청이 다시 DB를 읽는다.

```java
public ProductSummary getProductSummary(Long productId) {
    String key = "product:summary:" + productId;

    ProductSummary cached = redisTemplate.opsForValue().get(key);
    if (cached != null) {
        return cached;
    }

    ProductSummary summary = productRepository.findSummary(productId);
    redisTemplate.opsForValue().set(key, summary, Duration.ofMinutes(5));
    return summary;
}

@Transactional
public void updateProductName(Long productId, String name) {
    productRepository.updateName(productId, name);

    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
        @Override
        public void afterCommit() {
            redisTemplate.delete("product:summary:" + productId);
        }
    });
}
```

캐시는 커밋한 뒤에 지운다. 커밋 전에 지우면, 그 사이에 들어온 다른 요청이 아직 바뀌기 전 DB 값을 읽어 캐시에 다시 넣는다. 커밋 뒤에 지우는 일은 transaction synchronization, 이벤트, outbox 중 하나로 건다.

커밋 뒤에 지워도 틈은 남는다. 커밋 전에 옛 값을 읽어 간 요청이 삭제가 끝난 뒤에 캐시를 채우면, 옛 값이 다시 들어간다. 이 옛 값이 남는 시간의 상한이 TTL이다.

## 데이터별로 어떻게 잡나

| 데이터 | 전략 | 이유 |
|---|---|---|
| 잘 안 바뀌고 많이 읽힘 | 긴 TTL | 틀릴 일이 적어서 오래 둬도 된다 |
| 바뀐 직후 바로 보여야 함 | 짧은 TTL + 변경 시 삭제 | 틀린 값이 보이는 시간을 줄인다 |
| 만드는 데 비용이 큼 | mutex 또는 미리 갱신 | miss 한 번에 DB와 CPU 사용량이 같이 튄다 |
| "없음" 조회가 잦음 | 빈 결과도 짧게 캐싱 | 같은 miss가 계속 DB로 가는 걸 막는다 |
| 기본값으로 버틸 수 있음 | Redis 장애 시 기본값 응답 | Redis 장애가 서비스 장애로 번지지 않는다 |

## 캐시를 비우는 방법

| 방식 | 동작 | 약한 곳 |
|---|---|---|
| TTL 만료 | 시간이 지나면 자동 삭제 | TTL 동안은 옛 값이 보인다 |
| 변경 시 삭제 | DB를 바꾼 뒤 key 삭제 | 삭제가 실패하거나 key를 빠뜨리면 남는다 |
| 변경 시 덮어쓰기 | DB를 바꾼 뒤 새 값 저장 | 동시 요청이 옛 값으로 다시 덮을 수 있다 |
| 버전 key | key에 버전이나 갱신 시각을 넣음 | key 관리가 복잡하고 공간을 더 쓴다 |

보통은 "변경 시 삭제"를 쓴다. 그리고 삭제가 실패해도 TTL이 지나면 결국 맞춰지도록 TTL도 함께 건다.

## 자주 깨지는 곳

- TTL 없이 저장하면, 삭제가 한 번만 실패해도 옛 값이 영영 남는다.
- key에 조회 조건을 다 넣지 않으면, 다른 사용자나 다른 조건으로 만든 결과가 그대로 응답으로 나간다.
- DB 변경과 캐시 삭제는 하나의 트랜잭션이 아니다. 둘 다 성공한다고 믿고 넘어가면 삭제 실패를 모르고 지나치니, 로그와 메트릭으로 드러나게 한다.
- 인기 key가 만료되는 순간을 대비하지 않으면, 같은 key의 miss가 한꺼번에 DB로 몰린다(cache stampede). 배포 직후 캐시가 비었을 때도 마찬가지다.
- Redis가 죽었을 때 대안이 없으면 캐시 조회 실패가 곧 요청 실패가 된다. 그렇다고 모든 요청을 DB로 돌리면 이번엔 DB가 넘어간다.

## 운영에서 볼 것

- hit ratio만 보지 말고 Redis latency, DB QPS, evicted·expired key 수를 같이 본다.
- 캐시 삭제 실패, Redis timeout, fallback 실행은 로그로 남긴다.
- Redis 연결을 끊거나 캐시를 전부 비운 상태에서 DB와 API가 버티는지 한 번은 실험해 본다.

## 한 번에 설명하기

> Cache Aside는 캐시를 먼저 보고, 없으면 DB를 읽어 캐시에 넣는 방식입니다. 그 대신 DB와 캐시가 잠깐 다를 수 있어서, TTL을 정할 때는 이 데이터가 옛 값으로 몇 분까지 보여도 되는지부터 확인합니다.
>
> 원본이 바뀌면 커밋한 뒤에 key를 지우고, 삭제가 실패해도 TTL이 지나면 맞춰지게 합니다.
>
> 인기 key가 만료될 때 요청이 DB로 몰리는 경우와, Redis가 죽었을 때 어디로 돌릴지도 같이 정해 둡니다.

## 꼬리 질문

- TTL을 5분으로 정했다면 그 근거는?
- DB 변경 후 캐시 삭제가 실패하면 어떻게 되나?
- 캐시 삭제와 DB 업데이트 순서는 어떻게 잡나?
- 캐시 miss가 한꺼번에 몰리면 DB 부하를 어떻게 줄이나?
- 캐시를 쓰면 안 되는 데이터는?
- hit ratio가 높은데도 장애가 날 수 있는 이유는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: EXPIRE](https://redis.io/docs/latest/commands/expire/)
- [Redis Docs: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[why-redis]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/transaction/transaction|transaction]]
