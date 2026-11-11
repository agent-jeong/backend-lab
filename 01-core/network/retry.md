---
title: "재시도 전략과 백오프"
description: 실패한 요청을 언제, 몇 번, 얼마 간격으로 다시 보낼지와 멱등성
tags: [concept, network]
---

# 재시도 전략과 백오프

Retry는 네트워크가 잠깐 끊기는 것처럼 일시적인 이유로 실패한 요청을 다시 보내는 일이다. 잘못 걸면 장애를 줄이기는커녕 키운다.

재시도에서 사고가 나는 경우는 크게 네 가지다. 이미 과부하인 서버에 바로 다시 보내 부하를 더 얹거나(Retry Storm), 멱등하지 않은 결제 요청을 다시 보내 결제가 두 번 되거나, 간격 없이 반복해서 서버가 회복할 틈을 주지 않거나, 400처럼 다시 보내도 소용없는 에러까지 재시도하는 경우다.

## 무엇을 재시도하나

같은 요청을 다시 보냈을 때 성공할 수도 있을 때만 재시도한다.

| 구분 | 재시도 가능 | 재시도 불가 |
|---|---|---|
| 원인 | 일시적 장애 (네트워크 순단, 503) | 영구적 오류 (400, 401, 404) |
| HTTP 상태 | 408, 429, 500, 502, 503, 504 | 400, 401, 403, 404, 422 |
| 예외 | `ConnectException`, `SocketTimeoutException` | `IllegalArgumentException`, 비즈니스 에러 |

표의 "재시도 가능"도 늘 그런 건 아니다. 500은 원인에 따라 다르고, 502와 504는 서버가 이미 처리했는데 응답만 못 받았을 수 있어서 멱등한 요청만 재시도한다. 자세한 기준은 [[status-code]]에 있다.

## 간격을 어떻게 두나

### 고정 간격 (Fixed Delay)

```
시도1 → 실패 → 1초 대기 → 시도2 → 실패 → 1초 대기 → 시도3
```

단순하지만, 서버가 과부하일 때 같은 간격마다 요청이 한꺼번에 몰린다.

### 지수 백오프 (Exponential Backoff)

```
시도1 → 실패 → 1초 대기 → 시도2 → 실패 → 2초 대기 → 시도3 → 실패 → 4초 대기 → 시도4
```

재시도할 때마다 대기 시간을 늘려서 서버가 회복할 시간을 준다.

### 지수 백오프 + Jitter

```
시도1 → 실패 → 1~2초 중 무작위 대기 → 시도2 → 실패 → 2~4초 중 무작위 대기 → 시도3
```

여러 클라이언트가 동시에 실패하면 재시도도 같은 시점에 몰린다(Thundering Herd). Jitter로 대기 시간을 무작위로 흔들면 재시도 시점이 흩어진다. 아래 Spring Retry의 `random = true`는 지수 백오프로 정한 대기 시간에 1부터 `multiplier`까지의 무작위 배수를 곱한다. 위 그림의 1~2초, 2~4초가 그 결과다.

```java
// Spring Retry - 지수 백오프 + Jitter
@Retryable(
    retryFor = {ConnectException.class, SocketTimeoutException.class},
    maxAttempts = 3,
    backoff = @Backoff(delay = 1000, multiplier = 2, random = true)
)
public PaymentResult callPaymentApi(PaymentRequest request) {
    return paymentClient.pay(request);
}

@Recover
public PaymentResult recover(Exception e, PaymentRequest request) {
    log.error("결제 API 최종 실패: orderId={}", request.getOrderId(), e);
    throw new PaymentFailedException("결제 처리 실패", e);
}
```

## Retry와 멱등성

재시도는 같은 요청을 두 번 이상 보내는 일이다. 그래서 멱등하지 않은 요청을 그대로 다시 보내면 같은 일이 두 번 일어난다.

```
시도1: POST /api/payments → timeout (서버에서는 처리 완료)
시도2: POST /api/payments → 결제가 두 번 처리됨!
```

### 멱등키 (Idempotency Key)

클라이언트가 고유한 멱등키를 만들어 헤더에 싣는다.

```http
POST /api/payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

서버는 멱등키로 중복 요청을 알아본다.

```java
@PostMapping("/api/payments")
public PaymentResult pay(@RequestHeader("Idempotency-Key") String key,
                         @RequestBody PaymentRequest request) {
    // 이미 처리된 키면 저장된 결과를 반환
    return paymentService.processIdempotent(key, request);
}
```

| 메서드 | 멱등성 | 재시도 안전성 |
|---|---|---|
| GET | 멱등 | 안전 |
| PUT | 멱등 | 안전 |
| DELETE | 멱등 | 안전 |
| POST | 비멱등 | 멱등키 필요 |

## Retry Storm 막기

```
서버 과부하 → 응답 지연/실패 → 클라이언트들이 재시도
→ 서버 부하 증가 → 더 많은 실패 → 더 많은 재시도
→ 서버 완전 마비
```

1. 재시도 횟수에 상한을 둔다. 보통 2~3회다.
2. 지수 백오프에 Jitter를 붙여 재시도 시점을 흩뜨린다.
3. 실패가 이어지면 Circuit Breaker로 재시도 자체를 멈춘다.
4. 서버는 429(Too Many Requests)와 함께 `Retry-After` 헤더로 언제 다시 오라고 알려 준다.

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30

→ 클라이언트는 30초 후 재시도
```

## Retry와 Circuit Breaker

| 구분 | Retry | Circuit Breaker |
|---|---|---|
| 목적 | 일시적 실패를 복구 | 지속적 실패 시 빠른 실패 처리 |
| 동작 | 실패하면 다시 시도 | 실패율이 높으면 요청 차단 |
| 적합한 상황 | 네트워크 순단, 간헐적 에러 | 서버 다운, 지속적 과부하 |

둘을 같이 쓰면 Retry가 바깥, Circuit Breaker가 안쪽에 선다. 재시도 하나하나가 Circuit Breaker에 호출 하나로 쌓이고, 실패가 쌓여 회로가 열리면 그 뒤 재시도는 바로 막힌다. 이때 막힌 호출(`CallNotPermittedException`)까지 재시도하지 않게 빼 둔다. 순서와 설정은 [[circuit-breaker]]에 있다.

## 자주 깨지는 곳

- 모든 에러를 재시도하면, 400 Bad Request처럼 다시 보내도 결과가 같은 요청을 헛되이 반복한다.
- 백오프 없이 바로 재시도하면, 이미 힘든 서버에 부하를 더 얹는다.
- POST를 멱등키 없이 재시도하면 같은 처리가 두 번 일어난다.
- 재시도 횟수를 5회 이상으로 잡으면 대기 시간이 쌓여 사용자가 응답을 오래 기다린다.
- Circuit Breaker 없이 재시도만 두면, 이미 죽은 서버에도 계속 보내서 장애가 호출하는 쪽까지 번진다.

## 한 번에 설명하기

> 재시도는 다시 보내면 성공할 수도 있는 일시적인 장애에만 씁니다. 지수 백오프에 Jitter를 붙여 서버가 회복할 시간을 주고 재시도 시점을 흩뜨리며, 횟수는 2~3회로 묶습니다.
>
> POST처럼 멱등하지 않은 요청은 멱등키가 있을 때만 재시도합니다.
>
> 실패가 계속되면 Circuit Breaker로 재시도 자체를 끊어서 Retry Storm을 막습니다.

## 꼬리 질문

> [!question]- 재시도는 몇 번까지 하는가?
> 보통 2~3회면 됩니다. 재시도할 때마다 대기 시간이 쌓여서 사용자가 응답을 그만큼 늦게 받기 때문입니다. 첫 대기를 1초로 두고 지수 백오프로 3번 재시도하면 1초 + 2초 + 4초 = 7초를 더 기다립니다. 위 코드처럼 `maxAttempts = 3`이면 첫 시도를 포함한 횟수라서 재시도는 2번입니다. `random = true`라서 대기는 1~2초와 2~4초, 합쳐서 3~6초입니다.

> [!question]- Retry-After 헤더는 어떻게 쓰는가?
> 서버가 429나 503 응답에 `Retry-After: 30`을 붙여 보내면, 클라이언트는 30초 뒤에 다시 보내야 합니다. 이걸 무시하고 바로 재시도하면 서버에 쓸데없는 부하만 얹습니다.

> [!question]- 멱등키는 어디에 저장하는가?
> 서버 쪽 Redis나 DB에 둡니다. TTL을 걸어 일정 시간이 지나면 지워지게 합니다. 요청이 오면 같은 멱등키가 있는지 보고, 있으면 전에 처리한 결과를 돌려주고 없으면 새로 처리합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Amazon Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [RFC 9110: Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods)
- [Spring Retry: ExponentialRandomBackOffPolicy](https://github.com/spring-projects/spring-retry/blob/main/src/main/java/org/springframework/retry/backoff/ExponentialRandomBackOffPolicy.java)

## 관련 문서

- [[01-core/network/network|network]]
- [[timeout]]
- [[http-basics]]
- [[status-code]]
- [[circuit-breaker]]
- [[rate-limiting]]
