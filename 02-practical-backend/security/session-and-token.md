---
title: Session과 Token
description: 로그인 상태를 서버에 두는 세션과 클라이언트가 들고 다니는 토큰의 차이, 고르는 기준
tags: [concept, security]
---

# Session과 Token

Session은 로그인 상태를 서버에 저장하고, 클라이언트는 세션 id만 들고 다니는 방식이다. Token은 로그인 정보를 서명된 값으로 만들어 클라이언트가 요청마다 보내는 방식이다.

로그인 상태를 어디에 두느냐에 따라 로그아웃을 어떻게 처리할지, 서버를 늘릴 때 무엇이 필요한지, 탈취됐을 때 어떻게 막을지가 달라진다. 그래서 고를 때는 확장성보다 만료, 탈취, 로그아웃, 권한 변경을 어떻게 처리할지를 먼저 본다.

## 동작

1. 사용자가 로그인하면 서버가 인증 정보를 검증한다.
2. 세션 방식은 서버 저장소에 로그인 상태를 저장하고 세션 id를 쿠키로 보낸다.
3. 토큰 방식은 사용자 식별자, 만료 시간, 권한 정보를 담은 서명된 토큰을 발급한다.
4. 이후 요청에서 세션 id나 토큰을 검증해 인증된 사용자 정보를 만든다.
5. 만료, 로그아웃, 권한 변경, 토큰 탈취 상황에 맞춰 무효화 정책을 적용한다.

```java
public AuthenticatedUser authenticate(String accessToken) {
    TokenClaims claims = tokenVerifier.verify(accessToken);

    if (claims.isExpired()) {
        throw new UnauthorizedException("expired token");
    }

    return new AuthenticatedUser(claims.userId(), claims.roles());
}
```

토큰을 검증할 때는 서명, 만료 시간, 발급자, audience를 함께 확인한다. payload를 decode만 하는 것은 인증이 아니다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 서버에서 강제 로그아웃이 중요 | Session | 서버 상태를 삭제해 즉시 차단할 수 있다 |
| 여러 서비스가 독립적으로 검증 | Token | 서명 검증만으로 인증 정보를 확인할 수 있다 |
| 브라우저 기반 서비스 | HttpOnly Secure Cookie | 스크립트 탈취 위험을 줄인다 |
| 모바일 앱 API | Access Token + Refresh Token | 짧은 access token과 재발급 흐름을 분리한다 |
| 권한이 자주 바뀜 | 짧은 만료 또는 서버 검증 병행 | 오래된 토큰 권한이 남는 문제를 줄인다 |

| 방식 | 장점 | 약한 곳 |
|---|---|---|
| Session | 서버에서 인증 상태를 통제하기 쉽다 | 세션 저장소와 확장성 설계가 필요하다. 인스턴스가 여러 대면 공유 저장소나 sticky session이 필요하다 |
| Token | stateless 검증이 가능하고 서비스 간 전달이 쉽다 | 발급 뒤 강제 무효화와 권한 변경 반영이 어렵다 |
| Cookie | 브라우저 자동 전송과 HttpOnly 보호를 쓸 수 있다 | CSRF 대응이 필요하다 |
| Authorization Header | API 클라이언트에서 명시적으로 제어하기 쉽다 | 클라이언트 저장소에서 탈취될 수 있다 |

## 자주 깨지는 곳

- JWT를 쓰면 로그아웃이 저절로 해결된다고 여기면, 로그아웃한 뒤에도 토큰이 살아 있다. 발급한 토큰은 만료 전까지 유효하므로 강제 무효화는 따로 설계해야 한다.
- token payload에 민감 정보를 넣으면 누구나 읽는다. 서명만 한 JWT(JWS)의 payload는 암호화가 아니라 base64url 인코딩이라 누구나 읽는다.
- access token 만료 시간을 너무 길게 두면, 탈취되거나 권한이 바뀌어도 그 토큰이 오래 쓰인다.
- refresh token을 access token처럼 매 요청에 보내면, 오래 사는 토큰이 노출될 경로가 늘어난다.
- access token, refresh token, session cookie가 각각 무슨 일을 하는지 섞어 쓰면, 만료와 재발급 정책이 꼬인다.
- 쿠키를 쓰면서 CSRF를 막지 않으면, 다른 사이트에서 보낸 요청에도 로그인 상태가 따라간다.

## 확인하는 법

- 테스트: 만료된 세션이나 토큰으로 요청하면 인증 실패가 나는지 본다.
- 테스트: 로그아웃 뒤 기존 인증 정보가 다시 쓰이지 않는지 본다.
- 로그: 로그인, 재발급, 로그아웃, 인증 실패 사유를 남긴다.
- 보안 리뷰: 쿠키 옵션, 토큰 만료 시간, refresh token 저장 위치를 확인한다.

## 한 번에 설명하기

> Session은 로그인 상태를 서버가 들고 있고, Token은 서명된 로그인 정보를 클라이언트가 들고 다닙니다.
>
> 세션은 강제 로그아웃이 쉽지만 저장소와 서버를 늘릴 때의 설계가 필요하고, 토큰은 서버에 상태 없이 검증할 수 있지만 발급한 뒤에는 무효화하거나 바뀐 권한을 반영하기 어렵습니다. 그래서 확장성보다 만료, 탈취, 로그아웃, 권한 변경에 어떻게 대응할지를 기준으로 고릅니다.
>
> 서명만 한 JWT의 payload는 인코딩일 뿐이라 민감 정보를 넣지 않고, 쿠키를 쓰면 CSRF와 쿠키 옵션을 같이 봅니다.

## 꼬리 질문

- Session과 Token 방식의 가장 큰 차이는?
- JWT 로그아웃은 왜 단순하지 않은가?
- access token과 refresh token의 역할은 어떻게 나누나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [RFC 7519: JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)

## 관련 문서

- [[02-practical-backend/security/security|security]]
- [[authentication-and-authorization]]
- [[authorization-check-location]]
- [[oauth2-and-oidc]]
- [[01-core/network/http-basics|http-basics]]
