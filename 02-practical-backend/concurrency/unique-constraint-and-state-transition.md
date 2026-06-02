---
title: Unique 제약과 상태 전이
description: 락 없이도 동시성 문제를 줄이는 DB 제약과 상태 변경 설계
---

# Unique 제약과 상태 전이

## 한 줄 정의

Unique 제약과 상태 전이는 중복 생성과 잘못된 재처리를 DB 제약 조건과 명시적 상태 변경 조건으로 막는 동시성 제어 방법이다.

## 실무에서 왜 문제 되는가

- 중복 가입, 중복 쿠폰 발급, 중복 결제 요청은 lock 없이도 DB 제약으로 막아야 하는 경우가 많다.
- 이미 완료된 주문을 다시 결제하거나 이미 취소된 주문을 배송 처리하면 상태가 꼬인다.
- 애플리케이션에서 먼저 조회하고 없으면 insert하는 방식은 동시에 들어오면 중복을 만들 수 있다.
- 상태 전이 조건이 없으면 재시도와 중복 요청이 같은 결과를 여러 번 반영한다.

## 동작 원리

1. 중복되면 안 되는 business key를 정한다.
2. DB에 unique constraint를 둔다.
3. 상태 변경은 현재 상태 조건을 포함한 update로 수행한다.
4. 영향받은 row 수가 0이면 이미 처리됐거나 상태가 맞지 않는 것으로 판단한다.
5. 애플리케이션은 DB 제약 위반과 조건부 update 실패를 업무 응답으로 변환한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 사용자별 쿠폰 1회 발급 | unique(user_id, coupon_id) | 중복 생성은 DB가 막는 것이 가장 강하다 |
| 결제 요청 중복 방지 | idempotency key unique | 재시도와 중복 클릭을 함께 방어한다 |
| 주문 상태 변경 | where status = 현재 상태 | 잘못된 순서의 상태 변경을 막는다 |
| 재고 차감 | where stock >= quantity | 음수 재고를 방지한다 |
| soft delete가 있는 중복 방지 | active 조건 포함 또는 partial unique index | 삭제된 row와 활성 row의 중복 기준이 달라질 수 있다 |
| 복잡한 다중 자원 검증 | 락 또는 트랜잭션과 조합 | 제약 조건만으로 표현하기 어려울 수 있다 |

## 자주 나는 실수

- 중복 조회 후 insert를 하면 안전하다고 생각한다.
- unique 제약 없이 애플리케이션 코드로만 중복을 막는다.
- surrogate key인 id만 보고 business key의 중복 기준을 놓친다.
- nullable column이나 soft delete 때문에 unique 제약이 의도와 다르게 동작한다.
- 상태 변경 update에 현재 상태 조건을 넣지 않는다.
- DB 제약 위반을 시스템 장애처럼만 처리하고 업무 응답으로 변환하지 않는다.
- 상태 전이 실패와 서버 오류를 구분하지 않는다.

## 확인 방법

- 테스트: 같은 business key로 동시에 insert 요청을 보낸다.
- DB: unique index와 조건부 update의 영향을 확인한다.
- 로그: constraint violation, affected row count, 기존 상태를 남긴다.
- 운영 지표: 중복 요청 수, 상태 전이 실패 수, 멱등 응답 수를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 락 없이 중복 생성의 최종 방어선을 만든다 | 예외 처리와 사용자 응답 설계가 필요하다 |
| 상태 전이 규칙을 DB update 조건으로 표현할 수 있다 | 복잡한 업무 흐름은 상태 모델 설계가 필요하다 |
| 다중 서버 환경에서도 일관되게 동작한다 | 모든 동시성 문제를 대체하지는 못한다 |

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

@Transactional
public void completePayment(Long orderId) {
    int updated = orderRepository.markPaid(orderId);
    if (updated != 1) {
        throw new InvalidOrderStateException();
    }
}
```

현재 상태가 `PAYMENT_PENDING`일 때만 `PAID`로 변경한다. 이미 취소됐거나 결제 완료된 주문이라면 update count가 0이므로 중복 처리나 잘못된 순서의 처리를 막을 수 있다. unique 제약은 `id`가 아니라 `user_id`, `coupon_id`, `idempotency_key`처럼 업무적으로 중복되면 안 되는 business key를 기준으로 잡아야 한다.

## 핵심 요약

동시성 문제는 항상 lock으로만 풀 필요가 없다.

중복 생성은 unique 제약이 가장 강한 최종 방어선이다.

unique 제약은 business key, nullable column, soft delete 정책까지 고려해 설계해야 한다.

상태 변경은 현재 상태 조건을 포함한 update로 잘못된 순서를 막을 수 있다.

DB 제약 위반과 update 실패는 운영 장애가 아니라 예상 가능한 업무 상황으로 처리해야 한다.

락은 필요한 곳에 쓰되, 제약 조건과 상태 전이로 먼저 단순하게 막을 수 있는지 검토한다.

## 꼬리 질문

- 중복 생성 방지에 unique key가 중요한 이유는 무엇인가?
- 상태 전이 update에서 현재 상태 조건을 넣는 이유는 무엇인가?
- constraint violation은 항상 서버 오류로 처리해야 하는가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/transaction|transaction]]
