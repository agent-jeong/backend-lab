---
title: Filter vs Interceptor vs AOP
description: Spring 요청 처리 흐름에서 Filter, Interceptor, AOP의 실행 시점과 선택 기준
tags: [concept, spring]
---

# Filter vs Interceptor vs AOP

셋 다 공통 처리를 끼워 넣는 자리지만 끼어드는 층이 다르다. Filter는 서블릿 컨테이너에서 요청과 응답을 가로채고, Interceptor는 DispatcherServlet 이후 Controller 전후에서, AOP는 특정 빈의 메서드 실행 전후에서 동작한다.

어느 층인지 모르고 고르면 로깅, 인증, 인코딩 코드가 엉뚱한 자리에 들어간다. Spring Security의 Filter Chain도 Filter가 어디 있는지 알아야 읽힌다.

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

## 각각 무엇에 쓰나

### Filter

서블릿 스펙이라 Spring에 의존하지 않고, 요청과 응답 객체 자체를 바꿀 수 있다.

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

쓰는 곳: 인코딩 설정, CORS 처리, body를 래핑한 요청/응답 로깅, Spring Security 인증/인가(FilterChain), XSS 방어.

### Interceptor

Spring MVC가 제공하고, Controller 호출 전후에 동작한다.

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

쓰는 곳: 간단한 인증/인가 체크, Controller 기준 API 요청 로깅, 요청별 공통 데이터 세팅, Controller 단위 실행 시간 측정.

### AOP

Spring 빈의 메서드 단위로 동작한다. URL이 아니라 클래스와 메서드를 골라 적용한다.

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

쓰는 곳: 트랜잭션 관리(`@Transactional`), Service/Repository 메서드 실행 시간 측정, 재시도(`@Retryable`), 메서드 수준 권한 체크, 캐싱(`@Cacheable`).

## 요구사항별로 고르기

| 요구사항 | 선택 | 이유 |
|---|---|---|
| 모든 요청의 인코딩/CORS | Filter | DispatcherServlet 전에 처리해야 함 |
| 요청/응답 body 로깅 | Filter | body를 래핑해서 읽어야 함 |
| Spring Security 인증 | Filter | Security Filter Chain이 Filter 레벨 |
| 특정 URL의 인증 체크 | Interceptor | URL 패턴 + Spring 빈 접근 필요 |
| Controller 실행 전 공통 검증 | Interceptor | Handler 정보 접근 가능 |
| Service 메서드 실행 시간 | AOP | 메서드 단위 적용 |
| 트랜잭션, 캐싱, 재시도 | AOP | 메서드 수준 횡단 관심사 |

## 자주 깨지는 곳

- **Filter에 `@Autowired`로 빈을 주입하려 한다.** 동작하지 않는다. `DelegatingFilterProxy`가 필요하다.
- **Interceptor에서 request body를 읽는다.** body는 한 번만 읽히는 스트림이라 Controller에서 다시 읽지 못한다.
- **AOP를 URL 기준으로 걸려고 한다.** AOP는 빈과 메서드 기준이다.
- **공통 로직을 전부 AOP로 해결하려 한다.** Filter나 Interceptor가 맞는 자리를 놓친다.
- **`postHandle`이 항상 불린다고 믿는다.** Controller에서 예외가 나면 `postHandle`은 호출되지 않고 `afterCompletion`만 호출된다.

## 면접에서 말하기

> Filter는 서블릿 컨테이너에서 모든 요청을 가로채고, Interceptor는 Spring MVC에서 Controller 전후에, AOP는 빈의 메서드 단위로 동작합니다. 저는 요청과 응답 자체를 바꿔야 하면 Filter, URL과 Handler 기준이면 Interceptor, 메서드 수준 공통 관심사면 AOP를 고릅니다. Spring Security가 Filter에서, `@Transactional`이 AOP에서 동작한다는 걸 알면 전체 구조가 보입니다.

## 꼬리 질문

> [!question]- Spring Security는 왜 Filter에서 동작하는가?
> 인증/인가는 DispatcherServlet에 도달하기 전에 처리해야 합니다. 인증에 실패한 요청이 Controller까지 가면 쓸데없이 자원을 쓰고, 그 자체로 보안 위협이 됩니다.

> [!question]- Interceptor의 preHandle에서 false를 반환하면?
> Controller 메서드와 postHandle은 호출되지 않습니다. afterCompletion은 앞에서 true를 반환한 interceptor들만 역순으로 호출되고, false를 반환한 그 interceptor의 afterCompletion은 호출되지 않습니다. 응답은 preHandle에서 직접 써야 합니다.

> [!question]- Filter에서 request body를 로깅하려면?
> `ContentCachingRequestWrapper`로 request를 래핑해서 body를 여러 번 읽을 수 있게 합니다. 원본 request의 InputStream은 한 번만 읽히므로, 직접 읽으면 Controller가 읽을 게 없습니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring Security가 주로 Filter 체인에서 동작하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="인증/인가 판단은 DispatcherServlet에 도달하기 전 요청 경계에서 처리해야 하는 경우가 많기 때문이다." aria-pressed="false">A. Spring MVC 진입 전 HTTP 요청 경계에서 보안 처리가 필요하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Security가 Controller 내부 로직만 다루는 것은 아니다." aria-pressed="false">B. Controller 메서드 실행 후에만 인증해야 하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="보안 처리를 DB 트랜잭션 뒤로 미루면 안 된다." aria-pressed="false">C. 트랜잭션 커밋 뒤에만 권한을 확인해야 하기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Interceptor의 preHandle에서 false를 반환하면 이후 Handler 실행을 막을 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="인증 실패, 권한 부족, 요청 차단 같은 경우에 핸들러 진입 전 흐름을 중단할 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="preHandle의 반환값은 요청 진행 여부에 영향을 준다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Filter에서 request body를 로깅할 때 주의할 점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Servlet request body는 한 번 읽으면 다시 읽기 어려우므로 wrapping하고, 민감 정보 마스킹도 필요하다." aria-pressed="false">A. body 재사용 가능 wrapper와 민감 정보 마스킹을 고려한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="body를 무조건 읽으면 컨트롤러에서 body를 못 읽는 문제가 생길 수 있다." aria-pressed="false">B. 그냥 InputStream을 모두 읽고 버린다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="header만 복사해도 body 재사용 문제가 해결되지는 않는다." aria-pressed="false">C. 헤더만 복사하면 body도 자동 복원된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Spring Framework: Interceptors](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-config/interceptors.html)
- [Spring Framework: Filters](https://docs.spring.io/spring-framework/reference/web/webmvc/filters.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[spring-mvc-request-flow]]
- [[aop]]
- [[validation-and-exception-handling]]