---
title: Spring Security 인증과 인가 흐름
description: 요청이 Security 필터 체인을 지나며 인증되고 인가되는 순서와, 401과 403이 나오는 자리
tags: [concept, security]
---

# Spring Security 인증과 인가 흐름

Spring Security는 서블릿 필터 체인 안에서 요청의 인증 정보를 읽고, `SecurityContextHolder`에 사용자를 올리고, 마지막 필터에서 이 요청을 통과시킬지 정한다. Controller에 닿기 전에 모든 판단이 끝난다.

이 순서를 모르면 증상만 보고 헤맨다. JWT 필터를 끼웠는데 로그인 안 한 요청이 401이 아니라 403으로 떨어지고, `permitAll`로 열어 둔 상품 조회 API가 만료된 토큰을 들고 오면 401을 낸다. 주문 생성 POST만 403이 나는데 원인은 권한이 아니라 기본으로 켜진 CSRF 검사다. 셋 다 "어느 필터에서 무엇이 던져졌나"를 알면 바로 풀린다.

이 노트는 Spring Security 6.x(Spring Boot 3.x) 기준이다.

## 요청이 필터 체인에 들어가는 길

서블릿 컨테이너는 Spring 빈을 모른다. 그래서 다리 역할을 하는 필터가 둘 있다.

1. 서블릿 컨테이너에 등록된 `DelegatingFilterProxy`가 요청을 받는다. 이 필터는 일을 하지 않고 Spring 컨텍스트에서 빈 하나를 찾아 넘긴다.
2. 넘겨받는 빈이 `FilterChainProxy`다. 이 빈이 Spring Security의 입구다.
3. `FilterChainProxy`는 등록된 `SecurityFilterChain` 중 요청 URL에 맞는 첫 번째 체인 하나만 고른다. `/api/**` 체인과 나머지 체인이 있으면 `/api/orders`는 앞 체인만 탄다.
4. 고른 체인의 Security 필터들이 순서대로 돈다. 요청이 끝나면 `FilterChainProxy`가 `SecurityContextHolder`를 비운다.

체인에 들어 있는 필터 순서는 DEBUG 기동 로그에서 확인한다. 흐름을 따라갈 때 볼 필터는 몇 개뿐이다.

| 필터 | 하는 일 |
|---|---|
| `SecurityContextHolderFilter` | 세션 등 저장소에서 이전 인증 정보를 읽어 온다 |
| `CorsFilter` | CORS 응답 헤더를 붙이고 preflight를 처리한다 |
| `CsrfFilter` | 상태를 바꾸는 요청의 CSRF 토큰을 검사한다 |
| 인증 필터들 | 폼 로그인, Basic, Bearer 토큰 등에서 인증 정보를 읽어 `Authentication`을 만든다 |
| `AnonymousAuthenticationFilter` | 아무도 인증하지 않았으면 익명 사용자를 넣는다 |
| `ExceptionTranslationFilter` | 뒤쪽에서 난 인증, 인가 예외를 401, 403 응답으로 바꾼다 |
| `AuthorizationFilter` | 마지막에 서서 이 요청을 통과시킬지 정한다 |

Filter와 Interceptor가 어디서 도는지는 [[filter-interceptor-aop]]에 있다.

## 인증 필터에서 SecurityContextHolder까지

인증 필터의 일은 요청에서 자격 증명을 꺼내 검증하고, 결과를 `SecurityContextHolder`에 올리는 것이다. `SecurityContextHolder`는 기본으로 `ThreadLocal`에 저장한다. 같은 스레드의 Service 코드는 인자로 넘겨받지 않아도 현재 사용자를 꺼내 쓴다. 반대로 `@Async`처럼 스레드가 바뀌면 사용자 정보가 따라가지 않는다([[threadlocal-and-async-transaction]]).

JWT를 직접 검증하는 필터라면 이렇게 생긴다.

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final TokenVerifier tokenVerifier;

    public JwtAuthenticationFilter(TokenVerifier tokenVerifier) {
        this.tokenVerifier = tokenVerifier;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String header = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (header == null || !header.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }
        try {
            TokenClaims claims = tokenVerifier.verify(header.substring(7));
            var authorities = claims.roles().stream()
                    .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                    .toList();
            SecurityContext context = SecurityContextHolder.createEmptyContext();
            context.setAuthentication(
                    UsernamePasswordAuthenticationToken.authenticated(claims.userId(), null, authorities));
            SecurityContextHolder.setContext(context);
        } catch (InvalidTokenException e) {
            SecurityContextHolder.clearContext();
        }
        chain.doFilter(request, response);
    }
}
```

토큰이 없거나 틀려도 필터가 직접 응답을 쓰지 않는다. 인증 정보를 비운 채 넘기면 뒤쪽 `AuthorizationFilter`가 막고, `ExceptionTranslationFilter`가 응답 코드를 정한다. 그래야 401, 403 응답이 한 곳에서 나온다. 새 `SecurityContext`를 만들어 넣는 이유는 `getContext().setAuthentication()`이 여러 스레드 사이에서 경합을 일으킬 수 있어서다(Spring Security 문서 권고).

서명, 만료, 발급자 검증이 표준 JWT라면 직접 만들기 전에 `oauth2ResourceServer().jwt()`를 먼저 검토한다. 이 설정은 `BearerTokenAuthenticationFilter`와 401 응답용 진입점까지 함께 등록한다.

## 필터를 끼우고 규칙을 적는 곳

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain apiFilterChain(HttpSecurity http, TokenVerifier tokenVerifier) throws Exception {
        http
            .securityMatcher("/api/**")
            .csrf(csrf -> csrf.disable())                      // 쿠키 없이 헤더 토큰만 쓰는 API일 때만
            .cors(Customizer.withDefaults())                   // CorsConfigurationSource 빈을 쓴다
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(HttpMethod.GET, "/api/products/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .addFilterBefore(new JwtAuthenticationFilter(tokenVerifier),
                             UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(e -> e
                .authenticationEntryPoint(new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED)));
        return http.build();
    }
}
```

JWT 필터는 `UsernamePasswordAuthenticationFilter` 앞에 둔다. 인증 필터 자리에 있어야 `AnonymousAuthenticationFilter`보다 먼저 사용자를 넣는다. 필터를 `new`로 만든 이유도 있다. `@Component`로 등록하면 Spring Boot가 같은 필터를 서블릿 컨테이너에도 등록해서 요청마다 두 번, 다른 순서로 돈다. 빈이어야 한다면 `FilterRegistrationBean`을 만들고 `setEnabled(false)`로 컨테이너 등록을 끈다.

`authorizeHttpRequests`의 규칙은 위에서부터 보고 처음 맞는 하나만 적용한다. 넓은 규칙을 위에 두면 아래 규칙은 영영 안 쓰인다. `anyRequest()`는 맨 아래에 둔다.

URL 규칙으로는 "이 주문이 이 사용자 것인가"를 판단하지 못한다. 그런 검사는 메서드 보안이나 Service 코드에서 한다.

```java
@PreAuthorize("hasRole('ADMIN') or @orderAccess.isOwner(#orderId, authentication)")
public OrderDetail getOrder(long orderId) { ... }
```

`@EnableMethodSecurity`를 켜면 `@PreAuthorize`가 동작한다. 메서드 보안은 AOP 프록시로 돌기 때문에 같은 클래스 안에서 호출하면 검사가 빠진다([[aop]]). 권한 검사를 어느 계층에 둘지는 [[authorization-check-location]]에서 다룬다.

## 401과 403이 나오는 자리

인가에 실패하면 `AuthorizationFilter`나 메서드 보안이 `AccessDeniedException`을 던진다. `ExceptionTranslationFilter`가 이 예외를 받아 사용자가 익명인지 본다.

| 상황 | 처리하는 곳 | 응답 |
|---|---|---|
| 토큰 없이 보호된 URL 호출 | `AuthenticationEntryPoint` | 설정한 진입점이 정한다(위 설정은 401) |
| `oauth2ResourceServer` 사용 중 토큰 서명, 만료 오류 | `BearerTokenAuthenticationFilter`가 바로 진입점 호출 | 401 + `WWW-Authenticate` |
| 로그인했지만 `ADMIN`이 아님 | `AccessDeniedHandler` | 403 |
| `@PreAuthorize` 실패 | 예외가 필터 체인까지 올라오면 `AccessDeniedHandler` | 403 |

진입점을 설정하지 않으면 무엇이 나가는지 알아 둔다. 폼 로그인이면 로그인 페이지로 리다이렉트하고, Basic이면 401을 낸다. 인증 방식을 하나도 설정하지 않고 커스텀 필터만 끼웠다면 기본 진입점이 `Http403ForbiddenEntryPoint`라서 로그인 안 한 요청도 403이 나간다. 401과 403을 나누는 이유는 [[authentication-and-authorization]]에 있다.

## 자주 깨지는 곳

- `permitAll`이 필터를 건너뛴다고 여기면, 공개 API에서 401을 맞는다. 인가 판단은 마지막 필터에서 하므로 앞쪽 인증 필터는 그대로 돈다. 만료된 토큰을 들고 공개 API를 부르면 `oauth2ResourceServer`가 먼저 401을 낸다.
- 공개 API를 막지 않으려고 `web.ignoring()`으로 경로를 빼면, 그 경로는 보안 헤더를 포함한 Security 체인 전체를 타지 않는다. Spring Security는 `ignoring` 대신 `permitAll`을 권한다.
- JWT 필터를 `@Component`로 등록하면, 서블릿 컨테이너와 Security 체인에서 한 번씩 두 번 돈다.
- 진입점을 설정하지 않은 채 커스텀 인증 필터만 쓰면, 로그인하지 않은 요청이 401 대신 403으로 나가서 클라이언트가 재로그인 흐름을 타지 못한다.
- `@ControllerAdvice`에서 `Exception`을 통째로 잡으면, `@PreAuthorize`가 던진 `AccessDeniedException`까지 잡혀서 403이 500으로 바뀐다.
- 공개 API에서 예외가 나면 `/error`로 한 번 더 디스패치되는데, `AuthorizationFilter`는 이 ERROR 디스패치도 검사한다. `/error`가 인증 필요로 묶여 있으면 원래 오류 대신 401이 나간다.
- 쿠키 세션으로 인증하는 화면에서 CSRF를 끄면, 다른 사이트에서 보낸 주문 취소 요청이 그대로 처리된다. 끄는 건 헤더 토큰만 쓰는 API일 때다([[csrf]]).
- CORS를 `WebMvcConfigurer`에만 설정하면, 쿠키도 토큰도 없는 preflight가 Security 체인에서 먼저 막힌다. `http.cors()`로 Security에도 등록한다([[01-core/network/cors|cors]]).
- 규칙을 넓은 것부터 적으면, 뒤에 적은 `hasRole("ADMIN")`이 한 번도 적용되지 않는다.

## 운영에서 볼 것

- `logging.level.org.springframework.security=DEBUG`로 띄우면 기동 로그에 `Will secure ... with filters: ...` 줄이 체인마다 찍힌다. 커스텀 필터가 의도한 자리에 있는지 여기서 본다.
- 401, 403이 기대와 다르면 `logging.level.org.springframework.security=TRACE`로 잠깐 켜고 어느 필터에서 거부됐는지 본다. 로그가 많으므로 로컬이나 짧은 시간만 켠다.
- `@WebMvcTest`나 `MockMvc` 테스트로 "토큰 없음 401", "권한 없음 403", "공개 API에 만료 토큰"을 각각 고정해 둔다.
- 401과 403 비율을 따로 본다. 401이 갑자기 늘면 토큰 발급이나 시계 오차를, 403이 늘면 권한 규칙 변경을 먼저 의심한다.

## 한 번에 설명하기

> Spring Security는 서블릿 필터에서 동작합니다. 컨테이너에 등록된 `DelegatingFilterProxy`가 `FilterChainProxy` 빈에 요청을 넘기고, `FilterChainProxy`는 URL에 맞는 첫 번째 `SecurityFilterChain`을 실행합니다.
>
> 체인 앞쪽의 인증 필터가 토큰이나 세션을 검증해서 `SecurityContextHolder`에 사용자를 올리고, 마지막의 `AuthorizationFilter`가 규칙을 보고 통과 여부를 정합니다. 거부되면 `ExceptionTranslationFilter`가 익명 사용자는 `AuthenticationEntryPoint`로 보내 401을, 인증된 사용자는 `AccessDeniedHandler`로 보내 403을 냅니다.
>
> JWT 필터는 인증 필터 자리인 `UsernamePasswordAuthenticationFilter` 앞에 두고, 실패해도 직접 응답하지 않고 인증 정보를 비운 채 넘깁니다. `permitAll`도 필터는 다 지나간다는 점을 기억해서 공개 API의 토큰 처리를 따로 확인합니다.

## 꼬리 질문

> [!question]- DelegatingFilterProxy와 FilterChainProxy는 왜 둘 다 있나?
> 서블릿 컨테이너는 Spring 빈을 모르기 때문에, 컨테이너에는 `DelegatingFilterProxy`를 등록하고 이 필터가 Spring 컨텍스트의 `FilterChainProxy` 빈에 일을 넘깁니다. `FilterChainProxy`는 URL별로 어떤 `SecurityFilterChain`을 탈지 고르고, 요청이 끝나면 `SecurityContextHolder`를 비웁니다.

> [!question]- permitAll로 열어 둔 API인데 401이 나는 이유는?
> `permitAll`은 마지막 `AuthorizationFilter`에서 통과시키는 규칙일 뿐, 앞쪽 인증 필터는 그대로 돕니다. 요청에 만료되거나 잘못된 Bearer 토큰이 붙어 있으면 resource server의 인증 필터가 먼저 실패 처리해서 401을 냅니다.

> [!question]- 로그인하지 않은 요청이 401이 아니라 403으로 나간다. 왜인가?
> 인증 방식을 등록하지 않고 커스텀 필터만 끼우면 기본 `AuthenticationEntryPoint`가 `Http403ForbiddenEntryPoint`입니다. `exceptionHandling`에 401을 내는 진입점을 설정하거나 `oauth2ResourceServer`를 씁니다.

> [!question]- JWT 필터는 어디에 넣고, 빈으로 등록해도 되나?
> `addFilterBefore(..., UsernamePasswordAuthenticationFilter.class)`로 인증 필터 자리에 넣습니다. `@Component`로 등록하면 Spring Boot가 서블릿 컨테이너에도 등록해서 두 번 돌기 때문에, 빈이어야 한다면 `FilterRegistrationBean`으로 컨테이너 등록을 끕니다.

> [!question]- @PreAuthorize가 실패했는데 500이 나간다. 어디를 보나?
> 전역 예외 처리기가 `Exception`을 통째로 잡고 있는지 봅니다. `AccessDeniedException`이 거기서 잡히면 `ExceptionTranslationFilter`까지 올라가지 못해 403이 되지 않습니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Security 6.5: Architecture](https://docs.spring.io/spring-security/reference/6.5/servlet/architecture.html)
- [Spring Security 6.5: Authorize HttpServletRequests](https://docs.spring.io/spring-security/reference/6.5/servlet/authorization/authorize-http-requests.html)
- [Spring Security 6.5: Servlet Authentication Architecture](https://docs.spring.io/spring-security/reference/6.5/servlet/authentication/architecture.html)

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[session-and-token]]
- [[csrf]]
- [[01-core/network/cors|cors]]
- [[filter-interceptor-aop]]
- [[oauth2-and-oidc]]
