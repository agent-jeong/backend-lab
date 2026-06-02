---
title: 상태 전이와 Unique 제약
description: 멱등성을 DB 제약과 상태 변경 조건으로 보강하는 방법
---

# 상태 전이와 Unique 제약

## 한 줄 정의

상태 전이와 unique 제약은 이미 처리된 요청이 다시 반영되지 않도록 DB의 business key와 조건부 update로 멱등성을 보강하는 방법이다.

## 실무에서 왜 문제 되는가

- 애플리케이션에서 먼저 조회하고 insert하면 동시에 들어온 요청이 중복 row를 만들 수 있다.
- 이미 결제 완료된 주문을 다시 완료 처리하면 후속 이벤트와 정산이 중복될 수 있다.
- idempotency key가 있어도 DB 최종 방어선이 없으면 버그나 우회 경로에서 중복이 생긴다.
- 상태 전이 조건이 없으면 재시도 요청이 같은 상태 변경을 여러 번 실행한다.

## 동작 원리

1. 중복되면 안 되는 business key를 정한다.
2. unique constraint를 추가한다.
3. 상태 변경은 현재 상태 조건을 포함한 update로 수행한다.
4. update count가 0이면 이미 처리됐거나 상태가 맞지 않는 것으로 판단한다.
5. constraint violation과 상태 전이 실패를 업무 응답으로 변환한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 사용자별 쿠폰 1회 발급 | unique(user_id, coupon_id) | 중복 row 생성을 DB가 막는다 |
| 주문 결제 완료 | where status = PAYMENT_PENDING | 이미 완료된 주문의 재처리를 막는다 |
| 재고 차감 | where stock >= quantity | 음수 재고를 막는다 |
| 멱등 요청 저장 | unique(idempotency_key) | 같은 요청 처리를 하나로 수렴시킨다 |
| soft delete 포함 | partial unique 또는 active 조건 | 삭제 row와 활성 row 기준을 분리한다 |

## 자주 나는 실수

- unique 없이 애플리케이션 코드로만 중복을 막는다.
- 상태 변경 update에 현재 상태 조건을 넣지 않는다.
- constraint violation을 500 장애로만 처리한다.
- soft delete와 nullable column 때문에 unique가 의도와 다르게 동작한다.
- idempotency key만 믿고 업무 테이블의 unique 제약을 생략한다.

## 확인 방법

- 테스트: 같은 business key로 동시에 insert해 하나만 성공하는지 확인한다.
- 테스트: 완료 상태에서 같은 상태 전이 요청을 다시 보내 no-op 또는 기존 결과 반환이 되는지 확인한다.
- 로그: constraint name, business key, affected row count, current status를 남긴다.
- 메트릭: duplicate key violation, state transition failure count를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| DB가 중복 생성의 최종 방어선이 된다 | 업무별 business key 설계가 필요하다 |
| 재시도 요청을 no-op으로 처리하기 쉽다 | 복잡한 상태 모델은 설계 비용이 든다 |
| 다중 서버에서도 일관되게 동작한다 | 모든 외부 부작용을 막지는 못한다 |

## 짧은 예제

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

현재 상태 조건을 넣으면 이미 결제 완료된 주문이 다시 완료 처리되는 것을 막을 수 있다.

## 핵심 요약

멱등성은 애플리케이션 코드만으로 보장하기 어렵다.

중복되면 안 되는 데이터는 business key 기반 unique 제약으로 막아야 한다.

상태 변경은 현재 상태 조건을 포함해 이미 처리된 요청을 다시 반영하지 않게 만든다.

constraint violation과 update count 0은 예상 가능한 업무 상황으로 변환해야 한다.

idempotency key, unique 제약, 상태 전이는 함께 사용할 때 더 안정적이다.

## 꼬리 질문

- 멱등성 설계에서 unique constraint가 중요한 이유는 무엇인가?
- 상태 전이 update에 현재 상태 조건을 넣는 이유는 무엇인가?
- idempotency key가 있는데도 업무 테이블 unique가 필요한 경우는 언제인가?

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[02-practical-backend/concurrency/unique-constraint-and-state-transition|unique-constraint-and-state-transition]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
