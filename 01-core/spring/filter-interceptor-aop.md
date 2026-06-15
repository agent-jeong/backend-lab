---
title: Filter vs Interceptor vs AOP
description: Spring 요청 처리 흐름에서 Filter, Interceptor, AOP의 실행 시점과 선택 기준
---

# Filter vs Interceptor vs AOP

## 한 줄 정의

Filter는 서블릿 컨테이너 수준에서 요청/응답을 가로채고, Interceptor는 Spring MVC의 DispatcherServlet 이후에 동작하며, AOP는 특정 빈의 메서드 실행 전후에 동작하는 횡단 관심사 처리 기법이다.

## 실무에서 왜 중요한가

- 로깅, 인증, 인코딩 등 공통 처리를 어디에 구현할지 판단하지 못하면 부적절한 위치에 코드를 넣게 된다.
- Spring Security의 Filter Chain을 이해하려면 Filter의 위치를 알아야 한다.
- 면접에서 "세 가지의 차이와 선택 기준"을 설명하라는 질문이 자주 나온다.

## 실행 흐름

```
HTTP 요청
    │
    ▼
┌───────────────────────────────────────────���─┐
│  Servlet Container (Tomcat)                 │
│  ┌───────────────────────────────────────┐  │
│  │  Filter Chain                         │  │
│  │  Filter 1 → Filter 2 → Filter 3      │  │
│  └───────────────┬───────────────────────┘  │
└──────────────────┼──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Spring MVC (DispatcherServlet)             │
│  ┌───────────────────────────────────────┐  │
│  │  HandlerInterceptor                   │  │
│  │  preHandle → Controller → postHandle  │  │
│  └───────────────┬───────────────────────┘  │
│                  ▼                           │
│  ┌───────────────────────────────────────┐  │
│  │  AOP Proxy                            │  │
│  │  @Around → Service 메서드 → @Around   │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## 비교

| 구분 | Filter | Interceptor | AOP |
|---|---|---|---|
| 소속 | Servlet Container | Spring MVC | Spring Bean |
| 동작 위치 | DispatcherServlet 이전/이후 | Controller 이전/이후 | 빈 메서드 실행 전후 |
| 설정 대상 | URL 패턴 | URL 패턴 + Handler | 포인트컷 (클래스, 메서드) |
| Spring 빈 접근 | 제한적 (DelegatingFilterProxy 필요) | 가능 | 가능 |
| 예외 처리 | 직접 처리 (try-catch) | Spring MVC 예외 처리 활용 가능 | Spring MVC 예외 처리 활용 가능 |
| Request/Response 조작 | 가능 (래핑) | 가능 | 불가 |
| 적용 대상 | 모든 요청 (정적 리소스 포함) | Spring MVC 요청만 | 지정한 빈의 메서드 |

## 각각의 역할과 예시

### Filter

서블릿 스펙이므로 Spring에 의존하지 않는다. 요청/응답 자체를 조작할 수 있다.

```java
@Component
public class EncodingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response,
                         FilterChain chain) throws IOException, ServletException {
        request.setCharacterEncoding("UTF-8");
        chain.doFilter(request, response); // 다음 필터 또는 서블릿으로 전달
    }
}
```

**적합한 용도**:
- 인코딩 설정
- CORS 처리
- 요청/응답 로깅 (body 래핑)
- Spring Security 인증/인가 (FilterChain)
- XSS 방어

### Interceptor

Spring MVC에서 제공하며, Controller 호출 전후에 동작한다.

```java
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        String token = request.getHeader("Authorization");
        if (!tokenService.isValid(token)) {
            response.setStatus(401);
            return false; // Controller 호출 안 함
        }
        return true;
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response,
                           Object handler, ModelAndView modelAndView) {
        // Controller 실행 후, 뷰 렌더링 전
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        // 뷰 렌더링 후 (리소스 정리)
    }
}
```

**적합한 용도**:
- 인증/인가 체크 (간단한 경우)
- API 요청 로깅 (Controller 기준)
- 요청별 공통 데이터 세팅
- 실행 시간 측정 (Controller 단위)

### AOP

Spring 빈의 메서드 수준에서 동작한다. URL이 아닌 클래스/메서드 단위로 적용.

```java
@Aspect
@Component
public class ServiceLoggingAspect {

    @Around("execution(* com.example.service.*.*(..))")
    public Object logExecutionTime(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long elapsed = System.currentTimeMillis() - start;
        log.info("{} executed in {}ms", joinPoint.getSignature().getName(), elapsed);
        return result;
    }
}
```

**적합한 용도**:
- 트랜잭션 관리 (`@Transactional`)
- Service/Repository 메서드 실행 시간 측정
- 재시도 로직 (`@Retryable`)
- 메서드 수준 권한 체크
- 캐싱 (`@Cacheable`)

## 실무 선택 기준

| 요구사항 | 선택 | 이유 |
|---|---|---|
| 모든 요청의 인코딩/CORS | Filter | DispatcherServlet 전에 처리해야 함 |
| 요청/응답 body 로깅 | Filter | body를 래핑해서 읽어야 함 |
| Spring Security 인증 | Filter | Security Filter Chain이 Filter 레벨 |
| 특정 URL의 인증 체크 | Interceptor | URL 패턴 + Spring 빈 접근 필요 |
| Controller 실행 전 공통 검증 | Interceptor | Handler 정보 접근 가능 |
| Service 메서드 실행 시간 | AOP | 메서드 단위 적용 |
| 트랜잭션, 캐싱, 재시도 | AOP | 메서드 수준 횡단 관심사 |

## 자주 나는 실수

- Filter에서 Spring 빈을 주입받으려고 `@Autowired`를 쓰는데 동작하지 않는다 (DelegatingFilterProxy 필요).
- Interceptor에서 request body를 읽으면 Controller에서 다시 읽을 수 없다 (body는 1회성 스트림).
- AOP를 URL 기반으로 적용하려고 한다 (AOP는 빈/메서드 기반).
- 모든 공통 로직을 AOP로 해결하려고 해서 Filter/Interceptor가 더 적합한 경우를 놓친다.
- Interceptor의 `postHandle`은 Controller 예외 시 호출되지 않는 것을 모른다 (`afterCompletion`은 호출됨).

## 핵심 요약

Filter는 서블릿 컨테이너 수준에서 모든 요청을 가로채고, Interceptor는 Spring MVC의 Controller 전후에 동작하며, AOP는 빈의 메서드 단위에서 동작합니다.

요청/응답 조작이 필요하면 Filter, URL + Handler 기준 처리는 Interceptor, 메서드 수준 횡단 관심사는 AOP를 사용합니다.
Spring Security는 Filter 레벨에서 동작하고, `@Transactional`은 AOP로 동작한다는 것을 이해하면 전체 구조가 보입니다.

## 꼬리 질문

> [!question]- Spring Security는 왜 Filter에서 동작하는가?
> 인증/인가는 DispatcherServlet에 도달하기 전에 처리해야 합니다. 인증 실패한 요청이 Controller까지 도달하면 불필요한 리소스를 소비하고, 보안 위협이 됩니다.

> [!question]- Interceptor의 preHandle에서 false를 반환하면?
> Controller 메서드가 호출되지 않고, postHandle도 호출되지 않습니다. 하지만 afterCompletion은 호출됩니다. 응답 처리는 preHandle에서 직접 해야 합니다.

> [!question]- Filter에서 request body를 로깅하려면?
> `ContentCachingRequestWrapper`로 request를 래핑해서 body를 여러 번 읽을 수 있게 합니다. 원본 request의 InputStream은 1회성이므로 직접 읽으면 Controller에서 읽을 수 없습니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[spring-mvc-request-flow]]
- [[aop]]
- [[validation-and-exception-handling]]