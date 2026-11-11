---
title: "DB 락의 종류와 동작"
description: 락이 어디에 얼마나 걸리는지, 데드락은 왜 나고 어떻게 줄이는지
tags: [concept, database]
---

# DB 락의 종류와 동작

락(Lock)은 여러 트랜잭션이 같은 데이터를 동시에 고치지 못하게, 한쪽이 끝날 때까지 다른 쪽을 기다리게 하는 장치다.

재고가 음수가 되거나, 데드락이 났는데 원인을 못 찾거나, 락을 기다리느라 응답이 느려지는 일은 대부분 락이 어디에 얼마나 오래 걸리는지 몰라서 생긴다. 동시 요청을 애플리케이션 코드로만 막으려 하고 `SELECT FOR UPDATE`를 쓰지 않을 때도 같은 일이 난다.

> [!tip] 함께 읽기
> - [[lock-and-deadlock]]: 락 경합과 데드락이 났을 때 어떻게 대응하나
> - [[pessimistic-lock]]: 충돌이 잦을 때 행을 먼저 잠그는 방식

## 락의 종류

### Shared Lock과 Exclusive Lock

- 공유 락(Shared Lock, S Lock)은 읽기 락이다. 여러 트랜잭션이 동시에 잡을 수 있다. S Lock이 걸린 데이터에 쓰려는(X Lock) 트랜잭션은 기다린다.
- 배타 락(Exclusive Lock, X Lock)은 쓰기 락이다. X Lock이 걸린 데이터는 다른 트랜잭션이 읽기 락(S Lock)을 잡든 쓰기 락(X Lock)을 잡든 모두 기다린다.

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

InnoDB는 Row Lock이 기본이다. 그런데 인덱스를 못 타는 UPDATE는 테이블을 처음부터 끝까지 훑으면서 훑은 행에 락을 걸기 때문에, 생각보다 훨씬 넓게 잠글 수 있다.

### Gap Lock

InnoDB가 Repeatable Read에서 범위 조건으로 잠글 때, 행 자체가 아니라 행과 행 사이의 빈 구간에 거는 락이다.

```sql
-- id가 10, 20, 30인 행이 있을 때
SELECT * FROM products WHERE id BETWEEN 15 AND 25 FOR UPDATE;
-- → (10, 20] 과 (20, 30) 구간에 Gap Lock이 걸림
-- → 다른 트랜잭션이 id=12, id=22 등을 INSERT할 수 없음
```

InnoDB는 Repeatable Read에서 범위를 잠글 때 행 락과 그 앞 구간의 Gap Lock을 합친 Next-Key Lock을 기본으로 쓴다. 덕분에 잠금 읽기(`FOR UPDATE`)에서는 Phantom Read가 생기지 않는다. 대신 그 구간에는 INSERT를 못 해서 동시에 처리할 수 있는 양이 줄고, 데드락이 나는 원인이 되기도 한다. Read Committed에서는 Gap Lock을 거의 쓰지 않는다.

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

읽을 때부터 락을 걸어 둔다. 재고처럼 여러 요청이 자주 부딪히는 데이터에 맞다.

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

락을 걸지 않는다. 대신 version 조건이 붙은 UPDATE가 실행될 때 0건이 바뀌면 누군가 먼저 고쳤다고 판단한다. JPA에서는 이 UPDATE가 flush 때 나가니 보통 커밋 직전이다. 부딪힐 일이 드문 데이터에 맞다.

| 기준 | 비관적 락 | 낙관적 락 |
|---|---|---|
| 언제 잠그거나 충돌을 알아채나 | 조회할 때 잠금 | UPDATE 실행(flush) 때 알아챔, 보통 커밋 직전 |
| 부딪히면 | 기다림 | 예외가 나고 다시 시도 |
| 맞는 데이터 | 자주 부딪힘 (재고, 좌석) | 드물게 부딪힘 (프로필, 설정) |
| 성능 | 부딪히면 기다림 | 락 없이 처리, 부딪히면 재시도 비용 |

## 데드락

```
TX-A: UPDATE orders SET status = 'PAID' WHERE id = 1;      → orders id=1 X Lock 획득
TX-B: UPDATE products SET stock = stock - 1 WHERE id = 10;  → products id=10 X Lock 획득
TX-A: UPDATE products SET stock = stock - 1 WHERE id = 10;  → 대기 (TX-B가 X Lock 보유)
TX-B: UPDATE orders SET status = 'SHIPPED' WHERE id = 1;    → 대기 (TX-A가 X Lock 보유)
→ 데드락 발생
```

두 트랜잭션이 서로 상대가 쥔 락을 기다리면 데드락이다. 이렇게 대응한다.

- InnoDB는 데드락을 알아채면 트랜잭션 하나를 롤백한다. 그 트랜잭션은 애플리케이션이 다시 시도해야 한다.
- 모든 트랜잭션이 테이블과 행을 같은 순서로 잠그면 데드락이 생기지 않는다.
- 트랜잭션을 짧게 만들어 락을 쥐고 있는 시간을 줄인다.
- `innodb_lock_wait_timeout`으로 락을 얼마나 기다릴지 상한을 둔다.

## 자주 깨지는 곳

- UPDATE 조건에 인덱스가 없으면, 생각보다 넓은 범위가 잠긴다.
- 얼마나 자주 부딪히는지 보지 않고 락을 고르면 손해를 본다. 자주 부딪히는데 낙관적 락이면 재시도만 쌓이고, 드문데 비관적 락이면 괜히 기다린다.
- 데드락 원인은 안 보고 재시도만 붙이면, 같은 데드락이 계속 난다.
- 트랜잭션이 길면, 락을 오래 쥐고 있어서 기다리는 요청이 늘어난다.
- `SELECT FOR UPDATE` 없이 읽고 나서 고치면, 동시에 들어온 요청끼리 서로 덮어써서 Lost Update가 난다.

## 한 번에 설명하기

> 락은 같은 데이터를 동시에 고치지 못하게 막는 장치이고, 읽기용 Shared Lock과 쓰기용 Exclusive Lock이 있습니다.
>
> InnoDB는 행 단위로 잠그는 게 기본이지만, 인덱스를 못 타면 넓은 범위가 잠깁니다. 그래서 저는 UPDATE 조건에 인덱스가 있는지부터 봅니다.
>
> 재고나 좌석처럼 자주 부딪히는 데이터는 비관적 락, 프로필처럼 드물게 부딪히는 데이터는 낙관적 락을 씁니다. 데드락은 잠그는 순서를 맞추고 트랜잭션을 짧게 만들어서 줄입니다.

## 꼬리 질문

> [!question]- 비관적 락과 낙관적 락 중 어떤 것을 사용해야 하는가?
> 얼마나 자주 부딪히느냐로 고릅니다. 재고 차감이나 좌석 예약처럼 동시 요청이 같은 행을 고치면 비관적 락을 쓰고, 프로필 수정처럼 부딪힐 일이 드물면 낙관적 락을 씁니다.

> [!question]- 데드락이 발생하면 DB는 어떻게 처리하는가?
> InnoDB가 데드락을 알아서 찾아내고, 되돌리는 비용이 적은 쪽 트랜잭션을 롤백합니다. 롤백된 쪽은 애플리케이션에서 다시 시도해야 합니다.

> [!question]- SELECT FOR UPDATE는 언제 사용하는가?
> 읽은 값을 보고 고칠 때, 그 사이에 다른 트랜잭션이 끼어들어 고치지 못하게 하려고 씁니다. 재고를 읽고 나서 차감하는 것처럼 읽고 쓰는 흐름이라면 꼭 필요합니다.

> [!question]- Gap Lock이란?
> InnoDB가 Repeatable Read에서 범위 조건으로 잠글 때, 행과 행 사이의 빈 구간에 거는 락입니다. 다른 트랜잭션이 그 구간에 INSERT하지 못하게 해서 Phantom Read를 막습니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[transaction-and-isolation]]
- [[db-index]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
