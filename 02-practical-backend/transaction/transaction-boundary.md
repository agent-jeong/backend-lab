---
title: 트랜잭션 경계 설정
description: 트랜잭션 범위를 어디서 시작하고 끝낼지 정하는 실무 기준
---

# 트랜잭션 경계 설정

## 한 줄 정의

트랜잭션 경계는 어떤 작업들을 하나의 commit/rollback 단위로 묶을지 정하는 설계 결정이다.

## 실무에서 왜 문제 되는가

- 경계가 너무 좁으면 함께 성공해야 할 변경이 따로 commit되어 부분 성공이 생긴다.
- 경계가 너무 넓으면 락과 커넥션을 오래 잡아 처리량이 떨어진다.
- 외부 API나 메시지 발행까지 포함하면 DB rollback과 외부 부작용이 어긋난다.
- Service 계층 경계가 불명확하면 같은 기능도 호출 경로에 따라 정합성이 달라진다.

## 동작 원리

1. 업무 유스케이스가 시작된다.
2. 반드시 함께 성공해야 하는 DB 변경을 식별한다.
3. 해당 변경만 하나의 트랜잭션으로 묶는다.
4. 외부 부작용은 commit 이후 실행하거나 별도 복구 전략을 둔다.
5. 실패 시 rollback되는 것과 rollback되지 않는 것을 명확히 구분한다.

## 실무 판단 기준

| 상황 | 경계 | 이유 |
|---|---|---|
| 주문 생성과 주문 상세 저장 | 같은 트랜잭션 | 하나만 저장되면 데이터가 깨진다 |
| 결제 승인 API 호출 | 트랜잭션 밖 | 외부 API는 DB rollback 대상이 아니다 |
| 알림 발송 | commit 이후 비동기 | 알림 실패가 핵심 거래 실패가 되면 안 된다 |
| 재고 차감과 주문 생성 | 같은 트랜잭션 또는 명확한 보상 | 업무 불변식이 연결돼 있다 |
| 조회 후 긴 계산 | 트랜잭션 밖 계산 후 짧은 쓰기 | 락과 커넥션 점유를 줄인다 |

## 자주 나는 실수

- 컨트롤러부터 전체 요청을 하나의 트랜잭션으로 묶는다.
- 트랜잭션 안에서 네트워크 호출, 파일 처리, 긴 CPU 작업을 수행한다.
- repository 메서드마다 트랜잭션을 붙여 유스케이스 단위 정합성이 깨진다.
- 조회와 검증 사이에 다른 트랜잭션이 값을 바꿀 수 있다는 점을 놓친다.
- after commit 후속 작업 실패를 추적하거나 재시도하지 않는다.

## 확인 방법

- 테스트: 중간 실패 위치별로 어떤 데이터가 남는지 확인한다.
- 로그: 트랜잭션 시작부터 commit까지 걸린 시간을 남긴다.
- 메트릭: transaction duration, connection active time, lock wait를 본다.
- 코드 리뷰: 트랜잭션 안에 외부 I/O가 있는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 업무 정합성 단위를 명확히 표현한다 | 경계가 커지면 락과 장애 전파가 커진다 |
| rollback 범위를 예측하기 쉬워진다 | 외부 시스템 부작용은 별도 복구가 필요하다 |
| Service 계층 유스케이스와 잘 맞는다 | 복잡한 플로우는 이벤트와 보상 설계가 필요하다 |

## 짧은 예제

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

예제에서는 DB 변경만 `createOrder` 트랜잭션 안에 두고, 결제 요청은 바깥에서 호출한다. 실제 시스템에서는 결제 실패 시 주문을 취소 상태로 바꾸거나 재시도/보상 플로우를 별도로 설계해야 한다.

## 핵심 요약

트랜잭션 경계는 함께 commit 또는 rollback되어야 하는 DB 작업의 범위다.

경계가 좁으면 부분 성공이 생기고, 경계가 넓으면 락과 커넥션 점유가 늘어난다.

실무에서는 유스케이스 단위로 경계를 잡되 외부 I/O는 가능한 한 제외한다.

DB가 rollback할 수 없는 작업은 commit 이후 실행하거나 보상 트랜잭션으로 다룬다.

좋은 경계는 정합성 요구사항과 장애 전파 비용 사이의 균형이다.

## 꼬리 질문

- 트랜잭션 안에서 외부 API를 호출하면 어떤 문제가 생기는가?
- Service 메서드마다 `@Transactional`을 붙이면 안전한가?
- commit 이후 알림 발송이 실패하면 어떻게 처리할 것인가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[spring-transaction]]
- [[external-api-and-transaction]]
