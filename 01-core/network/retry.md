---
title: "재시도 전략과 백오프"
description: Retry 전략과 지수 백오프, 멱등성과의 관계
tags: [concept, network]
---

# 재시도 전략과 백오프

Retry는 일시적인 장애로 실패한 요청을 다시 보내는 전략이다. 잘못 설계하면 장애를 줄이는 게 아니라 키운다.

재시도에서 사고가 나는 지점은 넷이다. 과부하인 서버에 즉시 재시도해 부하를 더 얹고(Retry Storm), 비멱등 요청을 다시 보내 결제가 두 번 일어나고, 간격 없이 반복해 서버가 회복할 틈이 없고, 400처럼 다시 보내도 안 되는 에러까지 재시도한다.

## 무엇을 재시도하나

같은 요청을 다시 보냈을 때 성공할 가능성이 있을 때만 재시도한다.

| 구분 | 재시도 가능 | 재시도 불가 |
|---|---|---|
| 원인 | 일시적 장애 (네트워크 순단, 503) | 영구적 오류 (400, 401, 404) |
| HTTP 상태 | 408, 429, 500, 502, 503, 504 | 400, 401, 403, 404, 422 |
| 예외 | `ConnectException`, `SocketTimeoutException` | `IllegalArgumentException`, 비즈니스 에러 |

표의 "재시도 가능"은 조건부다. 500은 원인에 따라 다르고, 502, 504는 서버가 이미 처리했는데 응답만 못 받았을 수 있으므로 멱등 요청에서만 재시도한다. 자세한 기준은 [[status-code]].

## 간격을 어떻게 두나

### 고정 간격 (Fixed Delay)

```
시도1 → 실패 → 1초 대기 → 시도2 → 실패 → 1초 대기 → 시도3
```

단순하지만, 서버가 과부하일 때 일정한 간격마다 요청이 한꺼번에 몰린다.

### 지수 백오프 (Exponential Backoff)

```
시도1 → 실패 → 1초 대기 → 시도2 → 실패 → 2초 대기 → 시도3 → 실패 → 4초 대기 → 시도4
```

재시도할수록 대기 시간을 늘려 서버에 회복할 시간을 준다.

### 지수 백오프 + Jitter

```
시도1 → 실패 → 1초 + random(0~500ms) → 시도2 → 실패 → 2초 + random(0~500ms) → 시도3
```

여러 클라이언트가 동시에 실패하면 재시도도 같은 시점에 몰린다(Thundering Herd). Jitter로 대기 시간에 무작위 값을 더하면 재시도 시점이 흩어진다.

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

재시도는 같은 요청을 두 번 이상 보내는 일이다. 멱등하지 않은 요청은 그대로 다시 보내면 안 된다.

```
시도1: POST /api/payments → timeout (서버에서는 처리 완료)
시도2: POST /api/payments → 결제가 두 번 처리됨!
```

### 멱등키 (Idempotency Key)

```java
// 클라이언트가 고유한 멱등키를 생성해서 헤더에 포함
POST /api/payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

// 서버는 멱등키로 중복 요청을 감지
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

1. **최대 재시도 횟수 제한**: 보통 2~3회.
2. **지수 백오프 + Jitter**: 재시도 시점을 흩뜨린다.
3. **Circuit Breaker**: 연속으로 실패하면 재시도 자체를 멈춘다.
4. **서버 측 429 (Too Many Requests)**: `Retry-After` 헤더로 언제 다시 오라고 알려 준다.

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
| 조합 | Retry 후에도 실패하면 Circuit Breaker가 동작 |

## 자주 깨지는 곳

- **모든 에러를 재시도한다.** 400 Bad Request처럼 다시 보내도 같은 결과인 요청을 헛되이 반복한다.
- **백오프 없이 즉시 재시도한다.** 이미 힘든 서버에 부하를 더 얹는다.
- **POST를 멱등키 없이 재시도한다.** 같은 처리가 두 번 일어난다.
- **재시도 횟수를 5회 이상으로 잡는다.** 대기 시간이 쌓여 사용자 응답이 길어진다.
- **Circuit Breaker 없이 재시도만 둔다.** 다운된 서버에도 계속 보내 장애가 번진다.

## 면접에서 말하기

> 재시도는 다시 보냈을 때 성공할 수 있는 일시적 장애에만 적용합니다. 저는 지수 백오프에 Jitter를 붙여 서버에 회복 시간을 주고 재시도 시점을 흩뜨리며, 횟수는 2~3회로 제한합니다. POST 같은 비멱등 요청은 멱등키가 있을 때만 재시도합니다. 실패가 계속되면 Circuit Breaker로 재시도 자체를 끊어 Retry Storm을 막습니다.

## 꼬리 질문

> [!question]- 재시도 횟수는 몇 번이 적절한가?
> 보통 2~3회가 적절합니다. 재시도마다 대기 시간이 누적되어 사용자 응답 시간이 길어지기 때문입니다. 3회 × 지수 백오프면 1초 + 2초 + 4초 = 7초가 추가됩니다.

> [!question]- Retry-After 헤더는 어떻게 활용하는가?
> 서버가 429 또는 503 응답과 함께 `Retry-After: 30`을 보내면, 클라이언트는 30초 후에 재시도해야 합니다. 이를 무시하고 즉시 재시도하면 서버에 불필요한 부하를 줍니다.

> [!question]- 멱등키는 어디에 저장하는가?
> 서버에서 Redis나 DB에 저장합니다. TTL을 설정해서 일정 시간 후 자동 삭제합니다. 멱등키가 존재하면 이전 처리 결과를 반환하고, 없으면 새로 처리합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[timeout]]
- [[http-basics]]
- [[status-code]]