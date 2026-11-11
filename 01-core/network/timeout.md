---
title: "타임아웃 설계와 실무 기준"
description: Connection, Read, Write timeout이 각각 무엇을 기다리고, 값을 어떻게 잡는지
tags: [concept, network]
---

# 타임아웃 설계와 실무 기준

Timeout은 네트워크 요청의 단계마다 응답을 얼마까지 기다릴지 정한 시간이다. 설정하지 않으면 끝없이 기다리고, 그렇게 기다리는 동안 상대의 장애가 우리 서버로 옮겨 온다.

외부 결제 API 하나가 느려지면 그 API를 기다리는 스레드가 쌓이고, 커넥션 풀이 바닥나고, 결국 결제와 상관없는 상품 조회까지 멈춘다. 그래서 timeout은 얼마나 기다려 줄지보다, 느린 상대 하나 때문에 우리 서버 전체가 멈추지 않으려면 언제 끊어야 하는지를 보고 정한다. Connection timeout과 Read timeout은 걸리는 이유가 달라서 따로 잡는다.

## 종류

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

TCP 3-way handshake가 끝날 때까지 기다리는 시간이다. 서버가 죽었거나 방화벽이 막고 있으면 여기서 걸린다.

```java
// RestTemplate
factory.setConnectTimeout(3000);  // 3초

// WebClient
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 3000);
```

설정하지 않으면 서버가 응답하지 않을 때 OS 기본 TCP timeout(보통 75초~2분)까지 기다린다. 연결은 정상이면 금방 맺어지니 짧게 잡는다.

### Read Timeout (Response Timeout)

TCP 연결이 맺어진 뒤 서버 응답을 기다리는 시간이다. 서버가 처리하는 데 오래 걸리면 여기서 걸린다.

```java
// RestTemplate + SimpleClientHttpRequestFactory
factory.setReadTimeout(5000);  // 5초

// RestTemplate + HttpComponentsClientHttpRequestFactory (Spring 6, HttpClient 5)
// Spring 6.0은 factory.setReadTimeout()이 아무 효과가 없고, 6.1에는 메서드가 없다. SocketConfig로 건다
SocketConfig socketConfig = SocketConfig.custom()
    .setSoTimeout(Timeout.ofSeconds(5))
    .build();

// WebClient
WebClient webClient = WebClient.builder()
    .clientConnector(new ReactorClientHttpConnector(
        HttpClient.create()
            .responseTimeout(Duration.ofSeconds(5))
    ))
    .build();
```

Read timeout은 그 API가 보통 얼마 만에 응답하는지를 보고 잡는다. 결제 API처럼 처리가 긴 곳은 넉넉하게, 단순 조회 API는 짧게 잡는다.

## API별로 따로 잡는다

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

        PoolingHttpClientConnectionManager connectionManager =
            PoolingHttpClientConnectionManagerBuilder.create()
                .setDefaultSocketConfig(SocketConfig.custom()
                    .setSoTimeout(Timeout.ofMilliseconds(readTimeout))
                    .build())
                .build();

        CloseableHttpClient httpClient = HttpClients.custom()
            .setConnectionManager(connectionManager)
            .build();

        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory(httpClient);
        factory.setConnectTimeout(connectTimeout);
        return new RestTemplate(factory);
    }
}
```

`HttpComponentsClientHttpRequestFactory`(HttpClient 5)의 `setReadTimeout`은 버전마다 다르다. Spring 6.0에서는 메서드는 있지만 아무 효과가 없다. 호출해도 컴파일은 되니, read timeout이 걸린 줄 알고 넘어가기 쉽다. 6.1에서는 메서드가 빠져서 컴파일 오류가 난다. 이 두 버전에서는 위처럼 connection manager의 `SocketConfig`로 건다. 6.2부터는 `setReadTimeout`이 다시 생겼고, 소켓 timeout이 아니라 HttpClient의 response timeout을 건다.

## Timeout이 없으면 장애가 번진다

```
사용자 → 우리 서버 (스레드 200개) → 외부 결제 API (응답 지연)

1. 결제 API가 느려짐 (평소 1초 → 30초)
2. 우리 서버의 스레드가 30초씩 대기
3. 200개 스레드가 모두 결제 API 대기 상태
4. 다른 요청 (조회, 목록 등)도 처리 불가
5. → 전체 서비스 장애
```

막으려면 아래 세 가지를 같이 쓴다.

1. Read timeout은 예상 응답 시간의 2~3배 안쪽으로 잡는다.
2. Circuit Breaker(Resilience4j 등)를 두고, 실패가 이어지면 상대를 부르지 않고 바로 실패를 돌려준다.
3. Bulkhead로 외부 API마다 스레드 풀을 나눠서, 한 API의 장애가 다른 기능으로 넘어가지 않게 한다.

```java
// Resilience4j Circuit Breaker 예시
@CircuitBreaker(name = "payment", fallbackMethod = "paymentFallback")
public PaymentResult processPayment(PaymentRequest request) {
    return paymentClient.pay(request);
}

// 회로가 열려 보내지 않은 호출만 "처리 중"으로 받아 둔다
private PaymentResult paymentFallback(PaymentRequest request, CallNotPermittedException e) {
    return PaymentResult.pending(request.orderId());
}

// timeout 등 보낸 뒤의 실패는 결과를 모르니 실패로 알린다
private PaymentResult paymentFallback(PaymentRequest request, Exception e) {
    throw new PaymentUnavailableException("결제 서비스를 지금 사용할 수 없습니다", e);
}
```

fallback을 어떻게 나누는지는 [[circuit-breaker]]에 있다.

## 서버 측 Timeout

클라이언트 timeout만 잡아서는 모자라고, 서버 쪽 timeout도 같이 맞춘다.

| 설정 | 의미 | 기본값 (Tomcat) |
|---|---|---|
| `server.tomcat.connection-timeout` | 연결을 받은 뒤 요청 줄이 올 때까지 기다리는 시간 | 60초 (Spring Boot는 값을 정하지 않아 Tomcat 기본값을 쓴다. 단독 Tomcat의 server.xml은 20초로 잡는다) |
| `spring.mvc.async.request-timeout` | 비동기 요청 처리 시간 | 30초 |
| HikariCP `connectionTimeout` | DB 커넥션 획득 대기 시간 | 30초 |

서버가 요청을 처리하는 시간이 클라이언트의 Read timeout보다 길면, 클라이언트는 이미 끊었는데 서버는 계속 처리한다. 처리 결과를 받을 쪽이 없는데 자원만 쓴다.

## 자주 깨지는 곳

- timeout을 설정하지 않으면 외부 API 하나의 장애가 서비스 전체로 번진다.
- Connection timeout과 Read timeout에 같은 값을 넣으면, 연결 실패는 늦게 알아채고 느린 처리는 너무 일찍 끊는다.
- Read timeout을 너무 짧게 잡으면 정상인 요청까지 실패한다.
- 서버 쪽 timeout을 맞추지 않으면, 클라이언트는 끊었는데 서버는 계속 처리한다.
- 모든 외부 API에 같은 timeout을 쓰면 어느 한쪽은 틀린 값이 된다. 결제와 검색은 응답 시간이 다르다.

## 한 번에 설명하기

> Timeout은 연결을 맺을 때까지의 Connection timeout, 응답을 기다리는 Read timeout, 요청을 보내는 Write timeout으로 나뉩니다. 설정하지 않으면 외부 API 하나가 느려질 때 스레드가 전부 묶여서 서비스 전체가 멈춥니다.
>
> Connection timeout은 1~3초로 짧게 두고, Read timeout은 API마다 보통 얼마 만에 응답하는지를 보고 따로 잡습니다.
>
> 여기에 Circuit Breaker와 Bulkhead를 붙여서 한 곳의 장애가 다른 기능으로 번지지 않게 합니다.

## 꼬리 질문

> [!question]- Connection timeout이 발생하는 원인은?
> 서버가 죽었거나, 방화벽이 SYN 패킷을 막거나, 중간 네트워크 경로에 문제가 있을 때입니다. DNS로 IP는 찾았는데 TCP 연결이 맺어지지 않는 상황입니다.

> [!question]- Read timeout이 발생했는데 서버에서는 처리가 완료되었다면?
> 클라이언트는 실패로 알고 있는데 서버에서는 이미 처리가 끝난 상태입니다. 결제라면 다시 보냈다가 두 번 결제될 수 있어서, 멱등키로 중복을 막거나 상태 조회 API로 실제 결과를 확인해야 합니다.

> [!question]- Circuit Breaker는 어떻게 동작하는가?
> 실패가 정해 둔 기준을 넘으면 OPEN 상태가 되어, 상대에게 요청을 보내지 않고 바로 실패를 돌려줍니다. 일정 시간이 지나면 HALF_OPEN이 되어 요청 몇 개만 보내 보고, 성공하면 CLOSED로 돌아갑니다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 타임아웃 = "모름"으로 다루기
- [[inherited-access-system-incidents|이어받은 시스템의 장애 추적]]: deadline을 늘려도 안 되면 연결을 본다

## 참고

2026년 11월에 확인한 공식 문서다.

- [Amazon Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- [Spring Framework 6.0 Javadoc: HttpComponentsClientHttpRequestFactory](https://docs.spring.io/spring-framework/docs/6.0.x/javadoc-api/org/springframework/http/client/HttpComponentsClientHttpRequestFactory.html): `setReadTimeout`이 6.0부터 효과 없음
- [Spring Framework 최신 Javadoc: HttpComponentsClientHttpRequestFactory](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/http/client/HttpComponentsClientHttpRequestFactory.html): 6.2부터 `setReadTimeout`이 response timeout을 건다

## 관련 문서

- [[01-core/network/network|network]]
- [[retry]]
- [[tcp-connection]]
- [[http-basics]]
- [[circuit-breaker]]
