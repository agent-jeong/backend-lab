---
title: Unique 제약과 상태 전이
description: 락 없이도 동시성 문제를 줄이는 DB 제약과 상태 변경 설계
tags: [concept, concurrency]
---

# Unique 제약과 상태 전이

중복 생성은 DB unique 제약으로, 잘못된 재처리는 현재 상태를 조건으로 건 update로 막는 방법이다. 락 없이도 많은 동시성 문제를 푼다.

애플리케이션에서 먼저 조회하고 없으면 insert하는 방식은 동시에 들어오면 중복을 만든다. 상태 전이 조건이 없으면 재시도와 중복 요청이 같은 결과를 여러 번 반영하고, 이미 취소된 주문이 배송되는 식으로 상태가 꼬인다. 중복 가입, 중복 쿠폰 발급, 중복 결제 요청은 DB 제약으로 막는 게 가장 강하다.

> [!tip] 함께 읽기
> - [[state-transition-and-unique-constraint]]: 같은 도구를 멱등성 관점(재시도·중복 요청)에서 본 글

## 동작

1. 중복되면 안 되는 business key를 정한다.
2. DB에 unique constraint를 둔다.
3. 상태 변경은 현재 상태 조건을 포함한 update로 한다.
4. 영향받은 row 수가 0이면 이미 처리됐거나 상태가 맞지 않는 것으로 본다.
5. DB 제약 위반과 조건부 update 실패는 업무 응답으로 바꾼다.

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

현재 상태가 `PAYMENT_PENDING`일 때만 `PAID`로 바꾼다. 이미 취소됐거나 결제가 끝난 주문이면 update count가 0이라 중복 처리나 순서가 틀린 처리를 막는다. unique 제약은 `id`가 아니라 `user_id`, `coupon_id`, `idempotency_key`처럼 업무상 중복되면 안 되는 business key로 잡는다.

## 상황별 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 사용자별 쿠폰 1회 발급 | unique(user_id, coupon_id) | 중복 생성은 DB가 막는 것이 가장 강하다 |
| 결제 요청 중복 방지 | idempotency key unique | 재시도와 중복 클릭을 함께 막는다 |
| 주문 상태 변경 | where status = 현재 상태 | 잘못된 순서의 상태 변경을 막는다 |
| 재고 차감 | where stock >= quantity | 음수 재고를 막는다 |
| soft delete가 있는 중복 방지 | active 조건 포함 또는 partial unique index | 삭제된 row와 활성 row의 중복 기준이 다르다 |
| 복잡한 다중 자원 검증 | 락 또는 트랜잭션과 조합 | 제약 조건만으로 표현하기 어렵다 |

제약과 상태 전이는 다중 서버에서도 똑같이 동작하고 락 대기가 없다. 대신 모든 동시성 문제를 대체하지는 못하고, 복잡한 업무 흐름이면 상태 모델부터 설계해야 한다.

## 자주 깨지는 곳

- **조회 후 insert면 안전하다고 생각한다.** 동시에 들어온 두 요청이 모두 "없음"을 본다.
- **unique 제약 없이 애플리케이션 코드로만 중복을 막는다.**
- **surrogate key인 id만 본다.** business key의 중복 기준을 놓친다.
- **nullable column이나 soft delete를 잊는다.** unique 제약이 의도와 다르게 동작한다.
- **상태 변경 update에 현재 상태 조건을 넣지 않는다.**
- **DB 제약 위반을 시스템 장애로만 처리한다.** 예상 가능한 업무 상황이니 업무 응답으로 바꾼다.
- **상태 전이 실패와 서버 오류를 구분하지 않는다.**

## 운영에서 볼 것

- 같은 business key로 동시에 insert 요청을 보내는 테스트를 둔다.
- unique index와 조건부 update가 실제로 적용되는지 DB에서 확인한다.
- constraint violation, affected row count, 기존 상태를 로그로 남긴다.
- 중복 요청 수, 상태 전이 실패 수, 멱등 응답 수를 본다.

## 한 번에 설명하기

> 동시성 문제를 항상 락으로 풀 필요는 없습니다. 중복 생성은 unique 제약이 가장 강한 최종 방어선이고, 상태 변경은 현재 상태를 조건으로 건 update로 잘못된 순서를 막습니다. 저는 unique 제약을 business key 기준으로 잡고 nullable column과 soft delete 정책까지 확인하며, 제약 위반과 update 실패는 장애가 아니라 업무 응답으로 처리합니다. 락은 이렇게 막을 수 없는 곳에만 씁니다.

## 꼬리 질문

- 중복 생성 방지에 unique key가 중요한 이유는 무엇인가?
- 상태 전이 update에서 현재 상태 조건을 넣는 이유는 무엇인가?
- constraint violation은 항상 서버 오류로 처리해야 하는가?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 조건부 UPDATE 상태 전이
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: UNIQUE로 막는 중복 지급

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [MySQL 8.4: INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[02-practical-backend/transaction/transaction|transaction]]
