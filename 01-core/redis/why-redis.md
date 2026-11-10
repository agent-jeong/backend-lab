---
title: Redis를 사용하는 이유
description: Redis를 실무에서 사용하는 이유와 주의점
---

# Redis를 사용하는 이유

Redis는 메모리 기반 Key-Value 저장소다. 읽기/쓰기가 빠르고 만료 정책이 있어서, 캐시·세션·락·카운터처럼 원본이 아닌 보조 데이터를 다루는 데 자주 쓴다.

Redis를 "빠른 DB"로 보면 핵심 데이터를 잘못 넣게 된다. 도입할 때 먼저 물을 것은 속도가 아니라 **이 데이터가 Redis에서 사라져도 DB나 기본값으로 복구되는가**다.

## 동작

1. 애플리케이션이 key로 Redis에 값을 조회하거나 저장한다.
2. Redis는 대부분의 데이터를 메모리에서 처리하므로 응답이 빠르다.
3. key에 TTL을 걸면 시간이 지난 뒤 자동으로 만료된다.
4. 메모리가 부족하면 설정된 eviction policy에 따라 일부 key가 제거된다.
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

여기서 Redis는 원본 저장소가 아니라 읽기를 빠르게 하는 보조 저장소다. Redis 조회가 실패해도 DB 조회로 대신할 수 있어야 한다.

## 대표 사용처

| 사용처 | 예시 | 조심할 점 |
|---|---|---|
| 캐시 | 상품 상세, 설정값, 집계 결과 | 원본 DB와 값이 달라질 수 있다 |
| 세션 저장소 | 로그인 세션, 인증 상태 | Redis 장애 시 로그아웃이나 인증 실패가 생긴다 |
| 분산 락 | 중복 처리 방지, 단일 작업 실행 | 락 만료 시간과 작업 시간이 어긋나면 동시 실행된다 |
| 카운터 | 조회수, rate limit | 정확히 남아야 하면 DB 반영 전략이 따로 필요하다 |
| Pub/Sub | 서버 간 간단한 이벤트 전달 | 메시지가 유실될 수 있다 |
| Sorted Set | 랭킹, 우선순위 목록 | 점수 갱신과 조회 패턴을 같이 설계해야 한다 |

## 쓸지 말지

| 상황 | 판단 | 이유 |
|---|---|---|
| 자주 읽고 잘 안 바뀌는 데이터 | 쓴다 | 캐시로 DB 부하와 응답 시간을 줄인다 |
| 꼭 최신이어야 하는 결제/재고 원본 데이터 | 안 쓴다 | 원본 저장소는 정합성과 트랜잭션을 보장해야 한다 |
| 짧은 시간 중복 요청을 막아야 함 | 조건부 | TTL 기반 key나 분산 락으로 되지만 실패 시나리오가 있어야 한다 |
| 대용량 검색/분석 | 안 쓴다 | 검색 엔진이나 분석 저장소가 더 맞다 |
| 장애 때 없어도 되는 보조 데이터 | 쓴다 | fallback이나 재계산이 되면 Redis 의존도가 낮다 |

메모리 기반이라 빠르지만 메모리 비용이 크고, 복잡한 질의나 관계형 트랜잭션에는 맞지 않는다. TTL과 여러 자료구조 덕분에 분산 환경의 보조 상태를 다루기는 쉽다.

## 자주 깨지는 곳

- **핵심 비즈니스 데이터를 Redis에만 둔다.** eviction이나 장애로 사라지면 복구할 원본이 없다.
- **TTL을 걸지 않는다.** 오래된 데이터가 계속 쌓이고, 메모리가 차면 OOM이나 eviction으로 예상 못 한 데이터가 사라진다.
- **key 이름 규칙이 없다.** 장애 분석과 삭제 범위 판단이 어렵다.
- **Redis timeout을 길게 잡는다.** Redis가 멈추면 애플리케이션 스레드가 같이 고갈된다. timeout은 API timeout보다 충분히 짧게 둔다.
- **캐시, 세션, 분산 락, 랭킹, rate limit을 한 Redis에 섞는다.** 장애 하나의 영향 범위가 전부로 커진다.
- **hit ratio만 본다.** 옛 값 노출, eviction, timeout, fallback 실패를 놓친다.

## 운영에서 볼 것

- 테스트: Redis 장애, timeout, 느린 응답에서 서비스가 어떻게 동작하는지 확인한다. connection pool이 고갈될 때도 본다.
- 로그: Redis timeout, connection pool exhaustion, fallback 실행 여부.
- 메트릭: hit ratio, latency, memory usage, evicted keys, expired keys, connected clients. hit ratio 옆에 DB QPS를 둔다.
- 주기 점검: key prefix, TTL 분포, big key, hot key.

## 면접에서 말하기

> Redis는 메모리 기반 저장소라 빠르지만, 저는 무엇을 Redis로 풀지부터 정합니다. 캐시, 세션, 분산 락, 카운터처럼 사라져도 DB나 기본값으로 복구되는 보조 상태만 두고, 원본 데이터는 DB에 둡니다. 도입할 때는 TTL, key 설계, 메모리 사용량, 장애 시 fallback을 같이 설계합니다. 빠르다는 이유로 모든 조회를 Redis로 옮기면 정합성과 운영 복잡도가 커집니다.

## 꼬리 질문

- Redis를 DB 대신 사용하면 어떤 문제가 생기나?
- Redis와 RDB의 역할 차이를 어떻게 설명하나?
- 캐시 데이터가 오래돼도 되는 기준은 어떻게 정하나?
- Redis 장애 시 계속 동작해야 하는 기능과 실패해도 되는 기능은 어떻게 나누나?
- Redis를 쓰면 항상 성능이 좋아지나?
- Redis에 저장하면 안 되는 데이터는?
- Redis latency가 갑자기 오르면 어떤 지표부터 볼 것인가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
