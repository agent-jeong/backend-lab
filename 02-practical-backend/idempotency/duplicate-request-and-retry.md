---
title: 중복 요청과 재시도
description: timeout과 retry가 중복 처리로 이어지는 실무 흐름
tags: [concept, idempotency]
---

# 중복 요청과 재시도

같은 의도의 작업이 서버에 여러 번 도착하는 상황이다. 멱등성이 없으면 같은 부작용이 여러 번 반영된다.

클라이언트는 timeout 뒤 같은 요청을 다시 보내고, 서버 내부 retry는 외부 API 호출을 중복 실행하고, 사용자는 결제 버튼을 여러 번 누른다. 응답 전에 장애가 나면 요청이 성공했는지 실패했는지 모르는 상태가 생긴다. 재시도 정책만 있고 멱등 설계가 없으면 장애 복구가 곧 중복 처리가 된다.

## 동작

1. 클라이언트가 요청을 보낸다.
2. 서버나 외부 시스템이 요청을 처리한다.
3. 응답이 돌아가기 전에 timeout, 네트워크 단절, 프로세스 장애가 날 수 있다.
4. 호출자는 실패처럼 보이는 상황에서 같은 작업을 재시도한다.
5. 서버는 같은 의도의 요청인지 판단해 기존 결과 반환, no-op, 재처리 중 하나를 고른다.

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

timeout 뒤에는 같은 요청을 새 작업으로 만들지 말고, 기존 요청의 상태를 보고 결과를 확인하거나 복구한다. 실제 구현에서는 `requestKey`에 unique 제약을 둬서 동시에 들어온 같은 요청이 중복 생성되지 않게 한다.

## 상황별 대응

| 상황 | 선택 | 이유 |
|---|---|---|
| 응답 timeout | 상태 조회 후 재시도 | timeout은 실패가 아니라 결과 불명일 수 있다 |
| 외부 API 호출 retry | 같은 idempotency key 사용 | 외부 부작용 중복을 막는다 |
| 사용자 중복 클릭 | 서버 멱등성 우선 | UI 방어는 우회될 수 있다 |
| 일시적 5xx | 제한된 retry | 무한 재시도는 부하를 키운다 |
| 처리 중 상태 존재 | pending 응답 또는 조회 유도 | 같은 작업이 동시에 진행 중일 수 있다 |

retry는 일시 장애를 흡수하지만 멱등성 없이는 중복 처리 위험이 있다. 상태 조회 후 재시도는 결과 불명 상태를 줄이지만 외부 시스템에 조회 API가 있어야 할 수 있다. pending 상태를 두면 중간 상태를 운영에서 추적할 수 있지만 만료와 복구 정책이 따라와야 한다.

## 자주 깨지는 곳

- **timeout을 항상 실패로 본다.** 새 요청을 만들어 이중 처리가 된다.
- **retry마다 새 idempotency key를 발급한다.** 서버는 재시도를 새 요청으로 본다.
- **외부 API retry에 backoff와 최대 횟수가 없다.** 장애 때 retry storm이 부하를 키운다. timeout, backoff, 최대 횟수, circuit breaker 같은 부하 제어를 같이 둔다.
- **pending 상태를 정의하지 않는다.** 중간 장애 뒤 어디까지 처리됐는지 알 수 없어 복구가 어렵다.
- **중복 요청을 프론트엔드에서만 막는다.**

## 운영에서 볼 것

- 응답 직전 장애, timeout, 재시도를 시뮬레이션하는 테스트를 둔다.
- original request id, retry count, idempotency key, 처리 상태를 로그로 남긴다.
- timeout 후 성공률, retry storm, duplicate request count를 본다.
- 같은 업무 key로 짧은 시간에 반복 요청이 들어오는지 확인한다.

## 면접에서 말하기

> timeout은 실패가 아니라 성공, 실패, 결과 불명 중 하나입니다. 그래서 저는 같은 의도의 재시도에는 같은 idempotency key나 request key를 쓰게 하고, 서버는 그 key로 기존 결과를 돌려주거나 pending 상태를 조회해 복구합니다. retry 자체에는 backoff, 최대 횟수, circuit breaker를 붙여 장애 때 부하를 키우지 않게 합니다.

## 꼬리 질문

- timeout 이후 바로 새 결제 요청을 보내면 어떤 문제가 생기는가?
- retry와 idempotency key는 어떤 관계인가?
- pending 상태는 왜 필요한가?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 결과를 모르면 다시 보내지 않기
- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: 같은 웹훅 재전송

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[01-core/network/retry|retry]]
- [[01-core/network/timeout|timeout]]
