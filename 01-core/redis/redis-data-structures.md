---
title: Redis 자료구조
description: Redis 자료구조를 어디에 쓰고, 고를 때 무엇을 먼저 보는지
tags: [concept, redis]
---

# Redis 자료구조

Redis에는 String 말고도 Hash, Set, Sorted Set, List, Stream, Pub/Sub이 있다. 조회수를 1 올리거나, 좋아요를 눌렀는지 확인하거나, 랭킹 상위 10명을 뽑는 일을 명령 하나로 원자적으로 처리한다.

모든 값을 JSON 문자열로만 넣으면 이런 명령을 못 쓰고, 필드 하나를 바꿀 때도 통째로 읽고 다시 써야 한다. 자료구조를 잘못 고르면 메모리를 많이 먹고 조회나 삭제도 느려진다. 고를 때는 기능보다 먼저 데이터가 얼마나 커질지, 그리고 잃어도 되는지를 본다.

## 자료구조별 사용처

| 자료구조 | 대표 사용처 | 조심할 점 |
|---|---|---|
| String | 캐시, 카운터, 분산 락, 토큰 | 큰 JSON을 많이 넣으면 메모리와 네트워크 비용이 커진다 |
| Hash | 사용자 세션, 객체 필드 캐시 | 필드가 너무 많으면 big key가 된다 |
| Set | 중복 제거, 좋아요 여부, 권한 집합 | Set이 커지면 지우거나 전체를 조회하는 데 오래 걸린다 |
| Sorted Set | 랭킹, 우선순위 큐, 만료 후보 관리 | score를 어떻게 잡을지와 데이터 크기를 같이 정해야 한다 |
| List | 간단한 큐 | 장애 복구나 재처리가 필요하면 부족하다 |
| Stream | 이벤트 로그, consumer group 기반 처리 | 운영이 복잡하고 보관 기간을 관리해야 한다 |
| Pub/Sub | 서버 간 실시간 알림 | 메시지가 유실될 수 있다 |

## 요구사항별로 고르기

| 요구사항 | 선택 | 이유 |
|---|---|---|
| 단순 캐시 값 저장 | String | 구현이 단순하고 TTL 관리가 쉽다 |
| 필드 일부만 자주 갱신 | Hash | JSON 전체를 다시 저장하는 것보다 쌀 수 있다 |
| 중복 없는 membership 확인 | Set | `SISMEMBER`로 바로 확인한다 |
| 점수 기반 순위 조회 | Sorted Set | score 기준 정렬과 range 조회를 제공한다 |
| 유실돼도 되는 실시간 알림 | Pub/Sub | 단순하고 지연이 낮다 |
| 재처리가 필요한 이벤트 | Stream 또는 메시지 브로커 | 소비 상태와 재처리를 관리해야 한다 |

## 자주 깨지는 곳

- 모든 값을 큰 JSON String으로 넣으면, 필드 하나를 바꿔도 전체를 다시 써야 하고 원자 연산도 못 쓴다.
- 자료구조 하나에 데이터를 계속 쌓으면 Hash, Set, Sorted Set이 big key가 되고, 이 key를 다루는 명령이 Redis 전체를 느리게 만든다.
- 운영 중에 `KEYS *`를 쓰면 key가 많을 때 Redis가 그동안 다른 명령을 처리하지 못한다. key를 조사할 때는 scan을 쓴다.
- Pub/Sub을 주문이나 결제 이벤트에 쓰면, 장애 때 잃으면 안 되는 이벤트가 그대로 사라진다.
- key 단위 TTL과 field 단위 만료를 헷갈리면 데이터가 의도와 다른 때에 지워지거나 남는다. field별 만료가 지원되는지 먼저 확인한다.

## 운영에서 볼 것

- 테스트: 자료구조별 명령이 동시 요청에서 원자적으로 동작하는지 확인한다.
- 로그: 나중에 key prefix, 자료구조, 데이터 크기, 삭제 범위를 따라갈 수 있게 남긴다.
- 메트릭: memory usage, command latency, hot key, big key, network input/output을 본다.
- 주기 점검: scan으로 key를 조사하고, TTL 분포와 큰 자료구조 크기를 확인한다.

## 한 번에 설명하기

> Redis는 값을 넣고 빼는 캐시에 그치지 않고, 자료구조와 그 위에서 원자적으로 도는 명령을 함께 줍니다. String은 캐시와 카운터, Hash는 객체 필드, Set은 중복 없는 집합, Sorted Set은 랭킹에 씁니다.
>
> 고를 때는 데이터가 얼마나 커질지와 잃어도 되는지를 먼저 봅니다. 크기가 계속 자라면 big key가 되기 때문입니다.
>
> Pub/Sub은 메시지가 사라질 수 있어서, 다시 처리해야 하는 이벤트에는 Stream이나 메시지 브로커를 씁니다.

## 꼬리 질문

- 랭킹 기능에 Sorted Set을 쓰는 이유는?
- Redis Pub/Sub을 주문 이벤트 처리에 쓰면 어떤 문제가 생기나?
- Pub/Sub과 Stream은 어떻게 다른가?
- big key가 Redis 전체 지연에 영향을 주는 이유는?
- 모든 값을 큰 JSON String으로 저장하면 어떤 한계가 있나?
- Hash에 저장한 field별 생명주기는 어떻게 관리하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: Data types](https://redis.io/docs/latest/develop/data-types/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[websocket]]
