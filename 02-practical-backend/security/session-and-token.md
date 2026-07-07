---
title: Session과 Token
description: 서버 세션과 토큰 기반 인증의 차이와 선택 기준
---

# Session과 Token

## 한 줄 정의

Session은 인증 상태를 서버에 저장하고 클라이언트가 세션 id를 들고 다니는 방식이며, Token은 인증 정보를 서명된 값으로 만들어 클라이언트가 요청마다 전달하는 방식이다.

## 실무에서 왜 문제 되는가

- 인증 상태를 어디에 저장하느냐에 따라 로그아웃, 확장성, 탈취 대응 방식이 달라진다.
- 토큰은 서버 저장소가 없어도 검증할 수 있지만, 발급 후 강제 무효화가 어렵다.
- 세션은 서버에서 상태를 제어하기 쉽지만, 여러 인스턴스에서 공유 저장소나 sticky session이 필요할 수 있다.
- access token, refresh token, session cookie의 역할을 섞으면 만료와 재발급 정책이 복잡해진다.

## 동작 원리

1. 사용자가 로그인하면 서버가 인증 정보를 검증한다.
2. 세션 방식은 서버 저장소에 인증 상태를 저장하고 세션 id를 쿠키로 전달한다.
3. 토큰 방식은 사용자 식별자, 만료 시간, 권한 정보를 포함한 서명된 토큰을 발급한다.
4. 이후 요청에서 세션 id나 토큰을 검증해 인증된 사용자 정보를 만든다.
5. 만료, 로그아웃, 권한 변경, 토큰 탈취 상황에 맞춰 무효화 정책을 적용한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 서버에서 강제 로그아웃이 중요 | Session | 서버 상태를 삭제해 즉시 차단할 수 있다 |
| 여러 서비스가 독립적으로 검증 | Token | 서명 검증만으로 인증 정보를 확인할 수 있다 |
| 브라우저 기반 서비스 | HttpOnly Secure Cookie | 스크립트 탈취 위험을 줄인다 |
| 모바일 앱 API | Access Token + Refresh Token | 짧은 access token과 재발급 흐름을 분리한다 |
| 권한이 자주 바뀜 | 짧은 만료 또는 서버 검증 병행 | 오래된 토큰 권한이 남는 문제를 줄인다 |

## 자주 나는 실수

- JWT를 쓰면 로그아웃 문제가 자동으로 해결된다고 생각한다.
- token payload에 민감 정보를 넣는다.
- access token 만료 시간을 너무 길게 둔다.
- refresh token을 access token처럼 매 요청에 보낸다.
- 쿠키를 쓰면서 CSRF 대응을 고려하지 않는다.

## 확인 방법

- 테스트: 만료된 세션이나 토큰으로 요청하면 인증 실패가 나는지 확인한다.
- 테스트: 로그아웃 후 기존 인증 정보가 재사용되지 않는지 확인한다.
- 로그: 로그인, 재발급, 로그아웃, 인증 실패 사유를 남긴다.
- 보안 리뷰: 쿠키 옵션, 토큰 만료 시간, refresh token 저장 위치를 확인한다.

## 장점과 한계

| 방식 | 장점 | 한계 |
|---|---|---|
| Session | 서버에서 인증 상태를 통제하기 쉽다 | 세션 저장소와 확장성 설계가 필요하다 |
| Token | stateless 검증이 가능하고 서비스 간 전달이 쉽다 | 강제 무효화와 권한 변경 반영이 어렵다 |
| Cookie | 브라우저 자동 전송과 HttpOnly 보호를 활용할 수 있다 | CSRF 대응이 필요하다 |
| Authorization Header | API 클라이언트에서 명시적으로 제어하기 쉽다 | 클라이언트 저장소 탈취에 주의해야 한다 |

## 짧은 예제

```java
public AuthenticatedUser authenticate(String accessToken) {
    TokenClaims claims = tokenVerifier.verify(accessToken);

    if (claims.isExpired()) {
        throw new UnauthorizedException("expired token");
    }

    return new AuthenticatedUser(claims.userId(), claims.roles());
}
```

토큰 검증은 서명, 만료 시간, 발급자, audience 같은 조건을 함께 확인해야 한다. payload를 단순 decode하는 것은 인증이 아니다.

## 핵심 요약

Session은 인증 상태를 서버가 관리하고 Token은 서명된 인증 정보를 클라이언트가 전달한다.

세션은 강제 무효화가 쉽지만 저장소와 확장성 설계가 필요하다.

토큰은 stateless 검증이 가능하지만 발급 후 무효화와 권한 변경 반영이 어렵다.

브라우저 쿠키 기반 인증은 CSRF와 쿠키 옵션을 같이 고려해야 한다.

JWT payload는 암호화가 아니라 인코딩된 값이므로 민감 정보를 넣으면 안 된다.

인증 방식 선택은 확장성보다 만료, 탈취, 로그아웃, 권한 변경 대응을 기준으로 판단한다.

## 꼬리 질문

- Session과 Token 방식의 가장 큰 차이는 무엇인가?
- JWT 로그아웃은 왜 단순하지 않은가?
- access token과 refresh token의 역할을 어떻게 나눌 것인가?

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[authorization-check-location]]
- [[01-core/network/http-basics|http-basics]]
