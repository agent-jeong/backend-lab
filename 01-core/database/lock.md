---
title: "DB 락의 종류와 동작"
description: DB 락의 종류와 데드락 원인 및 해결
tags: [concept, database]
---

# DB 락의 종류와 동작

락(Lock)은 여러 트랜잭션이 같은 데이터를 동시에 고치지 못하게 접근을 제어하는 장치다.

재고가 음수가 되거나, 데드락이 났는데 원인을 못 찾거나, 락 경합으로 응답이 느려지는 일은 대부분 락이 어디에 얼마나 오래 걸리는지 몰라서 생긴다. 애플리케이션에서만 동시성을 처리하고 `SELECT FOR UPDATE`를 모르는 경우도 같은 결과를 낸다.

> [!tip] 함께 읽기
> - [[lock-and-deadlock]]: 락 경합과 데드락에 대응하는 기준
> - [[pessimistic-lock]]: 충돌이 잦을 때 행을 먼저 잠그는 방식

## 락의 종류

### Shared Lock과 Exclusive Lock

- **Shared Lock (S Lock, 공유 락)**: 읽기 락이다. 여러 트랜잭션이 동시에 가질 수 있다. S Lock이 걸린 데이터에 쓰기(X Lock)는 기다린다.
- **Exclusive Lock (X Lock, 배타 락)**: 쓰기 락이다. X Lock이 걸린 데이터에는 다른 트랜잭션의 읽기(S Lock)와 쓰기(X Lock)가 모두 기다린다.

| 요청 \ 보유 | S Lock | X Lock |
|---|---|---|
| S Lock | 호환 (동시 가능) | 대기 |
| X Lock | 대기 | 대기 |

### Row Lock과 Table Lock

| 구분 | Row Lock | Table Lock |
|---|---|---|
| 범위 | 행 단위 | 테이블 전체 |
| 동시성 | 높음 | 낮음 |
| InnoDB | 기본 | DDL 또는 특수 상황 |

InnoDB는 Row Lock이 기본이다. 그런데 인덱스를 못 타는 UPDATE는 Full Table Scan을 하면서 훑은 범위에 락을 걸어, 의도보다 훨씬 넓게 잠글 수 있다.

### Gap Lock

InnoDB의 Repeatable Read에서 범위 조건에 대해 **행 사이의 간격**에 거는 락이다.

```sql
-- id가 10, 20, 30인 행이 있을 때
SELECT * FROM products WHERE id BETWEEN 15 AND 25 FOR UPDATE;
-- → (10, 20] 과 (20, 30) 구간에 Gap Lock이 걸림
-- → 다른 트랜잭션이 id=12, id=22 등을 INSERT할 수 없음
```

Gap Lock은 Phantom Read를 막는다. 대신 그 구간의 INSERT가 막혀 동시성이 떨어지고, 데드락의 원인이 되기도 한다.

## 비관적 락과 낙관적 락

### 비관적 락 (Pessimistic Lock)

```sql
-- SELECT FOR UPDATE: 조회 시 X Lock 획득
SELECT * FROM products WHERE id = 1 FOR UPDATE;
```

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT p FROM Product p WHERE p.id = :id")
Product findByIdForUpdate(@Param("id") Long id);
```

읽을 때 미리 락을 건다. 충돌이 잦은 데이터에 맞다.

### 낙관적 락 (Optimistic Lock)

```java
@Entity
public class Product {

    @Version
    private Long version;
}
```

```java
// 업데이트 시 version 비교
// UPDATE products SET stock = ?, version = version + 1
// WHERE id = ? AND version = ?
// → 0 rows updated면 OptimisticLockException 발생
```

락을 걸지 않고, version 조건이 붙은 UPDATE가 실행될 때 충돌을 감지한다. JPA에서는 이 UPDATE가 flush 시점에 나가므로 보통 커밋 직전이다. 충돌이 드문 데이터에 맞다.

| 기준 | 비관적 락 | 낙관적 락 |
|---|---|---|
| 락·충돌 감지 시점 | 조회 시 락 | UPDATE 실행(flush) 시 감지, 보통 커밋 직전 |
| 충돌 처리 | 대기 | 예외 발생 후 재시도 |
| 맞는 상황 | 충돌 빈번 (재고, 좌석) | 충돌 드묾 (프로필, 설정) |
| 성능 | 락 경합 시 대기 | 락 없이 처리, 충돌 시 재시도 비용 |

## 데드락

```
TX-A: UPDATE orders SET status = 'PAID' WHERE id = 1;      → orders id=1 X Lock 획득
TX-B: UPDATE products SET stock = stock - 1 WHERE id = 10;  → products id=10 X Lock 획득
TX-A: UPDATE products SET stock = stock - 1 WHERE id = 10;  → 대기 (TX-B가 X Lock 보유)
TX-B: UPDATE orders SET status = 'SHIPPED' WHERE id = 1;    → 대기 (TX-A가 X Lock 보유)
→ 데드락 발생
```

두 트랜잭션이 서로 상대가 가진 락을 기다리면 데드락이다. 대응은 이렇다.

- **DB 자동 감지**: InnoDB는 데드락을 감지하면 트랜잭션 하나를 롤백한다.
- **접근 순서 통일**: 모든 트랜잭션이 테이블과 행을 같은 순서로 잠그면 데드락이 생기지 않는다.
- **트랜잭션 범위 축소**: 락을 쥐고 있는 시간을 줄인다.
- **타임아웃**: `innodb_lock_wait_timeout`으로 대기 시간을 제한한다.

## 자주 깨지는 곳

- **인덱스 없는 UPDATE.** 의도치 않게 넓은 범위가 잠긴다.
- **비관적·낙관적 락을 충돌 빈도와 상관없이 고른다.** 충돌이 잦은데 낙관적 락이면 재시도만 쌓이고, 드문데 비관적 락이면 괜히 기다린다.
- **데드락 원인은 안 보고 재시도만 붙인다.** 같은 데드락이 계속 난다.
- **트랜잭션 범위가 넓다.** 락을 오래 쥐어 경합이 커진다.
- **`SELECT FOR UPDATE` 없이 조회 후 업데이트한다.** 동시 요청끼리 덮어써서 Lost Update가 난다.

## 면접에서 말하기

> 락은 동시 수정을 막는 장치이고, 읽기용 Shared Lock과 쓰기용 Exclusive Lock이 있습니다. InnoDB는 Row Lock이 기본이지만 인덱스를 못 타면 넓은 범위가 잠기기 때문에, 저는 UPDATE 조건에 인덱스가 있는지부터 봅니다. 재고나 좌석처럼 충돌이 잦으면 비관적 락, 프로필처럼 드물면 낙관적 락을 씁니다. 데드락은 접근 순서를 통일하고 트랜잭션 범위를 줄여서 예방합니다.

## 꼬리 질문

> [!question]- 비관적 락과 낙관적 락 중 어떤 것을 사용해야 하는가?
> 충돌 빈도가 기준입니다. 재고 차감, 좌석 예약처럼 동시 요청이 같은 데이터를 수정하면 비관적 락, 사용자 프로필 수정처럼 충돌이 드물면 낙관적 락이 적합합니다.

> [!question]- 데드락이 발생하면 DB는 어떻게 처리하는가?
> InnoDB는 데드락을 자동으로 감지하고, 비용이 적은 트랜잭션을 롤백합니다. 롤백된 트랜잭션은 애플리케이션에서 재시도해야 합니다.

> [!question]- SELECT FOR UPDATE는 언제 사용하는가?
> 조회한 데이터를 기반으로 수정할 때, 다른 트랜잭션이 중간에 수정하는 것을 막으려면 사용합니다. 재고 조회 후 차감 같은 "읽고 쓰는" 패턴에서 필수입니다.

> [!question]- Gap Lock이란?
> InnoDB의 Repeatable Read에서 범위 조건에 대해 "행 사이의 간격"에 걸리는 락입니다. 다른 트랜잭션이 해당 범위에 INSERT하는 것을 방지해서 Phantom Read를 막습니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[transaction-and-isolation]]
- [[db-index]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
