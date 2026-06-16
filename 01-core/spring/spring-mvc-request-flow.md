---
title: Spring MVC 요청 처리 흐름
description: Spring MVC의 요청 처리 흐름과 각 컴포넌트의 역할
---

# Spring MVC 요청 처리 흐름

## 한 줄 정의

Spring MVC는 HTTP 요청을 DispatcherServlet이 받아서 Handler → 비즈니스 로직 → View 또는 Response Body로 변환하는 요청 처리 아키텍처다.

## 실무에서 왜 중요한가

요청 흐름을 모르면 다음 상황에서 원인을 파악하기 어렵다.

- 404가 발생했는데 컨트롤러 매핑 문제인지 필터 문제인지 구분하지 못한다.
- `@RequestBody`가 바인딩되지 않는 원인을 모른다.
- Filter, Interceptor, AOP의 실행 순서를 모르고 예외 처리 위치를 잘못 잡는다.
- `@ExceptionHandler`가 동작하지 않는 범위를 이해하지 못한다.

## 요청 처리 흐름

```
1. 클라이언트 → HTTP 요청
2. Filter (서블릿 필터)
3. DispatcherServlet
4. HandlerMapping → 어떤 Controller 메서드를 호출할지 결정
5. HandlerInterceptor.preHandle()
6. HandlerAdapter → Controller 메서드 실행
   - ArgumentResolver: 파라미터 바인딩 (@RequestBody, @PathVariable 등)
   - Controller → Service → Repository
   - ReturnValueHandler: 반환값 처리 (@ResponseBody → JSON 변환)
7. HandlerInterceptor.postHandle()
8. ViewResolver (뷰 반환 시) 또는 HttpMessageConverter (JSON 반환 시)
9. HandlerInterceptor.afterCompletion()
10. Filter (응답)
11. 클라이언트 ← HTTP 응답
```

## 핵심 컴포넌트

### DispatcherServlet

모든 HTTP 요청의 진입점이다. Front Controller 패턴으로 요청을 적절한 핸들러에 위임한다.

### HandlerMapping

요청 URL과 HTTP 메서드를 기반으로 어떤 Controller 메서드를 호출할지 결정한다.

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @GetMapping("/{id}")  // GET /api/orders/1 → 이 메서드에 매핑
    public OrderResponse getOrder(@PathVariable Long id) {
        return orderService.getOrder(id);
    }
}
```

### ArgumentResolver

Controller 메서드의 파라미터를 HTTP 요청에서 추출해서 바인딩한다.

| 어노테이션 | 소스 | 예시 |
|---|---|---|
| `@PathVariable` | URL 경로 | `/orders/{id}` |
| `@RequestParam` | 쿼리 파라미터 | `?page=1&size=10` |
| `@RequestBody` | 요청 본문 (JSON) | `{"name": "order1"}` |
| `@RequestHeader` | HTTP 헤더 | `Authorization: Bearer ...` |

### HttpMessageConverter

`@RequestBody`로 JSON → 객체 변환, `@ResponseBody`로 객체 → JSON 변환을 처리한다. Spring Boot에서는 Jackson이 기본 Converter다.

## Filter, Interceptor, AOP의 위치

요청 흐름에서 각 계층이 어디에서 동작하는지가 핵심이다.

```
HTTP 요청 → Filter → DispatcherServlet → Interceptor → AOP → Controller
```

각 계층의 상세 비교, 코드 예제, 실무 선택 기준은 [[filter-interceptor-aop]]에서 다룬다.

## 예외 처리 흐름

### @ExceptionHandler

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleBadRequest(IllegalArgumentException e) {
        return ResponseEntity.badRequest()
            .body(new ErrorResponse(e.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnexpected(Exception e) {
        log.error("Unexpected error", e);
        return ResponseEntity.internalServerError()
            .body(new ErrorResponse("서버 오류가 발생했습니다."));
    }
}
```

`@ExceptionHandler`는 Controller에서 발생한 예외를 처리한다. Filter에서 발생한 예외는 잡지 못한다.

## 자주 나는 실수

- `@RequestBody`에 기본 생성자가 없어서 바인딩이 실패한다.
- Filter에서 발생한 예외를 `@ExceptionHandler`로 처리하려 한다.
- Interceptor에서 `preHandle()`이 `false`를 반환하면 Controller가 실행되지 않는 것을 모른다.
- `@RestController`와 `@Controller`의 차이를 모르고 JSON 응답에 `@ResponseBody`를 빠뜨린다.
- Filter와 Interceptor의 역할을 구분하지 않고 혼용한다.

## 핵심 요약

Spring MVC는 DispatcherServlet이 모든 요청을 받아서 HandlerMapping → Controller → ViewResolver 순서로 처리합니다.

실행 순서는 Filter → Interceptor → AOP → Controller이며, 각 계층의 상세 비교는 [[filter-interceptor-aop]]를 참고합니다.

`@ExceptionHandler`는 Controller 계층의 예외만 처리합니다.
Filter에서 발생한 예외는 별도로 처리해야 합니다.

## 꼬리 질문

> [!question]- `@Controller`와 `@RestController`의 차이는?
> `@RestController`는 `@Controller` + `@ResponseBody`입니다. `@Controller`는 View 이름을 반환하고, `@RestController`는 반환값을 JSON으로 직렬화합니다.

> [!question]- `@RequestBody` 바인딩이 실패하는 원인은?
> 대표적으로 기본 생성자 누락, 필드명 불일치, Content-Type 미설정(`application/json`), Jackson 어노테이션 오류 등이 있습니다.

> [!question]- DispatcherServlet의 역할은?
> Front Controller 패턴의 구현체로, 모든 HTTP 요청을 중앙에서 받아 적절한 Handler에 위임합니다. HandlerMapping, HandlerAdapter, ViewResolver 등을 조합해서 요청을 처리합니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[filter-interceptor-aop]]
- [[validation-and-exception-handling]]