---
title: "TCP 연결과 3-way 핸드셰이크"
description: TCP 3-way/4-way handshake와 커넥션 풀, keep-alive
---

# TCP 연결과 3-way 핸드셰이크

## 한 줄 정의

TCP(Transmission Control Protocol)는 신뢰성 있는 데이터 전송을 보장하는 연결 지향 프로토콜로, 3-way handshake로 연결을 수립하고 4-way handshake로 종료한다.

## 실무에서 왜 중요한가

TCP 연결을 이해하지 못하면 다음 문제가 생긴다.

- 매 요청마다 TCP 연결을 새로 맺어서 응답 시간이 느리다.
- 커넥션 풀을 설정했는데 TIME_WAIT이 쌓여서 포트가 고갈된다.
- Keep-Alive를 모르고 커넥션을 계속 새로 생성한다.
- 외부 API 호출 시 연결 자체가 안 되는데 원인을 못 찾는다.

## TCP 3-way Handshake (연결 수립)

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

1. **SYN**: 클라이언트가 서버에 연결 요청
2. **SYN+ACK**: 서버가 요청을 수락하고 확인 응답
3. **ACK**: 클라이언트가 확인 응답을 보내고 연결 완료

이 과정에 1.5 RTT(Round Trip Time)가 소요된다. 서버가 물리적으로 멀면 수십~수백ms가 걸린다.

## TCP 4-way Handshake (연결 종료)

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

연결을 먼저 종료한 쪽에 TIME_WAIT 상태가 발생한다. 보통 60초(2 × MSL) 동안 유지된다.

```bash
# TIME_WAIT 상태 확인
netstat -an | grep TIME_WAIT | wc -l
ss -s  # 요약 통계
```

TIME_WAIT이 많으면 사용 가능한 로컬 포트가 부족해질 수 있다.

```bash
# 커널 파라미터로 완화
net.ipv4.tcp_tw_reuse = 1          # TIME_WAIT 소켓 재사용
net.ipv4.ip_local_port_range = 1024 65535  # 사용 가능 포트 범위 확장
```

## Keep-Alive

HTTP/1.1의 Keep-Alive는 TCP 연결을 재사용해서 매 요청마다 handshake를 반복하지 않게 한다.

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

HTTP/1.1에서는 기본적으로 Keep-Alive가 활성화되어 있다.

## 커넥션 풀 (Connection Pool)

매번 TCP 연결을 새로 맺으면 handshake 비용이 발생한다. 커넥션 풀은 미리 연결을 만들어두고 재사용한다.

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

### 커넥션 풀 사이즈 결정 기준

- **너무 작으면**: 대기(waiting)가 발생하고 응답 시간이 느려진다
- **너무 크면**: 서버 리소스(메모리, 파일 디스크립터)를 낭비하고, DB는 커넥션 수 제한에 걸린다
- **기준**: 동시 요청 수, 요청당 점유 시간, 대상 서버의 최대 커넥션 수를 고려

## TCP vs UDP

| 구분 | TCP | UDP |
|---|---|---|
| 연결 | 연결 지향 (handshake) | 비연결 |
| 신뢰성 | 보장 (재전송, 순서 보장) | 미보장 |
| 속도 | 상대적으로 느림 | 빠름 |
| 용도 | HTTP, DB 통신 | DNS 조회, 실시간 스트리밍, QUIC |

백엔드 API 통신은 대부분 TCP 기반이다. HTTP/3는 UDP 기반의 QUIC를 사용하지만, 프로토콜 내부에서 신뢰성을 보장한다.

## 자주 나는 실수

- 커넥션 풀 없이 매번 새 연결을 맺어서 handshake 오버헤드가 반복된다.
- TIME_WAIT을 모르고 대량 요청 후 포트 고갈 문제를 겪는다.
- 커넥션 풀의 max-lifetime을 설정하지 않아서 서버 측에서 끊긴 커넥션을 사용한다.
- Keep-Alive timeout과 서버 측 idle timeout이 맞지 않아서 연결 에러가 발생한다.
- DB 커넥션 풀 사이즈를 근거 없이 크게 설정해서 DB 부하가 증가한다.

## 핵심 요약

TCP는 3-way handshake로 연결을 수립하고, 4-way handshake로 종료합니다.
연결을 먼저 종료한 쪽에 TIME_WAIT이 발생하며, 대량 요청 시 포트 고갈의 원인이 됩니다.

Keep-Alive로 연결을 재사용하고, 커넥션 풀로 미리 연결을 만들어두면 handshake 비용을 줄일 수 있습니다.
풀 사이즈는 동시 요청 수, 요청 점유 시간, 대상 서버 제한을 고려해서 설정해야 합니다.

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