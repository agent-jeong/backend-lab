---
title: 트랜잭션이 필요한 이유
description: 여러 데이터 변경을 하나의 정합성 단위로 다루는 실무 기준
tags: [concept, transaction]
---

# 트랜잭션이 필요한 이유

트랜잭션은 여러 읽기와 쓰기를 하나의 작업 단위로 묶어, 성공하면 함께 반영하고 실패하면 함께 되돌리는 정합성 장치다.

트랜잭션이 없으면 주문은 생성됐는데 결제 상태는 반영되지 않는 부분 성공이 생긴다. 재고 차감, 포인트 사용, 쿠폰 사용처럼 여러 상태가 같이 바뀌는 작업이 특히 그렇다. 하지만 트랜잭션은 공짜가 아니다. 커넥션, 락, undo/redo 로그 비용이 들고, 넓게 잡을수록 락 점유가 길어져 장애가 다른 요청으로 번진다. 그래서 "어디까지 반드시 함께 성공해야 하는가"를 먼저 정하고 범위는 최소로 잡는다.

## 동작

1. 애플리케이션이 DB 커넥션을 얻고 트랜잭션을 시작한다.
2. 여러 SQL이 같은 트랜잭션 안에서 실행된다.
3. 모두 성공하면 commit으로 변경을 확정한다.
4. 중간에 실패하면 rollback으로 변경을 취소한다.
5. commit 전까지 다른 트랜잭션이 어떤 값을 볼지는 격리 수준과 락에 따라 달라진다.

```java
@Transactional
public void placeOrder(Long userId, Long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId)
        .orElseThrow();

    product.decreaseStock(quantity);
    orderRepository.save(Order.create(userId, productId, quantity));
}
```

재고 차감과 주문 생성은 함께 성공하거나 함께 실패해야 한다. 트랜잭션이 부분 성공을 막아 주지만, 재고 행에 락이 걸리므로 트랜잭션 안에서는 필요한 DB 작업만 짧게 한다.

## 언제 어떻게 묶나

| 상황 | 선택 | 이유 |
|---|---|---|
| 하나의 업무 불변식을 지켜야 함 | 하나의 DB 트랜잭션 | 부분 성공을 막아야 한다 |
| 조회만 수행함 | 트랜잭션 최소화 또는 read-only | 락과 커넥션 점유를 줄인다 |
| 외부 API 호출 포함 | DB 트랜잭션 밖으로 분리 | 외부 지연이 DB 락 점유로 이어진다 |
| 여러 서비스/DB에 걸친 작업 | 이벤트, 보상, Outbox | 단일 DB 트랜잭션으로 묶기 어렵다 |

트랜잭션이 막아 주는 건 한 DB 안의 부분 성공까지다. 외부 시스템 작업은 rollback되지 않고, 여러 DB나 서비스에 걸친 정합성은 따로 설계해야 한다. 동시 요청이 같은 데이터를 바꿀 때의 lost update, 중복 처리, 음수 재고도 트랜잭션만으로는 다 막히지 않는다.

## 자주 깨지는 곳

- **트랜잭션을 넓게 잡을수록 안전하다고 생각한다.** 락 경합과 지연만 커진다.
- **외부 API, 파일 업로드, 메시지 발행을 DB 트랜잭션 안에서 오래 수행한다.**
- **예외를 잡아 삼키고 정상 종료시킨다.** 실패한 작업이 commit된다.
- **정합성 조건을 애플리케이션 if문에만 둔다.** unique key, foreign key, check constraint로 DB에서도 막는다.
- **재시도 때 같은 작업이 중복 반영된다는 점을 잊는다.**

## 운영에서 볼 것

- 중간에 예외가 나면 이전 DB 변경이 rollback되는지 테스트한다.
- transaction begin, commit, rollback, 예외 발생 지점을 로그로 추적한다.
- DB 커넥션 점유 시간, lock wait, deadlock, slow query를 본다.

## 면접에서 말하기

> 트랜잭션은 여러 DB 작업을 하나의 정합성 단위로 묶어 성공하면 commit, 실패하면 rollback해서 부분 성공을 막습니다. 다만 커넥션, 락, undo/redo 로그 비용이 들기 때문에 저는 어디까지 반드시 함께 성공해야 하는지부터 정하고 범위를 최소로 잡습니다. 외부 API나 메시지 발행처럼 DB가 rollback할 수 없는 작업은 트랜잭션 밖으로 빼거나 보상 전략을 둡니다.

## 꼬리 질문

- 트랜잭션을 너무 넓게 잡으면 어떤 장애가 생길 수 있는가?
- 주문 생성과 결제 요청은 하나의 트랜잭션으로 묶을 수 있는가?
- DB 제약 조건 없이 애플리케이션 로직만으로 정합성을 지키면 어떤 문제가 있는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/database|database]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
