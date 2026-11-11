---
title: "TCP 연결과 3-way 핸드셰이크"
description: TCP 연결을 맺고 끊는 과정과, 연결을 다시 쓰는 Keep-Alive와 커넥션 풀
tags: [concept, network]
---

# TCP 연결과 3-way 핸드셰이크

TCP(Transmission Control Protocol)는 데이터가 빠짐없이 순서대로 도착하게 해 주는 프로토콜이다. 보내기 전에 먼저 연결을 맺는데, 3-way handshake로 맺고 4-way handshake로 끊는다.

연결을 맺고 끊는 데는 시간이 든다. 결제 API를 부를 때마다 새로 연결하면 그만큼 응답이 느려지고, 끊은 연결이 TIME_WAIT으로 쌓이면 쓸 포트가 바닥난다. 그래서 Keep-Alive와 커넥션 풀로 연결을 다시 쓴다. 외부 API에 아예 연결이 안 될 때는 handshake가 어디서 멈췄는지를 봐야 원인이 보인다.

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

연결을 맺는 데 1.5 RTT(Round Trip Time)가 든다. 서버가 물리적으로 멀면 수십~수백ms다.

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

연결을 먼저 끊은 쪽이 TIME_WAIT 상태로 들어간다. RFC는 이 시간을 2 × MSL(최대 4분)로 정해 두었지만, Linux는 60초로 고정돼 있다.

```bash
# TIME_WAIT 상태 확인
netstat -an | grep TIME_WAIT | wc -l
ss -s  # 요약 통계
```

TIME_WAIT이 많이 쌓이면 새 연결에 쓸 로컬 포트가 모자란다.

```bash
# 커널 파라미터로 완화
net.ipv4.tcp_tw_reuse = 1          # TIME_WAIT 소켓 재사용 (나가는 연결에만 적용)
net.ipv4.ip_local_port_range = 1024 65535  # 사용 가능 포트 범위 확장
```

`tcp_tw_reuse`는 클라이언트 쪽(나가는 연결)에만 효과가 있고, TCP timestamp가 켜져 있어야 동작한다. 커널 파라미터는 증상을 누를 뿐이고, 제대로 고치려면 Keep-Alive와 커넥션 풀로 연결을 덜 끊어야 한다.

## Keep-Alive

HTTP/1.1의 Keep-Alive는 TCP 연결을 끊지 않고 다음 요청에 다시 써서, 요청마다 handshake를 하지 않게 한다. HTTP/1.1에서는 기본으로 켜져 있다.

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

커넥션 풀은 연결을 미리 만들어 두고 돌려 쓴다. 그래서 요청마다 handshake를 하지 않아도 된다.

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

- 너무 작으면 요청이 커넥션을 기다리느라 응답이 느려진다.
- 너무 크면 메모리와 파일 디스크립터를 낭비하고, DB는 최대 커넥션 수 제한에 걸린다.
- 동시 요청 수, 요청당 커넥션을 쥐는 시간, 대상 서버의 최대 커넥션 수를 보고 정한다.

## TCP vs UDP

| 구분 | TCP | UDP |
|---|---|---|
| 연결 | 연결 지향 (handshake) | 비연결 |
| 신뢰성 | 보장 (재전송, 순서 보장) | 미보장 |
| 속도 | 상대적으로 느림 | 빠름 |
| 용도 | HTTP, DB 통신 | DNS 조회, 실시간 스트리밍, QUIC |

백엔드 API 통신은 대부분 TCP 위에서 돈다. HTTP/3는 UDP 위의 QUIC를 쓰지만, 재전송과 순서 맞추기는 QUIC가 직접 한다.

## 자주 깨지는 곳

- 커넥션 풀 없이 매번 새로 연결하면 요청마다 handshake 시간이 붙는다.
- 짧은 연결을 대량으로 만들고 끊으면 TIME_WAIT이 쌓여 포트가 바닥나고, 새 연결이 안 된다.
- 풀의 max-lifetime을 잡지 않으면, 서버 쪽에서 이미 끊은 커넥션을 꺼내 쓰다 에러가 난다.
- 클라이언트의 Keep-Alive timeout이 서버 idle timeout보다 길면, 상대가 먼저 닫은 연결로 요청을 보내 연결 에러가 난다.
- DB 커넥션 풀을 근거 없이 크게 잡으면 DB 부하만 늘어난다.

## 한 번에 설명하기

> TCP는 3-way handshake로 연결을 맺고 4-way handshake로 끊습니다. 먼저 끊은 쪽에는 TIME_WAIT이 남아서, 짧은 연결을 대량으로 만들면 포트가 바닥납니다.
>
> 그래서 Keep-Alive와 커넥션 풀로 연결을 다시 씁니다. 풀 크기는 동시 요청 수, 요청 하나가 커넥션을 쥐고 있는 시간, 상대 서버의 커넥션 제한을 보고 정합니다.
>
> max-lifetime은 서버 쪽 timeout보다 짧게 잡습니다.

## 꼬리 질문

> [!question]- TIME_WAIT은 왜 필요한가?
> 마지막 ACK가 유실되면 상대가 FIN을 다시 보내는데, 그때 응답해 줄 수 있어야 해서입니다. 또 늦게 도착한 이전 연결의 패킷이 같은 포트로 새로 맺은 연결에 섞여 들어가지 않게 막아 줍니다.

> [!question]- 커넥션 풀의 max-lifetime은 왜 설정하는가?
> DB나 프록시는 한동안 안 쓰인 커넥션을 자기 쪽에서 끊어 버리기도 합니다. max-lifetime을 서버 쪽 timeout보다 짧게 두면, 서버가 끊기 전에 풀이 먼저 커넥션을 바꿔서 이미 끊긴 커넥션을 쓰다 나는 에러를 막습니다.

> [!question]- 3-way handshake가 실패하면 어떻게 되는가?
> SYN을 보냈는데 SYN+ACK가 안 오면 OS가 몇 번 다시 보내 보고, 그래도 안 되면 `Connection timed out`이 납니다. 서버가 SYN을 거부해서 RST로 답하면 `Connection refused`가 납니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 9293: Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc9293)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[timeout]]
- [[tls]]