---
title: CORS
description: CORS 동작 원리와 Preflight, Spring에서의 설정 방법
---

# CORS

## 한 줄 정의

CORS(Cross-Origin Resource Sharing)는 브라우저가 다른 출처(Origin)의 서버에 요청할 때, 서버가 이를 허용하는지 확인하는 보안 메커니즘이다.

## 실무에서 왜 중요한가

CORS를 이해하지 못하면 다음 문제가 생긴다.

- 프론트엔드에서 API를 호출하면 브라우저에서 에러가 나는데 Postman에서는 정상이다.
- Preflight 요청을 모르고 OPTIONS 메서드를 차단해서 모든 API가 실패한다.
- CORS 설정을 `*`로 열어두고 운영에 배포해서 보안 문제가 생긴다.
- 인증 헤더(Cookie, Authorization)를 포함한 요청이 CORS에 막히는 원인을 모른다.

## Origin이란

Origin = **프로토콜 + 호스트 + 포트**의 조합이다.

```
https://app.example.com:443  → Origin
  │         │            │
  프로토콜   호스트        포트
```

| URL A | URL B | 같은 Origin? |
|---|---|---|
| `https://app.com` | `https://app.com/api` | O (경로는 무관) |
| `https://app.com` | `http://app.com` | X (프로토콜 다름) |
| `https://app.com` | `https://api.app.com` | X (호스트 다름) |
| `https://app.com` | `https://app.com:8080` | X (포트 다름) |

## CORS 동작 흐름

### Simple Request (단순 요청)

조건을 모두 만족하면 Preflight 없이 바로 요청한다.

- 메서드: GET, HEAD, POST
- 헤더: Accept, Content-Type(`application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain`만), Accept-Language 등 기본 헤더만
- Content-Type이 `application/json`이면 단순 요청이 **아니다**

```
Browser                          Server
  │── GET /api/data ──────────▶   │
  │   Origin: https://app.com     │
  │                                │
  │◀── 200 OK ────────────────   │
  │   Access-Control-Allow-Origin: https://app.com
```

### Preflight Request (사전 요청)

단순 요청 조건을 만족하지 않으면, 브라우저가 먼저 OPTIONS 요청을 보내서 허용 여부를 확인한다.

```
Browser                              Server
  │── OPTIONS /api/orders ────────▶   │  ← Preflight
  │   Origin: https://app.com         │
  │   Access-Control-Request-Method: POST
  │   Access-Control-Request-Headers: Content-Type, Authorization
  │                                    │
  │◀── 204 No Content ───────────   │  ← 허용 응답
  │   Access-Control-Allow-Origin: https://app.com
  │   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
  │   Access-Control-Allow-Headers: Content-Type, Authorization
  │   Access-Control-Max-Age: 3600
  │                                    │
  │── POST /api/orders ───────────▶   │  ← 실제 요청
  │   Origin: https://app.com         │
  │   Content-Type: application/json   │
  │                                    │
  │◀── 201 Created ──────────────   │
```

`Access-Control-Max-Age`는 Preflight 결과를 캐시하는 시간(초)이다. 이 시간 동안 같은 요청에 대해 Preflight를 다시 보내지 않는다.

## 주요 CORS 헤더

### 응답 헤더 (서버 → 브라우저)

| 헤더 | 용도 | 예시 |
|---|---|---|
| `Access-Control-Allow-Origin` | 허용할 Origin | `https://app.com` 또는 `*` |
| `Access-Control-Allow-Methods` | 허용할 HTTP 메서드 | `GET, POST, PUT, DELETE` |
| `Access-Control-Allow-Headers` | 허용할 요청 헤더 | `Content-Type, Authorization` |
| `Access-Control-Allow-Credentials` | 인증 정보 포함 허용 | `true` |
| `Access-Control-Max-Age` | Preflight 캐시 시간 (초) | `3600` |
| `Access-Control-Expose-Headers` | 브라우저에서 접근 가능한 응답 헤더 | `X-Total-Count` |

### 인증 정보 포함 요청 (Credentials)

Cookie나 Authorization 헤더를 포함하려면 양쪽 모두 설정이 필요하다.

```javascript
// 프론트엔드
fetch('https://api.example.com/data', {
    credentials: 'include'  // 쿠키 포함
});
```

```
// 서버 응답 헤더
Access-Control-Allow-Origin: https://app.example.com  ← * 불가!
Access-Control-Allow-Credentials: true
```

**`credentials: true`일 때 `Allow-Origin: *`는 허용되지 않는다.** 반드시 특정 Origin을 지정해야 한다.

## Spring에서 CORS 설정

### 방법 1: @CrossOrigin (컨트롤러 단위)

```java
@CrossOrigin(origins = "https://app.example.com")
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    // ...
}
```

### 방법 2: WebMvcConfigurer (전역 설정)

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE")
            .allowedHeaders("Content-Type", "Authorization")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

### 방법 3: CorsFilter (Spring Security 사용 시)

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.cors(cors -> cors.configurationSource(corsConfigurationSource()));
        // ...
        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("https://app.example.com"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("Content-Type", "Authorization"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }
}
```

Spring Security를 사용하면 `WebMvcConfigurer`만으로는 부족하다. Security 필터가 먼저 실행되어 Preflight가 차단될 수 있으므로, `CorsConfigurationSource`를 Security에 등록해야 한다.

## Postman에서는 되는데 브라우저에서 안 되는 이유

CORS는 **브라우저가 강제하는 보안 정책**이다. Postman, curl 같은 도구는 CORS를 확인하지 않으므로 요청이 성공한다.

```
Postman → 서버: CORS 헤더 무관하게 요청 성공
브라우저 → 서버: CORS 헤더 없으면 응답을 차단
```

서버는 정상적으로 응답했지만, 브라우저가 `Access-Control-Allow-Origin` 헤더가 없으면 응답을 JavaScript에 전달하지 않는다.

## 자주 나는 실수

- `Access-Control-Allow-Origin: *`으로 설정하고 `credentials: true`를 사용해서 에러가 발생한다.
- Spring Security 환경에서 `WebMvcConfigurer`만 설정하고 Security에 CORS를 등록하지 않는다.
- OPTIONS 메서드를 차단해서 Preflight가 실패한다.
- 개발 환경에서 프록시로 우회하다가 운영에서 CORS 문제를 발견한다.
- `Access-Control-Max-Age`를 설정하지 않아서 매 요청마다 Preflight가 발생한다.

## 핵심 요약

CORS는 브라우저가 다른 Origin의 요청을 제한하는 보안 정책으로, 서버가 응답 헤더로 허용 여부를 결정합니다.
`application/json` 요청은 Preflight(OPTIONS)가 먼저 발생하며, 서버가 이를 허용해야 실제 요청이 전송됩니다.

`credentials: true`일 때는 `Allow-Origin: *`를 사용할 수 없고 특정 Origin을 지정해야 합니다.
Spring Security 환경에서는 `CorsConfigurationSource`를 Security에 등록해야 합니다.

## 꼬리 질문

> [!question]- Preflight는 왜 필요한가?
> 브라우저가 실제 요청을 보내기 전에 서버가 해당 요청을 허용하는지 미리 확인하기 위해서입니다. 서버가 CORS를 지원하지 않는 경우, Preflight 없이 바로 요청하면 서버에서 의도하지 않은 부작용(데이터 변경 등)이 발생할 수 있습니다.

> [!question]- CORS를 서버가 아닌 프록시로 해결할 수 있는가?
> 개발 환경에서 프론트엔드 dev server의 프록시 설정으로 Same-Origin처럼 동작하게 할 수 있습니다. 운영에서는 Nginx 같은 리버스 프록시에서 CORS 헤더를 추가하거나, 프론트와 API를 같은 도메인으로 서빙하면 CORS 자체를 피할 수 있습니다.

> [!question]- Access-Control-Expose-Headers는 언제 사용하는가?
> 기본적으로 브라우저 JavaScript에서 접근할 수 있는 응답 헤더는 제한되어 있습니다. 페이지네이션의 `X-Total-Count` 같은 커스텀 헤더를 프론트에서 읽으려면 `Expose-Headers`에 명시해야 합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[status-code]]
- [[01-core/spring/spring-mvc-request-flow|spring-mvc-request-flow]]