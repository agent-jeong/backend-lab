---
title: HTTP Basics
description: HTTP 요청/응답 구조와 메서드, 헤더, 버전별 차이
---

# HTTP Basics

## 한 줄 정의

HTTP(HyperText Transfer Protocol)는 클라이언트와 서버 간 요청-응답 기반의 무상태(stateless) 통신 프로토콜이다.

## 실무에서 왜 중요한가

HTTP를 제대로 이해하지 못하면 다음 문제가 생긴다.

- API 설계 시 메서드(GET/POST/PUT/DELETE)를 의미에 맞지 않게 사용한다.
- 캐싱이 안 되는 이유를 모르고 매번 서버 요청이 발생한다.
- Content-Type을 잘못 설정해서 요청이 파싱되지 않는다.
- HTTP/1.1과 HTTP/2의 차이를 모르고 성능 문제를 겪는다.

## HTTP 요청 구조

```
POST /api/orders HTTP/1.1        ← 요청 라인 (메서드, 경로, 버전)
Host: api.example.com            ← 헤더
Content-Type: application/json
Authorization: Bearer eyJhbG...

{"itemId": 1, "quantity": 2}     ← 바디
```

## HTTP 응답 구조

```
HTTP/1.1 201 Created             ← 상태 라인 (버전, 상태코드, 사유)
Content-Type: application/json
Location: /api/orders/42

{"orderId": 42, "status": "CREATED"}
```

## HTTP 메서드

| 메서드 | 용도 | 멱등성 | 안전성 | 바디 |
|---|---|---|---|---|
| GET | 리소스 조회 | O | O | 없음 |
| POST | 리소스 생성 | X | X | 있음 |
| PUT | 리소스 전체 교체 | O | X | 있음 |
| PATCH | 리소스 부분 수정 | X | X | 있음 |
| DELETE | 리소스 삭제 | O | X | 없음 |

### 멱등성 (Idempotency)

같은 요청을 여러 번 보내도 결과가 동일한 성질이다. GET, PUT, DELETE는 멱등이고, POST는 멱등이 아니다.

```
GET /api/orders/1    → 여러 번 호출해도 같은 결과
POST /api/orders     → 호출할 때마다 새 주문 생성
PUT /api/orders/1    → 여러 번 호출해도 같은 상태로 교체
DELETE /api/orders/1 → 이미 삭제된 상태에서 다시 호출해도 결과 동일
```

멱등성은 retry 설계의 기반이 된다. 멱등한 요청은 실패 시 안전하게 재시도할 수 있다.

## 주요 헤더

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

서버에서 Content-Type이 맞지 않으면 `415 Unsupported Media Type`이 발생한다.

## HTTP 버전 비교

### HTTP/1.1

- 커넥션당 하나의 요청-응답 처리 (Head-of-Line Blocking)
- `Keep-Alive`로 커넥션 재사용 가능
- 텍스트 기반 프로토콜

### HTTP/2

- 하나의 커넥션에서 여러 요청을 동시 처리 (Multiplexing)
- 헤더 압축 (HPACK)
- 서버 푸시 지원
- 바이너리 프로토콜

```
HTTP/1.1: 요청1 → 응답1 → 요청2 → 응답2 → 요청3 → 응답3  (순차)
HTTP/2:   요청1, 요청2, 요청3 → 응답2, 응답1, 응답3        (병렬)
```

### HTTP/3

- TCP 대신 QUIC(UDP 기반) 사용
- 연결 설정이 빠르다 (0-RTT 가능)
- 패킷 손실 시 다른 스트림에 영향 없음

대부분의 백엔드 API 서버는 HTTP/1.1 또는 HTTP/2를 사용하며, 로드밸런서나 CDN에서 HTTP/2를 처리하고 내부 통신은 HTTP/1.1을 쓰는 경우가 많다.

## 무상태(Stateless)와 세션

HTTP는 기본적으로 무상태다. 각 요청은 독립적이며, 서버는 이전 요청을 기억하지 않는다.

상태 유지가 필요하면 다음 방법을 사용한다.

| 방식 | 저장 위치 | 특징 |
|---|---|---|
| 쿠키 + 세션 | 서버 메모리/DB | 서버가 상태 관리, 스케일아웃 시 세션 공유 필요 |
| JWT | 클라이언트 (토큰) | 서버 무상태 유지, 토큰 크기가 큼 |
| OAuth 2.0 | 인증 서버 | 외부 인증 위임 |

## 자주 나는 실수

- GET 요청에 바디를 넣어서 일부 프록시/서버에서 무시된다.
- POST와 PUT을 혼용해서 멱등성 설계가 깨진다.
- Content-Type을 설정하지 않아서 요청 파싱이 실패한다.
- HTTP/2의 멀티플렉싱을 모르고 커넥션을 과도하게 생성한다.
- 캐시 헤더를 설정하지 않아서 매번 서버 요청이 발생한다.

## 핵심 요약

HTTP는 요청 라인, 헤더, 바디로 구성된 무상태 프로토콜입니다.
메서드마다 멱등성과 안전성이 다르며, 이는 retry와 캐싱 설계의 기반이 됩니다.

HTTP/2는 멀티플렉싱으로 동시 요청을 처리하고, HTTP/3는 QUIC 기반으로 연결 지연을 줄입니다.
Content-Type, Authorization, Cache-Control 등 헤더를 정확히 설정해야 정상적인 통신이 가능합니다.

## 꼬리 질문

> [!question]- GET과 POST의 차이는?
> GET은 리소스 조회용으로 멱등하고 안전하며 바디가 없습니다. POST는 리소스 생성용으로 멱등하지 않고 바디에 데이터를 담습니다. GET은 캐싱이 가능하지만 POST는 기본적으로 캐싱되지 않습니다.

> [!question]- PUT과 PATCH의 차이는?
> PUT은 리소스 전체를 교체하는 것이고 멱등합니다. PATCH는 리소스의 일부 필드만 수정하는 것이고 멱등이 보장되지 않습니다. PUT은 보내지 않은 필드가 초기화될 수 있습니다.

> [!question]- HTTP/1.1의 Head-of-Line Blocking이란?
> 하나의 커넥션에서 앞선 요청의 응답이 올 때까지 다음 요청을 보낼 수 없는 문제입니다. HTTP/2는 멀티플렉싱으로 이를 해결했지만, TCP 레벨의 HOL Blocking은 여전히 존재합니다. HTTP/3(QUIC)가 이를 완전히 해결합니다.

> [!question]- 멱등성이 왜 중요한가?
> 네트워크 장애로 응답을 받지 못했을 때, 멱등한 요청은 안전하게 재시도할 수 있습니다. 결제, 주문 같은 비멱등 요청은 멱등키(Idempotency Key)를 사용해서 중복 처리를 방지해야 합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[status-code]]
- [[timeout]]
- [[tls]]