---
title: ACID와 격리 수준
description: 트랜잭션이 지켜 주는 네 가지 성질과, 격리 수준을 어떻게 고르는지
tags: [concept, transaction]
---

# ACID와 격리 수준

ACID는 트랜잭션이 지키는 네 가지 성질인 원자성, 일관성, 격리성, 지속성이다. 격리 수준은 동시에 도는 트랜잭션이 서로가 바꾼 값을 어디까지 볼 수 있는지 정한다.

격리 수준을 낮추면 dirty read, non-repeatable read, phantom read 같은 현상이 생긴다. 높이면 그런 현상은 줄지만 락을 기다리는 시간과 데드락이 늘어난다. 그런데 격리 수준을 올려도 "재고는 음수가 되면 안 된다" 같은 업무 규칙은 저절로 지켜지지 않는다. 금액, 재고, 상태 전이는 제약 조건과 락으로 따로 막는다.

> [!tip] 함께 읽기
> - [[transaction-and-isolation]]: 격리 수준별로 무엇이 보이고 막히는지(MVCC, 갭 락) 자세히 다룬 글

## 동작

1. 트랜잭션이 바꾼 내용은 commit 전까지 확정되지 않은 상태로 남는다.
2. DB는 undo/redo 로그, MVCC, 락으로 rollback과 장애 뒤 복구(crash recovery)를 처리한다.
3. 격리 수준은 다른 트랜잭션이 바꾼 값을, 커밋 전이든 후든 어디까지 읽을지 정한다.
4. 격리 수준이 높을수록 동시에 처리할 수 있는 양은 줄고 기다리는 시간은 늘어난다.

| 속성 | 의미 | 실무에서 |
|---|---|---|
| Atomicity | 모두 성공하거나 모두 실패 | 중간 실패 시 부분 반영을 막는다 |
| Consistency | 제약 조건과 불변식 유지 | DB 제약 조건과 애플리케이션 검증이 함께 필요하다 |
| Isolation | 동시에 실행돼도 간섭 제한 | 격리 수준과 락 전략을 골라야 한다 |
| Durability | commit 후 변경 보존 | 장애 뒤에도 commit 결과가 남아야 한다 |

DB가 rollback과 복구를 해 주지만, 외부 시스템에 보낸 변경은 ACID 바깥이다.

## 격리 수준

| 격리 수준 | 허용될 수 있는 현상 | 메모 |
|---|---|---|
| READ UNCOMMITTED | dirty read | 일반적인 업무 시스템에서는 거의 쓰지 않는다 |
| READ COMMITTED | non-repeatable read, phantom read | 커밋된 값만 읽어 dirty read를 막는다 |
| REPEATABLE READ | phantom read 가능성은 DB 구현에 따라 다름 | 같은 행 반복 조회 일관성이 필요할 때 쓴다 |
| SERIALIZABLE | 동시 실행을 직렬 실행처럼 보장 | 정합성은 강하지만 처리량 저하가 크다 |

이름이 같아도 DBMS마다 구현이 다르다. MySQL InnoDB의 `REPEATABLE READ`는 MVCC와 next-key lock 등으로 일부 phantom 상황을 막는다. PostgreSQL의 같은 이름이 그대로 똑같이 동작한다고 보면 안 된다.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public OrderSummary getOrderSummary(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    List<OrderLine> lines = orderLineRepository.findByOrderId(orderId);
    return OrderSummary.of(order, lines);
}
```

격리 수준은 코드 한 줄로 바뀌지만, 실제로 어떻게 동작할지는 DB 구현과 쿼리 모양에 달려 있다. 그래서 정합성이 걸린 쓰기에서는 격리 수준을 만지기보다 조건부 update, unique key, pessimistic lock처럼 막을 대상을 직접 막는 방법을 먼저 찾는 경우가 많다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD | DB 기본 격리 수준 우선 | 대부분의 업무에서 비용과 정합성 균형이 맞다 |
| 금액, 재고, 상태 전이 | 명시적 락 또는 조건부 update 검토 | 격리 수준만으로는 의도를 표현하기 어렵다 |
| 집계 기준으로 삽입 여부 판단 | unique key 또는 serializable 검토 | phantom read로 중복 생성될 수 있다 |
| 읽기 일관성이 필요함 | repeatable read 또는 snapshot 성격 확인 | 한 트랜잭션 안에서 기준 시점이 달라지면 안 된다 |

## 자주 깨지는 곳

- 격리 수준만 올리면 동시성 문제가 다 풀린다고 믿으면, 대기와 데드락만 늘고 중복 생성은 그대로 남기도 한다.
- 쓰는 DB의 기본 격리 수준을 확인하지 않으면, 동작을 추측으로 설명하게 된다.
- unique key로 막아야 할 중복을 격리 수준으로 막으려 하면, 비용만 들고 중복은 여전히 생긴다.
- 테스트 데이터가 적으면 phantom read나 lock wait가 재현되지 않는다.
- 읽기 전용 조회 트랜잭션과 쓰기 트랜잭션의 비용 차이를 보지 않으면, 조회에도 무거운 트랜잭션을 열게 된다.
- ACID가 무엇을 지켜 주는지 모르고 설정만 바꾸면, 격리 수준과 트랜잭션 범위를 엉뚱하게 잡는다.

## 운영에서 볼 것

- 트랜잭션 두 개 이상을 동시에 열어 읽기 현상을 직접 재현해 본다.
- 격리 수준 설정, lock wait, deadlock 로그를 확인한다.
- lock wait time, deadlock count, transaction duration을 본다.
- 쓰는 DB의 기본 격리 수준과 MVCC 구현을 확인한다.

## 한 번에 설명하기

> ACID는 트랜잭션이 지켜 주는 기본 성질이고, 격리 수준은 동시에 도는 트랜잭션끼리 어떤 읽기 현상까지 허용할지 정하는 설정입니다.
>
> 낮추면 처리량은 좋아지고, 높이면 락 대기와 데드락이 늘어납니다.
>
> 저는 DB 기본값과 그 DB가 실제로 어떻게 구현했는지부터 확인합니다. 재고나 금액 같은 업무 규칙은 격리 수준에 맡기지 않고 unique key, 조건부 update, 락으로 직접 막습니다.

## 꼬리 질문

- dirty read, non-repeatable read, phantom read는 각각 무엇이 다른가?
- 격리 수준을 높였는데도 중복 데이터가 생기는 이유는?
- unique key와 격리 수준은 각각 어떤 문제를 막는가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: InnoDB and the ACID Model](https://dev.mysql.com/doc/refman/8.4/en/mysql-acid.html)
- [MySQL 8.4: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[db-index]]
- [[lock]]
