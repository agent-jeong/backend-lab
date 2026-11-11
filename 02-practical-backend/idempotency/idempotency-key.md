---
title: 멱등키
description: 재시도인지 새 요청인지 알아보는 키를 어떻게 만들고 저장하는지
tags: [concept, idempotency]
---

# 멱등키

멱등키(idempotency key)는 같은 일을 하려는 요청을 알아보려고 클라이언트나 서버가 만드는 고유한 키다. 같은 키로 들어온 요청은 같은 결과로 처리한다.

이 키가 없으면 서버는 들어온 주문 요청이 새 주문인지, 앞선 주문의 재시도인지 구분하지 못한다. 키가 있다고 끝나는 것도 아니다. 같은 키에 내용이 다른 요청이 오면 엉뚱한 결과를 돌려주게 되고, 키를 너무 짧게 보관하면 늦게 온 재시도를 놓친다. 키 저장과 업무 처리를 따로 하면 주문은 있는데 키 기록은 없는 식으로 어긋난다.

## 동작

1. 요청마다 idempotency key를 받거나 만든다.
2. 키와 요청 내용(payload)의 hash를 저장한다.
3. 처음 보는 키면 업무를 처리하고 결과를 저장한다.
4. 같은 키가 다시 오면 payload hash를 비교한다.
5. payload가 같으면 저장된 결과를 돌려주고, 다르면 충돌로 처리한다.

```java
@Transactional
public OrderResponse createOrder(CreateOrderCommand command) {
    IdempotencyRecord record = idempotencyRepository
        .tryStart(command.idempotencyKey(), command.payloadHash())
        .orElseGet(() -> idempotencyRepository.findByKeyForUpdate(command.idempotencyKey())
            .orElseThrow());

    record.validateSamePayload(command.payloadHash());

    if (record.isCompleted()) {
        return record.toOrderResponse();
    }

    Order order = orderRepository.save(Order.create(command));
    record.complete(order.getId(), OrderResponse.from(order));
    return OrderResponse.from(order);
}
```

`tryStart`는 `idempotency_key`에 걸린 unique 제약을 이용해 처음 온 요청만 시작 상태로 저장한다. 같은 키가 다시 오면 payload hash를 확인하고, 이미 끝난 요청이면 저장해 둔 응답을 돌려준다. 같은 키로 동시에 들어온 요청은 같은 행을 두고 기다리게 할지, "처리 중"이라고 응답할지 정해 둔다.

`tryStart`는 예외를 던지지 않는 조건부 insert로 만든다. PostgreSQL은 `INSERT ... ON CONFLICT DO NOTHING`, MySQL은 `INSERT ... ON DUPLICATE KEY UPDATE id = id`를 쓴다. MySQL `INSERT IGNORE`는 중복 키 말고 값 변환 오류 같은 다른 오류도 경고로 바꿔 버리니 피한다. 일반 insert를 하고 중복 키 예외를 같은 트랜잭션 안에서 잡으면, PostgreSQL은 트랜잭션 전체를 abort 상태로 만들고 Spring은 트랜잭션을 rollback-only로 표시할 수 있다. 그러면 뒤에 오는 조회와 commit이 실패한다.

## 설계 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 클라이언트 재시도 | 클라이언트 생성 key | 같은 의도의 재시도에 같은 key를 재사용한다 |
| 서버 내부 작업 | 서버 생성 business key | 주문 id, 결제 요청 id처럼 업무 기준을 쓴다 |
| 같은 key 다른 payload | 409 Conflict | key 재사용 오류를 막는다 |
| 처리 결과 저장 | key, status, response 함께 저장 | 중복 요청에 같은 응답을 반환한다 |
| 보관 기간 | 업무 재시도 가능 시간 기준 | 너무 짧으면 늦은 재시도를 막지 못한다 |

보관 기간은 클라이언트가 재시도할 수 있는 시간과, 운영에서 복구하는 데 걸리는 시간을 보고 정한다. 외부 API를 재시도할 때도 쓸 수 있지만, 외부 시스템이 같은 키를 받아 줘야 제대로 효과가 난다.

## 자주 깨지는 곳

- 재시도할 때마다 새 키를 만들면, 키가 있으나 마나다.
- 키만 비교하고 payload를 보지 않으면, 내용이 바뀐 요청에 이전 결과를 돌려준다.
- 키 저장과 업무 처리를 다른 트랜잭션으로 나누면, 한쪽만 남는다.
- 키를 영원히 보관하면 저장소가 계속 커진다. TTL을 둔다.
- 실패한 응답을 저장할지, 저장한다면 어떻게 돌려줄지 정하지 않으면, 같은 키로 다시 온 요청을 어떻게 처리할지 애매해진다.

## 운영에서 볼 것

- 같은 키와 같은 payload로 여러 번 요청하면 같은 결과가 나오는지 테스트한다.
- 같은 키에 다른 payload가 오면 충돌 응답이 나가는지 테스트한다.
- 키, payload hash, 상태, 저장된 응답을 재사용했는지를 로그로 남긴다.
- 키 재사용 횟수, 충돌 횟수, 만료된 키로 들어온 재시도 수를 본다.

## 한 번에 설명하기

> 멱등키는 같은 일을 하려는 요청을 알아보는 기준입니다. 같은 키에 같은 내용이면 저장된 결과를 돌려주고, 같은 키에 다른 내용이면 409로 거절합니다.
>
> 저는 키 저장과 업무 처리를 같은 트랜잭션에 두고, 동시에 들어온 요청은 unique 제약을 건 조건부 insert로 하나만 통과시킵니다.
>
> 보관 기간은 클라이언트가 재시도할 수 있는 시간과 운영 복구에 걸리는 시간을 보고 정합니다.

## 꼬리 질문

- idempotency key는 누가 만들어야 하나?
- 같은 키에 다른 payload가 들어오면 어떻게 하나?
- idempotency key는 얼마나 오래 보관하나?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 상대가 멱등키를 받지 않을 때

## 참고

2026년 11월에 확인한 공식 문서다.

- [Stripe API: Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [IETF draft: The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[duplicate-request-and-retry]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/transaction/transaction-boundary|transaction-boundary]]
