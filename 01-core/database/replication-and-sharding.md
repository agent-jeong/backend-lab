---
title: Replication And Sharding
description: DB 복제와 샤딩의 동작 원리, 선택 기준, 실무 트레이드오프
---

# Replication And Sharding

## 한 줄 정의

Replication은 데이터를 여러 서버에 복제하여 읽기를 분산하고 가용성을 높이는 기법이고, Sharding은 데이터를 여러 서버에 분할 저장하여 쓰기와 저장 용량을 분산하는 기법이다.

## 실무에서 왜 중요한가

- 단일 DB의 읽기/쓰기 한계를 넘는 트래픽에서 어떻게 확장하는지 설명해야 한다.
- Replication 지연(lag)을 모르면 "방금 저장한 데이터가 안 보인다"는 버그를 만든다.
- Sharding 키를 잘못 선택하면 특정 샤드에 데이터가 몰려서 효과가 없다.
- 면접에서 "대규모 트래픽 처리 경험"과 직결되는 핵심 주제다.

## Replication (복제)

### 동작 원리

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

### MySQL Replication 흐름

1. Master에서 데이터 변경 시 **binlog**에 기록
2. Replica의 **IO Thread**가 binlog를 가져와 **relay log**에 저장
3. Replica의 **SQL Thread**가 relay log를 재실행하여 데이터 동기화

### Replication Lag (복제 지연)

```
시간 ──→
Master:  INSERT 완료 ─────────────────────────
Replica:              ───── lag ─── INSERT 반영
                      ↑
                      이 시점에 Replica를 읽으면 데이터가 없음
```

**문제 상황**: 사용자가 글을 작성한 직후 목록을 조회하면 방금 쓴 글이 안 보인다.

**대응 전략**:

| 전략 | 방법 | 적용 |
|---|---|---|
| 쓰기 후 읽기는 Master | 방금 쓴 사용자의 조회는 Master로 라우팅 | 가장 흔함 |
| 강제 동기화 대기 | semi-synchronous replication | 정합성 중요 시 |
| 버전 체크 | 쓰기 시점의 binlog position과 Replica position 비교 | 복잡하지만 정밀 |

### Spring에서 읽기/쓰기 분리

```java
@Transactional(readOnly = true)  // Replica로 라우팅
public List<Order> getOrders() { ... }

@Transactional  // Master로 라우팅
public void createOrder() { ... }
```

`AbstractRoutingDataSource`로 트랜잭션의 readOnly 속성에 따라 DataSource를 분기한다.

## Sharding (분할)

### 동작 원리

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

데이터를 **Shard Key** 기준으로 여러 DB에 분산 저장한다.

### Sharding 전략

| 전략 | 방법 | 장단점 |
|---|---|---|
| Hash Sharding | `shard = hash(key) % N` | 균등 분산, 샤드 추가 시 재배치 필요 |
| Range Sharding | `0~999 → Shard0, 1000~1999 → Shard1` | 범위 조회 유리, 핫스팟 발생 가능 |
| Directory Sharding | 별도 라우팅 테이블로 관리 | 유연하지만 라우팅 테이블이 SPOF |

### Shard Key 선택 기준

**좋은 Shard Key의 조건**:

1. **균등 분산**: 특정 샤드에 데이터가 몰리지 않아야 한다.
2. **쿼리 라우팅 가능**: 대부분의 쿼리에 Shard Key가 포함되어야 한다.
3. **변경되지 않음**: 키가 변경되면 데이터를 다른 샤드로 이동해야 한다.

| 예시 | 적합도 | 이유 |
|---|---|---|
| `user_id` | 좋음 | 대부분의 쿼리가 사용자 기준, 균등 분산 |
| `created_date` | 나쁨 | 최신 데이터에 쓰기가 집중 (핫스팟) |
| `country` | 주의 | 국가별 데이터량 차이가 크면 편향 발생 |

### Sharding의 어려움

| 문제 | 설명 |
|---|---|
| Cross-shard JOIN | 여러 샤드에 걸친 JOIN이 불가하거나 매우 비쌈 |
| Cross-shard 트랜잭션 | 분산 트랜잭션 필요, 성능과 복잡도 증가 |
| 샤드 추가/리밸런싱 | 데이터 이동이 필요, 서비스 영향 |
| Global unique ID | AUTO_INCREMENT 불가, 별도 ID 생성 전략 필요 (Snowflake 등) |
| 집계 쿼리 | 모든 샤드를 조회하고 합쳐야 함 |

## Replication vs Sharding

| 구분 | Replication | Sharding |
|---|---|---|
| 목적 | 읽기 분산, 가용성 | 쓰기 분산, 저장 용량 확장 |
| 데이터 | 전체 복사 | 분할 저장 |
| 확장 대상 | 읽기 처리량 | 읽기 + 쓰기 처리량 |
| 복잡도 | 낮음 | 높음 |
| 도입 시점 | 읽기 부하가 높을 때 | 단일 DB 용량/쓰기 한계 도달 시 |

### 확장 순서 (일반적)

```
1. 단일 DB + 인덱스/쿼리 최적화
2. 캐시(Redis) 도입
3. Read Replica 추가 (Replication)
4. 테이블 분리 (수직 분할)
5. Sharding (수평 분할) ← 최후의 수단
```

## 자주 나는 실수

- Replication lag을 고려하지 않고 쓰기 직후 Replica에서 읽어서 정합성 문제가 발생한다.
- Shard Key를 시간 기반으로 잡아서 최신 샤드에 부하가 집중된다.
- 필요하지 않은 시점에 Sharding을 도입해서 복잡도만 늘어난다.
- Cross-shard 쿼리가 많은 설계에서 Sharding을 적용해서 성능이 더 나빠진다.

## 핵심 요약

Replication은 데이터를 복제해서 읽기를 분산하고 가용성을 높입니다.
복제 지연(lag)이 있으므로, 쓰기 직후 읽기는 Master로 라우팅하는 전략이 필요합니다.

Sharding은 데이터를 분할 저장하여 쓰기와 용량을 분산합니다.
Shard Key는 균등 분산 + 쿼리에 항상 포함 + 변경 불가를 만족해야 합니다.

확장은 인덱스 최적화 → 캐시 → Replication → Sharding 순서로 검토하며, Sharding은 복잡도가 매우 높으므로 최후에 도입합니다.

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