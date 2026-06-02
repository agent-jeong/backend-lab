---
title: Cache Aside와 TTL
description: Redis 캐시 적용 시 정합성과 만료 정책을 다루는 실무 기준
---

# Cache Aside와 TTL

## 한 줄 정의

Cache Aside는 애플리케이션이 캐시 조회, DB 조회, 캐시 저장을 직접 제어하는 캐시 전략이고, TTL은 캐시 데이터의 최대 생존 시간이다.

## 실무에서 왜 문제 되는가

- 캐시는 응답 시간을 줄이지만 원본 DB와 값이 달라질 수 있다.
- TTL이 너무 길면 오래된 데이터를 보여주고, 너무 짧으면 캐시 효과가 약해진다.
- 캐시 미스가 한 번에 몰리면 DB 부하가 급증하는 cache stampede가 발생할 수 있다.
- 캐시 삭제와 DB 변경 순서를 잘못 잡으면 변경 후에도 이전 값을 계속 읽을 수 있다.

## 동작 원리

1. 애플리케이션이 Redis에서 key를 조회한다.
2. 캐시 hit이면 Redis 값을 반환한다.
3. 캐시 miss이면 DB에서 원본 데이터를 조회한다.
4. 조회 결과를 Redis에 TTL과 함께 저장한다.
5. 원본 데이터가 변경되면 관련 캐시를 삭제하거나 갱신한다.
6. TTL이 지나면 Redis가 key를 만료시키고 다음 요청에서 다시 DB를 조회한다.

## 실무 판단 기준

| 상황 | 전략 | 이유 |
|---|---|---|
| 변경이 적고 조회가 많은 데이터 | Cache Aside + 긴 TTL | 캐시 효율이 높고 정합성 부담이 낮다 |
| 변경 직후 최신 값이 중요함 | 짧은 TTL + 변경 시 캐시 삭제 | stale data 노출 시간을 줄인다 |
| 값 계산 비용이 큼 | Cache Aside + mutex 또는 사전 갱신 | 캐시 미스 시 DB와 CPU 부하가 커질 수 있다 |
| 데이터 없음도 자주 조회됨 | null 캐싱 + 짧은 TTL | 반복적인 DB miss를 줄인다 |
| 장애 시 기본값이 가능함 | fallback 값 사용 | Redis 장애가 서비스 장애로 번지는 것을 줄인다 |

## 캐시 무효화 기준

| 방식 | 설명 | 한계 |
|---|---|---|
| TTL 만료 | 일정 시간이 지나면 자동 삭제 | TTL 동안 오래된 값이 보일 수 있다 |
| 변경 시 삭제 | DB 변경 후 관련 key 삭제 | 삭제 실패나 key 누락에 취약하다 |
| 변경 시 갱신 | DB 변경 후 새 값으로 캐시 갱신 | 동시성 상황에서 이전 값으로 덮일 수 있다 |
| 버전 key | key에 버전이나 갱신 시각 포함 | key 관리와 저장 공간이 복잡해진다 |

## 자주 나는 실수

- TTL 없이 캐시를 저장해 오래된 데이터가 계속 남는다.
- 캐시 key에 조회 조건을 충분히 반영하지 않아 다른 요청의 값을 반환한다.
- DB 변경과 캐시 삭제를 하나의 완전한 트랜잭션처럼 오해한다.
- Redis 장애 시 fallback 없이 요청 전체를 실패시킨다.
- 캐시 삭제 실패 로그를 남기지 않아 정합성 문제를 추적하지 못한다.
- 캐시 미스가 몰리는 상황을 고려하지 않아 배포 직후 DB 부하가 튄다.

## 확인 방법

- 테스트: 데이터 변경 후 캐시가 삭제되거나 TTL 내 stale data 허용 범위에 있는지 확인한다.
- 로그: cache hit/miss, 캐시 삭제 실패, Redis timeout, fallback 실행을 남긴다.
- 메트릭: hit ratio, Redis latency, DB QPS, evicted keys, expired keys를 함께 본다.
- 장애 실험: Redis 연결 실패와 캐시 전체 만료 상황에서 DB와 API가 버티는지 확인한다.

## 실무 체크리스트

- 캐시 key가 모든 조회 조건을 포함하는가?
- TTL의 근거가 업무 허용 오차로 설명 가능한가?
- DB 변경 후 삭제해야 할 key 목록이 명확한가?
- 캐시 삭제 실패가 로그와 메트릭으로 드러나는가?
- Redis 장애 시 DB fallback 또는 기본값 응답이 가능한가?
- 특정 key 만료 시 DB 요청이 한 번에 몰리지 않도록 대비했는가?
- null 캐싱이 필요한 조회인지, 필요하다면 TTL을 짧게 잡았는가?

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 읽기 지연과 DB 부하를 줄인다 | 원본 DB와 캐시가 일시적으로 다를 수 있다 |
| 애플리케이션에서 제어하기 쉬운 패턴이다 | 캐시 key와 무효화 로직을 직접 관리해야 한다 |
| TTL로 오래된 데이터의 생존 시간을 제한한다 | 적절한 TTL을 정하려면 업무 허용 오차를 알아야 한다 |
| Redis 장애 시 DB fallback을 설계할 수 있다 | fallback이 몰리면 DB 장애로 이어질 수 있다 |

## 짧은 예제

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

이 예제는 읽기에서 Cache Aside를 사용하고, DB 트랜잭션 커밋 후 관련 캐시를 삭제한다. 캐시 삭제를 커밋 전에 실행하면 다른 요청이 아직 커밋되지 않은 이전 DB 값을 다시 캐시에 저장할 수 있다. 실무에서는 transaction synchronization, 이벤트 발행, outbox 등을 사용해 커밋 이후 삭제하고, Redis 삭제 실패를 로깅하거나 짧은 TTL로 stale data 노출 시간을 제한한다.

## 핵심 요약

Cache Aside는 캐시를 먼저 보고, 없으면 DB를 조회한 뒤 Redis에 저장하는 가장 흔한 캐시 패턴이다. TTL은 캐시 데이터가 오래 남아 정합성 문제를 만드는 것을 제한한다. 캐시를 적용할 때는 성능 개선뿐 아니라 stale data 허용 시간, 캐시 삭제 실패, Redis 장애, cache stampede를 함께 봐야 한다. 변경이 잦고 최신성이 중요한 데이터는 캐시 효과보다 정합성 비용이 클 수 있다. 좋은 캐시 설계는 "얼마나 빠른가"보다 "틀린 값을 얼마나 오래 보여줘도 되는가"를 먼저 정한다.

## 꼬리 질문

- TTL을 5분으로 정했다면 그 근거는 무엇인가?
- DB 변경 후 캐시 삭제가 실패하면 어떤 문제가 생기는가?
- 캐시 삭제와 DB 업데이트 순서는 어떻게 잡는가?
- 캐시 미스가 동시에 몰릴 때 DB 부하를 어떻게 줄일 수 있는가?
- 캐시를 적용하면 안 되는 데이터는 무엇인가?
- cache hit ratio가 높아도 장애가 날 수 있는 이유는 무엇인가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[why-redis]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/transaction/transaction|transaction]]
