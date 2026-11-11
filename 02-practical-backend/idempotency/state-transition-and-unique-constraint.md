---
title: 상태 전이와 Unique 제약
description: 이미 처리된 요청이 다시 반영되지 않게 DB 제약과 상태 조건으로 막는 방법
tags: [concept, idempotency]
---

# 상태 전이와 Unique 제약

이미 처리된 요청이 다시 반영되지 않게, 업무 키(business key)에 unique 제약을 걸고 현재 상태를 조건으로 건 update를 쓰는 방법이다. 멱등키만으로 부족한 부분을 DB에서 한 번 더 막는다.

멱등성은 애플리케이션 코드만으로 지키기 어렵다. 먼저 조회하고 insert하면 동시에 들어온 요청이 같은 행을 두 개 만든다. 이미 결제가 끝난 주문을 다시 완료 처리하면 후속 이벤트와 정산도 두 번 돈다. idempotency key가 있어도 DB에 마지막 방어선이 없으면, 버그나 키를 거치지 않는 경로로 중복이 생긴다.

> [!tip] 함께 읽기
> - [[unique-constraint-and-state-transition]]: 같은 도구를 동시성 관점(동시 요청 경합)에서 본 글

## 동작

1. 겹치면 안 되는 업무 키를 정한다.
2. unique constraint를 건다.
3. 상태를 바꿀 때는 현재 상태를 조건에 넣은 update를 쓴다.
4. 바뀐 행 수가 0이면 이미 처리됐거나 상태가 맞지 않는 것으로 본다.
5. 제약 위반과 상태 전이 실패는 업무 응답으로 바꿔 돌려준다.

```java
@Modifying
@Query("""
    update Order o
       set o.status = 'PAID'
     where o.id = :orderId
       and o.status = 'PAYMENT_PENDING'
""")
int markPaid(Long orderId);

public void completePayment(Long orderId) {
    int updated = orderRepository.markPaid(orderId);
    if (updated == 0) {
        throw new AlreadyProcessedOrInvalidStateException();
    }
}
```

현재 상태 조건이 있으니 이미 결제가 끝난 주문은 다시 완료 처리되지 않는다. 재시도로 들어온 요청은 아무것도 바꾸지 않고(no-op) 끝난다.

## 무엇을 제약으로 거나

| 상황 | 선택 | 이유 |
|---|---|---|
| 사용자별 쿠폰 1회 발급 | unique(user_id, coupon_id) | 중복 row 생성을 DB가 막는다 |
| 주문 결제 완료 | where status = PAYMENT_PENDING | 이미 완료된 주문의 재처리를 막는다 |
| 재고 차감 | where stock >= quantity | 음수 재고를 막는다 |
| 멱등 요청 저장 | unique(idempotency_key) | 같은 요청 처리를 하나로 수렴시킨다 |
| soft delete 포함 | partial unique 또는 active 조건 | 삭제 row와 활성 row 기준을 분리한다 |

DB 제약은 서버가 여러 대여도 똑같이 동작한다. 대신 업무마다 무엇을 업무 키로 삼을지 정해야 하고, 상태 모델이 복잡하면 설계에 손이 많이 간다. 외부 시스템에 이미 나간 요청까지 막아 주지는 못한다.

## 자주 깨지는 곳

- unique 없이 애플리케이션 코드로만 중복을 막으면, 동시에 들어온 요청이 그 검사를 같이 통과한다.
- 상태를 바꾸는 update에 현재 상태 조건을 넣지 않으면, 재시도가 같은 상태 변경을 여러 번 실행한다.
- 제약 위반을 500 장애로만 처리하면, 예상할 수 있는 중복 요청이 장애처럼 보인다. 업무 응답으로 바꾼다.
- soft delete와 nullable 컬럼을 잊으면, unique가 생각과 다르게 동작한다.
- idempotency key만 믿고 업무 테이블의 unique 제약을 빼면, 키를 거치지 않는 경로에서 중복이 생긴다.

## 운영에서 볼 것

- 같은 업무 키로 동시에 insert해서 하나만 성공하는지 테스트한다.
- 이미 완료된 상태에서 같은 상태 전이 요청을 다시 보내, 아무것도 안 바뀌거나 기존 결과가 돌아오는지 테스트한다.
- 제약 이름, 업무 키, 바뀐 행 수, 현재 상태를 로그로 남긴다.
- 중복 키 위반 수와 상태 전이 실패 수를 본다.

## 한 번에 설명하기

> 멱등성은 애플리케이션 코드만으로는 지키기 어렵습니다. 저는 겹치면 안 되는 데이터에 업무 키로 unique 제약을 걸고, 상태를 바꿀 때는 현재 상태를 조건에 넣어서 이미 처리된 요청이 다시 반영되지 않게 합니다.
>
> 제약 위반이나 바뀐 행 수 0은 장애가 아니라 업무 응답으로 돌려줍니다.
>
> 그리고 idempotency key와 함께 써서, 둘 중 하나가 뚫려도 다른 쪽에서 막히게 합니다.

## 꼬리 질문

- 멱등성을 설계할 때 unique constraint가 중요한 이유는?
- 상태를 바꾸는 update에 현재 상태 조건을 넣는 이유는?
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
