---
title: ACID와 격리 수준
description: 트랜잭션의 ACID 속성과 isolation level 선택 기준
---

# ACID와 격리 수준

## 한 줄 정의

ACID는 트랜잭션이 지켜야 하는 원자성, 일관성, 격리성, 지속성이고, 격리 수준은 동시에 실행되는 트랜잭션이 서로의 변경을 얼마나 볼 수 있는지 정하는 기준이다.

## 실무에서 왜 문제 되는가

- 격리 수준을 낮게 쓰면 dirty read, non-repeatable read, phantom read 같은 현상이 생길 수 있다.
- 격리 수준을 높이면 정합성은 강해지지만 락 경합, 대기, 데드락 가능성이 커질 수 있다.
- DBMS마다 같은 격리 수준 이름이라도 구현 방식이 다를 수 있다.
- 예를 들어 MySQL InnoDB의 `REPEATABLE READ`는 MVCC와 next-key lock 등으로 일부 phantom 상황을 막을 수 있지만, PostgreSQL의 같은 이름과 동작이 완전히 같다고 보면 안 된다.
- 면접에서 ACID를 암기식으로만 말하면 실무 판단 능력이 드러나지 않는다.

## 동작 원리

1. 트랜잭션은 변경 내용을 commit 전까지 임시 상태로 관리한다.
2. DB는 undo/redo 로그, MVCC, 락 등을 사용해 rollback과 crash recovery를 지원한다.
3. isolation level은 다른 트랜잭션의 미커밋/커밋 변경을 읽을 수 있는 범위를 제한한다.
4. 격리 수준이 높아질수록 동시성은 낮아지고 대기 비용은 커질 수 있다.

## ACID

| 속성 | 의미 | 실무 관점 |
|---|---|---|
| Atomicity | 모두 성공하거나 모두 실패 | 중간 실패 시 부분 반영을 막는다 |
| Consistency | 제약 조건과 불변식 유지 | DB 제약 조건과 애플리케이션 검증이 함께 필요하다 |
| Isolation | 동시에 실행돼도 간섭 제한 | 격리 수준과 락 전략을 선택해야 한다 |
| Durability | commit 후 변경 보존 | 장애 이후에도 commit 결과가 남아야 한다 |

## 격리 수준

| 격리 수준 | 허용될 수 있는 현상 | 실무 메모 |
|---|---|---|
| READ UNCOMMITTED | dirty read | 일반적인 업무 시스템에서는 거의 쓰지 않는다 |
| READ COMMITTED | non-repeatable read, phantom read | 커밋된 값만 읽어 dirty read를 막는다 |
| REPEATABLE READ | phantom read 가능성은 DB 구현에 따라 다름 | 같은 행 반복 조회 일관성이 중요할 때 사용한다 |
| SERIALIZABLE | 동시 실행을 직렬 실행처럼 보장 | 정합성은 강하지만 처리량 저하가 크다 |

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD | DB 기본 격리 수준 우선 | 대부분의 업무에서 비용과 정합성 균형이 맞다 |
| 금액, 재고, 상태 전이 | 명시적 락 또는 조건부 update 검토 | 격리 수준만으로는 의도를 표현하기 어렵다 |
| 집계 기준으로 삽입 여부 판단 | unique key 또는 serializable 검토 | phantom read로 중복 생성될 수 있다 |
| 읽기 일관성이 중요함 | repeatable read 또는 snapshot 성격 확인 | 한 트랜잭션 안에서 기준 시점이 중요하다 |

## 자주 나는 실수

- 격리 수준을 높이면 모든 동시성 문제가 해결된다고 생각한다.
- DB 기본 격리 수준을 확인하지 않고 동작을 추측한다.
- unique key가 필요한 문제를 isolation level만으로 해결하려 한다.
- 테스트 데이터가 적어 phantom read나 lock wait를 재현하지 못한다.
- read-only 조회 트랜잭션과 쓰기 트랜잭션의 비용 차이를 고려하지 않는다.

## 확인 방법

- 테스트: 두 개 이상의 트랜잭션을 동시에 열어 읽기 현상을 재현한다.
- 로그: transaction isolation, lock wait, deadlock 로그를 확인한다.
- 메트릭: lock wait time, deadlock count, transaction duration을 본다.
- DB 설정: 사용하는 DB의 기본 isolation level과 MVCC 구현을 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 격리 수준으로 동시 읽기/쓰기 가시성을 제어한다 | 높은 격리 수준은 대기와 데드락을 늘릴 수 있다 |
| ACID는 정합성 논의의 공통 언어가 된다 | 실제 정합성은 DB 제약, 락, 업무 로직까지 함께 봐야 한다 |
| DB가 rollback과 recovery를 제공한다 | 외부 시스템 변경은 ACID 범위에 포함되지 않는다 |

## 짧은 예제

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public OrderSummary getOrderSummary(Long orderId) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    List<OrderLine> lines = orderLineRepository.findByOrderId(orderId);
    return OrderSummary.of(order, lines);
}
```

격리 수준은 코드 한 줄로 바꿀 수 있지만, 실제 문제는 DB 구현과 쿼리 패턴에 따라 달라진다. 정합성이 중요한 쓰기 흐름에서는 isolation level보다 조건부 update, unique key, pessimistic lock 같은 구체적인 보호 장치를 먼저 검토하는 경우가 많다.

## 핵심 요약

ACID는 트랜잭션이 제공하는 정합성의 기본 성질이다.

격리 수준은 동시에 실행되는 트랜잭션 사이에서 어떤 읽기 현상을 허용할지 정한다.

낮은 격리 수준은 처리량에 유리하지만 읽기 일관성 문제가 생길 수 있다.

높은 격리 수준은 정합성에 유리하지만 락 대기와 데드락 비용이 커질 수 있다.

실무에서는 DB 기본값을 이해하고, 업무 불변식은 제약 조건과 락 전략으로 명확히 보호한다.

## 꼬리 질문

- dirty read, non-repeatable read, phantom read의 차이는 무엇인가?
- 격리 수준을 높였는데도 중복 데이터가 생길 수 있는 이유는 무엇인가?
- unique key와 isolation level은 각각 어떤 문제를 해결하는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[db-index]]
- [[lock]]
