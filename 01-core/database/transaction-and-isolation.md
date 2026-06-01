---
title: Transaction And Isolation
description: DB 트랜잭션 격리 수준과 동시성 문제
---

# Transaction And Isolation

## 한 줄 정의

트랜잭션 격리 수준(Isolation Level)은 동시에 실행되는 트랜잭션이 서로 얼마나 영향을 주는지를 제어하는 설정이다.

## 실무에서 왜 중요한가

격리 수준을 이해하지 못하면 다음 문제가 생긴다.

- 같은 데이터를 동시에 읽었는데 결과가 다른 이유를 모른다.
- 재고 차감에서 동시 요청이 오면 음수가 되는 원인을 모른다.
- Dirty Read, Non-Repeatable Read, Phantom Read를 구분하지 못한다.
- MySQL과 PostgreSQL의 기본 격리 수준이 다른 것을 모른다.

## 동시성 문제 종류

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

MySQL InnoDB의 Repeatable Read는 일반 SELECT에서 MVCC 스냅샷으로 Phantom Read를 방지하고, `SELECT FOR UPDATE` 등 잠금 읽기에서는 Gap Lock으로 방지한다. SQL 표준과 다르므로 DB별 동작을 확인해야 한다.

- **MySQL InnoDB 기본값**: Repeatable Read (MVCC + Gap Lock으로 대부분의 Phantom Read 방지)
- **PostgreSQL 기본값**: Read Committed

### MVCC (Multi-Version Concurrency Control)

InnoDB는 MVCC로 격리를 구현한다. 데이터를 수정하면 이전 버전을 Undo Log에 보관하고, 각 트랜잭션은 자신의 시작 시점 스냅샷을 읽는다.

```
TX-A 시작 (snapshot: version 1)
TX-B: UPDATE users SET name = '변경' WHERE id = 1; COMMIT;  (version 2)
TX-A: SELECT name FROM users WHERE id = 1;  → '원래값' (version 1 읽음)
```

읽기 시 락을 걸지 않아서 읽기와 쓰기가 서로 차단하지 않는다.

## 실무에서의 격리 수준 선택

대부분의 애플리케이션은 DB 기본값(MySQL: Repeatable Read, PostgreSQL: Read Committed)을 그대로 사용한다.

```java
// Spring에서 특정 메서드의 격리 수준 변경 (드물게 사용)
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferMoney(Long fromId, Long toId, BigDecimal amount) { }
```

격리 수준을 올리면 안전하지만 동시 처리량이 떨어진다. 대부분의 동시성 문제는 격리 수준보다 **락**이나 **애플리케이션 로직**으로 해결한다.

## 자주 나는 실수

- MySQL과 PostgreSQL의 기본 격리 수준이 다른 것을 모른다.
- Repeatable Read에서 Phantom Read가 발생하지 않는다고 단정한다 (DB마다 다름).
- 격리 수준만으로 모든 동시성 문제가 해결된다고 생각한다.
- MVCC의 존재를 모르고 "읽기에도 락이 걸린다"고 설명한다.
- Serializable을 사용하면 데드락 빈도가 높아지는 것을 모른다.

## 핵심 요약

트랜잭션 격리 수준은 동시 트랜잭션이 서로 얼마나 영향을 주는지를 제어합니다.
Dirty Read, Non-Repeatable Read, Phantom Read가 대표적인 동시성 문제입니다.

MySQL InnoDB는 Repeatable Read가 기본이며, MVCC로 읽기와 쓰기가 서로 차단하지 않습니다.
격리 수준만으로 모든 동시성 문제를 해결할 수 없고, 락이나 애플리케이션 로직을 함께 사용해야 합니다.

## 꼬리 질문

> [!question]- MySQL의 Repeatable Read에서 Phantom Read가 발생하지 않는 이유는?
> InnoDB의 MVCC는 트랜잭션 시작 시점의 스냅샷을 읽기 때문에 다른 트랜잭션이 INSERT한 행이 보이지 않습니다. 추가로 Gap Lock으로 범위에 대한 삽입을 차단합니다.

> [!question]- MVCC란 무엇인가?
> 데이터의 여러 버전을 유지해서 읽기 트랜잭션이 락 없이 일관된 데이터를 읽을 수 있게 하는 메커니즘입니다. Undo Log에 이전 버전을 보관하고, 각 트랜잭션은 자신의 시작 시점 스냅샷을 읽습니다.

> [!question]- Read Committed와 Repeatable Read의 실무적 차이는?
> Read Committed는 쿼리마다 최신 커밋된 데이터를 읽고, Repeatable Read는 트랜잭션 시작 시점의 스냅샷을 유지합니다. 같은 쿼리를 두 번 실행했을 때 결과가 달라질 수 있느냐가 핵심 차이입니다.

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[lock]]