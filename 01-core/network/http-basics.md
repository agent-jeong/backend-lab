---
title: "HTTP 기초와 요청/응답 구조"
description: HTTP 요청/응답 구조와 메서드, 헤더, 버전별 차이
tags: [concept, network]
---

# HTTP 기초와 요청/응답 구조

HTTP(HyperText Transfer Protocol)는 클라이언트와 서버가 요청-응답으로 주고받는 무상태(stateless) 통신 프로토콜이다.

API 설계의 기본기는 여기서 나온다. 메서드를 의미대로 쓰지 않으면 멱등성이 깨져 재시도가 위험해지고, Content-Type이 틀리면 요청이 파싱되지 않고, 캐시 헤더가 없으면 매번 서버까지 간다. HTTP/1.1과 HTTP/2의 차이를 모르면 커넥션을 쓸데없이 많이 만든다.

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

retry 설계는 멱등성에서 출발한다. 멱등한 요청은 실패하면 그대로 다시 보내도 된다.

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

대부분의 백엔드 API 서버는 HTTP/1.1이나 HTTP/2를 쓴다. 로드밸런서나 CDN이 바깥쪽 HTTP/2를 받고, 내부 통신은 HTTP/1.1로 하는 구성이 흔하다.

## 무상태(Stateless)와 세션

HTTP는 기본적으로 무상태다. 요청은 서로 독립적이고, 서버는 이전 요청을 기억하지 않는다. 상태가 필요하면 아래 중 하나를 쓴다.

| 방식 | 저장 위치 | 특징 |
|---|---|---|
| 쿠키 + 세션 | 서버 메모리/DB | 서버가 상태 관리, 스케일아웃 시 세션 공유 필요 |
| JWT | 클라이언트 (토큰) | 서버 무상태 유지, 토큰 크기가 큼 |
| OAuth 2.0 | 인증 서버 | 외부 인증 위임 |

## 자주 깨지는 곳

- **GET 요청에 바디를 넣는다.** 일부 프록시나 서버가 바디를 버린다.
- **POST와 PUT을 섞어 쓴다.** 멱등성 설계가 깨져 재시도가 위험해진다.
- **Content-Type을 안 넣는다.** 서버가 바디를 파싱하지 못한다.
- **HTTP/2 멀티플렉싱을 모르고 커넥션을 과하게 만든다.**
- **캐시 헤더를 안 준다.** 같은 리소스를 매번 서버에 다시 묻는다.

## 한 번에 설명하기

> HTTP는 요청 라인, 헤더, 바디로 이뤄진 무상태 프로토콜입니다. 메서드마다 멱등성과 안전성이 다르고, 저는 이걸 기준으로 어떤 요청을 재시도하고 캐싱할지 정합니다. HTTP/2는 커넥션 하나에서 여러 요청을 동시에 처리하고, HTTP/3는 QUIC 위에서 연결 지연과 패킷 유실 영향을 줄입니다.

## 꼬리 질문

> [!question]- GET과 POST의 차이는?
> GET은 리소스 조회용으로 멱등하고 안전하며 바디가 없습니다. POST는 리소스 생성용으로 멱등하지 않고 바디에 데이터를 담습니다. GET은 캐싱이 가능하지만 POST는 기본적으로 캐싱되지 않습니다.

> [!question]- PUT과 PATCH의 차이는?
> PUT은 리소스 전체를 교체하는 것이고 멱등합니다. PATCH는 리소스의 일부 필드만 수정하는 것이고 멱등이 보장되지 않습니다. PUT은 보내지 않은 필드가 초기화될 수 있습니다.

> [!question]- HTTP/1.1의 Head-of-Line Blocking이란?
> 하나의 커넥션에서 앞선 요청의 응답이 올 때까지 다음 요청을 보낼 수 없는 문제입니다. HTTP/2는 멀티플렉싱으로 이를 해결했지만, TCP 레벨의 HOL Blocking은 여전히 존재합니다. HTTP/3(QUIC)는 스트림마다 독립적으로 전송해서, 패킷 하나가 유실돼도 다른 스트림은 멈추지 않습니다.

> [!question]- 멱등성이 왜 중요한가?
> 네트워크 장애로 응답을 받지 못했을 때, 멱등한 요청은 안전하게 재시도할 수 있습니다. 결제, 주문 같은 비멱등 요청은 멱등키(Idempotency Key)를 사용해서 중복 처리를 방지해야 합니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)

## 관련 문서

- [[01-core/network/network|network]]
- [[status-code]]
- [[timeout]]
- [[tls]]
