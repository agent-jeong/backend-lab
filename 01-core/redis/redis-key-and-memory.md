---
title: Redis Key 설계와 메모리 관리
description: Redis key naming, TTL, hot key, big key, memory eviction 관리 기준
---

# Redis Key 설계와 메모리 관리

## 한 줄 정의

Redis key 설계와 메모리 관리는 key 이름, TTL, 데이터 크기, eviction 정책을 통제해 Redis를 예측 가능하게 운영하는 것이다.

## 실무에서 왜 문제 되는가

- key 규칙이 없으면 장애 시 어떤 데이터를 삭제해도 되는지 판단하기 어렵다.
- TTL이 없는 key가 계속 쌓이면 메모리 부족과 eviction이 발생할 수 있다.
- 특정 key에 요청이 몰리는 hot key는 Redis 단일 스레드 처리 지연을 만들 수 있다.
- 너무 큰 value나 자료구조는 big key가 되어 네트워크 전송, 삭제, 복제, 백업 비용을 키운다.
- maxmemory와 eviction policy를 모르고 운영하면 중요한 캐시가 예상치 못하게 사라질 수 있다.

## Key 설계 기준

| 기준 | 예시 | 이유 |
|---|---|---|
| 기능 prefix | `product:summary:{productId}` | 기능별 조회, 삭제, 모니터링이 쉽다 |
| 식별자 포함 | `user:session:{userId}` | key 충돌을 줄이고 추적이 쉽다 |
| 조회 조건 포함 | `search:result:{keyword}:{page}` | 다른 조건의 캐시가 섞이지 않는다 |
| 버전 포함 | `product:v2:summary:{productId}` | 캐시 구조 변경 시 이전 key와 충돌하지 않는다 |
| TTL 기준 분리 | `rank:daily:{date}` | 만료 정책과 데이터 생명주기를 추적하기 쉽다 |

## 실무 판단 기준

| 상황 | 판단 | 이유 |
|---|---|---|
| 데이터가 재계산 가능함 | TTL 필수 | 메모리 누적을 막고 stale data를 제한한다 |
| 데이터가 자주 변경됨 | 짧은 TTL 또는 캐시 제외 | 무효화 비용이 캐시 이득보다 클 수 있다 |
| 특정 key에 요청 집중 | hot key 분산 검토 | 단일 key 병목으로 Redis latency가 증가할 수 있다 |
| value 크기가 큼 | 쪼개기 또는 저장 방식 변경 | big key는 삭제, 복제, 네트워크 비용을 키운다 |
| 삭제 범위가 필요함 | prefix 규칙 설계 | 운영 중 안전한 scan/delete가 가능해야 한다 |

## Hot Key와 Big Key

| 구분 | 의미 | 문제 | 대응 |
|---|---|---|---|
| hot key | 특정 key에 요청이 과도하게 몰림 | Redis CPU/latency 증가 | 로컬 캐시, key 분산, TTL jitter, 사전 계산 |
| big key | value나 자료구조 크기가 과도하게 큼 | 네트워크 지연, 삭제 지연, 복제 비용 증가 | 데이터 분할, 자료구조 재설계, lazy unlink |

## Eviction Policy 판단

| 정책 | 의미 | 적합한 경우 |
|---|---|---|
| `noeviction` | 메모리 초과 시 쓰기 실패 | 데이터 손실보다 실패가 나은 경우 |
| `allkeys-lru` | 모든 key 중 덜 쓰인 key 제거 | 대부분이 캐시 데이터인 경우 |
| `volatile-lru` | TTL이 있는 key 중 덜 쓰인 key 제거 | TTL이 있는 캐시만 제거하고 싶은 경우 |
| `allkeys-lfu` | 모든 key 중 덜 자주 쓰인 key 제거 | 사용 빈도 차이가 큰 캐시 |
| `volatile-ttl` | TTL이 짧은 key 우선 제거 | 만료 임박 캐시를 먼저 제거하고 싶은 경우 |

실무에서는 같은 Redis에 세션, 락, 캐시를 섞을수록 eviction policy 선택이 어려워진다. 중요도가 다른 데이터는 Redis 인스턴스나 DB를 분리하는 편이 안전하다.

## 자주 나는 실수

- key prefix 없이 임의 문자열로 저장한다.
- TTL 없는 캐시 key를 계속 쌓는다.
- 운영에서 `KEYS *`로 전체 key를 조회한다.
- 큰 JSON을 하나의 String value로 저장해 big key를 만든다.
- 같은 TTL을 대량 key에 적용해 동시에 만료되게 만든다.
- eviction 발생을 캐시 miss 증가가 아니라 Redis 정상 동작으로만 본다.

## 확인 방법

- 테스트: key 생성 규칙과 TTL 설정 여부를 통합 테스트에서 확인한다.
- 로그: 주요 cache key prefix, miss 원인, delete 실패를 추적한다.
- 메트릭: memory usage, used memory peak, evicted keys, expired keys, command latency를 본다.
- 운영 점검: `SCAN` 기반 key 조사, big key 분석, hot key 분석, TTL 분포 확인을 수행한다.

## 핵심 요약

Redis key는 단순 문자열이 아니라 운영 단위다. prefix, 식별자, 조회 조건, 버전을 일관되게 넣어야 장애 시 추적과 삭제가 가능하다. 캐시 key에는 TTL을 두는 것이 기본이며, TTL은 정합성 허용 시간과 메모리 관리 기준을 함께 의미한다. hot key는 요청 집중으로 latency를 만들고, big key는 네트워크 전송, 삭제, 복제 비용을 키운다. eviction policy는 Redis에 어떤 종류의 데이터를 섞어 넣었는지에 따라 위험도가 달라진다.

## 꼬리 질문

- Redis key prefix를 어떻게 설계할 것인가?
- TTL 없는 key가 쌓이면 어떤 문제가 생기는가?
- hot key와 big key는 각각 어떤 증상으로 드러나는가?
- `KEYS *` 대신 `SCAN`을 써야 하는 이유는 무엇인가?
- eviction policy를 잘못 고르면 어떤 데이터가 사라질 수 있는가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[redis-data-structures]]
- [[redis-failure-and-fallback]]
- [[02-practical-backend/performance/performance|performance]]
