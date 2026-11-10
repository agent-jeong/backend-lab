---
title: 상태 전이와 Unique 제약
description: 멱등성을 DB 제약과 상태 변경 조건으로 보강하는 방법
tags: [concept, idempotency]
---

# 상태 전이와 Unique 제약

이미 처리된 요청이 다시 반영되지 않도록, DB의 business key unique 제약과 현재 상태를 조건으로 건 update로 멱등성을 보강하는 방법이다.

멱등성은 애플리케이션 코드만으로 지키기 어렵다. 먼저 조회하고 insert하면 동시에 들어온 요청이 중복 row를 만든다. 이미 결제가 끝난 주문을 다시 완료 처리하면 후속 이벤트와 정산이 중복된다. idempotency key가 있어도 DB에 최종 방어선이 없으면 버그나 우회 경로로 중복이 생긴다.

> [!tip] 함께 읽기
> - [[unique-constraint-and-state-transition]]: 같은 도구를 동시성 관점(동시 요청 경합)에서 본 글

## 동작

1. 중복되면 안 되는 business key를 정한다.
2. unique constraint를 추가한다.
3. 상태 변경은 현재 상태 조건을 포함한 update로 한다.
4. update count가 0이면 이미 처리됐거나 상태가 맞지 않는 것으로 본다.
5. constraint violation과 상태 전이 실패를 업무 응답으로 바꾼다.

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

현재 상태 조건이 있으면 이미 결제가 끝난 주문이 다시 완료 처리되지 않는다. 재시도 요청은 자연스럽게 no-op이 된다.

## 무엇을 제약으로 거나

| 상황 | 선택 | 이유 |
|---|---|---|
| 사용자별 쿠폰 1회 발급 | unique(user_id, coupon_id) | 중복 row 생성을 DB가 막는다 |
| 주문 결제 완료 | where status = PAYMENT_PENDING | 이미 완료된 주문의 재처리를 막는다 |
| 재고 차감 | where stock >= quantity | 음수 재고를 막는다 |
| 멱등 요청 저장 | unique(idempotency_key) | 같은 요청 처리를 하나로 수렴시킨다 |
| soft delete 포함 | partial unique 또는 active 조건 | 삭제 row와 활성 row 기준을 분리한다 |

DB 제약은 다중 서버에서도 똑같이 동작한다. 대신 업무별로 business key를 설계해야 하고, 복잡한 상태 모델은 설계 비용이 들며, 외부 부작용까지 막지는 못한다.

## 자주 깨지는 곳

- **unique 없이 애플리케이션 코드로만 중복을 막는다.**
- **상태 변경 update에 현재 상태 조건을 넣지 않는다.** 재시도가 같은 상태 변경을 여러 번 실행한다.
- **constraint violation을 500 장애로만 처리한다.** 예상 가능한 업무 상황이니 업무 응답으로 바꾼다.
- **soft delete와 nullable column을 잊는다.** unique가 의도와 다르게 동작한다.
- **idempotency key만 믿고 업무 테이블의 unique 제약을 생략한다.**

## 운영에서 볼 것

- 같은 business key로 동시에 insert해 하나만 성공하는지 테스트한다.
- 완료 상태에서 같은 상태 전이 요청을 다시 보내 no-op이나 기존 결과 반환이 되는지 테스트한다.
- constraint name, business key, affected row count, current status를 로그로 남긴다.
- duplicate key violation, state transition failure count를 본다.

## 한 번에 설명하기

> 멱등성은 애플리케이션 코드만으로는 지키기 어렵습니다. 저는 중복되면 안 되는 데이터에 business key 기반 unique 제약을 걸고, 상태 변경은 현재 상태를 조건으로 넣어 이미 처리된 요청이 다시 반영되지 않게 합니다. constraint violation과 update count 0은 장애가 아니라 업무 응답으로 바꾸고, idempotency key와 함께 써서 어느 한쪽이 뚫려도 막히게 합니다.

## 꼬리 질문

- 멱등성 설계에서 unique constraint가 중요한 이유는 무엇인가?
- 상태 전이 update에 현재 상태 조건을 넣는 이유는 무엇인가?
- idempotency key가 있는데도 업무 테이블 unique가 필요한 경우는 언제인가?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 상태 전이로 한 번만 처리
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: UNIQUE로 한 번만 지급

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[02-practical-backend/concurrency/unique-constraint-and-state-transition|unique-constraint-and-state-transition]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
