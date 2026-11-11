---
title: 중복 요청과 재시도
description: timeout 뒤의 재시도가 어떻게 두 번 처리로 이어지고, 어떻게 막는지
tags: [concept, idempotency]
---

# 중복 요청과 재시도

같은 일을 하려는 요청이 서버에 여러 번 도착하는 상황이다. 멱등하게 만들어 두지 않으면 같은 결과가 여러 번 반영된다.

클라이언트는 timeout이 나면 같은 요청을 다시 보내고, 서버 안의 재시도 로직은 외부 API를 한 번 더 부르고, 사용자는 결제 버튼을 여러 번 누른다. 응답이 가기 전에 장애가 나면 요청이 성공했는지 실패했는지 아무도 모른다. 재시도 정책만 있고 멱등 설계가 없으면, 장애를 복구하려고 다시 보낸 요청이 그대로 두 번째 결제가 된다.

## 동작

1. 클라이언트가 요청을 보낸다.
2. 서버나 외부 시스템이 요청을 처리한다.
3. 응답이 돌아가기 전에 timeout, 네트워크 끊김, 프로세스 장애가 날 수 있다.
4. 호출한 쪽은 실패한 것처럼 보이니 같은 작업을 다시 보낸다.
5. 서버는 같은 일을 하려는 요청인지 보고, 기존 결과를 돌려줄지, 아무것도 안 할지(no-op), 다시 처리할지 고른다.

```java
Payment payment = paymentRepository.findByRequestKey(requestKey)
    .orElseGet(() -> paymentRepository.save(Payment.pending(requestKey)));

if (payment.isCompleted()) {
    return PaymentResponse.from(payment);
}

if (payment.isPendingTooLong()) {
    paymentRecoveryService.checkExternalStatus(payment);
}
```

timeout 뒤에 온 같은 요청을 새 작업으로 만들지 않는다. 앞서 들어온 요청의 상태를 보고 결과를 확인하거나 복구한다. 실제로 만들 때는 `requestKey`에 unique 제약을 걸어서, 같은 요청이 동시에 들어와도 두 개가 생기지 않게 한다.

## 상황별 대응

| 상황 | 선택 | 이유 |
|---|---|---|
| 응답 timeout | 상태 조회 후 재시도 | timeout은 실패가 아니라 결과 불명일 수 있다 |
| 외부 API 호출 retry | 같은 idempotency key 사용 | 외부 부작용 중복을 막는다 |
| 사용자 중복 클릭 | 서버 멱등성 우선 | UI 방어는 우회될 수 있다 |
| 일시적 5xx | 제한된 retry | 무한 재시도는 부하를 키운다 |
| 처리 중 상태 존재 | pending 응답 또는 조회 유도 | 같은 작업이 동시에 진행 중일 수 있다 |

재시도는 잠깐의 장애를 넘기게 해 주지만, 멱등성이 없으면 두 번 처리될 수 있다. 상태를 먼저 조회하고 재시도하면 결과를 모르는 상태가 줄지만, 외부 시스템에 조회 API가 있어야 하는 경우가 많다. pending 상태를 두면 중간에 멈춘 건을 운영에서 찾을 수 있지만, 언제 만료시키고 어떻게 복구할지도 같이 정해야 한다.

## 자주 깨지는 곳

- timeout을 항상 실패로 보면, 새 요청을 만들어서 같은 결제가 두 번 나간다.
- 재시도할 때마다 새 idempotency key를 만들면, 서버는 재시도를 새 요청으로 본다.
- 외부 API 재시도에 backoff와 최대 횟수가 없으면, 장애 때 재시도가 한꺼번에 몰려(retry storm) 부하를 더 키운다. timeout, backoff, 최대 횟수, circuit breaker를 같이 둔다.
- pending 상태를 정해 두지 않으면, 중간에 장애가 났을 때 어디까지 처리됐는지 몰라 복구가 어렵다.
- 중복 요청을 프론트엔드에서만 막으면, 버튼을 우회한 요청이나 네트워크 재전송은 그대로 들어온다.

## 운영에서 볼 것

- 응답 직전 장애, timeout, 재시도를 흉내 내는 테스트를 둔다.
- 원래 요청 id, 재시도 횟수, idempotency key, 처리 상태를 로그로 남긴다.
- timeout 뒤 실제로 성공한 비율, 재시도 폭주, 중복 요청 수를 본다.
- 같은 업무 키로 짧은 시간에 요청이 반복해서 들어오는지 확인한다.

## 한 번에 설명하기

> timeout은 실패가 아닙니다. 실제로는 성공했을 수도, 실패했을 수도, 결과를 모를 수도 있습니다.
>
> 그래서 저는 같은 일을 다시 시도할 때는 같은 idempotency key나 request key를 쓰게 합니다. 서버는 그 key로 기존 결과를 돌려주거나, pending 상태를 조회해서 복구합니다.
>
> 재시도 자체에는 backoff, 최대 횟수, circuit breaker를 붙여서 장애 때 부하를 키우지 않게 합니다.

## 꼬리 질문

- timeout 뒤 바로 새 결제 요청을 보내면 어떤 문제가 생기나?
- 재시도와 idempotency key는 어떤 관계인가?
- pending 상태는 왜 필요한가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 결과를 모르면 다시 보내지 않기
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 같은 웹훅 재전송

## 참고

2026년 11월에 확인한 공식 문서다.

- [Amazon Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Amazon Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[01-core/network/retry|retry]]
- [[01-core/network/timeout|timeout]]
