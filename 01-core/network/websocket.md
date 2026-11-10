---
title: WebSocket
description: WebSocket 동작 원리와 HTTP 차이, 실무 적용 패턴
tags: [concept, network]
---

# WebSocket

WebSocket은 클라이언트와 서버가 TCP 연결 하나로 양방향(full-duplex) 실시간 통신을 하는 프로토콜이다.

실시간 알림을 폴링으로 만들면 서버 부하가 커지지만, 그렇다고 모든 걸 WebSocket으로 만들 일은 아니다. 서버에서 클라이언트로만 보내면 SSE로 충분하다. WebSocket을 쓰기로 했다면 끊겼을 때의 재연결과, 서버가 여러 대일 때의 메시지 전달까지 같이 설계해야 한다. 둘 중 하나라도 빠지면 사용자가 메시지를 놓친다.

## HTTP와 다른 점

| 구분 | HTTP | WebSocket |
|---|---|---|
| 통신 방향 | 요청-응답 (단방향) | 양방향 (full-duplex) |
| 연결 | 요청마다 연결 또는 Keep-Alive | 한 번 연결 후 유지 |
| 서버 → 클라이언트 | 불가 (클라이언트가 먼저 요청) | 가능 (서버가 먼저 전송 가능) |
| 오버헤드 | 매 요청마다 헤더 전송 | 핸드셰이크 이후 프레임 단위 (헤더 최소) |
| 적합한 상황 | CRUD API, 일반 웹 요청 | 실시간 알림, 채팅, 라이브 피드 |

```
HTTP:
Client → 새 데이터 있어? → Server: 없음
Client → 새 데이터 있어? → Server: 없음
Client → 새 데이터 있어? → Server: 있음! (폴링)

WebSocket:
Client ←→ Server: 연결 유지
Server → Client: 새 데이터 발생 시 즉시 전송 (push)
```

## 핸드셰이크

WebSocket은 HTTP Upgrade 요청으로 시작한다.

```
Client → Server:
GET /ws/chat HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

Server → Client:
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

101 응답 뒤 TCP 연결이 WebSocket으로 바뀐다. 이후로는 HTTP 헤더 없이 프레임 단위로 양방향 통신을 한다.

## Spring에서 구현하기

### STOMP + WebSocket (가장 흔함)

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic", "/queue");  // 구독 경로
        registry.setApplicationDestinationPrefixes("/app");  // 전송 경로
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
            .setAllowedOrigins("https://app.example.com")
            .withSockJS();  // WebSocket 미지원 브라우저 폴백
    }
}
```

```java
@Controller
public class ChatController {

    @MessageMapping("/chat/send")        // 클라이언트 → 서버
    @SendTo("/topic/chat/room/{roomId}") // 서버 → 구독자 전체
    public ChatMessage send(ChatMessage message) {
        return message;
    }
}
```

```java
// 서버에서 특정 사용자에게 메시지 전송
@Service
public class NotificationService {

    private final SimpMessagingTemplate messagingTemplate;

    public void sendToUser(String userId, Notification notification) {
        messagingTemplate.convertAndSendToUser(
            userId, "/queue/notifications", notification
        );
    }
}
```

### STOMP 프로토콜

STOMP(Simple Text Oriented Messaging Protocol)는 WebSocket 위에서 동작하는 메시징 프로토콜이다.

| 개념 | 설명 |
|---|---|
| SUBSCRIBE | 특정 경로의 메시지를 구독 |
| SEND | 서버로 메시지 전송 |
| MESSAGE | 서버가 구독자에게 메시지 전달 |

STOMP를 쓰면 메시지를 pub/sub 패턴으로 다룰 수 있어 raw WebSocket보다 구조가 잡힌다.

## 연결 관리

### 재연결

네트워크가 불안정하거나 서버가 재시작되면 연결이 끊긴다. 클라이언트는 지수 백오프로 다시 연결한다.

```javascript
// 클라이언트 재연결 로직 (지수 백오프)
function connect() {
    const socket = new WebSocket('wss://api.example.com/ws');

    socket.onclose = () => {
        setTimeout(() => connect(), backoff());  // 재연결
    };
}
```

### Heartbeat (Ping/Pong)

연결이 살아 있는지 주기적으로 확인하고, 일정 시간 응답이 없으면 끊고 다시 연결한다.

```
Client ── PING ──▶ Server
Client ◀── PONG ── Server  (연결 정상)

Client ── PING ──▶ Server
         (응답 없음)         → 연결 끊김으로 판단, 재연결
```

STOMP에서는 `heartbeat` 설정으로 자동 관리된다.

## 서버가 여러 대일 때

WebSocket 세션은 특정 서버 인스턴스에 붙어 있다. 서버가 여러 대면 메시지가 다른 서버의 사용자에게 닿지 않는다.

```
User A ── WebSocket ──▶ Server 1
User B ── WebSocket ──▶ Server 2

User A가 메시지 전송 → Server 1에서 처리
→ User B는 Server 2에 연결되어 있어서 메시지를 못 받음
```

외부 메시지 브로커로 서버 사이에서 메시지를 중계한다.

```
User A → Server 1 → Redis Pub/Sub (또는 RabbitMQ, Kafka)
                          ↓
                     Server 2 → User B
```

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // 외부 브로커 사용 (Redis, RabbitMQ 등)
        registry.enableStompBrokerRelay("/topic", "/queue")
            .setRelayHost("redis-host")
            .setRelayPort(61613);
    }
}
```

## WebSocket, SSE, 폴링 고르기

| 방식 | 방향 | 연결 | 맞는 상황 |
|---|---|---|---|
| 폴링 (Polling) | 클라이언트 → 서버 | 반복 요청 | 간단한 구현, 실시간성 낮아도 됨 |
| SSE (Server-Sent Events) | 서버 → 클라이언트 | HTTP 유지 | 서버 → 클라이언트 단방향 (알림, 피드) |
| WebSocket | 양방향 | TCP 유지 | 양방향 실시간 (채팅, 게임) |

- 서버에서 클라이언트로만 보내면 SSE가 더 간단하다.
- 양방향 실시간이 필요하면 WebSocket을 쓴다.
- 실시간성이 중요하지 않으면 폴링이 가장 단순하다.

## 자주 깨지는 곳

- **단순 알림에 WebSocket을 쓴다.** SSE로 충분한데 구조만 복잡해진다.
- **재연결 로직이 없다.** 한 번 끊기면 복구되지 않는다.
- **인메모리 세션으로 만들고 서버를 늘린다.** 다른 서버에 붙은 사용자에게 메시지가 사라진다.
- **WebSocket 연결에 인증을 안 건다.** 누구나 접속할 수 있다.
- **Heartbeat 없이 운영한다.** 실제로는 끊겼지만 서버는 모르는 유령 연결이 쌓인다.

## 면접에서 말하기

> WebSocket은 HTTP Upgrade로 시작해서 TCP 연결 하나로 양방향 실시간 통신을 하는 프로토콜입니다. 저는 서버에서 클라이언트로만 보내면 SSE를, 채팅처럼 양방향이 필요할 때만 WebSocket을 고릅니다. Spring에서는 STOMP로 pub/sub 구조를 잡고, 서버가 여러 대면 Redis Pub/Sub 같은 외부 브로커로 메시지를 중계합니다. 재연결과 Heartbeat도 같이 둡니다.

## 꼬리 질문

> [!question]- WebSocket 연결에 인증은 어떻게 적용하는가?
> 핸드셰이크가 HTTP로 시작하므로, 이 시점에 Cookie나 토큰으로 인증합니다. Spring에서는 `HandshakeInterceptor`에서 인증을 처리하거나, STOMP CONNECT 프레임의 헤더에 토큰을 포함하는 방식을 사용합니다.

> [!question]- SSE(Server-Sent Events)는 어떻게 동작하는가?
> HTTP 연결을 유지한 채 서버가 `text/event-stream` 형식으로 데이터를 지속적으로 보냅니다. HTTP 기반이므로 CORS, 인증 등 기존 인프라를 그대로 활용할 수 있고, 브라우저가 자동 재연결을 지원합니다.

> [!question]- WebSocket은 로드밸런서를 통과할 수 있는가?
> L7 로드밸런서가 HTTP Upgrade를 지원해야 합니다. AWS ALB, Nginx 등은 WebSocket을 지원하지만, 일부 프록시는 별도 설정이 필요합니다. Sticky Session으로 같은 서버로 라우팅하거나, 외부 브로커로 서버 간 메시지를 중계해야 합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]