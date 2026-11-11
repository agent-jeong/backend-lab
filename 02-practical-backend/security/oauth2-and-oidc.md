---
title: OAuth 2.0과 OpenID Connect
description: 비밀번호를 넘기지 않고 권한을 위임하는 OAuth와 그 위에서 로그인한 사람을 알려 주는 OIDC, 소셜 로그인을 서버에서 처리하는 법
tags: [concept, security]
---

# OAuth 2.0과 OpenID Connect

OAuth 2.0은 사용자가 비밀번호를 넘기지 않고도 다른 서비스가 자기 자원에 제한된 범위로 접근하게 허락하는 규약이다. OpenID Connect(OIDC)는 그 위에 "방금 로그인한 사람이 누구인가"를 알려 주는 ID token을 더한 규약이다. 흔히 말하는 소셜 로그인은 거의 OIDC다.

둘을 섞으면 구멍이 생긴다. OAuth의 access token은 "이 API를 불러도 된다"는 허가증일 뿐 로그인 증명이 아니다. 그런데 이것만 받아 사용자를 식별하거나, 콜백에서 `state`를 확인하지 않거나, 받은 토큰을 브라우저 저장소에 그대로 두면 공격자 계정으로 로그인되거나 토큰이 스크립트 한 줄에 털린다.

이 노트는 RFC 6749(OAuth 2.0), RFC 7636(PKCE), OIDC Core 1.0, 그리고 2025년에 나온 RFC 9700(OAuth 2.0 보안 모범 사례)을 기준으로 한다.

## 등장하는 네 역할

| 역할 | 하는 일 | 소셜 로그인에서 |
|---|---|---|
| 리소스 소유자(resource owner) | 자원 접근을 허락하는 사람 | 로그인하는 사용자 |
| 클라이언트(client) | 사용자 대신 자원에 접근하려는 애플리케이션 | 우리 `example-service` |
| 인가 서버(authorization server) | 사용자를 인증하고 동의를 받아 토큰을 발급한다 | 로그인 제공자의 인증 서버 |
| 리소스 서버(resource server) | access token을 받고 자원을 내준다 | 제공자의 프로필 API |

클라이언트에는 두 종류가 있다. 서버처럼 `client_secret`을 숨길 수 있으면 confidential client, 브라우저 SPA나 모바일 앱처럼 숨길 수 없으면 public client다. 어느 쪽이냐에 따라 토큰을 어디서 교환할지가 달라진다.

## Authorization Code와 PKCE 흐름

1. 클라이언트가 추측할 수 없는 값 세 개를 만들어 사용자 세션에 묶어 둔다. CSRF 방어용 `state`, PKCE용 `code_verifier`, OIDC라면 `nonce`다. `code_verifier`는 43자 이상의 무작위 문자열이고, 이것을 SHA-256으로 해시해 base64url로 바꾼 값이 `code_challenge`다.
2. 브라우저를 인가 서버로 보낸다.

```http
GET https://auth.example.com/authorize
  ?response_type=code
  &client_id=example-service
  &redirect_uri=https://api.example.com/login/oauth2/code/example
  &scope=openid profile
  &state=<random>
  &nonce=<random>
  &code_challenge=<BASE64URL(SHA256(code_verifier))>
  &code_challenge_method=S256
```

3. 사용자가 인가 서버에서 로그인하고 동의한다. 비밀번호는 인가 서버만 본다.
4. 인가 서버가 브라우저를 `redirect_uri`로 돌려보내며 `code`와 `state`를 붙인다.
5. 클라이언트는 받은 `state`가 세션에 둔 값과 같은지 확인한다. 다르면 여기서 멈춘다.
6. 클라이언트 서버가 브라우저를 거치지 않고 인가 서버의 token endpoint를 직접 부른다. `code`, `redirect_uri`, 클라이언트 인증 정보, `code_verifier`를 보낸다.
7. 인가 서버는 `code_verifier`를 해시한 값이 1번의 `code_challenge`와 같은지 보고 토큰을 내준다. access token, 경우에 따라 refresh token, `openid` scope를 요청했다면 ID token이 온다.

PKCE가 막는 것은 code 가로채기다. 리다이렉트 URL에 실린 `code`가 로그나 악성 앱에 새도, 공격자는 `code_verifier`를 모르므로 토큰으로 바꾸지 못한다. RFC 7636은 원래 모바일 같은 public client용으로 나왔지만, RFC 9700은 public client에는 PKCE를 필수로, confidential client에도 권장으로 정했다. 방식은 `S256`을 쓴다. `plain`은 요청에 verifier가 그대로 드러난다.

## 토큰마다 받는 쪽이 다르다

| 토큰 | 누가 받나 | 하는 일 | 다룰 때 |
|---|---|---|---|
| authorization code | 클라이언트 | 토큰으로 한 번 바꾸는 교환권 | 한 번만 쓰고, RFC 6749는 수명 10분 이하를 권한다 |
| access token | 리소스 서버 | API를 불러도 된다는 허가 | 짧게 살고, scope만큼만 쓴다 |
| refresh token | 인가 서버 | 새 access token을 받는다 | 리소스 서버에는 절대 보내지 않는다 |
| ID token | 클라이언트 | 누가 언제 로그인했는지 알려 준다 | `aud`가 우리 `client_id`인지 검증한다 |

access token과 refresh token의 역할 분리는 [[session-and-token]]에서 다룬 것과 같다. 다른 점은 이 토큰들이 우리 서버가 아니라 외부 인가 서버가 발급한 것이라는 점이다.

## OIDC가 더하는 것

OAuth만으로는 로그인한 사람이 누구인지 표준으로 알 수 없다. access token은 리소스 서버가 읽으라고 만든 값이라 클라이언트가 내용을 해석하는 용도가 아니다. OIDC는 `scope`에 `openid`를 넣으면 ID token을 함께 준다. ID token은 서명된 JWT이고 `iss`(발급자), `sub`(사용자 식별자), `aud`(받을 클라이언트), `exp`(만료), `iat`(발급 시각), 요청에 넣었다면 `nonce`를 담는다.

클라이언트는 ID token에서 다음을 확인한다.

- `iss`가 설정해 둔 발급자와 정확히 같다.
- `aud`에 우리 `client_id`가 들어 있고, 믿지 않는 다른 audience가 없다.
- `exp`가 지나지 않았다.
- 1번에서 보낸 `nonce`와 값이 같다.

사용자를 우리 DB와 연결할 때는 `iss`와 `sub`를 함께 키로 쓴다. OIDC Core는 이 둘의 조합만 사용자를 안정적으로 가리킨다고 정한다. 이메일은 바뀔 수 있고, 제공자가 다르면 같은 이메일이 다른 사람일 수 있다.

## 소셜 로그인을 서버에서 처리하기

브라우저 서비스라면 토큰 교환을 우리 서버가 하고, 제공자 토큰은 서버에만 두고, 브라우저에는 우리 세션 쿠키만 준다.

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          example:
            client-id: example-service
            client-secret: ${OAUTH_CLIENT_SECRET}
            scope: openid,profile
        provider:
          example:
            issuer-uri: https://auth.example.com
```

Spring Security의 `oauth2Login()`은 위 흐름의 2번부터 7번을 대신 해 준다. 기본 콜백 주소는 `{baseUrl}/login/oauth2/code/{registrationId}`이고, `state` 저장과 비교, 토큰 교환, ID token 검증을 처리한다. 로그인이 끝나면 `iss`와 `sub`로 우리 사용자를 찾거나 만들고, 그다음부터는 HttpOnly, Secure 쿠키의 우리 세션으로 인증한다. 제공자 API를 다시 불러야 할 때 쓰는 토큰은 `OAuth2AuthorizedClientService`가 보관한다. 기본 구현은 메모리라서 서버가 재시작하면 사라지고 다른 인스턴스와 공유되지 않는다.

| 상황 | 토큰 교환 위치 | 브라우저에 두는 것 |
|---|---|---|
| 서버가 화면도 그리거나 API 서버가 있는 SPA | 우리 서버(confidential client) | 우리 세션 쿠키 |
| 서버 없이 도는 SPA, 모바일 앱 | 클라이언트 앱(public client) + PKCE 필수 | 짧은 access token, `client_secret` 없음 |

## 자주 깨지는 곳

- implicit 흐름(`response_type=token`)을 쓰면, access token이 리다이렉트 URL에 실려 브라우저 기록과 Referer로 샌다. RFC 9700은 쓰지 말라고 하고 Authorization Code와 PKCE로 대신한다.
- 콜백에서 `state`를 확인하지 않으면, 공격자가 자기 `code`가 실린 콜백 링크를 피해자에게 열게 해서 피해자 브라우저가 공격자 계정으로 로그인된다. 피해자가 저장한 결제 수단이 공격자 계정에 붙는다.
- 인가 서버에 `redirect_uri`를 접두사나 와일드카드로 등록하면, 같은 도메인의 열린 리다이렉트를 거쳐 `code`가 공격자에게 간다. RFC 9700은 정확한 문자열 비교를 요구한다.
- access token이나 refresh token을 `localStorage`에 두면, XSS 스크립트 한 줄로 읽혀 나간다. 서버에 두고 브라우저에는 HttpOnly 쿠키만 준다([[xss]]).
- 제공자 access token을 받아 우리 API의 인증 수단으로 그대로 쓰면, 그 토큰이 우리 서비스를 위해 발급됐는지 확인할 방법이 없다. 로그인 뒤에는 우리 세션이나 우리 토큰을 따로 발급한다.
- ID token을 우리 API에 Bearer로 보내면, `aud`가 클라이언트인 토큰을 리소스 서버용으로 쓰는 셈이 된다. ID token은 클라이언트가 로그인 결과를 확인하고 끝낸다.
- 이메일로 사용자를 매칭하면, 이메일을 바꾼 사용자가 새 계정으로 갈리거나 다른 제공자의 같은 이메일이 기존 계정에 붙는다.
- `client_secret`을 SPA나 앱 번들에 넣으면, 누구나 꺼내서 우리 클라이언트인 척한다.
- 인스턴스가 여러 대인데 인가 요청 정보(기본은 HTTP 세션)와 authorized client를 각 인스턴스 메모리에만 두면, 콜백이 다른 인스턴스로 가는 순간 `state`를 못 찾아 로그인이 실패한다. 세션 공유나 저장소 교체가 필요하다.

## 운영에서 볼 것

- 로그인 실패를 사유별로 센다. 콜백의 `error` 파라미터, `state` 불일치, ID token 검증 실패를 따로 남기면 설정 문제인지 공격 시도인지 갈린다.
- 로그에 `code`, access token, refresh token, ID token 원문을 남기지 않는다([[sensitive-data-logging]]).
- 인가 서버 콘솔에 등록된 `redirect_uri` 목록을 주기로 점검하고, 쓰지 않는 개발용 주소를 지운다.
- 제공자의 서명 키가 바뀌는 시점에 ID token 검증 실패가 튀는지 본다. `issuer-uri`를 쓰면 키 목록(JWKS)을 제공자 메타데이터에서 읽어 온다.

## 한 번에 설명하기

> OAuth 2.0은 비밀번호를 넘기지 않고 권한을 위임하는 규약이고, 결과물인 access token은 리소스 서버에 내미는 허가증입니다. 로그인한 사람이 누구인지는 OIDC가 ID token으로 알려 주고, 사용자 식별은 ID token의 `iss`와 `sub` 조합으로 합니다.
>
> 흐름은 Authorization Code에 PKCE를 붙여 씁니다. 브라우저에는 `code`만 오고, 토큰 교환은 서버가 `code_verifier`와 함께 백채널로 하기 때문에 `code`가 새도 토큰을 빼앗기지 않습니다. 콜백에서는 `state`를, ID token에서는 `iss`, `aud`, `exp`, `nonce`를 확인합니다.
>
> 브라우저 서비스라면 제공자 토큰은 서버에 두고, 로그인 뒤에는 HttpOnly 쿠키의 우리 세션으로 인증합니다. implicit 흐름과 토큰의 `localStorage` 저장은 쓰지 않습니다.

## 꼬리 질문

> [!question]- OAuth와 OIDC는 무엇이 다른가?
> OAuth는 인가 위임 규약이라 access token은 "이 API를 불러도 된다"는 뜻만 담습니다. OIDC는 OAuth 위에 ID token을 더해서 누가 언제 어느 발급자에게 로그인했는지를 클라이언트가 검증할 수 있게 합니다.

> [!question]- PKCE는 무엇을 막나? 서버 앱에도 필요한가?
> 인가 코드를 가로챈 공격자가 토큰으로 바꾸는 것을 막습니다. 토큰 교환 때 원래 `code_verifier`를 내야 하기 때문입니다. RFC 9700은 public client에는 필수, `client_secret`이 있는 서버 앱에도 권장으로 정했습니다.

> [!question]- state를 확인하지 않으면 어떤 공격이 되나?
> 공격자가 자기 계정으로 받은 `code`가 담긴 콜백 링크를 피해자에게 열게 하면, 피해자 브라우저가 공격자 계정으로 로그인됩니다. 피해자가 그 상태에서 입력한 정보가 공격자 계정에 쌓입니다. `state`를 세션에 묶어 두고 콜백에서 비교하면 막힙니다.

> [!question]- 소셜 로그인으로 받은 access token을 우리 API 인증에 써도 되나?
> 쓰지 않습니다. 그 토큰은 제공자 API를 위해 발급된 것이라 우리 서비스용인지 확인할 수 없습니다. 로그인 결과로 우리 사용자를 찾은 뒤 우리 세션이나 우리 토큰을 따로 발급합니다.

> [!question]- 사용자를 이메일로 식별하면 왜 안 되나?
> 이메일은 사용자가 바꿀 수 있고, 제공자마다 같은 이메일이 다른 사람일 수 있습니다. OIDC Core는 `iss`와 `sub`의 조합만 안정적인 식별자로 정하므로 이 둘을 키로 저장합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 6749: The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)
- [RFC 7636: Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[session-and-token]]
- [[spring-security-flow]]
- [[csrf]]
- [[xss]]
