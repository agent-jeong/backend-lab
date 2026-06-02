---
title: Redis 자료구조
description: Redis 자료구조별 실무 사용처와 주의점
---

# Redis 자료구조

## 한 줄 정의

Redis 자료구조는 단순 key-value 저장을 넘어 카운터, 집합, 랭킹, 큐, 세션 같은 문제를 Redis 명령으로 직접 다루게 해준다.

## 실무에서 왜 문제 되는가

- 모든 데이터를 String JSON으로만 저장하면 Redis가 제공하는 원자 연산과 자료구조 장점을 놓친다.
- 자료구조를 잘못 고르면 메모리 사용량, 조회 비용, 삭제 비용이 커진다.
- 큰 Hash, 큰 Set, 큰 Sorted Set은 big key가 되어 Redis 지연을 만들 수 있다.
- Pub/Sub처럼 유실 가능성이 있는 구조를 영속 메시징처럼 사용하면 장애 시 데이터가 사라질 수 있다.

## 자료구조별 실무 사용처

| 자료구조 | 대표 사용처 | 주의점 |
|---|---|---|
| String | 캐시, 카운터, 분산 락, 토큰 | 큰 JSON을 많이 넣으면 메모리와 네트워크 비용이 커진다 |
| Hash | 사용자 세션, 객체 필드 캐시 | 필드가 너무 많으면 big key가 될 수 있다 |
| Set | 중복 제거, 좋아요 여부, 권한 집합 | 큰 Set 삭제/조회 비용을 조심해야 한다 |
| Sorted Set | 랭킹, 우선순위 큐, 만료 후보 관리 | score 설계와 데이터 크기 관리가 중요하다 |
| List | 간단한 큐 | 장애 복구와 재처리 요구가 있으면 한계가 있다 |
| Stream | 이벤트 로그, consumer group 기반 처리 | 운영 복잡도와 보관 기간 관리가 필요하다 |
| Pub/Sub | 서버 간 실시간 알림 | 메시지 유실 가능성이 있다 |

## 실무 판단 기준

| 요구사항 | 선택 | 이유 |
|---|---|---|
| 단순 캐시 값 저장 | String | 구현이 단순하고 TTL 관리가 쉽다 |
| 필드 일부만 자주 갱신 | Hash | 전체 JSON 재저장보다 효율적일 수 있다 |
| 중복 없는 membership 확인 | Set | `SISMEMBER`로 빠르게 확인할 수 있다 |
| 점수 기반 순위 조회 | Sorted Set | score 기반 정렬과 range 조회를 제공한다 |
| 유실되어도 되는 실시간 알림 | Pub/Sub | 단순하고 지연이 낮다 |
| 재처리가 필요한 이벤트 | Stream 또는 메시지 브로커 | 소비 상태와 재처리 관리가 필요하다 |

## 자주 나는 실수

- 모든 값을 큰 JSON String으로 저장한다.
- 자료구조 하나에 너무 많은 데이터를 넣어 big key를 만든다.
- 운영 중 `KEYS *` 같은 위험한 명령을 사용한다.
- Pub/Sub을 유실되면 안 되는 주문/결제 이벤트에 사용한다.
- key TTL과 field 단위 만료 지원 여부를 혼동해 데이터 생명주기를 잘못 설계한다.

## 확인 방법

- 테스트: 자료구조별 명령이 동시 요청에서 원자적으로 동작하는지 확인한다.
- 로그: key prefix, 자료구조, 데이터 크기, 삭제 범위를 추적 가능하게 남긴다.
- 메트릭: memory usage, command latency, hot key, big key, network input/output을 본다.
- 운영 점검: scan 기반 key 조사, TTL 분포, 큰 자료구조 크기를 주기적으로 확인한다.

## 핵심 요약

Redis는 단순 캐시 저장소가 아니라 여러 자료구조와 원자 명령을 제공한다. String은 캐시와 카운터, Hash는 객체 필드, Set은 중복 없는 집합, Sorted Set은 랭킹에 자주 쓰인다. Pub/Sub은 간단한 실시간 알림에는 적합하지만 메시지 유실 가능성이 있어 영속 이벤트 처리에는 신중해야 한다. 자료구조 선택은 기능 구현뿐 아니라 메모리, big key, hot key, 장애 복구 요구사항까지 함께 보고 정해야 한다.

## 꼬리 질문

- 랭킹 기능에 Sorted Set을 쓰는 이유는 무엇인가?
- Redis Pub/Sub을 주문 이벤트 처리에 쓰면 어떤 문제가 생길 수 있는가?
- Pub/Sub과 Stream은 어떤 차이가 있는가?
- big key가 Redis 전체 지연에 영향을 줄 수 있는 이유는 무엇인가?
- 모든 값을 큰 JSON String으로 저장하면 어떤 한계가 있는가?
- Hash에 저장한 field별 생명주기를 어떻게 관리할 것인가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[websocket]]
