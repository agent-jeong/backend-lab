---
title: Idempotency Key
description: 같은 의도의 요청을 식별해 중복 처리를 막는 키 설계
---

# Idempotency Key

## 한 줄 정의

Idempotency key는 같은 의도의 요청을 식별하기 위해 클라이언트나 서버가 생성하는 고유 키이며, 같은 키의 요청은 같은 결과로 처리되어야 한다.

## 실무에서 왜 문제 되는가

- 중복 요청을 구분할 기준이 없으면 서버는 새 요청인지 재시도인지 알 수 없다.
- 같은 key에 다른 payload가 들어오면 잘못된 결과 재사용이 생길 수 있다.
- key 저장 기간이 너무 짧으면 늦은 재시도를 막지 못한다.
- key 저장을 업무 처리와 분리하면 처리 결과는 생겼는데 key 기록이 없는 불일치가 생길 수 있다.

## 동작 원리

1. 요청마다 idempotency key를 받거나 생성한다.
2. key와 요청 payload hash를 저장한다.
3. 처음 보는 key이면 업무 처리를 실행하고 결과를 저장한다.
4. 같은 key가 다시 오면 payload hash를 비교한다.
5. 같은 payload이면 저장된 결과를 반환하고, 다른 payload이면 충돌로 처리한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 클라이언트 재시도 | 클라이언트 생성 key | 같은 의도의 재시도에 같은 key를 재사용한다 |
| 서버 내부 작업 | 서버 생성 business key | 주문 id, 결제 요청 id처럼 업무 기준을 사용한다 |
| 같은 key 다른 payload | 409 Conflict | key 재사용 오류를 막는다 |
| 처리 결과 저장 | key, status, response 함께 저장 | 중복 요청에 같은 응답을 반환한다 |
| 보관 기간 | 업무 재시도 가능 시간 기준 | 너무 짧으면 늦은 재시도를 막지 못한다 |

## 자주 나는 실수

- retry할 때마다 새로운 key를 만든다.
- key만 비교하고 payload가 달라진 요청을 허용한다.
- key 저장과 업무 처리를 별도 트랜잭션으로 분리한다.
- key를 영구 보관해 저장소가 계속 커진다.
- 실패 응답을 어떻게 저장할지 정하지 않는다.

## 확인 방법

- 테스트: 같은 key와 같은 payload를 반복 요청하면 같은 결과가 반환되는지 확인한다.
- 테스트: 같은 key와 다른 payload는 충돌 응답으로 처리되는지 확인한다.
- 로그: key, payload hash, status, response reuse 여부를 남긴다.
- 메트릭: key hit count, conflict count, expired key retry count를 본다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 중복 요청을 명확히 식별할 수 있다 | key 저장소와 TTL 정책이 필요하다 |
| 같은 응답을 재사용할 수 있다 | payload hash와 상태 관리가 필요하다 |
| 외부 API 재시도에 안전하다 | 외부 시스템도 같은 key를 지원해야 효과가 커진다 |

## 짧은 예제

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

`tryStart`는 `idempotency_key` unique 제약을 이용해 처음 요청만 시작 상태로 저장하는 동작을 의미한다. 같은 key가 다시 들어오면 payload hash를 확인한 뒤, 이미 완료된 요청이면 저장된 응답을 반환한다. 동시에 들어온 같은 key 요청은 같은 row를 기준으로 대기하거나 처리 중 응답을 반환하도록 정책을 정한다.

## 핵심 요약

Idempotency key는 같은 의도의 요청을 식별하는 기준이다.

같은 key와 같은 payload는 같은 결과를 반환해야 한다.

같은 key인데 payload가 다르면 key 재사용 오류로 보고 충돌 응답을 반환하는 것이 안전하다.

key 저장, 업무 처리, 결과 저장은 가능한 한 같은 트랜잭션 경계에서 다뤄야 한다.

동시 요청을 고려해 key 생성은 unique 제약과 row lock 또는 조건부 insert를 기준으로 설계한다.

보관 기간은 클라이언트 재시도 가능 시간, 외부 시스템 정산 주기, 운영 복구 시간을 기준으로 정한다.

## 꼬리 질문

- idempotency key는 누가 생성해야 하는가?
- 같은 key에 다른 payload가 들어오면 어떻게 처리해야 하는가?
- idempotency key를 얼마나 오래 보관해야 하는가?

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[duplicate-request-and-retry]]
- [[state-transition-and-unique-constraint]]
- [[02-practical-backend/transaction/transaction-boundary|transaction-boundary]]
