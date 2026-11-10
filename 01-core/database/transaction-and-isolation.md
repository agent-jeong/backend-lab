---
title: "트랜잭션 격리 수준과 동시성 문제"
description: DB 트랜잭션 격리 수준과 동시성 문제
tags: [concept, database]
---

# 트랜잭션 격리 수준과 동시성 문제

트랜잭션 격리 수준(Isolation Level)은 동시에 실행되는 트랜잭션이 서로에게 얼마나 영향을 주는지 정하는 설정이다.

격리 수준을 알아야 같은 데이터를 읽었는데 결과가 다른 이유를 설명할 수 있다. 다만 재고가 음수가 되는 문제는 격리 수준을 올려도 대개 안 풀린다. 그건 락이나 원자적 UPDATE로 푼다. MySQL과 PostgreSQL은 기본 격리 수준부터 다르다.

> [!tip] 함께 읽기
> - [[acid-and-isolation]]: ACID와 격리 수준을 고르는 기준

## 동시성 문제

| 문제 | 설명 | 예시 |
|---|---|---|
| Dirty Read | 커밋되지 않은 데이터를 읽음 | TX-A가 수정 중인 데이터를 TX-B가 읽음 |
| Non-Repeatable Read | 같은 행을 다시 읽었는데 값이 변경됨 | TX-B가 커밋해서 TX-A의 재조회 결과가 달라짐 |
| Phantom Read | 같은 조건으로 다시 조회했는데 행이 추가/삭제됨 | TX-B가 INSERT해서 TX-A의 범위 조회 결과가 달라짐 |

## 격리 수준

| 격리 수준 | Dirty Read | Non-Repeatable Read | Phantom Read | 성능 |
|---|---|---|---|---|
| Read Uncommitted | O | O | O | 최고 |
| **Read Committed** | X | O | O | 좋음 |
| **Repeatable Read** | X | X | O (SQL 표준) | 보통 |
| Serializable | X | X | X | 최저 |

- MySQL InnoDB 기본값: Repeatable Read
- PostgreSQL 기본값: Read Committed

MySQL InnoDB의 Repeatable Read는 일반 SELECT에서는 MVCC 스냅샷으로, `SELECT ... FOR UPDATE` 같은 잠금 읽기에서는 Next-Key Lock(Gap Lock 포함)으로 Phantom Read를 막는다. 그래도 완전히 막지는 못한다. 같은 트랜잭션에서 일반 SELECT와 UPDATE/잠금 읽기를 섞으면, 잠금 읽기는 스냅샷이 아니라 최신 커밋 데이터를 보므로 다른 트랜잭션이 INSERT한 행이 나타날 수 있다.

### MVCC (Multi-Version Concurrency Control)

InnoDB는 MVCC로 격리를 구현한다. 데이터를 고치면 이전 버전을 Undo Log에 남기고, 읽기는 스냅샷(read view)을 기준으로 보이는 버전을 고른다.

- Repeatable Read: 트랜잭션의 **첫 번째 일반 SELECT 시점**에 스냅샷을 만들고 끝까지 쓴다. `BEGIN` 시점이 아니다.
- Read Committed: SELECT마다 새 스냅샷을 만든다.

```
TX-A: 첫 SELECT 실행 (snapshot: version 1)
TX-B: UPDATE users SET name = '변경' WHERE id = 1; COMMIT;  (version 2)
TX-A: SELECT name FROM users WHERE id = 1;  → '원래값' (version 1 읽음)
```

일반 SELECT는 락을 걸지 않아서 읽기와 쓰기가 서로 막지 않는다. 반대로 `FOR UPDATE`, `UPDATE`, `DELETE`는 스냅샷이 아니라 최신 커밋 버전을 읽고 락을 건다.

## 격리 수준이 막지 못하는 것: Lost Update

위 표에는 없지만 실무에서 가장 자주 터진다. 두 트랜잭션이 같은 값을 읽고 각자 계산해서 쓰면 먼저 쓴 값이 사라진다.

```
재고 = 10
TX-A: SELECT stock → 10
TX-B: SELECT stock → 10
TX-A: UPDATE stock = 9; COMMIT
TX-B: UPDATE stock = 9; COMMIT   → 2개 팔렸는데 재고는 9
```

- MySQL InnoDB는 Repeatable Read에서도 이걸 막지 않는다. UPDATE는 스냅샷이 아니라 최신 행에 락을 걸고 그대로 덮어쓴다.
- PostgreSQL Repeatable Read는 같은 행을 동시에 고치면 뒤 트랜잭션을 serialization 에러로 실패시킨다. 애플리케이션에 재시도가 있어야 한다.
- 실무 해법은 격리 수준이 아니라 `UPDATE ... SET stock = stock - 1 WHERE stock > 0` 같은 원자적 UPDATE, `SELECT ... FOR UPDATE`, `@Version` 낙관적 락이다. 자세한 비교는 [[lock]].

## 실무에서 격리 수준 고르기

대부분의 애플리케이션은 DB 기본값(MySQL: Repeatable Read, PostgreSQL: Read Committed)을 그대로 쓴다.

```java
// Spring에서 특정 메서드의 격리 수준 변경 (드물게 사용)
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferMoney(Long fromId, Long toId, BigDecimal amount) { }
```

격리 수준을 올리면 안전해지는 대신 동시 처리량이 떨어진다. 동시성 문제 대부분은 격리 수준보다 락이나 애플리케이션 로직으로 푼다.

## 자주 깨지는 곳

- **MySQL과 PostgreSQL의 기본 격리 수준이 같다고 생각한다.** DB를 바꾸면 같은 코드의 동작이 달라진다.
- **Repeatable Read면 Phantom Read가 없다고 단정한다.** DB마다 다르고, InnoDB도 잠금 읽기를 섞으면 새 행이 보인다.
- **격리 수준으로 모든 동시성 문제가 풀린다고 믿는다.** Repeatable Read여도 read-modify-write는 Lost Update가 난다.
- **MVCC를 모르고 "읽기에도 락이 걸린다"고 설명한다.**
- **Serializable을 쓰면 데드락이 잦아진다는 걸 모른다.**

## 한 번에 설명하기

> 격리 수준은 동시 트랜잭션이 서로 얼마나 영향을 주는지 정하는 설정이고, Dirty Read, Non-Repeatable Read, Phantom Read를 어디까지 막느냐로 나뉩니다. MySQL InnoDB는 Repeatable Read가 기본이고, MVCC 덕분에 일반 읽기와 쓰기가 서로 막지 않습니다. 다만 재고 차감 같은 Lost Update는 격리 수준으로 안 막히기 때문에, 저는 원자적 UPDATE나 `SELECT ... FOR UPDATE`, `@Version`으로 처리합니다.

## 꼬리 질문

> [!question]- MySQL의 Repeatable Read에서 Phantom Read가 대부분 발생하지 않는 이유는?
> 일반 SELECT는 첫 조회 시점의 MVCC 스냅샷을 계속 읽어서 다른 트랜잭션이 INSERT한 행이 보이지 않습니다. 잠금 읽기(`FOR UPDATE`)는 Next-Key Lock으로 범위에 대한 INSERT를 막습니다. 다만 일반 SELECT와 잠금 읽기·UPDATE를 섞으면 잠금 읽기는 최신 데이터를 보므로 새 행이 나타날 수 있습니다.

> [!question]- Repeatable Read면 재고 차감이 안전한가?
> 아닙니다. 둘 다 같은 재고를 읽고 각자 UPDATE하면 Lost Update가 납니다. InnoDB는 이를 막지 않으므로 원자적 UPDATE(`stock = stock - 1 WHERE stock > 0`), `SELECT ... FOR UPDATE`, 또는 `@Version`으로 처리합니다.

> [!question]- MVCC란 무엇인가?
> 데이터의 여러 버전을 유지해서 읽기 트랜잭션이 락 없이 일관된 데이터를 읽을 수 있게 하는 메커니즘입니다. Undo Log에 이전 버전을 보관하고, 각 트랜잭션은 자신의 스냅샷을 읽습니다. InnoDB Repeatable Read에서는 그 스냅샷이 트랜잭션 시작이 아니라 첫 일반 SELECT 시점에 만들어집니다.

> [!question]- Read Committed와 Repeatable Read의 실무적 차이는?
> Read Committed는 쿼리마다 최신 커밋된 데이터를 읽고, Repeatable Read는 첫 조회 시점의 스냅샷을 트랜잭션 끝까지 유지합니다. 같은 쿼리를 두 번 실행했을 때 결과가 달라질 수 있느냐가 핵심 차이입니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)
- [MySQL 8.4: Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)
- [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[lock]]
