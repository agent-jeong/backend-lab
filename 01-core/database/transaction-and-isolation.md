---
title: "트랜잭션 격리 수준과 동시성 문제"
description: 동시에 도는 트랜잭션이 서로의 데이터를 어디까지 보는지, 격리 수준으로 못 막는 건 무엇인지
tags: [concept, database]
---

# 트랜잭션 격리 수준과 동시성 문제

트랜잭션 격리 수준(Isolation Level)은 동시에 도는 트랜잭션이 서로가 고친 데이터를 어디까지 볼 수 있는지 정하는 설정이다.

한 트랜잭션 안에서 같은 주문을 두 번 읽었는데 값이 다르게 나왔다면 격리 수준을 봐야 한다. 다만 재고가 음수가 되는 문제는 격리 수준을 올려도 대개 안 풀리고, 락이나 원자적 UPDATE로 푼다. 그리고 MySQL과 PostgreSQL은 기본 격리 수준부터 다르다.

> [!tip] 함께 읽기
> - [[acid-and-isolation]]: ACID와 격리 수준을 어떻게 고르나

## 동시성 문제

| 문제 | 설명 | 예시 |
|---|---|---|
| Dirty Read | 아직 커밋 안 된 데이터를 읽는다 | TX-A가 고치는 중인 데이터를 TX-B가 읽는다 |
| Non-Repeatable Read | 같은 행을 다시 읽었더니 값이 바뀌어 있다 | TX-B가 커밋해서 TX-A가 다시 읽은 값이 달라진다 |
| Phantom Read | 같은 조건으로 다시 읽었더니 행이 늘거나 줄었다 | TX-B가 INSERT해서 TX-A의 범위 조회 결과가 달라진다 |

## 격리 수준

| 격리 수준 | Dirty Read | Non-Repeatable Read | Phantom Read | 성능 |
|---|---|---|---|---|
| Read Uncommitted | O | O | O | 최고 |
| **Read Committed** | X | O | O | 좋음 |
| **Repeatable Read** | X | X | O (SQL 표준) | 보통 |
| Serializable | X | X | X | 최저 |

- MySQL InnoDB 기본값: Repeatable Read
- PostgreSQL 기본값: Read Committed

MySQL InnoDB의 Repeatable Read는 일반 SELECT에서는 MVCC 스냅샷으로, `SELECT ... FOR UPDATE` 같은 잠금 읽기에서는 Next-Key Lock(Gap Lock 포함)으로 Phantom Read를 막는다. 그래도 완전히 막지는 못한다. 같은 트랜잭션에서 일반 SELECT와 UPDATE나 잠금 읽기를 섞으면, 잠금 읽기는 스냅샷이 아니라 가장 최근에 커밋된 데이터를 읽기 때문에 다른 트랜잭션이 INSERT한 행이 보일 수 있다.

### MVCC (Multi-Version Concurrency Control)

InnoDB는 MVCC로 트랜잭션끼리 떼어 놓는다. 데이터를 고치면 이전 버전을 Undo Log에 남겨 두고, 읽을 때는 스냅샷(read view)을 기준으로 어느 버전을 보여 줄지 고른다.

- Repeatable Read는 트랜잭션에서 처음 일반 SELECT를 실행할 때 스냅샷을 만들고 끝까지 그걸 쓴다. `BEGIN` 시점이 아니다.
- Read Committed는 SELECT마다 스냅샷을 새로 만든다.

```
TX-A: 첫 SELECT 실행 (snapshot: version 1)
TX-B: UPDATE users SET name = '변경' WHERE id = 1; COMMIT;  (version 2)
TX-A: SELECT name FROM users WHERE id = 1;  → '원래값' (version 1 읽음)
```

일반 SELECT는 락을 걸지 않아서 읽기와 쓰기가 서로를 기다리지 않는다. 반대로 `FOR UPDATE`, `UPDATE`, `DELETE`는 스냅샷이 아니라 가장 최근에 커밋된 버전을 읽고 락을 건다.

## 격리 수준이 막지 못하는 것: Lost Update

위 표에는 없지만 실무에서 가장 자주 터지는 문제다. 두 트랜잭션이 같은 값을 읽고 각자 계산해서 쓰면, 먼저 쓴 값이 덮여서 사라진다.

```
재고 = 10
TX-A: SELECT stock → 10
TX-B: SELECT stock → 10
TX-A: UPDATE stock = 9; COMMIT
TX-B: UPDATE stock = 9; COMMIT   → 2개 팔렸는데 재고는 9
```

- MySQL InnoDB는 Repeatable Read에서도 이걸 막지 않는다. UPDATE는 스냅샷이 아니라 최신 행에 락을 걸고 그대로 덮어쓴다.
- PostgreSQL Repeatable Read는 같은 행을 동시에 고치면 뒤에 온 트랜잭션을 serialization 에러로 실패시킨다. 그래서 애플리케이션에 재시도가 있어야 한다.
- 실무에서는 격리 수준 말고 `UPDATE ... SET stock = stock - 1 WHERE stock > 0` 같은 원자적 UPDATE, `SELECT ... FOR UPDATE`, `@Version` 낙관적 락으로 푼다. 셋의 비교는 [[lock]]에 있다.

## 실무에서 격리 수준 고르기

애플리케이션 대부분은 DB 기본값(MySQL: Repeatable Read, PostgreSQL: Read Committed)을 그대로 쓴다.

```java
// Spring에서 특정 메서드의 격리 수준 변경 (드물게 사용)
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferMoney(Long fromId, Long toId, BigDecimal amount) { }
```

격리 수준을 올리면 안전해지는 대신 동시에 처리할 수 있는 양이 준다. 동시 요청 문제는 대부분 격리 수준보다 락이나 애플리케이션 로직으로 푼다.

## 자주 깨지는 곳

- MySQL과 PostgreSQL의 기본 격리 수준이 같다고 생각하면, DB를 옮겼을 때 같은 코드가 다르게 동작해서 당황한다.
- Repeatable Read면 Phantom Read가 없다고 단정하면 틀린다. DB마다 다르고, InnoDB도 잠금 읽기를 섞으면 새 행이 보인다.
- 격리 수준만 올리면 동시 요청 문제가 다 풀린다고 믿으면, 읽고 계산해서 쓰는(read-modify-write) 코드에서 Repeatable Read여도 Lost Update가 난다.
- MVCC를 모르면 "읽기에도 락이 걸린다"고 잘못 설명하게 된다.
- Serializable로 올리면 데드락이 잦아진다는 걸 모르고 올리면, 안전해지려다 데드락을 늘린다.

## 한 번에 설명하기

> 격리 수준은 동시에 도는 트랜잭션이 서로가 고친 데이터를 어디까지 보는지 정하는 설정이고, Dirty Read, Non-Repeatable Read, Phantom Read를 어디까지 막느냐로 나뉩니다.
>
> MySQL InnoDB는 Repeatable Read가 기본이고, MVCC 덕분에 일반 읽기와 쓰기가 서로를 기다리지 않습니다.
>
> 다만 재고 차감 같은 Lost Update는 격리 수준으로 안 막힙니다. 그래서 저는 원자적 UPDATE나 `SELECT ... FOR UPDATE`, `@Version`으로 막습니다.

## 꼬리 질문

> [!question]- MySQL의 Repeatable Read에서 Phantom Read가 대부분 발생하지 않는 이유는?
> 일반 SELECT는 처음 읽을 때 만든 MVCC 스냅샷을 계속 보기 때문에, 다른 트랜잭션이 INSERT한 행이 안 보입니다. 잠금 읽기(`FOR UPDATE`)는 Next-Key Lock으로 그 범위에 INSERT 자체를 못 하게 막습니다. 다만 일반 SELECT와 잠금 읽기나 UPDATE를 섞으면, 잠금 읽기는 최신 데이터를 보니까 새 행이 나타날 수 있습니다.

> [!question]- Repeatable Read면 재고 차감이 안전한가?
> 아닙니다. 두 트랜잭션이 같은 재고를 읽고 각자 UPDATE하면 Lost Update가 납니다. InnoDB는 이걸 막아 주지 않아서, 원자적 UPDATE(`stock = stock - 1 WHERE stock > 0`)나 `SELECT ... FOR UPDATE`, `@Version` 중 하나로 막습니다.

> [!question]- MVCC란 무엇인가?
> 데이터의 버전을 여러 개 남겨 두고, 읽는 쪽은 락 없이 자기 시점의 버전을 읽게 하는 방식입니다. 이전 버전은 Undo Log에 남겨 두고, 트랜잭션마다 자기 스냅샷을 봅니다. InnoDB Repeatable Read에서는 그 스냅샷이 트랜잭션을 시작할 때가 아니라 처음 일반 SELECT를 할 때 만들어집니다.

> [!question]- Read Committed와 Repeatable Read의 실무적 차이는?
> Read Committed는 쿼리마다 그때까지 커밋된 최신 데이터를 읽고, Repeatable Read는 처음 읽을 때의 스냅샷을 트랜잭션이 끝날 때까지 씁니다. 그래서 한 트랜잭션에서 같은 쿼리를 두 번 돌렸을 때 결과가 달라질 수 있느냐가 다릅니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)
- [MySQL 8.4: Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)
- [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[lock]]
