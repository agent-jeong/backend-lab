---
title: 트랜잭션 경계 설정
description: 어떤 작업까지 한 트랜잭션으로 묶고 어디서 끊을지 정하는 기준
tags: [concept, transaction]
---

# 트랜잭션 경계 설정

트랜잭션 경계는 어떤 작업들을 한 번에 commit하고 한 번에 rollback할지 정하는 일이다.

경계를 너무 좁게 잡으면 함께 성공해야 할 변경이 따로 commit된다. 주문은 저장됐는데 주문 상세는 빠지는 식이다. 너무 넓게 잡으면 락과 커넥션을 오래 쥐어서 처리량이 떨어지고, 외부 API나 메시지 발행까지 안에 들어가면 DB는 rollback됐는데 외부에는 이미 요청이 나간 상태가 된다. 그래서 무엇이 꼭 같이 맞아야 하는지와, 범위를 넓혔을 때 장애가 얼마나 번지는지를 같이 놓고 정한다.

## 동작

1. 주문하기 같은 업무 흐름이 시작된다.
2. 반드시 함께 성공해야 하는 DB 변경을 골라낸다.
3. 그 변경만 한 트랜잭션으로 묶는다.
4. 외부 호출 같은 부작용은 commit 뒤에 실행하거나 따로 복구 방법을 둔다.
5. 실패했을 때 rollback되는 것과 안 되는 것을 미리 나눠 둔다.

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

DB 변경만 `createOrder` 트랜잭션 안에 두고, 결제 요청은 그 바깥에서 부른다. 실제 시스템이라면 결제가 실패했을 때 주문을 취소 상태로 바꾸거나 재시도와 보상 흐름을 따로 만든다.

## 어디까지 묶나

| 상황 | 경계 | 이유 |
|---|---|---|
| 주문 생성과 주문 상세 저장 | 같은 트랜잭션 | 하나만 저장되면 데이터가 깨진다 |
| 결제 승인 API 호출 | 트랜잭션 밖 | 외부 API는 DB rollback 대상이 아니다 |
| 알림 발송 | commit 이후 비동기 | 알림 실패가 핵심 거래 실패가 되면 안 된다 |
| 재고 차감과 주문 생성 | 같은 트랜잭션 또는 명확한 보상 | 업무 불변식이 연결돼 있다 |
| 조회 후 긴 계산 | 트랜잭션 밖 계산 후 짧은 쓰기 | 락과 커넥션 점유를 줄인다 |

경계는 Service 계층에서 업무 흐름 하나(유스케이스) 단위로 잡으면 무엇이 rollback될지 예측하기 쉽다. Service 경계가 흐릿하면 같은 기능도 어느 경로로 불렀느냐에 따라 결과가 달라진다. 흐름이 더 복잡해지면 이벤트와 보상 설계가 필요하다.

## 자주 깨지는 곳

- 컨트롤러부터 요청 전체를 한 트랜잭션으로 묶으면, 필요 없는 작업까지 락과 커넥션을 쥔 채 돈다.
- 트랜잭션 안에서 네트워크 호출, 파일 처리, 오래 걸리는 계산을 하면, 그 시간만큼 락과 커넥션을 쥔다.
- repository 메서드마다 트랜잭션을 붙이면, 함께 저장돼야 할 변경이 따로 commit된다.
- 조회하고 검증하는 사이에 다른 트랜잭션이 값을 바꿀 수 있다는 걸 놓치면, 이미 바뀐 값으로 판단하게 된다.
- commit 뒤에 도는 후속 작업의 실패를 추적하거나 재시도하지 않으면, 알림이나 이벤트가 조용히 빠진다.

## 운영에서 볼 것

- 중간 어디서 실패하느냐에 따라 어떤 데이터가 남는지 테스트한다.
- 트랜잭션 시작부터 commit까지 걸린 시간을 로그로 남긴다.
- 트랜잭션 지속 시간, 커넥션 사용 시간, lock wait를 본다.
- 코드 리뷰에서 트랜잭션 안에 외부 I/O가 있는지 본다.

## 한 번에 설명하기

> 트랜잭션 경계는 함께 commit되거나 함께 rollback돼야 하는 DB 작업의 범위입니다. 좁으면 일부만 저장되고, 넓으면 락과 커넥션을 오래 쥡니다.
>
> 저는 업무 흐름 하나를 기준으로 경계를 잡고, 외부 I/O는 되도록 밖으로 뺍니다.
>
> DB가 되돌릴 수 없는 작업은 commit 뒤에 실행하거나 보상 트랜잭션으로 처리합니다.

## 꼬리 질문

- 트랜잭션 안에서 외부 API를 부르면 어떤 문제가 생기나?
- Service 메서드마다 `@Transactional`을 붙이면 안전한가?
- commit 뒤 알림 발송이 실패하면 어떻게 처리하나?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 전송 기록 선커밋 후 외부 호출
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 저장·응답·발급을 나눈 경계

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html)
- [Spring Framework: Transaction-bound Events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[spring-transaction]]
- [[external-api-and-transaction]]
