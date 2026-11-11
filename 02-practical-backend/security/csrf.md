---
title: CSRF
description: 브라우저가 쿠키를 알아서 붙여 보내는 점을 노린 요청 위조와, 서버에서 막는 방법
tags: [concept, security]
---

# CSRF

CSRF는 로그인한 브라우저가 인증 쿠키를 알아서 붙여 보낸다는 점을 노려, 사용자가 하지도 않은 요청을 서버에 보내게 만드는 공격이다. 사용자는 공격 페이지를 열기만 해도 요청이 나간다.

조회는 크게 문제가 안 된다. 위험한 건 주문, 결제, 비밀번호 변경, 이메일 변경처럼 상태를 바꾸는 API다. 사용자가 누른 적도 없는 주문 취소가 처리될 수 있다.

## 공격이 성립하는 순서

1. 사용자가 서비스에 로그인해 인증 쿠키를 갖고 있다.
2. 공격자가 사용자의 브라우저로 특정 상태 변경 요청을 보내게 만든다.
3. 브라우저는 조건에 따라 그 요청에 인증 쿠키를 붙인다.
4. 서버가 요청의 출처나 CSRF token을 확인하지 않으면 정상 사용자 요청으로 처리한다.

그래서 서버는 상태를 바꾸는 요청에서 token, Origin, SameSite 정책을 함께 검사한다.

```http
POST /orders/123/cancel HTTP/1.1
Cookie: SESSION=...
X-CSRF-TOKEN: token-from-server
```

쿠키로 인증한다면, 상태를 바꾸는 요청에서는 쿠키 말고도 사용자가 정말 보낸 요청인지 확인할 값을 하나 더 검사한다.

## 상황별 대응

| 상황 | 대응 | 이유 |
|---|---|---|
| 쿠키 기반 세션 인증 | CSRF token 또는 SameSite 설정 | 브라우저 자동 쿠키 전송을 제어한다 |
| 상태 변경 요청 | POST/PUT/PATCH/DELETE 보호 | 사용자 의도가 중요한 요청이다 |
| Authorization header 기반 API | CSRF 위험 낮음 | 브라우저가 임의 header를 자동으로 붙이지 않는다 |
| 외부 도메인 form 요청 차단 | Origin/Referer 검증 | token 외 추가 방어선이 된다 |
| SameSite=None | Secure 필수 | cross-site 쿠키 전송 위험을 명시적으로 다룬다 |

Authorization header로 인증하는 API는 CSRF 위험이 상대적으로 낮다. 그 대신 토큰을 어디에 저장하느냐에 따라 다른 위험이 생긴다.

| 대응 | 장점 | 약한 곳 |
|---|---|---|
| CSRF token | 요청이 우리 화면에서 나왔는지 확인한다 | 토큰 발급과 검증 흐름이 필요하다 |
| SameSite cookie | 브라우저 수준에서 cross-site 전송을 줄인다 | 혼자서 모든 환경과 요구사항을 해결하지 못한다 |
| Origin 검증 | 구현이 비교적 단순하다 | 요청에 따라 header가 없거나 프록시 영향을 받는다 |

## 자주 깨지는 곳

- CORS를 설정했으니 CSRF도 막혔다고 여기면 뚫린다. CORS는 다른 출처에서 응답을 읽을 수 있는지만 정한다. form 전송 같은 단순 요청은 CORS 설정과 상관없이 그대로 나간다.
- GET 요청으로 상태를 바꾸면, 링크나 이미지 태그 하나만으로 상태가 바뀐다. GET은 상태를 바꾸지 않아야 한다.
- SameSite 기본값만 믿고 브라우저나 환경마다 다른 동작을 확인하지 않으면, 어떤 환경에서는 쿠키가 그대로 붙어 나간다.
- CSRF token을 쿠키에만 넣고 요청 값과 비교하지 않으면 방어가 안 된다. 쿠키는 공격 요청에도 자동으로 붙는다.
- JSON API라서 CSRF가 불가능하다고 단정하면, 실제로 그런지 확인하지 않은 채 방어를 빼게 된다.

## 확인하는 법

- 테스트: 인증 쿠키가 있는 상태에서 외부 origin의 상태 변경 요청이 거부되는지 본다.
- 테스트: CSRF token이 없거나 다른 요청이 실패하는지 본다.
- 코드 리뷰: GET 요청이 상태를 바꾸지 않는지 확인한다.
- 보안 점검: 쿠키의 SameSite, Secure, HttpOnly 설정을 확인한다.

## 한 번에 설명하기

> CSRF는 브라우저가 인증 쿠키를 자동으로 붙여 보내는 점을 노려서, 사용자가 의도하지 않은 상태 변경 요청을 보내게 하는 공격입니다. CORS는 응답을 읽을 수 있는지를 정하는 것이라 CSRF 방어와는 목적이 다릅니다.
>
> 쿠키로 인증한다면 상태를 바꾸는 요청에 CSRF token, SameSite, Origin 검사를 같이 두고, GET으로는 상태를 바꾸지 않게 합니다.
>
> Authorization header 방식은 CSRF 위험은 낮지만, 토큰을 어디에 저장하느냐에 따른 위험을 따로 봅니다.

## 꼬리 질문

- CORS와 CSRF는 어떤 점이 다른가?
- 쿠키 기반 인증에서 CSRF를 어떻게 막나?
- GET 요청으로 상태를 바꾸면 왜 위험한가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Spring Security: CSRF](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html)

## 관련 문서

- [[security]]
- [[session-and-token]]
- [[01-core/network/cors|cors]]
