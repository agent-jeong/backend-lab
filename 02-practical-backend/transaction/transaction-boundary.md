---
title: 트랜잭션 경계 설정
description: 트랜잭션 범위를 어디서 시작하고 끝낼지 정하는 실무 기준
tags: [concept, transaction]
---

# 트랜잭션 경계 설정

트랜잭션 경계는 어떤 작업들을 하나의 commit/rollback 단위로 묶을지 정하는 설계 결정이다.

경계가 좁으면 함께 성공해야 할 변경이 따로 commit되어 부분 성공이 생긴다. 넓으면 락과 커넥션을 오래 잡아 처리량이 떨어지고, 외부 API나 메시지 발행까지 들어가면 DB rollback과 외부 부작용이 어긋난다. 좋은 경계는 정합성 요구사항과 장애 전파 비용 사이에서 정한다.

## 동작

1. 업무 유스케이스가 시작된다.
2. 반드시 함께 성공해야 하는 DB 변경을 골라낸다.
3. 그 변경만 하나의 트랜잭션으로 묶는다.
4. 외부 부작용은 commit 이후 실행하거나 별도 복구 전략을 둔다.
5. 실패했을 때 rollback되는 것과 안 되는 것을 구분해 둔다.

```java
public void checkout(CheckoutCommand command) {
    Long orderId = orderService.createOrder(command);
    paymentClient.requestPayment(orderId, command.paymentToken());
}

@Transactional
public Long createOrder(CheckoutCommand command) {
    Order order = orderRepository.save(Order.create(command.userId()));
    stockService.decrease(command.productId(), command.quantity());
    return order.getId();
}
```

DB 변경만 `createOrder` 트랜잭션 안에 두고 결제 요청은 바깥에서 호출한다. 실제 시스템에서는 결제가 실패하면 주문을 취소 상태로 바꾸거나 재시도/보상 흐름을 따로 설계한다.

## 어디까지 묶나

| 상황 | 경계 | 이유 |
|---|---|---|
| 주문 생성과 주문 상세 저장 | 같은 트랜잭션 | 하나만 저장되면 데이터가 깨진다 |
| 결제 승인 API 호출 | 트랜잭션 밖 | 외부 API는 DB rollback 대상이 아니다 |
| 알림 발송 | commit 이후 비동기 | 알림 실패가 핵심 거래 실패가 되면 안 된다 |
| 재고 차감과 주문 생성 | 같은 트랜잭션 또는 명확한 보상 | 업무 불변식이 연결돼 있다 |
| 조회 후 긴 계산 | 트랜잭션 밖 계산 후 짧은 쓰기 | 락과 커넥션 점유를 줄인다 |

경계는 Service 계층의 유스케이스 단위로 잡으면 rollback 범위를 예측하기 쉽다. Service 경계가 불명확하면 같은 기능도 호출 경로에 따라 정합성이 달라진다. 흐름이 복잡해지면 이벤트와 보상 설계가 필요하다.

## 자주 깨지는 곳

- **컨트롤러부터 전체 요청을 하나의 트랜잭션으로 묶는다.**
- **트랜잭션 안에서 네트워크 호출, 파일 처리, 긴 CPU 작업을 한다.** 그 시간만큼 락과 커넥션을 쥔다.
- **repository 메서드마다 트랜잭션을 붙인다.** 유스케이스 단위 정합성이 깨진다.
- **조회와 검증 사이에 다른 트랜잭션이 값을 바꿀 수 있다는 점을 놓친다.**
- **after commit 후속 작업의 실패를 추적하거나 재시도하지 않는다.**

## 운영에서 볼 것

- 중간 실패 위치별로 어떤 데이터가 남는지 테스트한다.
- 트랜잭션 시작부터 commit까지 걸린 시간을 로그로 남긴다.
- transaction duration, connection active time, lock wait를 본다.
- 코드 리뷰에서 트랜잭션 안에 외부 I/O가 있는지 확인한다.

## 면접에서 말하기

> 트랜잭션 경계는 함께 commit되거나 rollback되어야 하는 DB 작업의 범위입니다. 좁으면 부분 성공이 생기고 넓으면 락과 커넥션 점유가 늘어납니다. 저는 유스케이스 단위로 경계를 잡되 외부 I/O는 가능한 한 빼고, DB가 rollback할 수 없는 작업은 commit 이후 실행하거나 보상 트랜잭션으로 다룹니다.

## 꼬리 질문

- 트랜잭션 안에서 외부 API를 호출하면 어떤 문제가 생기는가?
- Service 메서드마다 `@Transactional`을 붙이면 안전한가?
- commit 이후 알림 발송이 실패하면 어떻게 처리할 것인가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 전송 기록 선커밋 후 외부 호출
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 저장·응답·발급을 나눈 경계

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[spring-transaction]]
- [[external-api-and-transaction]]
