---
title: Timeout
description: Connection/Read/Write timeout의 차이와 실무 설정 기준
---

# Timeout

## 한 줄 정의

Timeout은 네트워크 요청의 각 단계에서 응답을 기다리는 최대 시간으로, 설정하지 않으면 무한 대기로 장애가 전파된다.

## 실무에서 왜 중요한가

Timeout을 제대로 설정하지 않으면 다음 문제가 생긴다.

- 외부 API가 느려질 때 우리 서버의 스레드가 전부 대기 상태에 빠진다.
- 타임아웃 없이 무한 대기하다가 커넥션 풀이 고갈된다.
- Connection timeout과 Read timeout을 구분하지 못해서 적절한 값을 설정하지 못한다.
- 하나의 느린 외부 서비스가 전체 시스템을 마비시킨다 (장애 전파).

## Timeout 종류

```
Client                              Server
  │                                    │
  │── TCP SYN ──────────────────────▶  │
  │        ↕ Connection Timeout        │
  │◀── TCP SYN+ACK ────────────────   │
  │                                    │
  │── HTTP Request ─────────────────▶  │
  │        ↕ Read (Response) Timeout   │  ← 서버 처리 시간
  │◀── HTTP Response ───────────────   │
  │                                    │
```

| Timeout | 구간 | 기본 권장값 |
|---|---|---|
| Connection Timeout | TCP 연결 수립까지 | 1~3초 |
| Read Timeout | 요청 전송 후 응답 수신까지 | 3~10초 (API에 따라 다름) |
| Write Timeout | 요청 데이터 전송까지 | 5~10초 |

### Connection Timeout

TCP 3-way handshake가 완료되기까지의 시간이다. 서버가 다운되었거나 방화벽에 의해 차단된 경우 이 timeout에 걸린다.

```java
// RestTemplate
factory.setConnectTimeout(3000);  // 3초

// WebClient
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 3000);
```

서버가 응답하지 않는 상황에서 OS 기본 TCP timeout(보통 75초~2분)까지 대기하게 되므로, 반드시 짧게 설정해야 한다.

### Read Timeout (Response Timeout)

TCP 연결이 수립된 후, 서버의 응답을 기다리는 시간이다. 서버의 처리 시간이 긴 경우 이 timeout에 걸린다.

```java
// RestTemplate
factory.setReadTimeout(5000);  // 5초

// WebClient
WebClient webClient = WebClient.builder()
    .clientConnector(new ReactorClientHttpConnector(
        HttpClient.create()
            .responseTimeout(Duration.ofSeconds(5))
    ))
    .build();
```

Read timeout은 API의 예상 응답 시간에 맞게 설정한다. 결제 API처럼 처리 시간이 긴 경우 넉넉하게, 단순 조회 API는 짧게 설정한다.

## 실무 설정 예시

```yaml
# application.yml - 외부 API별 timeout 설정
external-api:
  payment:
    connect-timeout: 3000
    read-timeout: 30000    # 결제는 처리 시간이 길 수 있음
  notification:
    connect-timeout: 2000
    read-timeout: 5000     # 알림은 빠르게 응답해야 함
  search:
    connect-timeout: 1000
    read-timeout: 3000     # 검색은 빠른 응답 기대
```

```java
@Configuration
public class ExternalApiConfig {

    @Bean
    public RestTemplate paymentRestTemplate(
            @Value("${external-api.payment.connect-timeout}") int connectTimeout,
            @Value("${external-api.payment.read-timeout}") int readTimeout) {

        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        return new RestTemplate(factory);
    }
}
```

## Timeout과 장애 전파

```
사용자 → 우리 서버 (스레드 200개) → 외부 결제 API (응답 지연)

1. 결제 API가 느려짐 (평소 1초 → 30초)
2. 우리 서버의 스레드가 30초씩 대기
3. 200개 스레드가 모두 결제 API 대기 상태
4. 다른 요청 (조회, 목록 등)도 처리 불가
5. → 전체 서비스 장애
```

**대응 방법:**

1. **적절한 Read Timeout**: 예상 응답 시간의 2~3배 이내
2. **Circuit Breaker**: 연속 실패 시 빠르게 실패 처리 (Resilience4j 등)
3. **Bulkhead**: 외부 API별 스레드 풀을 분리해서 한 API의 장애가 다른 기능에 영향을 주지 않게 함

```java
// Resilience4j Circuit Breaker 예시
@CircuitBreaker(name = "payment", fallbackMethod = "paymentFallback")
public PaymentResult processPayment(PaymentRequest request) {
    return paymentClient.pay(request);
}

private PaymentResult paymentFallback(PaymentRequest request, Exception e) {
    // 대체 처리: 결제 큐에 넣고 나중에 처리
    return PaymentResult.pending();
}
```

## 서버 측 Timeout

클라이언트 timeout만 설정하면 안 되고, 서버 측 timeout도 함께 고려해야 한다.

| 설정 | 의미 | 기본값 (Tomcat) |
|---|---|---|
| `server.tomcat.connection-timeout` | 요청 헤더 수신 대기 시간 | 20초 |
| `spring.mvc.async.request-timeout` | 비동기 요청 처리 시간 | 30초 |
| HikariCP `connectionTimeout` | DB 커넥션 획득 대기 시간 | 30초 |

서버의 요청 처리 시간이 클라이언트의 Read timeout보다 길면, 클라이언트는 timeout으로 끊었지만 서버는 계속 처리하는 상황이 발생한다.

## 자주 나는 실수

- timeout을 설정하지 않아서 외부 API 장애가 전체 서비스로 전파된다.
- Connection timeout과 Read timeout을 구분하지 않고 같은 값을 설정한다.
- Read timeout을 너무 짧게 설정해서 정상 요청도 실패한다.
- 서버 측 timeout을 고려하지 않아서 클라이언트는 끊었는데 서버는 계속 처리한다.
- 모든 외부 API에 같은 timeout을 설정해서 특성에 맞지 않는다.

## 핵심 요약

Timeout은 Connection(연결), Read(응답 대기), Write(전송)로 구분됩니다.
설정하지 않으면 외부 API 장애가 전체 서비스로 전파될 수 있습니다.

Connection timeout은 1~3초, Read timeout은 API 특성에 맞게 설정합니다.
Circuit Breaker와 Bulkhead를 함께 사용하면 장애 전파를 더 효과적으로 차단할 수 있습니다.

## 꼬리 질문

> [!question]- Connection timeout이 발생하는 원인은?
> 서버가 다운되었거나, 방화벽이 SYN 패킷을 차단하거나, 네트워크 경로에 문제가 있는 경우입니다. DNS는 정상이지만 TCP 연결이 수립되지 않는 상황입니다.

> [!question]- Read timeout이 발생했는데 서버에서는 처리가 완료되었다면?
> 클라이언트는 timeout으로 실패 처리했지만, 서버는 정상 처리를 완료한 상태입니다. 결제 같은 경우 중복 처리가 발생할 수 있으므로, 멱등키로 중복을 방지하거나 상태 조회 API로 결과를 확인해야 합니다.

> [!question]- Circuit Breaker는 어떻게 동작하는가?
> 연속 실패가 임계치를 넘으면 OPEN 상태로 전환되어 요청을 보내지 않고 즉시 실패를 반환합니다. 일정 시간 후 HALF_OPEN으로 전환되어 일부 요청을 시도하고, 성공하면 CLOSED로 복구합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[retry]]
- [[tcp-connection]]
- [[http-basics]]