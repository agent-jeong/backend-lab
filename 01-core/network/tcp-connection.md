---
title: "TCP 연결과 3-way 핸드셰이크"
description: TCP 3-way/4-way handshake와 커넥션 풀, keep-alive
---

# TCP 연결과 3-way 핸드셰이크

TCP(Transmission Control Protocol)는 데이터가 빠짐없이 순서대로 도착하도록 보장하는 연결 지향 프로토콜이다. 3-way handshake로 연결을 맺고 4-way handshake로 끊는다.

연결을 맺고 끊는 데는 비용이 든다. 매 요청마다 새로 연결하면 응답이 느려지고, 끊은 연결이 TIME_WAIT으로 쌓이면 포트가 고갈된다. 그래서 Keep-Alive와 커넥션 풀로 연결을 재사용한다. 외부 API에 연결 자체가 안 될 때 원인을 찾으려면 handshake가 어디서 멈췄는지 알아야 한다.

## 3-way Handshake: 연결 맺기

```
Client                     Server
  │                          │
  │─── SYN ──────────────────▶│  1. 연결 요청
  │                          │
  │◀── SYN + ACK ────────────│  2. 요청 수락 + 확인
  │                          │
  │─── ACK ──────────────────▶│  3. 확인
  │                          │
  │     연결 수립 완료          │
```

1. **SYN**: 클라이언트가 서버에 연결을 요청한다.
2. **SYN+ACK**: 서버가 요청을 수락하고 확인 응답을 보낸다.
3. **ACK**: 클라이언트가 확인 응답을 보내면 연결이 완료된다.

여기에 1.5 RTT(Round Trip Time)가 든다. 서버가 물리적으로 멀면 수십~수백ms다.

## 4-way Handshake: 연결 끊기

```
Client                     Server
  │                          │
  │─── FIN ──────────────────▶│  1. 연결 종료 요청
  │                          │
  │◀── ACK ──────────────────│  2. 종료 요청 확인
  │                          │
  │◀── FIN ──────────────────│  3. 서버도 종료 준비 완료
  │                          │
  │─── ACK ──────────────────▶│  4. 종료 확인
  │                          │
  │   TIME_WAIT (2MSL 대기)    │
```

### TIME_WAIT

연결을 먼저 끊은 쪽이 TIME_WAIT 상태에 들어간다. RFC는 2 × MSL(최대 4분)을 정의하지만, Linux는 60초로 고정되어 있다.

```bash
# TIME_WAIT 상태 확인
netstat -an | grep TIME_WAIT | wc -l
ss -s  # 요약 통계
```

TIME_WAIT이 많이 쌓이면 쓸 수 있는 로컬 포트가 모자란다.

```bash
# 커널 파라미터로 완화
net.ipv4.tcp_tw_reuse = 1          # TIME_WAIT 소켓 재사용 (나가는 연결에만 적용)
net.ipv4.ip_local_port_range = 1024 65535  # 사용 가능 포트 범위 확장
```

`tcp_tw_reuse`는 클라이언트 쪽(나가는 연결)에만 효과가 있고 TCP timestamp가 켜져 있어야 한다. 근본 해결은 커널 파라미터가 아니라 Keep-Alive와 커넥션 풀로 연결을 덜 끊는 것이다.

## Keep-Alive

HTTP/1.1의 Keep-Alive는 TCP 연결을 재사용해 요청마다 handshake를 반복하지 않게 한다. HTTP/1.1에서는 기본으로 켜져 있다.

```
Keep-Alive 없이:
요청1: SYN → SYN+ACK → ACK → HTTP 요청/응답 → FIN
요청2: SYN → SYN+ACK → ACK → HTTP 요청/응답 → FIN  (연결 다시 수립)

Keep-Alive 사용:
요청1: SYN → SYN+ACK → ACK → HTTP 요청/응답
요청2:                        HTTP 요청/응답          (연결 재사용)
요청3:                        HTTP 요청/응답          (연결 재사용)
                              FIN                     (일정 시간 후 종료)
```

## 커넥션 풀

커넥션 풀은 연결을 미리 만들어 두고 돌려 쓴다. 매번 handshake 비용을 내지 않는다.

### DB 커넥션 풀 (HikariCP)

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10       # 최대 커넥션 수
      minimum-idle: 5             # 유지할 최소 유휴 커넥션
      connection-timeout: 3000    # 커넥션 획득 대기 시간 (ms)
      max-lifetime: 1800000       # 커넥션 최대 수명 (30분)
      idle-timeout: 600000        # 유휴 커넥션 유지 시간 (10분)
```

### HTTP 클라이언트 커넥션 풀

```java
// RestTemplate 커넥션 풀 설정
HttpComponentsClientHttpRequestFactory factory =
    new HttpComponentsClientHttpRequestFactory();

PoolingHttpClientConnectionManager cm =
    new PoolingHttpClientConnectionManager();
cm.setMaxTotal(100);              // 전체 최대 커넥션
cm.setDefaultMaxPerRoute(20);     // 호스트당 최대 커넥션

CloseableHttpClient httpClient = HttpClients.custom()
    .setConnectionManager(cm)
    .build();

factory.setHttpClient(httpClient);
```

### 풀 크기 정하기

- **너무 작으면** 커넥션을 기다리느라 응답이 느려진다.
- **너무 크면** 서버 리소스(메모리, 파일 디스크립터)를 낭비하고, DB는 최대 커넥션 수 제한에 걸린다.
- 동시 요청 수, 요청당 커넥션을 쥐는 시간, 대상 서버의 최대 커넥션 수를 보고 정한다.

## TCP vs UDP

| 구분 | TCP | UDP |
|---|---|---|
| 연결 | 연결 지향 (handshake) | 비연결 |
| 신뢰성 | 보장 (재전송, 순서 보장) | 미보장 |
| 속도 | 상대적으로 느림 | 빠름 |
| 용도 | HTTP, DB 통신 | DNS 조회, 실시간 스트리밍, QUIC |

백엔드 API 통신은 대부분 TCP 위에서 돈다. HTTP/3는 UDP 기반의 QUIC를 쓰지만, 신뢰성은 프로토콜 안에서 보장한다.

## 자주 깨지는 곳

- **커넥션 풀 없이 매번 새로 연결한다.** handshake 비용을 요청마다 낸다.
- **TIME_WAIT을 모른다.** 대량 요청 뒤 포트 고갈로 연결이 안 된다.
- **풀의 max-lifetime을 안 잡는다.** 서버 쪽에서 이미 끊은 커넥션을 꺼내 쓰다 에러가 난다.
- **Keep-Alive timeout과 서버 idle timeout이 어긋난다.** 상대가 먼저 닫은 연결로 요청을 보내 연결 에러가 난다.
- **DB 커넥션 풀을 근거 없이 크게 잡는다.** DB 부하만 늘어난다.

## 면접에서 말하기

> TCP는 3-way handshake로 연결을 맺고 4-way handshake로 끊습니다. 먼저 끊은 쪽에는 TIME_WAIT이 남아서, 짧은 연결을 대량으로 만들면 포트가 고갈됩니다. 그래서 저는 Keep-Alive와 커넥션 풀로 연결을 재사용하고, 풀 크기는 동시 요청 수와 요청당 점유 시간, 대상 서버의 커넥션 제한을 보고 정합니다. max-lifetime은 서버 쪽 timeout보다 짧게 잡습니다.

## 꼬리 질문

> [!question]- TIME_WAIT은 왜 필요한가?
> 마지막 ACK가 유실되었을 때 상대방이 FIN을 재전송하면 응답할 수 있어야 하기 때문입니다. 또한 이전 연결의 패킷이 새 연결에 영향을 주지 않도록 보장합니다.

> [!question]- 커넥션 풀의 max-lifetime은 왜 설정하는가?
> DB나 프록시가 일정 시간 후 유휴 커넥션을 강제로 끊을 수 있습니다. max-lifetime을 서버 측 timeout보다 짧게 설정하면, 이미 끊긴 커넥션을 사용하는 에러를 방지할 수 있습니다.

> [!question]- 3-way handshake가 실패하면 어떻게 되는가?
> SYN을 보내고 SYN+ACK를 받지 못하면 OS가 일정 횟수 재시도 후 `Connection timed out` 에러가 발생합니다. 서버가 SYN을 거부하면 RST를 응답하고 `Connection refused` 에러가 발생합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[timeout]]
- [[tls]]