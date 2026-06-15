---
title: "DB 락의 종류와 동작"
description: DB 락의 종류와 데드락 원인 및 해결
---

# DB 락의 종류와 동작

## 한 줄 정의

락(Lock)은 동시에 같은 데이터를 수정하는 것을 방지하기 위해 데이터에 대한 접근을 제어하는 메커니즘이다.

## 실무에서 왜 중요한가

락을 이해하지 못하면 다음 문제가 생긴다.

- 데드락이 발생했는데 원인을 찾지 못한다.
- 재고 차감에서 동시 요청으로 음수 재고가 발생한다.
- SELECT FOR UPDATE를 모르고 애플리케이션에서만 동시성을 처리한다.
- 락 경합이 심해서 응답 시간이 느려지는 원인을 모른다.

## 락의 종류

### Shared Lock (S Lock, 공유 락)

읽기 락이다. 여러 트랜잭션이 동시에 S Lock을 획득할 수 있다. S Lock이 걸린 데이터에 쓰기(X Lock)는 대기한다.

### Exclusive Lock (X Lock, 배타 락)

쓰기 락이다. X Lock이 걸린 데이터에 다른 트랜잭션의 읽기(S Lock)와 쓰기(X Lock) 모두 대기한다.

| 요청 \ 보유 | S Lock | X Lock |
|---|---|---|
| S Lock | 호환 (동시 가능) | 대기 |
| X Lock | 대기 | 대기 |

### Row Lock vs Table Lock

| 구분 | Row Lock | Table Lock |
|---|---|---|
| 범위 | 행 단위 | 테이블 전체 |
| 동시성 | 높음 | 낮음 |
| InnoDB | 기본 | DDL 또는 특수 상황 |

InnoDB는 Row Lock이 기본이다. 인덱스를 사용하지 않는 UPDATE는 Full Table Scan이 발생하면서 의도치 않게 넓은 범위의 락이 걸릴 수 있다.

### Gap Lock

InnoDB의 Repeatable Read에서 범위 조건에 대해 **행 사이의 간격**에 걸리는 락이다.

```sql
-- id가 10, 20, 30인 행이 있을 때
SELECT * FROM products WHERE id BETWEEN 15 AND 25 FOR UPDATE;
-- → (10, 20] 과 (20, 30) 구간에 Gap Lock이 걸림
-- → 다른 트랜잭션이 id=12, id=22 등을 INSERT할 수 없음
```

Gap Lock은 Phantom Read를 방지하지만, INSERT가 차단되어 동시성이 떨어질 수 있다. 데드락의 원인이 되기도 한다.

## 비관적 락 vs 낙관적 락

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

데이터를 읽을 때 미리 락을 건다. 충돌이 자주 발생하는 상황에 적합하다.

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

락을 걸지 않고 커밋 시점에 충돌을 감지한다. 충돌이 드물게 발생하는 상황에 적합하다.

### 비교

| 기준 | 비관적 락 | 낙관적 락 |
|---|---|---|
| 락 시점 | 조회 시 | 커밋 시 |
| 충돌 처리 | 대기 | 예외 발생 후 재시도 |
| 적합한 상황 | 충돌 빈번 (재고, 좌석) | 충돌 드묾 (프로필, 설정) |
| 성능 | 락 경합 시 대기 | 락 없이 처리, 충돌 시 재시도 비용 |

## 데드락

```
TX-A: UPDATE orders SET status = 'PAID' WHERE id = 1;      → orders id=1 X Lock 획득
TX-B: UPDATE products SET stock = stock - 1 WHERE id = 10;  → products id=10 X Lock 획득
TX-A: UPDATE products SET stock = stock - 1 WHERE id = 10;  → 대기 (TX-B가 X Lock 보유)
TX-B: UPDATE orders SET status = 'SHIPPED' WHERE id = 1;    → 대기 (TX-A가 X Lock 보유)
→ 데드락 발생
```

### 데드락 해결

- **DB 자동 감지**: InnoDB는 데드락을 감지하면 하나의 트랜잭션을 롤백한다.
- **접근 순서 통일**: 모든 트랜잭션이 테이블/행을 같은 순서로 접근하면 데드락을 예방할 수 있다.
- **트랜잭션 범위 최소화**: 락 보유 시간을 줄인다.
- **타임아웃 설정**: `innodb_lock_wait_timeout`으로 대기 시간을 제한한다.

## 자주 나는 실수

- 인덱스 없는 UPDATE로 의도치 않게 넓은 범위에 락이 걸린다.
- 비관적 락과 낙관적 락의 사용 기준을 모르고 선택한다.
- 데드락 원인을 분석하지 않고 재시도 로직만 추가한다.
- 트랜잭션 범위가 넓어서 락 보유 시간이 길어진다.
- SELECT FOR UPDATE 없이 조회 후 업데이트해서 Lost Update가 발생한다.

## 핵심 요약

락은 동시 데이터 수정을 방지하는 메커니즘으로, Shared Lock(읽기)과 Exclusive Lock(쓰기)이 있습니다.
InnoDB는 Row Lock이 기본이며, 인덱스를 사용하지 않으면 넓은 범위에 락이 걸릴 수 있습니다.

비관적 락은 충돌이 잦을 때(재고, 좌석), 낙관적 락은 충돌이 드물 때(프로필, 설정) 사용합니다.
데드락은 테이블/행 접근 순서를 통일하고 트랜잭션 범위를 최소화해서 예방합니다.

## 꼬리 질문

> [!question]- 비관적 락과 낙관적 락 중 어떤 것을 사용해야 하는가?
> 충돌 빈도가 기준입니다. 재고 차감, 좌석 예약처럼 동시 요청이 같은 데이터를 수정하면 비관적 락, 사용자 프로필 수정처럼 충돌이 드물면 낙관적 락이 적합합니다.

> [!question]- 데드락이 발생하면 DB는 어떻게 처리하는가?
> InnoDB는 데드락을 자동으로 감지하고, 비용이 적은 트랜잭션을 롤백합니다. 롤백된 트랜잭션은 애플리케이션에서 재시도해야 합니다.

> [!question]- SELECT FOR UPDATE는 언제 사용하는가?
> 조회한 데이터를 기반으로 수정할 때, 다른 트랜잭션이 중간에 수정하는 것을 막으려면 사용합니다. 재고 조회 후 차감 같은 "읽고 쓰는" 패턴에서 필수입니다.

> [!question]- Gap Lock이란?
> InnoDB의 Repeatable Read에서 범위 조건에 대해 "행 사이의 간격"에 걸리는 락입니다. 다른 트랜잭션이 해당 범위에 INSERT하는 것을 방지해서 Phantom Read를 막습니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[transaction-and-isolation]]
- [[db-index]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]