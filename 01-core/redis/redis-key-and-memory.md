---
title: Redis Key 설계와 메모리 관리
description: Redis key naming, TTL, hot key, big key, memory eviction 관리 기준
tags: [concept, redis]
---

# Redis Key 설계와 메모리 관리

Redis key 설계와 메모리 관리는 key 이름, TTL, 데이터 크기, eviction 정책을 정해 두고 Redis를 예측 가능하게 운영하는 일이다.

Redis key는 그냥 문자열이 아니라 **운영 단위**다. 규칙 없이 쌓으면 장애 때 무엇을 지워도 되는지 판단할 수 없고, TTL 없는 key가 쌓이면 메모리가 차서 eviction이 시작된다.

## Key 이름 규칙

| 기준 | 예시 | 이유 |
|---|---|---|
| 기능 prefix | `product:summary:{productId}` | 기능별로 조회, 삭제, 모니터링하기 쉽다 |
| 식별자 포함 | `user:session:{userId}` | key 충돌을 줄이고 추적하기 쉽다 |
| 조회 조건 포함 | `search:result:{keyword}:{page}` | 다른 조건의 캐시가 섞이지 않는다 |
| 버전 포함 | `product:v2:summary:{productId}` | 캐시 구조를 바꿔도 이전 key와 충돌하지 않는다 |
| TTL 기준 분리 | `rank:daily:{date}` | 만료 정책과 데이터 생명주기를 추적하기 쉽다 |

## 상황별 판단

| 상황 | 판단 | 이유 |
|---|---|---|
| 데이터를 다시 계산할 수 있음 | TTL 필수 | 메모리 누적을 막고 옛 값이 남는 시간을 제한한다 |
| 데이터가 자주 바뀜 | 짧은 TTL 또는 캐시하지 않음 | 무효화 비용이 캐시 이득보다 클 수 있다 |
| 특정 key에 요청 집중 | hot key 분산 검토 | 단일 key 병목으로 Redis latency가 오른다 |
| value가 큼 | 쪼개거나 저장 방식 변경 | big key는 삭제, 복제, 네트워크 비용을 키운다 |
| 범위 삭제가 필요함 | prefix 규칙 설계 | 운영 중 안전하게 scan/delete 할 수 있어야 한다 |

TTL은 정합성 허용 시간이면서 메모리 관리 기준이기도 하다. 캐시 key에는 기본으로 둔다.

## Hot Key와 Big Key

| 구분 | 의미 | 문제 | 대응 |
|---|---|---|---|
| hot key | 특정 key에 요청이 과도하게 몰림 | Redis CPU/latency 증가 | 로컬 캐시, key 분산, TTL jitter, 사전 계산 |
| big key | value나 자료구조 크기가 과도하게 큼 | 네트워크 지연, 삭제 지연, 복제 비용 증가 | 데이터 분할, 자료구조 재설계, lazy unlink |

hot key는 Redis의 단일 스레드 처리에 요청이 몰려 지연을 만든다. big key는 네트워크 전송, 삭제, 복제, 백업 비용을 모두 키운다.

## Eviction Policy

| 정책 | 의미 | 맞는 경우 |
|---|---|---|
| `noeviction` | 메모리 초과 시 쓰기 실패 | 데이터를 잃느니 실패하는 편이 나을 때 |
| `allkeys-lru` | 모든 key 중 덜 쓰인 key 제거 | 대부분이 캐시 데이터일 때 |
| `volatile-lru` | TTL이 있는 key 중 덜 쓰인 key 제거 | TTL이 있는 캐시만 지우고 싶을 때 |
| `allkeys-lfu` | 모든 key 중 덜 자주 쓰인 key 제거 | 사용 빈도 차이가 큰 캐시 |
| `volatile-ttl` | TTL이 짧은 key 우선 제거 | 만료가 임박한 캐시부터 지우고 싶을 때 |

maxmemory와 eviction policy를 모르고 운영하면 중요한 캐시가 예고 없이 사라진다. 같은 Redis에 세션, 락, 캐시를 섞을수록 정책을 고르기 어려워지므로, 중요도가 다른 데이터는 Redis 인스턴스나 DB를 나눈다.

## 자주 깨지는 곳

- **prefix 없이 임의 문자열로 저장한다.** 장애 때 어떤 key를 지워도 되는지 모른다.
- **TTL 없는 캐시 key를 계속 쌓는다.** 메모리가 차고 eviction이 시작된다.
- **운영에서 `KEYS *`로 전체 key를 조회한다.** 조사는 `SCAN`으로 한다.
- **큰 JSON을 String value 하나에 넣는다.** big key가 된다.
- **대량 key에 같은 TTL을 건다.** 한꺼번에 만료되어 DB로 miss가 몰린다.
- **eviction을 정상 동작으로만 본다.** 실제로는 캐시 miss 증가이고 DB 부하로 이어진다.

## 운영에서 볼 것

- 테스트: key 생성 규칙과 TTL 설정 여부를 통합 테스트에서 확인한다.
- 로그: 주요 cache key prefix, miss 원인, delete 실패.
- 메트릭: memory usage, used memory peak, evicted keys, expired keys, command latency.
- 점검: `SCAN` 기반 key 조사, big key 분석, hot key 분석, TTL 분포.

## 면접에서 말하기

> Redis key는 운영 단위라서 prefix, 식별자, 조회 조건, 버전을 일관되게 넣습니다. 그래야 장애 때 추적하고 범위를 정해 지울 수 있습니다. 캐시 key에는 TTL을 기본으로 두고, hot key는 요청 집중으로 latency를, big key는 전송·삭제·복제 비용을 만든다는 점을 봅니다. eviction policy는 그 Redis에 어떤 데이터를 섞었느냐에 따라 위험이 달라서, 중요도가 다른 데이터는 인스턴스를 나눕니다.

## 꼬리 질문

- Redis key prefix를 어떻게 설계할 것인가?
- TTL 없는 key가 쌓이면 어떤 문제가 생기나?
- hot key와 big key는 각각 어떤 증상으로 드러나나?
- `KEYS *` 대신 `SCAN`을 써야 하는 이유는?
- eviction policy를 잘못 고르면 어떤 데이터가 사라지나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Redis Docs: Keys and values](https://redis.io/docs/latest/develop/using-commands/keyspace/)
- [Redis Docs: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[redis-data-structures]]
- [[redis-failure-and-fallback]]
- [[02-practical-backend/performance/performance|performance]]
