---
title: 트랜잭션이 필요한 이유
description: 여러 변경을 한 번에 반영하거나 한 번에 취소해야 하는 이유와 그 비용
tags: [concept, transaction]
---

# 트랜잭션이 필요한 이유

트랜잭션은 여러 번의 읽기와 쓰기를 하나로 묶어서, 다 성공하면 함께 반영하고 하나라도 실패하면 함께 되돌리는 장치다.

트랜잭션이 없으면 주문은 만들어졌는데 결제 상태는 그대로인 일이 생긴다. 재고 차감, 포인트 사용, 쿠폰 사용처럼 여러 상태가 같이 바뀌는 작업에서 특히 잘 생긴다. 다만 트랜잭션은 공짜가 아니다. 커넥션과 락을 쥐고, undo/redo 로그도 쌓는다. 넓게 잡을수록 락을 오래 쥐어서 한 요청의 지연이 다른 요청으로 번진다. 그래서 "무엇이 반드시 같이 성공해야 하나"를 먼저 정하고, 범위는 그만큼만 잡는다.

## 동작

1. 애플리케이션이 DB 커넥션을 얻고 트랜잭션을 시작한다.
2. 여러 SQL이 같은 트랜잭션 안에서 실행된다.
3. 모두 성공하면 commit해서 변경을 확정한다.
4. 중간에 실패하면 rollback해서 변경을 취소한다.
5. commit 전까지 다른 트랜잭션이 어떤 값을 볼지는 격리 수준과 락에 따라 다르다.

```java
@Transactional
public void placeOrder(Long userId, Long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId)
        .orElseThrow();

    product.decreaseStock(quantity);
    orderRepository.save(Order.create(userId, productId, quantity));
}
```

재고 차감과 주문 생성은 같이 성공하거나 같이 실패해야 한다. 트랜잭션이 둘 중 하나만 반영되는 일을 막아 주지만, 그동안 재고 행에 락이 걸려 있으니 트랜잭션 안에서는 꼭 필요한 DB 작업만 짧게 한다.

## 언제 어떻게 묶나

| 상황 | 선택 | 이유 |
|---|---|---|
| 하나의 업무 불변식을 지켜야 함 | 하나의 DB 트랜잭션 | 부분 성공을 막아야 한다 |
| 조회만 수행함 | 트랜잭션 최소화 또는 read-only | 락과 커넥션 점유를 줄인다 |
| 외부 API 호출 포함 | DB 트랜잭션 밖으로 분리 | 외부 지연이 DB 락 점유로 이어진다 |
| 여러 서비스/DB에 걸친 작업 | 이벤트, 보상, Outbox | 단일 DB 트랜잭션으로 묶기 어렵다 |

트랜잭션이 막아 주는 건 DB 하나 안에서 일부만 반영되는 일까지다. 외부 시스템에 보낸 요청은 rollback되지 않고, 여러 DB나 서비스에 걸친 정합성은 따로 설계해야 한다. 여러 요청이 동시에 같은 데이터를 바꿀 때 생기는 lost update, 중복 처리, 음수 재고도 트랜잭션만으로는 다 막지 못한다.

## 자주 깨지는 곳

- 트랜잭션을 넓게 잡을수록 안전하다고 생각하면, 락 경합과 지연만 커진다.
- 외부 API, 파일 업로드, 메시지 발행을 DB 트랜잭션 안에서 하면, 그 시간 내내 락과 커넥션을 쥔다.
- 예외를 잡아 삼키고 정상 종료시키면, 실패한 작업이 commit된다.
- 정합성 조건을 애플리케이션 if문에만 두면, 동시에 들어온 요청이 그 검사를 같이 통과한다. unique key, foreign key, check constraint로 DB에서도 막는다.
- 재시도하면 같은 작업이 두 번 반영된다는 걸 잊으면, 주문이나 차감이 중복으로 남는다.

## 운영에서 볼 것

- 중간에 예외가 나면 앞서 바꾼 DB 변경이 정말 rollback되는지 테스트한다.
- 트랜잭션 시작, commit, rollback, 예외가 난 지점을 로그로 따라갈 수 있게 한다.
- DB 커넥션 점유 시간, lock wait, deadlock, slow query를 본다.

## 한 번에 설명하기

> 트랜잭션은 여러 DB 작업을 하나로 묶어서, 다 성공하면 commit하고 실패하면 rollback해 일부만 반영되는 일을 막습니다.
>
> 대신 커넥션과 락을 쥐고 undo/redo 로그도 쌓기 때문에, 저는 무엇이 반드시 같이 성공해야 하는지부터 정하고 범위를 그만큼만 잡습니다.
>
> 외부 API 호출이나 메시지 발행처럼 DB가 되돌릴 수 없는 작업은 트랜잭션 밖으로 빼거나 보상 방법을 따로 둡니다.

## 꼬리 질문

- 트랜잭션을 너무 넓게 잡으면 어떤 장애가 생기나?
- 주문 생성과 결제 요청을 한 트랜잭션으로 묶을 수 있나?
- DB 제약 조건 없이 애플리케이션 로직만으로 정합성을 지키면 무엇이 문제인가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: InnoDB and the ACID Model](https://dev.mysql.com/doc/refman/8.4/en/mysql-acid.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/database|database]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
