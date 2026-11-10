---
title: "DB 복제(Replication)와 샤딩"
description: DB 복제와 샤딩의 동작 원리, 선택 기준, 실무 트레이드오프
tags: [concept, database]
---

# DB 복제(Replication)와 샤딩

Replication은 같은 데이터를 여러 서버에 복제해 읽기를 나누고 가용성을 높인다. Sharding은 데이터를 여러 서버에 쪼개 저장해 쓰기와 저장 용량을 나눈다.

둘 다 단일 DB 한계를 넘는 방법이지만 대가가 다르다. Replication은 복제 지연 때문에 "방금 저장한 데이터가 안 보이는" 버그를 만들고, Sharding은 Shard Key를 잘못 고르면 한 샤드에 데이터가 몰려 나눈 의미가 없어진다.

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

| 구성 요소 | 역할 |
|---|---|
| Master (Primary) | 모든 쓰기 처리, binlog 생성 |
| Replica (Secondary) | Master의 binlog를 받아 재실행, 읽기 처리 |

MySQL에서는 이렇게 흘러간다.

1. Master가 데이터를 바꾸면 binlog에 기록한다.
2. Replica의 IO Thread가 binlog를 가져와 relay log에 저장한다.
3. Replica의 SQL Thread가 relay log를 재실행해 데이터를 맞춘다.

### 복제 지연 (Replication Lag)

```
시간 ──→
Master:  INSERT 완료 ─────────────────────────
Replica:              ───── lag ─── INSERT 반영
                      ↑
                      이 시점에 Replica를 읽으면 데이터가 없음
```

사용자가 글을 쓴 직후 목록을 열면 방금 쓴 글이 안 보인다. 대응은 셋 중 하나다.

| 전략 | 방법 | 적용 |
|---|---|---|
| 쓰기 후 읽기는 Master | 방금 쓴 사용자의 조회는 Master로 라우팅 | 가장 흔함 |
| 강제 동기화 대기 | semi-synchronous replication | 정합성이 꼭 필요할 때 |
| 버전 체크 | 쓰기 시점의 binlog position과 Replica position 비교 | 복잡하지만 정밀 |

### Spring에서 읽기/쓰기 분리

```java
@Transactional(readOnly = true)  // Replica로 라우팅
public List<Order> getOrders() { ... }

@Transactional  // Master로 라우팅
public void createOrder() { ... }
```

`AbstractRoutingDataSource`로 트랜잭션의 readOnly 속성을 보고 DataSource를 나눈다.

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

데이터를 Shard Key 기준으로 여러 DB에 나눠 저장한다.

| 전략 | 방법 | 장단점 |
|---|---|---|
| Hash Sharding | `shard = hash(key) % N` | 균등 분산, 샤드 추가 시 재배치 필요 |
| Range Sharding | `0~999 → Shard0, 1000~1999 → Shard1` | 범위 조회 유리, 핫스팟 발생 가능 |
| Directory Sharding | 별도 라우팅 테이블로 관리 | 유연하지만 라우팅 테이블이 SPOF |

### Shard Key 고르기

좋은 Shard Key는 세 조건을 만족한다.

1. **균등 분산**: 특정 샤드에 데이터가 몰리지 않는다.
2. **쿼리 라우팅 가능**: 대부분의 쿼리에 Shard Key가 들어 있다.
3. **변하지 않음**: 키가 바뀌면 데이터를 다른 샤드로 옮겨야 한다.

| 예시 | 적합도 | 이유 |
|---|---|---|
| `user_id` | 좋음 | 대부분의 쿼리가 사용자 기준, 균등 분산 |
| `created_date` | 나쁨 | 최신 데이터에 쓰기가 집중 (핫스팟) |
| `country` | 주의 | 국가별 데이터량 차이가 크면 편향 발생 |

### Sharding이 어려운 이유

| 문제 | 설명 |
|---|---|
| Cross-shard JOIN | 여러 샤드에 걸친 JOIN이 불가하거나 매우 비쌈 |
| Cross-shard 트랜잭션 | 분산 트랜잭션 필요, 성능과 복잡도 증가 |
| 샤드 추가/리밸런싱 | 데이터 이동이 필요, 서비스 영향 |
| Global unique ID | AUTO_INCREMENT 불가, 별도 ID 생성 전략 필요 (Snowflake 등) |
| 집계 쿼리 | 모든 샤드를 조회하고 합쳐야 함 |

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

- **쓰기 직후 Replica에서 읽는다.** 복제 지연 때문에 방금 쓴 데이터가 안 보인다.
- **Shard Key를 시간 기반으로 잡는다.** 최신 샤드에만 쓰기가 몰린다.
- **필요 없는 시점에 Sharding을 들인다.** 얻는 것 없이 복잡도만 는다.
- **Cross-shard 쿼리가 많은 설계에 Sharding을 적용한다.** 모든 샤드를 훑느라 오히려 느려진다.

## 면접에서 말하기

> Replication은 데이터를 복제해 읽기를 나누고 가용성을 높이는 방법입니다. 복제 지연이 있어서, 저는 쓰기 직후의 읽기는 Master로 보냅니다. Sharding은 데이터를 쪼개 쓰기와 용량을 나누는데, Shard Key는 고르게 분산되고, 대부분의 쿼리에 들어 있고, 바뀌지 않는 값이어야 합니다. 확장은 인덱스 최적화, 캐시, Replication 순으로 하고, Sharding은 복잡도가 매우 커서 마지막에 검토합니다.

## 꼬리 질문

> [!question]- Replication lag으로 인한 정합성 문제를 어떻게 해결하는가?
> 쓰기 직후 읽기는 Master로 라우팅합니다. 또는 semi-synchronous replication으로 최소 1개 Replica에 전파를 보장합니다. 모든 읽기를 Master로 보내면 Replication의 의미가 없으므로 선별적으로 적용합니다.

> [!question]- Shard Key를 잘못 선택하면 어떤 문제가 생기는가?
> 특정 샤드에 데이터가 집중(핫스팟)되어 해당 샤드만 과부하가 걸립니다. 또한 대부분의 쿼리에 Shard Key가 포함되지 않으면 모든 샤드를 조회(scatter-gather)해야 해서 오히려 느려집니다.

> [!question]- Sharding 없이 확장할 수 있는 방법은?
> 인덱스/쿼리 최적화, 캐시(Redis), Read Replica, 테이블 수직 분할, 아카이빙 등으로 단일 DB의 한계를 최대한 늘린 뒤에 Sharding을 검토합니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[01-core/database/transaction-and-isolation|transaction-and-isolation]]
- [[02-practical-backend/performance/performance|performance]]
- [[connection-pool-and-timeout]]
