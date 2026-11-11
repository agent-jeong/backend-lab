---
title: 서킷 브레이커
description: 느린 외부 의존성을 계속 부르지 않고 바로 실패시켜 장애가 우리 서버로 번지지 않게 막는 방법
tags: [concept, network]
---

# 서킷 브레이커

서킷 브레이커는 외부 호출의 실패와 지연을 세다가 기준을 넘으면 한동안 호출 자체를 막고 바로 실패를 돌려주는 장치다. 전기 차단기처럼 문제가 생긴 회로를 끊어서 나머지를 지킨다.

주문 API가 외부 결제 API를 부르는데 결제 쪽이 평소 200ms에서 10초로 느려졌다고 하자. timeout을 걸어도 요청마다 10초씩 Tomcat 스레드와 HTTP 커넥션을 쥐고 있으니, 금방 스레드 풀이 바닥나고 결제와 상관없는 상품 조회까지 멈춘다. 결제 API가 지금 아프다는 걸 이미 알면 매번 기다릴 필요가 없다. 서킷 브레이커는 그 판단을 대신 내려서, 실패는 빨리 돌려주고 상대에게는 회복할 시간을 준다.

## 상태와 전이

서킷 브레이커는 세 상태를 오간다. 아래 동작과 기본값은 Resilience4j 2.x 기준이다.

```
          실패율 또는 느린 호출 비율이 기준 이상
 CLOSED ───────────────────────────────────▶ OPEN
   ▲                                          │
   │ 시험 호출이 기준 미만                     │ waitDurationInOpenState 경과
   │                                          ▼
   └────────────────────────────────────── HALF_OPEN
                 시험 호출이 기준 이상이면 다시 OPEN
```

| 상태 | 호출 | 하는 일 |
|---|---|---|
| CLOSED | 모두 보낸다 | 최근 호출의 결과를 슬라이딩 윈도에 쌓고 실패율과 느린 호출 비율을 계산한다 |
| OPEN | 보내지 않는다 | `CallNotPermittedException`을 바로 던진다. 정해 둔 시간이 지나면 HALF_OPEN으로 간다 |
| HALF_OPEN | 정해 둔 수만 보낸다 | 시험 호출 결과로 CLOSED로 돌아갈지 OPEN으로 다시 갈지 정한다 |

Resilience4j에는 이 셋 말고 `DISABLED`, `FORCED_OPEN`, `METRICS_ONLY` 같은 특수 상태도 있다. 장애 대응 중에 사람이 손으로 회로를 열거나 끌 때 쓴다.

## 무엇을 실패로 세나

판단은 최근 호출을 담은 슬라이딩 윈도에서 한다. 윈도는 최근 N건을 보는 `COUNT_BASED`와 최근 N초를 보는 `TIME_BASED`가 있다.

| 설정 | 기본값 | 뜻 |
|---|---|---|
| `slidingWindowType` | `COUNT_BASED` | 윈도를 호출 수로 셀지 시간으로 셀지 |
| `slidingWindowSize` | 100 | 윈도 크기. 호출 수 또는 초 |
| `minimumNumberOfCalls` | 100 | 이만큼 쌓이기 전에는 실패율을 계산하지 않는다 |
| `failureRateThreshold` | 50 | 실패율이 이 퍼센트 이상이면 OPEN |
| `slowCallDurationThreshold` | 60000ms | 이 시간보다 오래 걸린 호출을 느린 호출로 센다 |
| `slowCallRateThreshold` | 100 | 느린 호출 비율이 이 퍼센트 이상이면 OPEN |
| `waitDurationInOpenState` | 60000ms | OPEN에서 HALF_OPEN으로 넘어가기까지 기다리는 시간 |
| `permittedNumberOfCallsInHalfOpenState` | 10 | HALF_OPEN에서 보내 볼 시험 호출 수 |

기본값을 그대로 쓰면 거의 열리지 않는다. 최소 100건이 쌓여야 계산을 시작하고, 느린 호출은 60초를 넘겨야 세고, 느린 호출이 100%여야 열린다. 그래서 느린 호출 기준은 그 API의 timeout보다 짧게, 평소 p99보다 조금 길게 잡는다. `minimumNumberOfCalls`는 트래픽이 적은 API라면 줄인다.

기본으로는 모든 예외를 실패로 센다. 잔액 부족처럼 상대가 정상적으로 거절한 4xx 업무 예외까지 세면, 사용자 입력이 잘못됐을 뿐인데 회로가 열린다. 이런 예외는 `ignoreExceptions`에 넣거나, 실패로 셀 예외만 `recordExceptions`에 적는다.

## Resilience4j로 붙이기

Spring Boot 3.x에서는 `resilience4j-spring-boot3`에 `spring-boot-starter-aop`와 actuator를 같이 넣는다.

```yaml
resilience4j:
  circuitbreaker:
    instances:
      payment:
        slidingWindowType: COUNT_BASED
        slidingWindowSize: 50
        minimumNumberOfCalls: 20
        failureRateThreshold: 50
        slowCallDurationThreshold: 2s
        slowCallRateThreshold: 50
        waitDurationInOpenState: 30s
        permittedNumberOfCallsInHalfOpenState: 5
        registerHealthIndicator: true
        ignoreExceptions:
          - com.example.payment.PaymentRejectedException
```

위 숫자는 예시다. 실제 값은 그 API의 평소 지연과 트래픽을 보고 정한다.

```java
@Service
public class PaymentGateway {

    private final PaymentClient paymentClient;

    public PaymentGateway(PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }

    @CircuitBreaker(name = "payment", fallbackMethod = "payFallback")
    public PaymentResult pay(PaymentRequest request) {
        return paymentClient.pay(request);
    }

    private PaymentResult payFallback(PaymentRequest request, CallNotPermittedException e) {
        return PaymentResult.pending(request.orderId());
    }

    private PaymentResult payFallback(PaymentRequest request, Exception e) {
        throw new PaymentUnavailableException("결제 서비스를 지금 사용할 수 없습니다", e);
    }
}
```

fallback 메서드는 원래 메서드와 같은 클래스에 두고, 같은 파라미터 뒤에 예외 하나를 더 받는다. fallback이 여러 개면 예외 타입이 가장 가깝게 맞는 쪽이 불린다.

## fallback은 무엇을 돌려주나

fallback은 실패를 숨기는 곳이 아니라, 실패했을 때 사용자에게 무엇을 보여 줄지 정하는 곳이다.

| 상황 | fallback | 이유 |
|---|---|---|
| 상품 추천, 리뷰 개수 | 빈 목록이나 캐시된 값 | 없어도 주문은 된다 |
| 배송 예정일 조회 | 기본 문구("2~3일 내 출고") | 정확도보다 화면이 뜨는 게 낫다 |
| 결제 승인 | 실패나 "처리 중" 상태를 그대로 알린다 | 결제를 성공처럼 꾸미면 돈이 맞지 않는다 |
| 재고 차감 | 주문을 막고 에러를 준다 | 재고를 모른 채 받으면 초과 판매가 난다 |

결제를 "처리 중"으로 받아 두고 나중에 처리하려면, 그 요청을 저장하고 다시 보낼 때 멱등키를 실어야 한다. 이 흐름은 [[payment-order-idempotency]]에 있다.

## timeout, retry와 함께 쓰는 순서

서킷 브레이커는 혼자서는 느린 호출을 끊지 못한다. 호출을 끝내는 건 timeout이고, 서킷 브레이커는 그 결과를 셀 뿐이다. 그래서 세 가지를 같이 둔다.

Resilience4j Spring Boot 3 모듈의 기본 aspect 순서는 아래와 같다. 바깥에 있는 것이 나중에 판단한다.

```
Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( 실제 호출 ) ) ) ) )
```

1. 가장 안쪽에서 HTTP client의 connect timeout과 read timeout이 호출을 끊는다. `@TimeLimiter`는 `CompletableFuture` 같은 비동기 반환형에만 걸리므로, 동기 호출은 client timeout으로 끊는다. 값을 정하는 법은 [[timeout]]에 있다.
2. 서킷 브레이커가 그 실패와 느린 호출을 세고, 기준을 넘으면 회로를 연다.
3. 가장 바깥의 Retry가 실패한 호출을 다시 시도한다. 시도 하나하나가 서킷 브레이커에 호출 하나로 쌓인다.

Retry가 바깥에 있으면 회로가 열린 뒤에도 `CallNotPermittedException`을 재시도한다. 어차피 막힐 호출을 기다리느라 응답만 늦어지므로, Retry 설정의 `ignoreExceptions`에 이 예외를 넣는다. 재시도 횟수와 백오프는 [[retry]]에 있다.

## Bulkhead로 자원을 나누기

서킷 브레이커는 실패율이 쌓여야 열리므로, 열리기 전까지는 느린 호출이 스레드를 계속 잡는다. Bulkhead는 의존성마다 동시에 쓸 수 있는 자원의 상한을 둬서 그 사이를 막는다. 배의 격벽처럼 한 칸에 물이 차도 다른 칸은 멀쩡하게 둔다.

| 종류 | 동작 | 기본값 |
|---|---|---|
| `Bulkhead`(세마포어) | 호출하는 스레드에서 그대로 돌리고, 동시 호출 수만 센다 | `maxConcurrentCalls` 25, `maxWaitDuration` 0 |
| `ThreadPoolBulkhead` | 의존성 전용 스레드 풀과 큐에서 돌린다 | 큐 100, 스레드 수는 CPU 코어 수 기준 |

상한을 넘은 호출은 기다리지 않고 `BulkheadFullException`으로 바로 실패한다. 결제 API의 동시 호출을 30개로 묶어 두면, 결제가 아무리 느려져도 Tomcat 스레드 200개 중 30개만 결제에 묶이고 나머지는 다른 요청을 처리한다. 커넥션 풀과 스레드 풀 크기를 어떻게 보는지는 [[connection-pool-and-timeout]]에 있다.

## 자주 깨지는 곳

- timeout 없이 서킷 브레이커만 두면, 느린 호출이 끝나지 않아 실패로 세지지도 않고 스레드만 묶인다.
- 기본값을 그대로 두면, 100건이 쌓이기 전이나 60초보다 짧은 지연에서는 회로가 열리지 않는다.
- 4xx 업무 예외까지 실패로 세면, 잘못된 입력이 몰릴 때 멀쩡한 의존성의 회로가 열린다.
- 결제 승인 fallback이 성공을 돌려주면, 실제로는 결제되지 않은 주문이 결제 완료로 남는다.
- 의존성 여러 개가 서킷 브레이커 인스턴스 하나를 같이 쓰면, 알림 API 장애로 결제 호출까지 막힌다.
- Retry가 `CallNotPermittedException`까지 재시도하면, 회로가 열려 있는 동안 사용자는 백오프 시간만큼 더 기다린 뒤 같은 실패를 받는다.
- 인스턴스마다 서킷 브레이커 상태를 따로 가진다는 걸 모르면, 서버 10대 중 일부만 회로가 열린 상태를 보고 설정이 안 먹는다고 착각한다.

## 운영에서 볼 것

- `resilience4j.circuitbreaker.state`로 인스턴스별 상태를, `resilience4j.circuitbreaker.failure.rate`로 실패율을 본다. 상태가 OPEN으로 바뀌면 알림을 보낸다.
- `resilience4j.circuitbreaker.calls`를 결과별로 나눠 성공, 실패, 무시된 호출, 막힌 호출 수를 본다.
- `registerHealthIndicator: true`와 `management.health.circuitbreakers.enabled=true`를 켜면 `/actuator/health`에 회로 상태가 나온다. 이 값을 로드밸런서 헬스체크에 넣으면, 외부 API 하나가 죽었을 때 우리 서버 전체가 빠지므로 넣지 않는다.
- 상태 전이 이벤트(CLOSED에서 OPEN 등)를 로그로 남겨, 장애 시각과 맞춰 본다.
- 외부 API를 일부러 느리게 만든 테스트로 회로가 정말 열리는지, fallback이 무엇을 돌려주는지 확인한다.

## 한 번에 설명하기

> 서킷 브레이커는 외부 호출의 실패율과 느린 호출 비율을 세다가 기준을 넘으면 호출을 막고 바로 실패를 돌려주는 장치입니다. 상태는 CLOSED, OPEN, HALF_OPEN이고, OPEN에서 일정 시간이 지나면 몇 건만 보내 보고 회복했는지 판단합니다.
>
> 호출을 실제로 끊는 건 timeout이라서 timeout을 먼저 두고, 서킷 브레이커는 그 결과를 셉니다. Retry는 가장 바깥에 두되, 회로가 열려서 난 예외는 재시도하지 않게 합니다.
>
> 회로가 열리기 전에도 느린 호출이 스레드를 다 잡지 않도록 Bulkhead로 의존성별 동시 호출 수를 묶습니다. fallback은 추천처럼 없어도 되는 기능에만 대체값을 주고, 결제처럼 돈이 걸린 호출은 실패를 그대로 알립니다.

## 꼬리 질문

> [!question]- HALF_OPEN 상태는 왜 필요한가요?
> OPEN에서 바로 CLOSED로 돌아가면, 상대가 아직 회복하지 않았을 때 모든 요청이 한꺼번에 몰려 다시 쓰러뜨립니다. HALF_OPEN에서는 정해 둔 몇 건만 보내 보고, 그 결과가 기준 미만일 때만 CLOSED로 돌아갑니다.

> [!question]- 서킷 브레이커와 Retry는 어느 쪽을 바깥에 두나요?
> Resilience4j 기본 순서는 Retry가 바깥, 서킷 브레이커가 안쪽입니다. 재시도 하나하나가 서킷 브레이커에 실패로 쌓여서 장애를 빨리 알아챕니다. 대신 회로가 열려서 나는 `CallNotPermittedException`은 Retry가 다시 시도하지 않게 제외합니다.

> [!question]- 서킷 브레이커 상태는 서버마다 다른가요?
> Resilience4j는 상태를 각 애플리케이션 인스턴스 메모리에 둡니다. 그래서 서버마다 본 호출이 달라 일부만 OPEN일 수 있습니다. 대부분은 그대로 두는 편이 낫습니다. 각 서버가 자기가 본 실패로 판단하면, 특정 서버의 네트워크 문제도 그 서버에서만 막힙니다.

> [!question]- Bulkhead가 있으면 서킷 브레이커는 필요 없나요?
> 둘은 막는 것이 다릅니다. Bulkhead는 동시에 묶일 수 있는 자원 수를 제한해서 다른 기능을 지키지만, 상대가 죽어 있어도 상한까지는 계속 보냅니다. 서킷 브레이커는 상대가 아프다고 판단하면 보내는 것 자체를 멈춥니다. 그래서 같이 씁니다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 회로가 열려 막힌 호출은 "안 감"이라 나중에 다시 보내도 되고, timeout으로 끝난 호출은 "모름"으로 남겨야 하는 이유

## 참고

2026년 11월에 확인한 공식 문서다.

- [Resilience4j: CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker)
- [Resilience4j: Getting Started with Spring Boot 3](https://resilience4j.readme.io/docs/getting-started-3)
- [Martin Fowler: CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html)

## 관련 문서

- [[01-core/network/network|network]]
- [[timeout]]
- [[retry]]
- [[connection-pool-and-timeout]]
- [[payment-order-idempotency]]
- [[external-api-and-transaction]]
- [[request-journey]]
