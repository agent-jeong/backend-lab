---
title: XSS
description: 신뢰할 수 없는 값이 페이지에서 코드로 실행되는 공격과, 서버와 프론트가 각자 막을 자리
tags: [concept, security]
---

# XSS

XSS(Cross-Site Scripting)는 사용자가 넣은 값이 페이지에 들어가면서 글자가 아니라 코드로 실행되는 공격이다. 상품 리뷰에 적힌 `<script>`가 그 리뷰를 여는 모든 사람의 브라우저에서 돈다.

이 스크립트는 우리 사이트의 출처(origin)에서 실행되므로, 피해자가 할 수 있는 일은 다 한다. 주문을 넣고, 배송지를 바꾸고, 화면에 보이는 개인정보를 읽어 밖으로 보낸다. `localStorage`에 둔 토큰은 그대로 가져간다. 관리자가 보는 문의 목록에 심어 두면 관리자 권한으로 같은 일을 한다. 그래서 XSS는 입력값 하나가 계정 탈취로 이어지는 공격이다.

## 세 가지 갈래

| 종류 | 값이 들어오는 길 | 예 |
|---|---|---|
| 저장형(stored) | DB에 저장됐다가 다른 사람 화면에 나간다 | 리뷰, 게시글, 닉네임, 배송 메모 |
| 반사형(reflected) | 요청 값이 그 응답에 그대로 다시 나온다 | 검색어를 결과 제목에 다시 찍는 페이지, 입력값을 그대로 찍는 오류 페이지 |
| DOM 기반 | 서버를 거치지 않고 프론트 JS가 URL이나 저장소 값을 DOM에 넣는다 | `location.hash`를 `innerHTML`에 넣는 코드 |

OWASP는 저장형과 반사형을 "공격 값이 피해자에게 닿는 경로", 서버 측과 DOM 기반을 "위험하게 다룬 곳"으로 나눠 본다. 저장형이면서 DOM 기반인 경우도 있다. 막을 자리를 정할 때는 이름보다 "이 값이 어디서 HTML이나 JS로 해석되나"를 따라간다.

## 서버가 할 일

### 출력할 때 그 자리에 맞게 인코딩한다

XSS는 값을 넣는 시점이 아니라 화면에 내보내는 시점에 막는다. 같은 값이라도 HTML 본문, 속성, `<script>` 안, URL에 들어갈 때 해석 규칙이 달라서 인코딩 방식도 다르다.

| 들어가는 자리 | 인코딩 | 예 |
|---|---|---|
| HTML 본문 | HTML 엔티티 | `<` 를 `&lt;`로 |
| 따옴표로 감싼 속성 값 | HTML 속성 인코딩 | `value="..."` |
| `<script>` 안 문자열 | JS 문자열 인코더 | 직접 이스케이프하지 말고 라이브러리 |
| URL 파라미터 | URL 인코딩 후 속성 인코딩 | `href="/search?q=..."` |

이벤트 핸들러 속성(`onclick`), `<script>` 블록 전체, CSS, 주석 안은 인코딩해도 막히지 않는 자리다. 신뢰할 수 없는 값을 아예 넣지 않는다.

### 템플릿 엔진의 자동 escape를 끄지 않는다

서버에서 HTML을 그린다면 대부분의 템플릿 엔진이 기본으로 HTML 본문 인코딩을 해 준다.

```html
<p th:text="${review.content}">리뷰 내용</p>   <!-- escape 된다 -->
<p th:utext="${review.content}">리뷰 내용</p>  <!-- escape 안 된다 -->
```

Thymeleaf의 `th:text`는 `<`, `>`를 엔티티로 바꾸고, `th:utext`는 그대로 내보낸다. 사용자 값에는 `th:text`만 쓴다. 코드 리뷰에서는 escape를 끄는 문법(`th:utext`, 다른 엔진의 `{{{ }}}` 같은 것)만 골라 보면 빠르다.

### HTML을 받아야 하면 sanitizer로 걸러 낸다

공지 편집기처럼 굵게, 링크, 목록을 허용해야 하면 인코딩하면 기능이 깨진다. 이때는 허용 목록(allowlist) 방식의 HTML sanitizer로 허용한 태그와 속성만 남긴다. OWASP는 브라우저 쪽에 DOMPurify를 권하고, Java 서버라면 OWASP Java HTML Sanitizer가 같은 일을 한다. 금지어 목록으로 `<script>`만 지우는 코드는 대소문자, 인코딩, 다른 태그의 이벤트 속성으로 바로 우회된다.

sanitizer를 통과한 HTML을 다시 문자열로 고치면, 고친 결과는 검사를 거치지 않은 HTML이 된다. 라이브러리는 새 우회 기법이 나올 때마다 갱신되므로 버전을 계속 올린다.

### 응답 타입과 헤더를 정확히 준다

- JSON 응답은 `Content-Type: application/json`으로 보낸다. `text/html`로 나가면 JSON 안의 문자열이 HTML로 해석된다.
- `X-Content-Type-Options: nosniff`로 브라우저가 타입을 추측하지 못하게 한다. Spring Security는 이 헤더를 기본으로 붙인다.
- Spring Security는 `X-XSS-Protection: 0`을 기본으로 보낸다. 브라우저의 옛 XSS 필터는 더는 방어 수단이 아니다.

## API 서버와 SPA의 역할 분담

API 서버가 JSON만 주고 React 같은 SPA가 화면을 그리면, 인코딩 책임은 화면을 그리는 쪽으로 간다.

| 일 | API 서버 | SPA |
|---|---|---|
| 데이터 | 원본 그대로 JSON으로 준다 | 프레임워크의 기본 출력(`{value}`)으로 그린다 |
| HTML 콘텐츠 | 저장 전에 sanitizer로 허용 태그만 남긴다 | `dangerouslySetInnerHTML`, `innerHTML`에 넣기 전에 다시 sanitize한다 |
| URL 값 | `http`, `https` 스킴만 받도록 검증한다 | `href`에 넣기 전에 스킴을 확인한다 |
| 헤더 | `Content-Type`, CSP, 쿠키 속성을 준다 | 인라인 스크립트를 줄여 CSP를 빡빡하게 걸 수 있게 한다 |

API 서버가 모든 문자열을 HTML 이스케이프해서 저장하거나 응답하면 오히려 망가진다. 모바일 앱과 CSV 다운로드에는 `&lt;`가 그대로 찍히고, SPA가 한 번 더 escape하면 이중 인코딩이 된다. 어느 자리에 출력될지 모르는 API 단계에서는 문맥에 맞는 인코딩을 고를 수 없다.

## Content-Security-Policy

CSP는 이 페이지가 어디서 온 스크립트만 실행할지를 브라우저에게 알리는 응답 헤더다. 인코딩이 한 곳에서 빠져도, 허용하지 않은 인라인 스크립트는 브라우저가 실행하지 않는다.

```text
Content-Security-Policy: script-src 'nonce-{RANDOM}' 'strict-dynamic'; object-src 'none'; base-uri 'none'
```

OWASP가 권하는 strict 정책은 요청마다 새 nonce를 만들어 우리 `<script nonce="...">`에만 붙인다. `'unsafe-inline'`을 허용하면 인라인 공격 스크립트도 실행되므로 XSS 방어 효과가 거의 없다. Spring Security는 CSP를 기본으로 넣지 않는다. `headers(h -> h.contentSecurityPolicy(csp -> csp.policyDirectives("...")))`로 직접 설정한다.

CSP는 두 번째 방어선이다. OWASP도 첫 번째 방어로 삼지 말라고 한다. 기존 서비스에 걸 때는 `Content-Security-Policy-Report-Only`로 위반 보고만 받아 보고, 깨지는 화면이 없을 때 강제로 바꾼다.

## HttpOnly 쿠키가 막는 것과 못 막는 것

HttpOnly 쿠키는 JS의 `document.cookie`로 읽히지 않는다. 그래서 공격 스크립트가 세션 쿠키를 훔쳐 공격자 서버로 보내는 일은 막는다.

못 막는 것이 더 많다. 공격 스크립트는 피해자 페이지 안에서 `fetch('/api/orders', ...)`를 부르고, 브라우저는 HttpOnly 쿠키를 알아서 붙인다. 쿠키 값을 몰라도 피해자로서 요청을 보낸다. 화면의 개인정보를 읽고, 입력 폼을 가짜로 바꿔 비밀번호를 받는 것도 그대로 된다. OWASP도 쿠키 속성은 피해를 줄일 뿐 스크립트 실행을 막지 못한다고 적는다. 그래도 토큰을 `localStorage`에 두는 것보다는 낫다. `localStorage`는 스크립트가 값을 읽어 가서, 피해자가 탭을 닫은 뒤에도 공격자가 계속 쓴다([[session-and-token]]).

## 자주 깨지는 곳

- 모든 요청 파라미터를 Filter나 Interceptor에서 일괄 escape하면, 출력 문맥을 모른 채 인코딩해서 JS나 URL 자리는 뚫리고 정상 화면은 이중 인코딩으로 깨진다. OWASP가 안티 패턴으로 꼽는 방식이다.
- 사용자 값에 `th:utext`나 `innerHTML`을 쓰면, 템플릿 엔진과 프레임워크가 해 주던 escape가 꺼진다.
- 프로필 링크 같은 URL 값을 검증 없이 `href`에 넣으면, `javascript:` 스킴으로 클릭 한 번에 스크립트가 돈다.
- 오류 페이지나 검색 결과에 입력값을 그대로 찍으면, 링크 하나로 반사형 XSS가 된다.
- 관리자 화면은 내부용이라고 escape를 빼면, 사용자가 남긴 문의 내용이 관리자 권한으로 실행된다.
- CSP에 `'unsafe-inline'`을 넣고 CSP를 적용했다고 여기면, 인라인 공격 스크립트가 그대로 돈다.
- HttpOnly를 켰으니 XSS가 막혔다고 여기면, 쿠키를 훔치지 않고도 피해자 권한으로 요청을 보내는 공격을 놓친다.
- XSS가 하나라도 있으면 CSRF token도 지켜 주지 못한다. 같은 출처의 스크립트는 페이지에 있는 CSRF token을 읽어 요청에 붙인다([[csrf]]).

## 운영에서 볼 것

- 테스트에 `<script>alert(1)</script>`, `"><img src=x onerror=alert(1)>` 같은 값을 리뷰, 닉네임, 검색어로 넣고 응답에서 escape됐는지 확인한다.
- `curl -I https://api.example.com/`로 `Content-Type`, `X-Content-Type-Options`, `Content-Security-Policy` 헤더가 붙는지 본다.
- CSP 위반 보고를 받는 엔드포인트를 두고 위반 건수를 본다. 갑자기 늘면 새 배포가 인라인 스크립트를 넣었거나 실제 주입 시도다.
- 위반 보고와 오류 로그에는 사용자가 넣은 원문이 섞이므로 그대로 쌓지 않는다([[sensitive-data-logging]]).
- 코드 검색으로 `th:utext`, `innerHTML`, `dangerouslySetInnerHTML`, `v-html` 사용처를 주기로 훑는다.

## 한 번에 설명하기

> XSS는 신뢰할 수 없는 값이 페이지에서 코드로 실행되는 공격입니다. 저장형, 반사형, DOM 기반이 있지만 막는 원리는 같아서, 값이 출력되는 자리마다 그 문맥에 맞게 인코딩합니다.
>
> 서버에서 HTML을 그리면 템플릿 엔진의 자동 escape를 끄지 않고, HTML을 받아야 하는 기능만 allowlist sanitizer로 거릅니다. API 서버는 데이터를 원본 그대로 주고, 화면을 그리는 SPA가 프레임워크의 escape를 쓰도록 역할을 나눕니다.
>
> 그 위에 nonce를 쓰는 CSP를 두 번째 방어선으로 걸고, 세션 쿠키는 HttpOnly로 둡니다. 다만 HttpOnly는 쿠키를 읽지 못하게 할 뿐, 스크립트가 피해자로서 요청을 보내는 것은 막지 못한다는 점을 구분합니다.

## 꼬리 질문

> [!question]- 입력할 때 막나, 출력할 때 막나?
> 출력할 때 막습니다. 같은 값이 HTML 본문, 속성, 스크립트, URL 중 어디에 들어가느냐에 따라 필요한 인코딩이 다른데, 입력 시점에는 어디에 출력될지 모릅니다. 입력 검증은 형식을 좁히는 보조 수단으로 같이 씁니다.

> [!question]- HttpOnly 쿠키를 쓰면 XSS를 막을 수 있나?
> 막지 못합니다. 스크립트가 쿠키 값을 읽어 가는 것만 막습니다. 공격 스크립트는 피해자 페이지에서 API를 부르고, 브라우저가 HttpOnly 쿠키를 알아서 붙이기 때문에 피해자 권한으로 요청이 나갑니다.

> [!question]- REST API 서버는 XSS에서 무엇을 책임지나?
> 데이터는 원본으로 주고 `Content-Type: application/json`과 `nosniff`를 정확히 보냅니다. HTML을 받는 기능이면 저장 전에 allowlist sanitizer로 거르고, URL 값은 허용 스킴만 받습니다. 화면에 넣는 시점의 인코딩은 SPA가 프레임워크 기본 출력으로 맡습니다.

> [!question]- CSP가 있으면 출력 인코딩을 안 해도 되나?
> 안 됩니다. CSP는 인코딩이 빠진 곳에서 피해를 줄이는 두 번째 방어선이고, 브라우저 지원과 정책 설정에 따라 효과가 달라집니다. `'unsafe-inline'`이 들어간 정책은 인라인 공격을 막지 못합니다.

> [!question]- Filter에서 모든 파라미터를 escape하면 안 되나?
> 출력 문맥을 모르는 자리에서 HTML 인코딩만 하게 되어, 스크립트나 URL 자리는 여전히 뚫리고 정상 데이터는 이중 인코딩으로 깨집니다. 헤더나 다른 시스템에서 온 데이터, DOM 기반 XSS도 놓칩니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP: DOM based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [OWASP: Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)

## 관련 문서

- [[security]]
- [[csrf]]
- [[session-and-token]]
- [[sensitive-data-logging]]
- [[spring-security-flow]]
- [[oauth2-and-oidc]]
