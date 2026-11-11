---
title: "DB 복제(Replication)와 샤딩"
description: DB 한 대로 버티기 어려울 때 복제와 샤딩이 각각 무엇을 나누고, 무엇을 대가로 치르는지
tags: [concept, database]
---

# DB 복제(Replication)와 샤딩

Replication은 같은 데이터를 여러 서버에 복사해 두고 읽기를 나눠 받는다. 한 대가 죽어도 다른 서버가 남는다. Sharding은 데이터를 여러 서버에 쪼개 담아 쓰기와 저장 용량을 나눈다.

둘 다 DB 한 대로는 버티기 어려울 때 쓰지만 치르는 대가가 다르다. Replication은 복제가 늦어져서 방금 쓴 글이 목록에 안 보이는 버그를 만든다. Sharding은 Shard Key를 잘못 고르면 한 샤드에 데이터가 몰려서 나눈 보람이 없다.

## Replication

### 동작

```
        쓰기 (INSERT/UPDATE/DELETE)
Client ─────────────────────────────→ Master (Primary)
                                        │
                                        │ binlog 복제
                                        ▼
                                    Replica 1 (읽기 전용)
                                    Replica 2 (읽기 전용)
                                        ▲
Client ─────────────────────────────────┘
        읽기 (SELECT)
```

| 구성 요소 | 하는 일 |
|---|---|
| Master (Primary) | 쓰기를 전부 받고 binlog를 남긴다 |
| Replica (Secondary) | Master의 binlog를 받아 다시 실행하고, 읽기를 받는다 |

MySQL에서는 이렇게 흘러간다.

1. Master가 데이터를 바꾸면 binlog에 기록한다.
2. Replica의 IO Thread가 binlog를 가져와 relay log에 저장한다.
3. Replica의 SQL Thread가 relay log를 다시 실행해 데이터를 맞춘다.

### 복제 지연 (Replication Lag)

```
시간 ──→
Master:  INSERT 완료 ─────────────────────────
Replica:              ───── lag ─── INSERT 반영
                      ↑
                      이 시점에 Replica를 읽으면 데이터가 없음
```

사용자가 글을 쓰고 바로 목록을 열면 방금 쓴 글이 안 보인다. 대응은 셋 중 하나다.

| 전략 | 방법 | 언제 |
|---|---|---|
| 쓰고 나서 읽는 건 Master로 | 방금 쓴 사용자의 조회만 Master로 보낸다 | 가장 흔하다 |
| 복제될 때까지 기다리기 | semi-synchronous replication | 바로 보여야만 할 때 |
| 위치 비교 | 쓸 때의 binlog position과 Replica의 position을 비교한다 | 복잡하지만 정확하다 |

### Spring에서 읽기/쓰기 분리

```java
@Transactional(readOnly = true)  // Replica로 라우팅
public List<Order> getOrders() { ... }

@Transactional  // Master로 라우팅
public void createOrder() { ... }
```

`AbstractRoutingDataSource`가 트랜잭션의 readOnly 값을 보고 어느 DataSource로 보낼지 고른다.

## Sharding

### 동작

```
Client 요청 (user_id = 12345)
       │
       ▼
  Shard Router (user_id % 4 = 1)
       │
  ┌────┼────┬────┐
  ▼    ▼    ▼    ▼
Shard0 Shard1 Shard2 Shard3
       ↑
   여기에 저장
```

Shard Key 값을 보고 데이터를 여러 DB에 나눠 담는다.

| 전략 | 방법 | 장단점 |
|---|---|---|
| Hash Sharding | `shard = hash(key) % N` | 고르게 퍼지지만, 샤드를 늘리면 데이터를 다시 옮겨야 한다 |
| Range Sharding | `0~999 → Shard0, 1000~1999 → Shard1` | 범위 조회가 쉽지만, 한 샤드에 몰릴 수 있다(핫스팟) |
| Directory Sharding | 어느 키가 어느 샤드인지 라우팅 테이블에 적어 둔다 | 유연하지만, 라우팅 테이블이 죽으면 전부 멈춘다(SPOF) |

### Shard Key 고르기

좋은 Shard Key는 세 가지를 갖췄다.

1. 데이터가 특정 샤드에 몰리지 않고 고르게 퍼진다.
2. 대부분의 쿼리에 Shard Key가 들어 있어서, 어느 샤드로 갈지 바로 안다.
3. 값이 바뀌지 않는다. 바뀌면 데이터를 다른 샤드로 옮겨야 한다.

| 예시 | 괜찮은가 | 이유 |
|---|---|---|
| `user_id` | 좋음 | 쿼리 대부분이 사용자 기준이고, 고르게 퍼진다 |
| `created_date` | 나쁨 | 최신 날짜 샤드에만 쓰기가 몰린다 (핫스팟) |
| `country` | 조심 | 나라별 데이터 양 차이가 크면 한쪽으로 쏠린다 |

### Sharding이 어려운 이유

| 문제 | 설명 |
|---|---|
| Cross-shard JOIN | 여러 샤드에 걸친 JOIN은 안 되거나 매우 비싸다 |
| Cross-shard 트랜잭션 | 분산 트랜잭션이 필요해서 느려지고 복잡해진다 |
| 샤드 추가/리밸런싱 | 데이터를 옮겨야 하고, 그동안 서비스가 영향을 받는다 |
| Global unique ID | AUTO_INCREMENT를 못 쓰니 ID를 따로 만들어야 한다 (Snowflake 등) |
| 집계 쿼리 | 모든 샤드를 조회해서 합쳐야 한다 |

## 무엇을 언제 쓰나

| 구분 | Replication | Sharding |
|---|---|---|
| 목적 | 읽기 분산, 가용성 | 쓰기 분산, 저장 용량 확장 |
| 데이터 | 전체 복사 | 분할 저장 |
| 확장 대상 | 읽기 처리량 | 읽기 + 쓰기 처리량 |
| 복잡도 | 낮음 | 높음 |
| 도입 시점 | 읽기 부하가 높을 때 | 단일 DB 용량/쓰기 한계 도달 시 |

보통은 이 순서로 확장한다.

```
1. 단일 DB + 인덱스/쿼리 최적화
2. 캐시(Redis) 도입
3. Read Replica 추가 (Replication)
4. 테이블 분리 (수직 분할)
5. Sharding (수평 분할) ← 최후의 수단
```

## 자주 깨지는 곳

- 쓰자마자 Replica에서 읽으면, 복제가 늦어서 방금 쓴 데이터가 안 보인다.
- Shard Key를 시간으로 잡으면, 최신 샤드에만 쓰기가 몰린다.
- 아직 필요 없는데 Sharding을 들이면, 얻는 것 없이 복잡하기만 하다.
- 여러 샤드에 걸친 쿼리가 많은 설계에 Sharding을 하면, 모든 샤드를 훑느라 오히려 느려진다.

## 한 번에 설명하기

> Replication은 데이터를 복사해 두고 읽기를 나눠 받는 방법이라, 한 대가 죽어도 버틸 수 있습니다. 복제가 늦을 수 있어서, 저는 쓰자마자 읽는 요청은 Master로 보냅니다.
>
> Sharding은 데이터를 쪼개서 쓰기와 용량을 나눕니다. Shard Key는 고르게 퍼지고, 대부분의 쿼리에 들어 있고, 바뀌지 않는 값으로 고릅니다.
>
> 확장은 인덱스와 쿼리 손보기, 캐시, Replication 순서로 하고, Sharding은 너무 복잡해서 맨 마지막에 꺼냅니다.

## 꼬리 질문

> [!question]- Replication lag으로 인한 정합성 문제를 어떻게 해결하는가?
> 쓰자마자 읽는 요청만 Master로 보냅니다. 아니면 semi-synchronous replication으로 Replica 하나 이상에 전달된 걸 확인하고 나서 응답합니다. 읽기를 다 Master로 보내면 Replica를 둔 이유가 없으니, 꼭 필요한 요청만 골라서 보냅니다.

> [!question]- Shard Key를 잘못 선택하면 어떤 문제가 생기는가?
> 데이터가 한 샤드에 몰려서(핫스팟) 그 샤드만 과부하가 걸립니다. 그리고 쿼리 대부분에 Shard Key가 없으면 매번 모든 샤드를 조회해서 합쳐야(scatter-gather) 해서 오히려 느려집니다.

> [!question]- Sharding 없이 확장할 수 있는 방법은?
> 인덱스와 쿼리를 손보고, 캐시(Redis)를 두고, Read Replica를 붙이고, 테이블을 수직으로 나누고, 오래된 데이터를 아카이빙합니다. 이렇게 DB 한 대로 갈 수 있는 데까지 간 다음에 Sharding을 꺼냅니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[01-core/database/transaction-and-isolation|transaction-and-isolation]]
- [[02-practical-backend/performance/performance|performance]]
- [[connection-pool-and-timeout]]
- [[nosql-and-cap]]
