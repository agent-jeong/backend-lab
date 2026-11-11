---
title: CORS
description: 브라우저가 다른 출처 요청을 막는 방식과 Preflight, Spring에서 CORS를 여는 법
tags: [concept, network]
---

# CORS

CORS(Cross-Origin Resource Sharing)는 브라우저가 다른 출처(Origin)의 서버로 요청할 때, 그 서버가 요청을 받아 주는지 먼저 확인하는 장치다. `https://app.example.com`의 화면이 `https://api.example.com`의 주문 API를 부르는 경우가 그렇다.

CORS는 브라우저만 검사한다. 그래서 Postman에서는 잘 되는데 브라우저에서만 막히는 일이 생긴다. 실제로 자주 부딪히는 건 세 가지다. 서버가 OPTIONS를 막아 Preflight가 실패하거나, Cookie나 Authorization 헤더를 실은 요청이 막히거나, `*`로 열어 둔 채 운영에 배포하는 경우다.

## Origin

Origin은 프로토콜, 호스트, 포트 세 가지를 묶은 것이다. 셋 중 하나라도 다르면 다른 Origin이다.

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

## 동작

### Simple Request (단순 요청)

아래 조건을 모두 만족하면 브라우저는 Preflight 없이 바로 요청한다.

- 메서드: GET, HEAD, POST
- 헤더: Accept, Content-Type(`application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain`만), Accept-Language 등 기본 헤더만
- Content-Type이 `application/json`이면 단순 요청이 아니다

```
Browser                          Server
  │── GET /api/data ──────────▶   │
  │   Origin: https://app.com     │
  │                                │
  │◀── 200 OK ────────────────   │
  │   Access-Control-Allow-Origin: https://app.com
```

### Preflight Request (사전 요청)

단순 요청 조건을 하나라도 벗어나면, 브라우저가 먼저 OPTIONS 요청을 보내 이 요청을 받아 주는지 묻는다.

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

`Access-Control-Max-Age`는 Preflight 결과를 브라우저가 기억하는 시간(초)이다. 그동안 같은 요청에는 Preflight를 다시 보내지 않는다.

## 응답 헤더 (서버 → 브라우저)

| 헤더 | 용도 | 예시 |
|---|---|---|
| `Access-Control-Allow-Origin` | 허용할 Origin | `https://app.com` 또는 `*` |
| `Access-Control-Allow-Methods` | 허용할 HTTP 메서드 | `GET, POST, PUT, DELETE` |
| `Access-Control-Allow-Headers` | 허용할 요청 헤더 | `Content-Type, Authorization` |
| `Access-Control-Allow-Credentials` | 인증 정보 포함 허용 | `true` |
| `Access-Control-Max-Age` | Preflight 캐시 시간 (초) | `3600` |
| `Access-Control-Expose-Headers` | 브라우저에서 접근 가능한 응답 헤더 | `X-Total-Count` |

### 인증 정보를 실은 요청 (Credentials)

Cookie나 Authorization 헤더를 실으려면 프론트와 서버 양쪽을 다 설정해야 한다.

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

`credentials: true`일 때는 `Allow-Origin: *`를 쓸 수 없다. Origin을 하나하나 적어야 한다.

## Spring에서 설정하기

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

Spring Security를 쓰면 `WebMvcConfigurer`만으로는 모자라다. Security 필터가 먼저 돌면서 Preflight를 막을 수 있어서, `CorsConfigurationSource`를 Security에도 등록한다.

## Postman에서는 되는데 브라우저에서 안 되는 이유

CORS를 검사하는 건 브라우저다. Postman이나 curl은 CORS를 검사하지 않으니 요청이 그냥 성공한다.

```
Postman → 서버: CORS 헤더 무관하게 요청 성공
브라우저 → 서버: CORS 헤더 없으면 응답을 차단
```

서버는 정상으로 응답했어도, `Access-Control-Allow-Origin` 헤더가 없으면 브라우저가 그 응답을 JavaScript에 넘겨주지 않는다.

## 자주 깨지는 곳

- `Allow-Origin: *`에 `credentials: true`를 같이 쓰면 브라우저가 에러를 낸다.
- Spring Security를 쓰면서 `WebMvcConfigurer`만 설정하면, Security 필터가 Preflight를 먼저 막는다.
- OPTIONS 메서드를 막으면 Preflight가 실패해서 Preflight가 필요한 API가 모두 막힌다.
- 개발 환경에서 프록시로 CORS를 피해 가면, 운영에 올리고 나서야 CORS 문제를 발견한다.
- `Access-Control-Max-Age`를 설정하지 않으면 요청할 때마다 Preflight가 나간다.

## 한 번에 설명하기

> CORS는 브라우저가 다른 Origin으로 가는 요청을 막는 정책이고, 받아 줄지는 서버가 응답 헤더로 알려 줍니다.
>
> `application/json` 요청은 OPTIONS로 Preflight가 먼저 나가서, CORS 에러가 나면 서버가 OPTIONS를 막고 있지 않은지부터 봅니다.
>
> 쿠키를 실어야 하면 `Allow-Origin: *` 대신 Origin을 직접 적고, Spring Security를 쓰면 `CorsConfigurationSource`를 Security에 등록합니다.

## 꼬리 질문

> [!question]- Preflight는 왜 필요한가?
> 실제 요청을 보내기 전에 서버가 이 요청을 받아 주는지 먼저 물어보려는 겁니다. CORS를 모르는 서버에 바로 PUT이나 DELETE를 보내면, 응답은 막히더라도 서버에서는 데이터가 이미 바뀌어 버릴 수 있습니다.

> [!question]- CORS를 서버가 아닌 프록시로 해결할 수 있는가?
> 개발할 때는 프론트엔드 dev server의 프록시 설정으로 같은 Origin처럼 보이게 할 수 있습니다. 운영에서는 Nginx 같은 리버스 프록시에서 CORS 헤더를 붙이거나, 프론트와 API를 같은 도메인으로 내보내면 CORS 문제가 아예 생기지 않습니다.

> [!question]- Access-Control-Expose-Headers는 언제 사용하는가?
> 브라우저 JavaScript가 읽을 수 있는 응답 헤더는 기본으로 몇 개뿐입니다. 페이지네이션의 `X-Total-Count` 같은 커스텀 헤더를 프론트에서 읽으려면 `Expose-Headers`에 적어 줘야 합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[status-code]]
- [[01-core/spring/spring-mvc-request-flow|spring-mvc-request-flow]]