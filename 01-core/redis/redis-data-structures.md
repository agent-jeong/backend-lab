---
title: Redis 자료구조
description: Redis 자료구조별 실무 사용처와 주의점
tags: [concept, redis]
---

# Redis 자료구조

Redis는 String 말고도 Hash, Set, Sorted Set, List, Stream, Pub/Sub을 제공한다. 카운터, 집합, 랭킹, 큐, 세션 같은 문제를 Redis 명령 하나로 원자적으로 처리할 수 있다.

모든 값을 String JSON으로만 넣으면 이 원자 연산을 못 쓰고, 자료구조를 잘못 고르면 메모리·조회·삭제 비용이 커진다. 고를 때는 기능보다 **크기와 유실 허용 여부**를 먼저 본다.

## 자료구조별 사용처

| 자료구조 | 대표 사용처 | 조심할 점 |
|---|---|---|
| String | 캐시, 카운터, 분산 락, 토큰 | 큰 JSON을 많이 넣으면 메모리와 네트워크 비용이 커진다 |
| Hash | 사용자 세션, 객체 필드 캐시 | 필드가 너무 많으면 big key가 된다 |
| Set | 중복 제거, 좋아요 여부, 권한 집합 | 큰 Set은 삭제·조회 비용이 크다 |
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

- **모든 값을 큰 JSON String으로 넣는다.** 필드 하나를 바꿔도 전체를 다시 쓰고, 원자 연산도 못 쓴다.
- **자료구조 하나에 데이터를 계속 쌓는다.** 큰 Hash·Set·Sorted Set은 big key가 되어 Redis 전체 지연을 만든다.
- **운영 중 `KEYS *`를 쓴다.** 조사는 scan 기반으로 한다.
- **Pub/Sub을 주문·결제 이벤트에 쓴다.** 유실되면 안 되는 이벤트가 장애 때 그대로 사라진다.
- **key TTL과 field 단위 만료를 혼동한다.** field별 만료가 지원되는지 확인하지 않으면 데이터 생명주기가 틀어진다.

## 운영에서 볼 것

- 테스트: 자료구조별 명령이 동시 요청에서 원자적으로 동작하는지 확인한다.
- 로그: key prefix, 자료구조, 데이터 크기, 삭제 범위를 추적할 수 있게 남긴다.
- 메트릭: memory usage, command latency, hot key, big key, network input/output.
- 주기 점검: scan으로 key를 조사하고, TTL 분포와 큰 자료구조 크기를 확인한다.

## 면접에서 말하기

> Redis는 단순 캐시가 아니라 자료구조와 원자 명령을 함께 제공합니다. String은 캐시와 카운터, Hash는 객체 필드, Set은 중복 없는 집합, Sorted Set은 랭킹에 씁니다. 고를 때는 데이터가 얼마나 커질지와 유실돼도 되는지를 먼저 보는데, 크기가 계속 자라면 big key가 되고, Pub/Sub은 메시지가 유실될 수 있어서 재처리가 필요한 이벤트에는 Stream이나 메시지 브로커를 씁니다.

## 꼬리 질문

- 랭킹 기능에 Sorted Set을 쓰는 이유는?
- Redis Pub/Sub을 주문 이벤트 처리에 쓰면 어떤 문제가 생기나?
- Pub/Sub과 Stream은 어떻게 다른가?
- big key가 Redis 전체 지연에 영향을 주는 이유는?
- 모든 값을 큰 JSON String으로 저장하면 어떤 한계가 있나?
- Hash에 저장한 field별 생명주기는 어떻게 관리하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Redis Docs: Data types](https://redis.io/docs/latest/develop/data-types/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[cache-aside-and-ttl]]
- [[02-practical-backend/performance/performance|performance]]
- [[websocket]]
