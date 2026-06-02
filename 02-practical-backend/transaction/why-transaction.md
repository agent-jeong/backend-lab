---
title: 트랜잭션이 필요한 이유
description: 여러 데이터 변경을 하나의 정합성 단위로 다루는 실무 기준
---

# 트랜잭션이 필요한 이유

## 한 줄 정의

트랜잭션은 여러 읽기와 쓰기를 하나의 작업 단위로 묶어, 성공하면 함께 반영하고 실패하면 함께 되돌리는 정합성 장치다.

## 실무에서 왜 문제 되는가

- 주문은 생성됐는데 결제 상태가 반영되지 않는 식의 부분 성공이 발생할 수 있다.
- 재고 차감, 포인트 사용, 쿠폰 사용처럼 여러 상태가 함께 바뀌는 작업은 중간 실패에 취약하다.
- 동시 요청이 같은 데이터를 수정하면 lost update, 중복 처리, 음수 재고 같은 문제가 생길 수 있다.
- 트랜잭션을 너무 넓게 잡으면 락 점유 시간이 길어지고 장애가 다른 요청으로 전파된다.

## 동작 원리

1. 애플리케이션이 DB 커넥션을 얻고 트랜잭션을 시작한다.
2. 여러 SQL이 같은 트랜잭션 안에서 실행된다.
3. 모두 성공하면 commit으로 변경을 확정한다.
4. 중간에 실패하면 rollback으로 변경을 취소한다.
5. commit 전까지 다른 트랜잭션이 어떤 값을 볼지는 격리 수준과 락에 따라 달라진다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 하나의 업무 불변식을 지켜야 함 | 하나의 DB 트랜잭션 | 부분 성공을 막아야 한다 |
| 조회만 수행함 | 트랜잭션 최소화 또는 read-only | 락과 커넥션 점유를 줄인다 |
| 외부 API 호출 포함 | DB 트랜잭션 밖으로 분리 | 외부 지연이 DB 락 점유로 이어질 수 있다 |
| 여러 서비스/DB에 걸친 작업 | 이벤트, 보상, Outbox | 단일 DB 트랜잭션으로 묶기 어렵다 |

## 자주 나는 실수

- 트랜잭션을 넓게 잡을수록 항상 안전하다고 생각한다.
- 외부 API, 파일 업로드, 메시지 발행을 DB 트랜잭션 안에서 오래 수행한다.
- 예외를 잡아 삼킨 뒤 정상 종료시켜 commit이 발생한다.
- 정합성 조건을 애플리케이션 if문에만 두고 DB 제약 조건을 두지 않는다.
- 재시도 시 같은 작업이 중복 반영될 수 있다는 점을 고려하지 않는다.

## 확인 방법

- 테스트: 중간 예외 발생 시 이전 DB 변경이 rollback되는지 확인한다.
- 로그: transaction begin, commit, rollback, 예외 발생 지점을 추적한다.
- 메트릭: DB 커넥션 점유 시간, lock wait, deadlock, slow query를 본다.
- DB 제약: unique key, foreign key, check constraint로 불변식을 보강한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 부분 성공을 줄이고 정합성을 지킨다 | 범위가 커지면 락 경합과 지연이 커진다 |
| 실패 시 rollback으로 복구가 단순해진다 | 외부 시스템 작업은 rollback되지 않는다 |
| 업무 단위를 명확히 표현할 수 있다 | 여러 DB나 서비스에 걸친 정합성은 별도 설계가 필요하다 |

## 짧은 예제

```java
@Transactional
public void placeOrder(Long userId, Long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId)
        .orElseThrow();

    product.decreaseStock(quantity);
    orderRepository.save(Order.create(userId, productId, quantity));
}
```

재고 차감과 주문 생성은 함께 성공하거나 함께 실패해야 한다. 이때 트랜잭션은 부분 성공을 막지만, 재고 행에 락이 걸릴 수 있으므로 트랜잭션 안에서는 필요한 DB 작업만 짧게 수행해야 한다.

## 핵심 요약

트랜잭션은 여러 DB 작업을 하나의 정합성 단위로 묶는다.

성공 시 commit, 실패 시 rollback으로 부분 성공을 줄인다.

하지만 트랜잭션은 공짜가 아니며 커넥션, 락, undo/redo 로그 비용을 만든다.

실무에서는 "어디까지 반드시 함께 성공해야 하는가"를 먼저 정하고 범위를 최소화한다.

외부 API나 메시지 발행처럼 DB가 rollback할 수 없는 작업은 트랜잭션 밖으로 분리하거나 보상 전략을 둔다.

## 꼬리 질문

- 트랜잭션을 너무 넓게 잡으면 어떤 장애가 생길 수 있는가?
- 주문 생성과 결제 요청은 하나의 트랜잭션으로 묶을 수 있는가?
- DB 제약 조건 없이 애플리케이션 로직만으로 정합성을 지키면 어떤 문제가 있는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/database|database]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
