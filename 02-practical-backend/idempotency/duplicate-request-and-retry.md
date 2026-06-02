---
title: 중복 요청과 재시도
description: timeout과 retry가 중복 처리로 이어지는 실무 흐름
---

# 중복 요청과 재시도

## 한 줄 정의

중복 요청과 재시도는 같은 의도의 작업이 여러 번 서버에 도착하는 상황이며, 멱등성이 없으면 같은 부작용이 여러 번 반영될 수 있다.

## 실무에서 왜 문제 되는가

- 클라이언트가 timeout 후 같은 요청을 다시 보낼 수 있다.
- 서버 내부 retry가 외부 API 호출을 중복 실행할 수 있다.
- 사용자가 결제 버튼이나 쿠폰 발급 버튼을 여러 번 누를 수 있다.
- 응답 전 장애가 나면 요청이 성공했는지 실패했는지 알 수 없는 상태가 생긴다.
- 재시도 정책만 있고 멱등 설계가 없으면 장애 복구가 중복 처리로 이어진다.

## 동작 원리

1. 클라이언트가 요청을 보낸다.
2. 서버 또는 외부 시스템은 요청을 처리한다.
3. 응답 전달 전에 timeout, 네트워크 단절, 프로세스 장애가 발생할 수 있다.
4. 호출자는 실패로 보이는 상황에서 같은 작업을 재시도한다.
5. 서버는 같은 의도의 요청인지 판단해 기존 결과 반환, no-op, 재처리 중 하나를 선택한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 응답 timeout | 상태 조회 후 재시도 | timeout은 실패가 아니라 결과 불명일 수 있다 |
| 외부 API 호출 retry | 같은 idempotency key 사용 | 외부 부작용 중복을 막는다 |
| 사용자 중복 클릭 | 서버 멱등성 우선 | UI 방어는 우회될 수 있다 |
| 일시적 5xx | 제한된 retry | 무한 재시도는 부하를 키운다 |
| 처리 중 상태 존재 | pending 응답 또는 조회 유도 | 같은 작업이 동시에 진행 중일 수 있다 |

## 자주 나는 실수

- timeout을 항상 실패로 보고 새 요청을 만든다.
- retry마다 새로운 idempotency key를 발급한다.
- 외부 API retry에 backoff와 최대 횟수를 두지 않는다.
- pending 상태를 정의하지 않아 중간 장애 복구가 어렵다.
- 중복 요청을 프론트엔드에서만 막는다.

## 확인 방법

- 테스트: 응답 직전 장애, timeout, 재시도를 시뮬레이션한다.
- 로그: original request id, retry count, idempotency key, 처리 상태를 남긴다.
- 메트릭: timeout 후 성공률, retry storm, duplicate request count를 본다.
- 운영 확인: 같은 업무 key로 짧은 시간에 반복 요청이 들어오는지 확인한다.

## 장점과 한계

| 접근 | 장점 | 한계 |
|---|---|---|
| retry | 일시 장애를 흡수한다 | 멱등성 없이는 중복 처리 위험이 있다 |
| 상태 조회 후 재시도 | 결과 불명 상태를 줄인다 | 외부 시스템 조회 API가 필요할 수 있다 |
| pending 상태 | 중간 상태를 운영에서 추적할 수 있다 | 만료와 복구 정책이 필요하다 |

## 짧은 예제

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

timeout 이후에는 같은 요청을 새 작업으로 만들기보다, 기존 요청의 상태를 기준으로 결과를 확인하거나 복구한다. 실제 구현에서는 `requestKey`에 unique 제약을 두어 동시에 들어온 같은 요청이 중복 생성되지 않게 해야 한다.

## 핵심 요약

재시도는 장애 대응에 필요하지만 멱등성이 없으면 중복 처리 위험을 만든다.

timeout은 실패가 아니라 성공, 실패, 결과 불명 중 하나일 수 있다.

같은 의도의 재시도는 같은 idempotency key나 request key를 사용해야 한다.

중간 장애를 다루려면 pending 상태와 상태 조회 또는 복구 플로우가 필요하다.

retry에는 timeout, backoff, 최대 횟수, circuit breaker 같은 부하 제어가 함께 필요하다.

## 꼬리 질문

- timeout 이후 바로 새 결제 요청을 보내면 어떤 문제가 생기는가?
- retry와 idempotency key는 어떤 관계인가?
- pending 상태는 왜 필요한가?

## 관련 문서

- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[idempotency-key]]
- [[01-core/network/retry|retry]]
- [[01-core/network/timeout|timeout]]
