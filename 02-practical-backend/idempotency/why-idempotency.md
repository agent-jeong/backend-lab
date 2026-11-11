---
title: 멱등성이 필요한 이유
description: 같은 요청이 여러 번 처리돼도 결과가 한 번 처리한 것과 같아야 하는 이유
tags: [concept, idempotency]
---

# 멱등성이 필요한 이유

멱등성은 같은 요청을 한 번 처리하든 여러 번 처리하든 최종 결과가 같게 만드는 성질이다.

"요청은 한 번만 온다"는 가정은 운영에서 금방 깨진다. 사용자는 버튼을 여러 번 누르고, timeout이 나면 클라이언트나 서버가 다시 보내고, 메시지 브로커는 장애를 복구하면서 같은 메시지를 또 보낸다. 이 중복이 결제, 쿠폰, 포인트, 재고 차감에 그대로 반영되면 돈이 틀어진다.

## 동작

1. 요청을 구분할 기준을 정한다.
2. 이미 처리한 요청인지 확인한다.
3. 처음 보는 요청이면 처리하고 결과를 저장한다.
4. 이미 처리한 요청이면 저장된 결과를 돌려주거나, 아무것도 하지 않고(no-op) 끝낸다.
5. 실패와 timeout은 성공, 실패, 결과 모름으로 나눠서 복구한다.

```java
public PaymentResponse approve(PaymentRequest request) {
    return idempotencyService.execute(
        request.idempotencyKey(),
        () -> paymentService.approve(request)
    );
}
```

같은 `idempotencyKey`로 들어온 요청은 결제 승인 로직을 다시 돌리지 않고, 저장해 둔 결과로 응답한다.

## 어디에 필요한가

| 상황 | 선택 | 이유 |
|---|---|---|
| 조회 API | 별도 멱등 설계가 거의 필요 없음 | 같은 조회는 상태를 바꾸지 않는다 |
| 생성/결제/차감 API | 멱등성 필수 | 중복 처리되면 업무 결과가 달라진다 |
| 외부 API 재시도 | 멱등키 사용 | timeout 후 중복 부작용을 막아야 한다 |
| 메시지 소비 | 처리 이력 저장 | at-least-once 전달에서는 중복 소비가 가능하다 |
| 단순 상태 변경 | 조건부 update | 이미 처리된 상태를 다시 처리하지 않는다 |

멱등하게 만들어 두면 재시도와 중복 클릭에 안전해지고 장애 복구가 단순해진다. 대신 요청을 무엇으로 구분할지, 어디에 저장할지, 얼마나 보관할지와 그 저장 비용을 정해야 한다. 이미 일어난 부작용을 알아서 되돌려 주지도 않는다.

## 락과 멱등성은 다르다

| 구분 | lock | 멱등성 |
|---|---|---|
| 막는 것 | 같은 순간에 겹친 실행 | 이미 처리된 요청의 재실행 |
| 기준 | 지금 누가 자원을 쥐고 있는가 | 이 요청을 전에 처리했는가 |
| 시간차 재시도 | 막지 못한다. 첫 요청이 끝나 락이 풀린 뒤 온 재시도는 그대로 실행된다 | 저장된 결과를 반환하거나 no-op으로 끝낸다 |
| 필요한 저장소 | 락 저장소(DB row, Redis 등) | 처리 이력, idempotency key, unique 제약 |

예를 들어 결제 승인 요청이 timeout으로 끝나고, 클라이언트가 5초 뒤 다시 보낸다고 하자. 첫 요청은 이미 끝나서 락도 풀렸으니, 락은 두 번째 승인을 막지 못한다. 같은 키로 처리한 결과가 남아 있어야 이중 결제를 막는다. 실무에서는 둘을 같이 쓴다. 락(또는 unique insert)으로 동시에 들어온 요청을 줄 세우고, 처리 이력으로 나중에 온 재시도를 알아본다.

## 자주 깨지는 곳

- 멱등성을 HTTP 메서드의 성질로만 이해하면, POST로 만든 결제 API에서 중복을 막을 생각을 못 한다.
- timeout을 실패로 단정하고 같은 결제 요청을 새로 보내면, 첫 요청이 성공했을 때 결제가 두 번 된다.
- 프론트엔드에서 버튼을 비활성화하는 것만으로 중복을 막으려 하면, 네트워크 재전송이나 직접 호출은 그대로 들어온다.
- 락을 쓰면 멱등성이 필요 없다고 생각하면, 위 표처럼 시간을 두고 온 재시도를 막지 못한다.
- 처리 결과를 저장하지 않으면, 중복 요청에 같은 응답을 돌려줄 수 없다.

## 운영에서 볼 것

- 같은 요청을 여러 번 보내도 행 수, 금액, 재고가 변하지 않는지 테스트한다.
- idempotency key, request id, 처리 상태, 기존 응답을 돌려줬는지를 로그로 남긴다.
- 중복 요청 수, 멱등키로 기존 결과를 돌려준 횟수, 재시도 횟수를 본다.
- pending이나 결과를 모르는 상태가 오래 남아 있지 않은지 본다.

## 한 번에 설명하기

> 멱등성은 같은 요청이 여러 번 와도 한 번 처리한 것과 같은 결과가 남게 하는 성질입니다. 중복 클릭, timeout 뒤 재시도, 메시지 재전달은 운영에서 실제로 일어납니다.
>
> 락은 같은 순간에 겹친 실행만 막고, 이미 처리된 요청은 알아보지 못합니다.
>
> 그래서 저는 결제, 쿠폰, 포인트, 재고처럼 상태를 바꾸는 기능에 처리 이력과 DB 제약을 둬서, 같은 요청이 다시 와도 결과가 바뀌지 않게 합니다.

## 꼬리 질문

- 멱등성과 중복 요청 방지는 무엇이 다른가?
- timeout 뒤 재시도하면 어떤 위험이 있나?
- 락을 써도 멱등성이 필요한 이유는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 9110: Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods)
- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[duplicate-request-and-retry]]
- [[02-practical-backend/transaction/external-api-and-transaction|external-api-and-transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
