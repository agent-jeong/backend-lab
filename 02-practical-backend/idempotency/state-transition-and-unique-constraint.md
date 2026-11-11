---
title: 상태 전이와 Unique 제약
description: 이미 처리된 요청이 다시 반영되지 않게 DB 제약과 상태 조건으로 막는 방법
tags: [concept, idempotency]
---

# 상태 전이와 Unique 제약

재시도로 다시 온 요청이 결과를 한 번 더 만들지 않게 unique 제약과 상태 조건으로 막고, 막힌 요청에는 앞서 낸 결과를 돌려주는 방법이다. 멱등키만으로 부족한 부분을 DB에서 한 번 더 막는다.

멱등성은 애플리케이션 코드만으로 지키기 어렵다. 이미 결제가 끝난 주문을 다시 완료 처리하면 후속 이벤트와 정산도 두 번 돈다. idempotency key가 있어도 DB에 마지막 방어선이 없으면, 버그나 키를 거치지 않는 경로로 중복이 생긴다. 막는 것만으로도 끝나지 않는다. 재시도한 클라이언트에게 오류를 돌려주면, 클라이언트는 처음 요청이 실패한 줄 알고 또 보낸다.

> [!tip] 함께 읽기
> - [[unique-constraint-and-state-transition]]: unique 제약과 조건부 update를 만드는 법(코드, 제약을 걸 곳, soft delete와 NULL)은 이 글에 있다. 여기서는 막힌 요청에 무엇을 돌려줄지만 다룬다.

## 다시 온 요청을 처리하는 흐름

1. 겹치면 안 되는 업무 키에 unique 제약을 걸고, 상태 변경에는 현재 상태 조건을 건다.
2. insert가 unique 위반으로 막히거나 update가 바꾼 행이 0이면, 현재 상태를 다시 읽어 왜 막혔는지 본다.
3. 이미 목표 상태라면 같은 요청이 다시 온 것이니, 앞서 낸 결과를 그대로 돌려준다.
4. 다른 상태라면 순서가 어긋난 요청이니 업무 오류로 돌려준다.
5. 기존 결과를 돌려줬다는 사실을 로그로 남긴다.

```java
@Transactional
public PaymentResponse completePayment(Long orderId) {
    int updated = orderRepository.markPaid(orderId);
    Order order = orderRepository.findById(orderId).orElseThrow();
    if (updated == 1 || order.isPaid()) {
        return PaymentResponse.from(order);   // 처음 요청이든 재시도든 같은 결과
    }
    throw new InvalidOrderStateException(orderId, order.getStatus());
}
```

`markPaid`는 [[unique-constraint-and-state-transition]]에 있는 조건부 update와 같다. JPQL bulk update는 영속성 컨텍스트를 거치지 않아서, `clearAutomatically = true`가 없으면 이미 들고 있던 `Order`를 `findById`가 옛 상태 그대로 돌려준다. 바뀐 행이 0이라고 바로 예외를 던지면, 처음 요청이 성공했는데도 재시도한 클라이언트는 실패 응답을 받는다. 그래서 이미 `PAID`면 그때 낸 결과를 돌려주고, `CANCELED`처럼 다른 상태일 때만 오류로 돌려준다.

## 막힌 이유별 응답

| 막힌 이유 | 현재 상태 | 응답 |
|---|---|---|
| 조건부 update 0행 | 이미 목표 상태(`PAID`) | 앞서 낸 결과를 그대로 반환 |
| 조건부 update 0행 | 다른 상태(`CANCELED`) | 업무 오류(409 Conflict) |
| unique 위반 | 같은 요청이 만든 행이 있음 | 그 행으로 결과를 만들어 반환 |
| unique 위반 | 다른 요청이 같은 업무 키를 씀 | 업무 오류(409 Conflict) |
| 앞선 요청이 처리 중 | 아직 목표 상태가 아님 | 처리 중 응답 또는 잠시 뒤 조회 유도 |

unique 위반 뒤 같은 요청인지는 그 행에 저장해 둔 요청 key나 payload hash로 가른다. 앞서 낸 결과를 다시 만들려면 승인 번호처럼 응답에 들어간 값을 행에 남겨 둬야 한다. 외부 시스템에 이미 나간 요청까지 막아 주지는 못한다.

## 자주 깨지는 곳

- 바뀐 행 수 0을 바로 예외로 바꾸면, 처음 요청은 성공했는데 재시도한 클라이언트는 실패 응답을 받고 또 보낸다.
- 이미 처리된 요청과 순서가 어긋난 요청을 같은 오류로 돌려주면, 클라이언트가 다시 시도해야 할지 판단하지 못한다.
- 제약 위반을 500 장애로만 처리하면, 예상할 수 있는 재시도가 장애처럼 보인다.
- 응답에 들어간 값을 저장하지 않으면, 재시도에 처음과 같은 응답을 돌려줄 수 없다.
- idempotency key만 믿고 업무 테이블의 unique 제약을 빼면, 키를 거치지 않는 경로에서 중복이 생긴다.

## 운영에서 볼 것

- 이미 완료된 상태에서 같은 상태 전이 요청을 다시 보내, 아무것도 안 바뀌고 처음과 같은 응답이 돌아오는지 테스트한다.
- 같은 업무 키로 동시에 insert해서 행은 하나만 생기고 나머지 요청도 같은 결과를 받는지 테스트한다.
- 제약 이름, 업무 키, 바뀐 행 수, 현재 상태, 기존 결과를 돌려줬는지를 로그로 남긴다.
- 기존 결과를 돌려준 횟수와 상태 전이 실패 수를 나눠 본다.

## 한 번에 설명하기

> 멱등성은 애플리케이션 코드만으로는 지키기 어렵습니다. 저는 업무 키에 unique 제약을 걸고, 상태를 바꿀 때는 현재 상태를 조건에 넣어서 이미 처리된 요청이 다시 반영되지 않게 합니다.
>
> 막혔을 때는 바로 오류를 내지 않고 현재 상태를 다시 읽습니다. 이미 목표 상태면 재시도로 보고 앞서 낸 결과를 돌려주고, 다른 상태일 때만 업무 오류로 돌려줍니다.
>
> 그리고 idempotency key와 함께 써서, 둘 중 하나가 뚫려도 다른 쪽에서 막히게 합니다.

## 꼬리 질문

- 조건부 update가 0행을 바꿨을 때 바로 예외를 던지면 무엇이 문제인가?
- 이미 처리된 요청과 순서가 어긋난 요청은 어떻게 나눠 응답하나?
- idempotency key가 있는데도 업무 테이블에 unique가 필요한 경우는?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 상태 전이로 한 번만 처리
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: UNIQUE로 한 번만 지급

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[02-practical-backend/concurrency/unique-constraint-and-state-transition|unique-constraint-and-state-transition]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
