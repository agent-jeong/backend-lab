---
title: ACID와 격리 수준
description: 트랜잭션의 ACID 속성과 isolation level 선택 기준
tags: [concept, transaction]
---

# ACID와 격리 수준

ACID는 트랜잭션이 지켜야 하는 원자성, 일관성, 격리성, 지속성이다. 격리 수준은 동시에 도는 트랜잭션이 서로의 변경을 얼마나 볼 수 있는지 정하는 기준이다.

격리 수준을 낮추면 dirty read, non-repeatable read, phantom read 같은 현상이 생기고, 높이면 정합성은 강해지는 대신 락 경합, 대기, 데드락이 늘어난다. 그런데 격리 수준을 올린다고 업무 불변식이 지켜지지는 않는다. 금액, 재고, 상태 전이는 제약 조건과 락 전략으로 따로 보호한다.

## 동작

1. 트랜잭션은 변경 내용을 commit 전까지 임시 상태로 둔다.
2. DB는 undo/redo 로그, MVCC, 락 등으로 rollback과 crash recovery를 지원한다.
3. isolation level은 다른 트랜잭션의 미커밋/커밋 변경을 어디까지 읽을지 제한한다.
4. 격리 수준이 높을수록 동시성은 낮아지고 대기 비용은 커진다.

| 속성 | 의미 | 실무에서 |
|---|---|---|
| Atomicity | 모두 성공하거나 모두 실패 | 중간 실패 시 부분 반영을 막는다 |
| Consistency | 제약 조건과 불변식 유지 | DB 제약 조건과 애플리케이션 검증이 함께 필요하다 |
| Isolation | 동시에 실행돼도 간섭 제한 | 격리 수준과 락 전략을 골라야 한다 |
| Durability | commit 후 변경 보존 | 장애 뒤에도 commit 결과가 남아야 한다 |

DB가 rollback과 recovery를 제공하지만, 외부 시스템 변경은 ACID 범위에 들어가지 않는다.

## 격리 수준

| 격리 수준 | 허용될 수 있는 현상 | 메모 |
|---|---|---|
| READ UNCOMMITTED | dirty read | 일반적인 업무 시스템에서는 거의 쓰지 않는다 |
| READ COMMITTED | non-repeatable read, phantom read | 커밋된 값만 읽어 dirty read를 막는다 |
| REPEATABLE READ | phantom read 가능성은 DB 구현에 따라 다름 | 같은 행 반복 조회 일관성이 필요할 때 쓴다 |
| SERIALIZABLE | 동시 실행을 직렬 실행처럼 보장 | 정합성은 강하지만 처리량 저하가 크다 |

같은 이름이라도 DBMS마다 구현이 다르다. MySQL InnoDB의 `REPEATABLE READ`는 MVCC와 next-key lock 등으로 일부 phantom 상황을 막지만, PostgreSQL의 같은 이름과 동작이 완전히 같다고 보면 안 된다.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public OrderSummary getOrderSummary(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    List<OrderLine> lines = orderLineRepository.findByOrderId(orderId);
    return OrderSummary.of(order, lines);
}
```

격리 수준은 코드 한 줄로 바뀌지만, 실제 결과는 DB 구현과 쿼리 패턴에 따라 달라진다. 정합성이 걸린 쓰기 흐름에서는 isolation level보다 조건부 update, unique key, pessimistic lock 같은 구체적인 보호 장치를 먼저 보는 경우가 많다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD | DB 기본 격리 수준 우선 | 대부분의 업무에서 비용과 정합성 균형이 맞다 |
| 금액, 재고, 상태 전이 | 명시적 락 또는 조건부 update 검토 | 격리 수준만으로는 의도를 표현하기 어렵다 |
| 집계 기준으로 삽입 여부 판단 | unique key 또는 serializable 검토 | phantom read로 중복 생성될 수 있다 |
| 읽기 일관성이 필요함 | repeatable read 또는 snapshot 성격 확인 | 한 트랜잭션 안에서 기준 시점이 달라지면 안 된다 |

## 자주 깨지는 곳

- **격리 수준을 높이면 모든 동시성 문제가 풀린다고 생각한다.** 대기와 데드락만 늘고 중복 생성은 그대로일 수 있다.
- **DB 기본 격리 수준을 확인하지 않고 동작을 추측한다.**
- **unique key가 필요한 문제를 isolation level로 풀려고 한다.**
- **테스트 데이터가 적다.** phantom read나 lock wait가 재현되지 않는다.
- **read-only 조회 트랜잭션과 쓰기 트랜잭션의 비용 차이를 보지 않는다.**
- **ACID 원리를 모른 채 설정만 바꾼다.** 격리 수준과 트랜잭션 범위를 잘못 잡는다.

## 운영에서 볼 것

- 트랜잭션 두 개 이상을 동시에 열어 읽기 현상을 재현해 본다.
- transaction isolation, lock wait, deadlock 로그를 확인한다.
- lock wait time, deadlock count, transaction duration을 본다.
- 사용하는 DB의 기본 isolation level과 MVCC 구현을 확인한다.

## 면접에서 말하기

> ACID는 트랜잭션이 보장하는 정합성의 기본 성질이고, 격리 수준은 동시에 도는 트랜잭션 사이에서 어떤 읽기 현상을 허용할지 정하는 기준입니다. 낮추면 처리량에 유리하고 높이면 락 대기와 데드락 비용이 커집니다. 저는 DB 기본값과 그 DB의 구현을 먼저 확인하고, 업무 불변식은 격리 수준이 아니라 unique key, 조건부 update, 락으로 명시적으로 보호합니다.

## 꼬리 질문

- dirty read, non-repeatable read, phantom read의 차이는 무엇인가?
- 격리 수준을 높였는데도 중복 데이터가 생길 수 있는 이유는 무엇인가?
- unique key와 isolation level은 각각 어떤 문제를 해결하는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[db-index]]
- [[lock]]
