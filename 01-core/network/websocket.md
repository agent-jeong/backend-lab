---
title: WebSocket
description: WebSocket이 HTTP와 어떻게 다르고, SSE나 폴링 대신 언제 쓰며, 서버가 여러 대일 때 무엇을 챙기는지
tags: [concept, network]
---

# WebSocket

WebSocket은 TCP 연결 하나를 열어 둔 채, 클라이언트와 서버가 아무 때나 서로 메시지를 보내는(full-duplex) 프로토콜이다.

주문 상태 알림을 폴링으로 만들면 클라이언트가 몇 초마다 서버에 물어봐야 해서 서버 부하가 커진다. 그렇다고 다 WebSocket으로 만들 필요는 없다. 서버에서 클라이언트로만 보내면 SSE로 충분하다. WebSocket을 쓰기로 했다면 연결이 끊겼을 때 다시 붙는 방법과, 서버가 여러 대일 때 메시지를 다른 서버의 사용자에게 전하는 방법까지 같이 만들어야 한다. 둘 중 하나라도 빠지면 사용자가 메시지를 놓친다.

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

101 응답을 받으면 같은 TCP 연결이 WebSocket 연결이 된다. 그다음부터는 HTTP 헤더 없이 프레임 단위로 양쪽이 주고받는다.

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

    @MessageMapping("/chat/room/{roomId}/send") // 클라이언트 → 서버 (/app/chat/room/7/send)
    @SendTo("/topic/chat/room/{roomId}")         // 서버 → 그 방 구독자 전체
    public ChatMessage send(@DestinationVariable Long roomId, ChatMessage message) {
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

STOMP(Simple Text Oriented Messaging Protocol)는 WebSocket 위에서 메시지를 주고받는 규칙을 정한 프로토콜이다.

| 개념 | 설명 |
|---|---|
| SUBSCRIBE | 특정 경로의 메시지를 구독 |
| SEND | 서버로 메시지 전송 |
| MESSAGE | 서버가 구독자에게 메시지 전달 |

STOMP를 쓰면 경로를 구독하고 그 경로로 발행하는 pub/sub 방식으로 메시지를 다룰 수 있다. raw WebSocket으로 메시지 종류와 수신자를 직접 나누는 것보다 정리가 쉽다.

## 연결 관리

### 재연결

네트워크가 불안정하거나 서버가 재시작되면 연결이 끊긴다. 클라이언트는 지수 백오프로 간격을 늘려 가며 다시 연결한다.

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

연결이 살아 있는지 주기적으로 확인하고, 한동안 응답이 없으면 끊고 다시 연결한다.

```
Client ── PING ──▶ Server
Client ◀── PONG ── Server  (연결 정상)

Client ── PING ──▶ Server
         (응답 없음)         → 연결 끊김으로 판단, 재연결
```

STOMP에서는 `heartbeat`를 설정하면 이걸 알아서 해 준다.

## 서버가 여러 대일 때

WebSocket 세션은 연결을 받은 서버 한 대에만 있다. 서버가 여러 대면 한 서버에서 보낸 메시지가 다른 서버에 붙은 사용자에게 닿지 않는다.

```
User A ── WebSocket ──▶ Server 1
User B ── WebSocket ──▶ Server 2

User A가 메시지 전송 → Server 1에서 처리
→ User B는 Server 2에 연결되어 있어서 메시지를 못 받음
```

그래서 외부 메시지 브로커를 두고 서버끼리 메시지를 넘겨준다.

```
User A → Server 1 → 외부 메시지 브로커 (RabbitMQ 등). Redis Pub/Sub을 쓰려면 중계 코드를 직접 짠다
                          ↓
                     Server 2 → User B
```

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // STOMP를 지원하는 외부 브로커로 중계한다 (RabbitMQ STOMP 플러그인, ActiveMQ 등)
        // Redis는 STOMP를 지원하지 않으므로 여기 쓸 수 없다
        registry.enableStompBrokerRelay("/topic", "/queue")
            .setRelayHost("rabbitmq-host")
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
- 채팅처럼 양쪽이 실시간으로 주고받아야 하면 WebSocket을 쓴다.
- 몇 초 늦어도 괜찮으면 폴링이 가장 단순하다.

## 자주 깨지는 곳

- 단순 알림에 WebSocket을 쓰면, SSE로 충분한 일에 구조만 복잡해진다.
- 재연결 로직이 없으면 한 번 끊긴 연결이 다시 붙지 않는다.
- 세션을 서버 메모리에만 두고 서버를 늘리면, 다른 서버에 붙은 사용자에게 가야 할 메시지가 사라진다.
- WebSocket 연결에 인증을 걸지 않으면 누구나 접속할 수 있다.
- Heartbeat 없이 운영하면, 실제로는 끊겼는데 서버는 모르는 연결이 계속 쌓인다.

## 한 번에 설명하기

> WebSocket은 HTTP Upgrade 요청으로 시작해서, TCP 연결 하나로 양쪽이 실시간으로 주고받는 프로토콜입니다. 서버에서 클라이언트로만 보내면 SSE를 쓰고, 채팅처럼 양쪽이 주고받아야 할 때만 WebSocket을 고릅니다.
>
> Spring에서는 STOMP로 pub/sub 구조를 잡고, 서버가 여러 대면 RabbitMQ 같은 외부 STOMP 브로커로 서버끼리 메시지를 넘깁니다. Redis Pub/Sub을 쓰려면 STOMP 중계가 아니라 서버가 직접 구독해서 다시 뿌리는 코드를 짭니다.
>
> 연결이 끊길 때를 대비해 재연결과 Heartbeat도 같이 둡니다.

## 꼬리 질문

> [!question]- WebSocket 연결에 인증은 어떻게 적용하는가?
> 핸드셰이크는 HTTP 요청이라서, 이때 Cookie나 토큰으로 인증합니다. Spring에서는 `HandshakeInterceptor`에서 인증하거나, STOMP CONNECT 프레임 헤더에 토큰을 실어 보냅니다.

> [!question]- SSE(Server-Sent Events)는 어떻게 동작하는가?
> HTTP 연결을 열어 둔 채 서버가 `text/event-stream` 형식으로 데이터를 계속 흘려보냅니다. 그냥 HTTP라서 CORS나 인증을 기존 방식 그대로 쓸 수 있고, 끊기면 브라우저가 알아서 다시 연결합니다.

> [!question]- WebSocket은 로드밸런서를 통과할 수 있는가?
> L7 로드밸런서가 HTTP Upgrade를 지원하면 통과합니다. AWS ALB나 Nginx는 지원하지만, 따로 설정해야 하는 프록시도 있습니다. 그리고 Sticky Session으로 같은 사용자를 같은 서버로 보내거나, 외부 브로커로 서버끼리 메시지를 넘겨줘야 합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]