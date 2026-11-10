---
title: 멱등키
description: 같은 의도의 요청을 식별해 중복 처리를 막는 키 설계
---

# 멱등키

Idempotency key는 같은 의도의 요청을 알아보기 위해 클라이언트나 서버가 만드는 고유 키다. 같은 key의 요청은 같은 결과로 처리한다.

이 기준이 없으면 서버는 새 요청인지 재시도인지 구분하지 못한다. key만 있다고 끝나지도 않는다. 같은 key에 다른 payload가 오면 엉뚱한 결과를 재사용하고, 보관 기간이 짧으면 늦은 재시도를 놓치고, key 저장을 업무 처리와 분리하면 결과는 있는데 key 기록은 없는 불일치가 생긴다.

## 동작

1. 요청마다 idempotency key를 받거나 만든다.
2. key와 요청 payload hash를 저장한다.
3. 처음 보는 key면 업무를 처리하고 결과를 저장한다.
4. 같은 key가 다시 오면 payload hash를 비교한다.
5. payload가 같으면 저장된 결과를 반환하고, 다르면 충돌로 처리한다.

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

`tryStart`는 `idempotency_key` unique 제약을 이용해 처음 요청만 시작 상태로 저장한다. 같은 key가 다시 오면 payload hash를 확인하고, 이미 완료된 요청이면 저장된 응답을 반환한다. 동시에 들어온 같은 key 요청은 같은 row를 기준으로 기다리게 할지, 처리 중 응답을 줄지 정책을 정한다.

`tryStart`는 예외를 던지지 않는 조건부 insert(`INSERT ... ON CONFLICT DO NOTHING`, MySQL `INSERT IGNORE` 등)로 구현한다. 일반 insert 후 중복 키 예외를 같은 트랜잭션 안에서 잡으면, PostgreSQL은 트랜잭션 전체를 abort 상태로 만들고 Spring은 트랜잭션을 rollback-only로 표시할 수 있어 뒤의 조회와 commit이 실패한다.

## 설계 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 클라이언트 재시도 | 클라이언트 생성 key | 같은 의도의 재시도에 같은 key를 재사용한다 |
| 서버 내부 작업 | 서버 생성 business key | 주문 id, 결제 요청 id처럼 업무 기준을 쓴다 |
| 같은 key 다른 payload | 409 Conflict | key 재사용 오류를 막는다 |
| 처리 결과 저장 | key, status, response 함께 저장 | 중복 요청에 같은 응답을 반환한다 |
| 보관 기간 | 업무 재시도 가능 시간 기준 | 너무 짧으면 늦은 재시도를 막지 못한다 |

보관 기간은 클라이언트가 재시도할 수 있는 시간과 운영 복구에 걸리는 시간을 기준으로 정한다. 외부 API 재시도에도 쓸 수 있지만, 외부 시스템도 같은 key를 지원해야 효과가 커진다.

## 자주 깨지는 곳

- **retry할 때마다 새 key를 만든다.** key가 있으나 마나다.
- **key만 비교하고 payload를 보지 않는다.** 내용이 달라진 요청에 이전 결과를 돌려준다.
- **key 저장과 업무 처리를 별도 트랜잭션으로 나눈다.** 한쪽만 남는 불일치가 생긴다.
- **key를 영구 보관한다.** 저장소가 계속 커진다. TTL 정책을 둔다.
- **실패 응답을 어떻게 저장할지 정하지 않는다.**

## 운영에서 볼 것

- 같은 key·같은 payload를 반복 요청하면 같은 결과가 나오는지 테스트한다.
- 같은 key·다른 payload가 충돌 응답으로 처리되는지 테스트한다.
- key, payload hash, status, 응답 재사용 여부를 로그로 남긴다.
- key hit count, conflict count, 만료된 key로 들어온 재시도 수를 본다.

## 면접에서 말하기

> Idempotency key는 같은 의도의 요청을 알아보는 기준입니다. 같은 key에 같은 payload면 저장된 결과를 돌려주고, 같은 key에 다른 payload면 409로 거절합니다. 저는 key 저장과 업무 처리를 같은 트랜잭션에 두고, 동시 요청은 unique 제약 기반 조건부 insert로 하나만 통과시킵니다. 보관 기간은 클라이언트 재시도 가능 시간과 운영 복구 시간을 기준으로 정합니다.

## 꼬리 질문

- idempotency key는 누가 생성해야 하는가?
- 같은 key에 다른 payload가 들어오면 어떻게 처리해야 하는가?
- idempotency key를 얼마나 오래 보관해야 하는가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 상대가 멱등키를 받지 않을 때

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[duplicate-request-and-retry]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/transaction/transaction-boundary|transaction-boundary]]
