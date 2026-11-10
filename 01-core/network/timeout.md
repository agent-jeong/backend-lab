---
title: "타임아웃 설계와 실무 기준"
description: Connection/Read/Write timeout의 차이와 실무 설정 기준
tags: [concept, network]
---

# 타임아웃 설계와 실무 기준

Timeout은 네트워크 요청의 각 단계에서 응답을 기다리는 최대 시간이다. 설정하지 않으면 무한정 기다리고, 그 대기가 장애를 옮긴다.

외부 API 하나가 느려지면 그 API를 기다리는 스레드가 쌓이고, 커넥션 풀이 바닥나고, 결국 상관없는 기능까지 멈춘다. 그래서 timeout은 "얼마나 기다릴까"보다 **"느린 상대 하나 때문에 우리 서버 전체가 멈추지 않게"**를 기준으로 정한다. Connection timeout과 Read timeout은 걸리는 원인이 달라서 따로 잡는다.

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

TCP 3-way handshake가 끝나기까지의 시간이다. 서버가 죽었거나 방화벽이 막고 있으면 여기서 걸린다.

```java
// RestTemplate
factory.setConnectTimeout(3000);  // 3초

// WebClient
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 3000);
```

설정하지 않으면 서버가 응답하지 않을 때 OS 기본 TCP timeout(보통 75초~2분)까지 기다린다. 그래서 짧게 잡는다.

### Read Timeout (Response Timeout)

TCP 연결이 맺어진 뒤 서버 응답을 기다리는 시간이다. 서버 처리가 오래 걸리면 여기서 걸린다.

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

Read timeout은 API의 예상 응답 시간에 맞춘다. 결제 API처럼 처리가 긴 곳은 넉넉하게, 단순 조회 API는 짧게 잡는다.

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

        HttpComponentsClientHttpRequestFactory factory =
            new HttpComponentsClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        return new RestTemplate(factory);
    }
}
```

## Timeout이 없으면 장애가 번진다

```
사용자 → 우리 서버 (스레드 200개) → 외부 결제 API (응답 지연)

1. 결제 API가 느려짐 (평소 1초 → 30초)
2. 우리 서버의 스레드가 30초씩 대기
3. 200개 스레드가 모두 결제 API 대기 상태
4. 다른 요청 (조회, 목록 등)도 처리 불가
5. → 전체 서비스 장애
```

대응은 세 가지를 같이 쓴다.

1. **Read Timeout**: 예상 응답 시간의 2~3배 이내로 잡는다.
2. **Circuit Breaker**: 연속으로 실패하면 바로 실패를 돌려준다(Resilience4j 등).
3. **Bulkhead**: 외부 API별로 스레드 풀을 나눠, 한 API의 장애가 다른 기능으로 넘어가지 않게 한다.

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

클라이언트 timeout만으로는 부족하고, 서버 측 timeout도 같이 맞춘다.

| 설정 | 의미 | 기본값 (Tomcat) |
|---|---|---|
| `server.tomcat.connection-timeout` | 요청 헤더 수신 대기 시간 | 20초 |
| `spring.mvc.async.request-timeout` | 비동기 요청 처리 시간 | 30초 |
| HikariCP `connectionTimeout` | DB 커넥션 획득 대기 시간 | 30초 |

서버의 요청 처리 시간이 클라이언트의 Read timeout보다 길면, 클라이언트는 이미 끊었는데 서버는 계속 처리한다.

## 자주 깨지는 곳

- **timeout을 설정하지 않는다.** 외부 API 장애가 전체 서비스로 번진다.
- **Connection timeout과 Read timeout에 같은 값을 넣는다.** 연결 실패는 늦게 알아채고, 느린 처리는 너무 일찍 끊는다.
- **Read timeout을 너무 짧게 잡는다.** 정상 요청까지 실패한다.
- **서버 측 timeout을 안 맞춘다.** 클라이언트는 끊었는데 서버는 계속 처리한다.
- **모든 외부 API에 같은 timeout을 쓴다.** 결제와 검색은 응답 시간이 다르다.

## 면접에서 말하기

> Timeout은 연결을 맺기까지의 Connection timeout, 응답을 기다리는 Read timeout, 요청을 보내는 Write timeout으로 나뉩니다. 설정하지 않으면 외부 API 하나가 느려질 때 스레드가 모두 묶여 전체 서비스가 멈춥니다. 저는 Connection timeout은 1~3초로 짧게, Read timeout은 API마다 예상 응답 시간을 보고 따로 잡습니다. 여기에 Circuit Breaker와 Bulkhead를 붙여 장애가 번지지 않게 합니다.

## 꼬리 질문

> [!question]- Connection timeout이 발생하는 원인은?
> 서버가 다운되었거나, 방화벽이 SYN 패킷을 차단하거나, 네트워크 경로에 문제가 있는 경우입니다. DNS는 정상이지만 TCP 연결이 수립되지 않는 상황입니다.

> [!question]- Read timeout이 발생했는데 서버에서는 처리가 완료되었다면?
> 클라이언트는 timeout으로 실패 처리했지만, 서버는 정상 처리를 완료한 상태입니다. 결제 같은 경우 중복 처리가 발생할 수 있으므로, 멱등키로 중복을 방지하거나 상태 조회 API로 결과를 확인해야 합니다.

> [!question]- Circuit Breaker는 어떻게 동작하는가?
> 연속 실패가 임계치를 넘으면 OPEN 상태로 전환되어 요청을 보내지 않고 즉시 실패를 반환합니다. 일정 시간 후 HALF_OPEN으로 전환되어 일부 요청을 시도하고, 성공하면 CLOSED로 복구합니다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: 타임아웃 = "모름"으로 다루기
- [[inherited-access-system-incidents|이어받은 출입 시스템의 장애 추적]]: deadline을 늘려도 안 되면 연결을 본다

## 관련 문서

- [[01-core/network/network|network]]
- [[retry]]
- [[tcp-connection]]
- [[http-basics]]