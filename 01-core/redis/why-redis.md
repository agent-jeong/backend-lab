---
title: Redis를 사용하는 이유
description: Redis를 실무에서 사용하는 이유와 주의점
---

# Redis를 사용하는 이유

## 한 줄 정의

Redis는 메모리 기반 Key-Value 저장소로, 빠른 읽기/쓰기와 만료 정책이 필요한 보조 데이터 처리에 자주 사용된다.

## 실무에서 왜 문제 되는가

- Redis를 단순히 "빠른 DB"로 보면 핵심 데이터를 잘못 저장해 정합성 문제가 생긴다.
- 캐시, 세션, 분산 락, 랭킹, rate limit처럼 목적이 다른 기능을 같은 Redis에 섞으면 장애 영향 범위가 커진다.
- TTL, eviction, 장애 시 fallback을 고려하지 않으면 Redis 장애가 곧 서비스 장애로 전파된다.
- 메모리 저장소이므로 데이터 크기, key 개수, 만료 정책을 관리하지 않으면 OOM이나 eviction으로 예상치 못한 데이터 손실이 생긴다.

## 대표 사용처

| 사용처 | 예시 | 주의점 |
|---|---|---|
| 캐시 | 상품 상세, 설정값, 집계 결과 | 원본 DB와 정합성 차이가 생길 수 있다 |
| 세션 저장소 | 로그인 세션, 인증 상태 | Redis 장애 시 로그아웃 또는 인증 실패가 발생할 수 있다 |
| 분산 락 | 중복 처리 방지, 단일 작업 실행 | 락 만료 시간과 작업 시간이 어긋나면 동시 실행될 수 있다 |
| 카운터 | 조회수, rate limit | 정확한 영속성이 필요하면 DB 반영 전략이 필요하다 |
| Pub/Sub | 서버 간 간단한 이벤트 전달 | 메시지 유실 가능성을 고려해야 한다 |
| Sorted Set | 랭킹, 우선순위 목록 | 점수 갱신과 조회 패턴을 함께 설계해야 한다 |

## 동작 원리

1. 애플리케이션이 key로 Redis에 값을 조회하거나 저장한다.
2. Redis는 대부분의 데이터를 메모리에서 처리하므로 응답이 빠르다.
3. key에 TTL을 설정하면 시간이 지난 뒤 자동으로 만료된다.
4. 메모리가 부족하면 설정된 eviction policy에 따라 일부 key가 제거될 수 있다.
5. Redis가 느려지거나 장애가 나면 Redis를 호출하는 애플리케이션 경로도 함께 느려질 수 있다.

## 실무 판단 기준

| 상황 | Redis 사용 판단 | 이유 |
|---|---|---|
| 자주 읽고 변경이 적은 데이터 | 적합 | 캐시로 DB 부하와 응답 시간을 줄일 수 있다 |
| 반드시 최신이어야 하는 결제/재고 원본 데이터 | 부적합 | 원본 저장소는 정합성과 트랜잭션을 보장해야 한다 |
| 짧은 시간 중복 요청을 막아야 함 | 조건부 적합 | TTL 기반 key나 분산 락으로 처리할 수 있지만 실패 시나리오가 필요하다 |
| 대용량 검색/분석 | 부적합 | 검색 엔진이나 분석 저장소가 더 적합할 수 있다 |
| 장애 시 없어도 되는 보조 데이터 | 적합 | fallback 또는 재계산이 가능하면 Redis 의존도가 낮다 |

## 자주 나는 실수

- 핵심 비즈니스 데이터를 Redis에만 저장한다.
- 모든 key에 TTL을 걸지 않아 오래된 데이터가 계속 쌓인다.
- key 이름 규칙이 없어 장애 분석과 삭제 범위 판단이 어렵다.
- Redis timeout을 길게 잡아 장애 시 애플리케이션 스레드가 함께 고갈된다.
- 캐시 hit ratio만 보고 stale data, eviction, timeout, fallback 실패를 보지 않는다.

## 확인 방법

- 테스트: Redis 장애, timeout, 느린 응답 상황에서 서비스가 어떻게 동작하는지 확인한다.
- 로그: Redis timeout, connection pool exhaustion, fallback 실행 여부를 남긴다.
- 메트릭: hit ratio, latency, memory usage, evicted keys, expired keys, connected clients를 본다.
- 운영 점검: key prefix, TTL 분포, big key, hot key를 주기적으로 확인한다.

## 실무 체크리스트

- 이 데이터는 Redis에 없어도 DB나 기본값으로 복구 가능한가?
- TTL이 없거나 너무 긴 key가 쌓이지 않는가?
- Redis timeout이 API timeout보다 충분히 짧은가?
- Redis connection pool이 고갈될 때 애플리케이션이 어떻게 동작하는가?
- key prefix로 기능, 데이터 종류, 삭제 범위를 구분할 수 있는가?
- 캐시 hit ratio와 함께 DB QPS, Redis latency, eviction도 같이 보고 있는가?

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 메모리 기반이라 응답이 빠르다 | 메모리 비용이 크고 용량 관리가 필요하다 |
| TTL과 다양한 자료구조를 제공한다 | 복잡한 질의나 관계형 트랜잭션에는 적합하지 않다 |
| DB 부하를 줄일 수 있다 | 캐시 정합성과 무효화 문제가 생긴다 |
| 분산 환경의 보조 상태를 다루기 쉽다 | Redis 장애가 애플리케이션 장애로 전파될 수 있다 |

## 짧은 예제

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

이 예제에서 Redis는 원본 저장소가 아니라 읽기 성능을 높이는 보조 저장소다. Redis 조회가 실패해도 DB 조회로 대체할 수 있어야 한다.

## 핵심 요약

Redis는 빠른 메모리 저장소지만, 실무에서는 "어떤 문제를 Redis로 풀 것인가"가 더 중요하다. 캐시, 세션, 분산 락, 카운터처럼 Redis에 적합한 사용처는 대부분 보조 상태나 짧은 생명주기의 데이터다. 핵심 원본 데이터는 DB에 두고 Redis는 성능, 부하 완화, 임시 상태 관리에 사용한다. Redis를 도입하면 TTL, key 설계, 메모리 사용량, 장애 시 fallback을 함께 설계해야 한다. Redis가 빠르다는 이유만으로 모든 조회를 Redis로 옮기면 정합성과 운영 복잡도가 커질 수 있다.

## 꼬리 질문

- Redis를 DB 대신 사용하면 어떤 문제가 생길 수 있는가?
- Redis와 RDB의 역할 차이를 어떻게 설명할 수 있는가?
- 캐시 데이터가 오래되어도 되는 기준은 어떻게 정하는가?
- Redis 장애 시 서비스가 계속 동작해야 하는 기능과 실패해도 되는 기능은 어떻게 나누는가?
- Redis를 쓰면 항상 성능이 좋아지는가?
- Redis에 저장하면 안 되는 데이터는 무엇인가?
- Redis latency가 갑자기 증가하면 어떤 지표부터 확인할 것인가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
