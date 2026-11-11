---
title: "HTTP 기초와 요청/응답 구조"
description: HTTP 요청과 응답이 어떻게 생겼는지, 메서드와 헤더, 버전별로 무엇이 다른지
tags: [concept, network]
---

# HTTP 기초와 요청/응답 구조

HTTP(HyperText Transfer Protocol)는 클라이언트가 요청을 보내고 서버가 응답하는 방식으로 통신하는 프로토콜이다. 서버는 요청마다 따로 처리하고 이전 요청을 기억하지 않는다(stateless).

API를 만들 때 고르는 것 대부분이 HTTP에서 나온다. 주문 생성을 PUT으로 만드는 식으로 메서드를 뜻과 다르게 쓰면 재시도했을 때 주문이 두 번 생길 수 있고, Content-Type이 틀리면 서버가 바디를 읽지 못하고, 캐시 헤더가 없으면 같은 요청이 매번 서버까지 간다. HTTP/1.1과 HTTP/2가 어떻게 다른지 모르면 커넥션을 쓸데없이 많이 만든다.

## 요청과 응답

```
POST /api/orders HTTP/1.1        ← 요청 라인 (메서드, 경로, 버전)
Host: api.example.com            ← 헤더
Content-Type: application/json
Authorization: Bearer eyJhbG...

{"itemId": 1, "quantity": 2}     ← 바디
```

```
HTTP/1.1 201 Created             ← 상태 라인 (버전, 상태코드, 사유)
Content-Type: application/json
Location: /api/orders/42

{"orderId": 42, "status": "CREATED"}
```

## 메서드

| 메서드 | 용도 | 멱등성 | 안전성 | 바디 |
|---|---|---|---|---|
| GET | 리소스 조회 | O | O | 없음 |
| POST | 리소스 생성 | X | X | 있음 |
| PUT | 리소스 전체 교체 | O | X | 있음 |
| PATCH | 리소스 부분 수정 | X | X | 있음 |
| DELETE | 리소스 삭제 | O | X | 없음 |

### 멱등성 (Idempotency)

같은 요청을 여러 번 보내도 결과가 같은 성질이다. GET, PUT, DELETE는 멱등이고 POST는 아니다.

```
GET /api/orders/1    → 여러 번 호출해도 같은 결과
POST /api/orders     → 호출할 때마다 새 주문 생성
PUT /api/orders/1    → 여러 번 호출해도 같은 상태로 교체
DELETE /api/orders/1 → 이미 삭제된 상태에서 다시 호출해도 결과 동일
```

재시도해도 되는지는 멱등성으로 판단한다. 멱등한 요청은 실패하면 그대로 다시 보내도 된다.

## 헤더

### 요청 헤더

| 헤더 | 용도 | 예시 |
|---|---|---|
| `Content-Type` | 요청 바디 형식 | `application/json` |
| `Accept` | 원하는 응답 형식 | `application/json` |
| `Authorization` | 인증 정보 | `Bearer <token>` |
| `Cache-Control` | 캐시 제어 | `no-cache` |

### 응답 헤더

| 헤더 | 용도 | 예시 |
|---|---|---|
| `Content-Type` | 응답 바디 형식 | `application/json` |
| `Cache-Control` | 캐시 정책 | `max-age=3600` |
| `Location` | 생성된 리소스 위치 | `/api/orders/42` |
| `Set-Cookie` | 쿠키 설정 | `sessionId=abc; HttpOnly` |

### Content-Type과 직렬화

```
Content-Type: application/json           → JSON 바디
Content-Type: application/x-www-form-urlencoded → key=value&key2=value2
Content-Type: multipart/form-data        → 파일 업로드
```

서버가 받을 수 없는 Content-Type이면 `415 Unsupported Media Type`이 난다.

## 버전별 차이

**HTTP/1.1**
- 커넥션 하나에서 요청-응답을 하나씩 처리한다(Head-of-Line Blocking).
- `Keep-Alive`로 커넥션을 재사용한다.
- 텍스트 기반 프로토콜이다.

**HTTP/2**
- 커넥션 하나에서 여러 요청을 동시에 처리한다(Multiplexing).
- 헤더를 압축한다(HPACK).
- 서버 푸시를 지원한다.
- 바이너리 프로토콜이다.

```
HTTP/1.1: 요청1 → 응답1 → 요청2 → 응답2 → 요청3 → 응답3  (순차)
HTTP/2:   요청1, 요청2, 요청3 → 응답2, 응답1, 응답3        (병렬)
```

**HTTP/3**
- TCP 대신 QUIC(UDP 기반)을 쓴다.
- 연결 설정이 빠르다(0-RTT 가능).
- 패킷이 유실돼도 다른 스트림은 영향을 받지 않는다.

백엔드 API 서버는 대부분 HTTP/1.1이나 HTTP/2를 쓴다. 바깥에서 오는 HTTP/2는 로드밸런서나 CDN이 받고, 그 안쪽은 HTTP/1.1로 통신하는 구성이 흔하다.

## 무상태(Stateless)와 세션

HTTP는 기본으로 무상태다. 요청은 서로 따로 처리되고, 서버는 이전 요청을 기억하지 않는다. 로그인처럼 상태가 필요하면 아래 중 하나를 쓴다.

| 방식 | 저장 위치 | 특징 |
|---|---|---|
| 쿠키 + 세션 | 서버 메모리/DB | 서버가 상태 관리, 스케일아웃 시 세션 공유 필요 |
| JWT | 클라이언트 (토큰) | 서버 무상태 유지, 토큰 크기가 큼 |
| OAuth 2.0 | 인증 서버 | 외부 인증 위임 |

## 자주 깨지는 곳

- GET 요청에 바디를 넣으면 일부 프록시나 서버가 바디를 버린다.
- POST와 PUT을 뜻과 상관없이 섞어 쓰면, 어떤 요청을 다시 보내도 되는지 판단할 수 없어 재시도가 위험해진다.
- Content-Type을 넣지 않으면 서버가 바디를 파싱하지 못한다.
- HTTP/2는 커넥션 하나로 여러 요청을 동시에 보내는데, 이걸 모르고 HTTP/1.1처럼 커넥션을 많이 만들면 자원만 낭비한다.
- 캐시 헤더를 주지 않으면 같은 리소스를 매번 서버에 다시 묻는다.

## 한 번에 설명하기

> HTTP는 요청 라인, 헤더, 바디로 이뤄지고, 서버가 이전 요청을 기억하지 않는 무상태 프로토콜입니다.
>
> 메서드마다 멱등한지, 안전한지가 다르고, 저는 이걸 보고 어떤 요청을 재시도하고 어떤 응답을 캐싱할지 정합니다.
>
> HTTP/2는 커넥션 하나에서 여러 요청을 동시에 처리하고, HTTP/3는 QUIC 위에서 돌아서 연결을 맺는 시간과 패킷 유실의 영향을 줄입니다.

## 꼬리 질문

> [!question]- GET과 POST의 차이는?
> GET은 조회용이라 여러 번 보내도 결과가 같고 서버 상태도 바꾸지 않으며, 바디가 없습니다. POST는 생성용이라 보낼 때마다 새로 만들어지고, 데이터는 바디에 담습니다. GET 응답은 캐싱할 수 있지만 POST는 기본으로 캐싱되지 않습니다.

> [!question]- PUT과 PATCH의 차이는?
> PUT은 리소스 전체를 갈아 끼우는 거라 멱등합니다. PATCH는 일부 필드만 고치는 거라 멱등하다고 장담할 수 없습니다. PUT으로 보낼 때 빠뜨린 필드는 초기화될 수 있습니다.

> [!question]- HTTP/1.1의 Head-of-Line Blocking이란?
> 커넥션 하나에서 앞 요청의 응답이 올 때까지 다음 요청을 보내지 못하는 문제입니다. HTTP/2는 멀티플렉싱으로 이걸 풀었지만, TCP 단에서 생기는 HOL Blocking은 그대로 남아 있습니다. HTTP/3(QUIC)는 스트림마다 따로 전송해서, 패킷 하나가 유실돼도 다른 스트림은 멈추지 않습니다.

> [!question]- 멱등성이 왜 중요한가?
> 네트워크 장애로 응답을 못 받았을 때, 멱등한 요청은 그냥 다시 보내면 됩니다. 결제나 주문처럼 멱등하지 않은 요청은 멱등키(Idempotency Key)를 붙여서 두 번 처리되지 않게 막아야 합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)

## 관련 문서

- [[01-core/network/network|network]]
- [[status-code]]
- [[timeout]]
- [[tls]]
- [[rest-api-design]]
