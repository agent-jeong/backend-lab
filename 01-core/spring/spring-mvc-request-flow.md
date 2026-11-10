---
title: Spring MVC 요청 처리 흐름
description: Spring MVC의 요청 처리 흐름과 각 컴포넌트의 역할
---

# Spring MVC 요청 처리 흐름

Spring MVC에서는 DispatcherServlet이 모든 HTTP 요청을 받아 Handler를 고르고, 비즈니스 로직을 거친 결과를 View나 Response Body로 바꿔 돌려준다.

이 흐름을 알아야 장애 위치를 좁힐 수 있다. 404가 컨트롤러 매핑 문제인지 필터 문제인지, `@RequestBody`가 왜 바인딩되지 않는지, `@ExceptionHandler`가 왜 어떤 예외는 못 잡는지가 모두 "요청이 지금 어느 단계에 있나"로 풀린다.

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

## 단계별 컴포넌트

### DispatcherServlet

모든 HTTP 요청의 진입점이다. Front Controller 패턴으로 요청을 받아 맞는 핸들러에 넘긴다.

### HandlerMapping

요청 URL과 HTTP 메서드를 보고 어떤 Controller 메서드를 부를지 정한다.

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

HTTP 요청에서 값을 꺼내 Controller 메서드 파라미터에 바인딩한다.

| 어노테이션 | 소스 | 예시 |
|---|---|---|
| `@PathVariable` | URL 경로 | `/orders/{id}` |
| `@RequestParam` | 쿼리 파라미터 | `?page=1&size=10` |
| `@RequestBody` | 요청 본문 (JSON) | `{"name": "order1"}` |
| `@RequestHeader` | HTTP 헤더 | `Authorization: Bearer ...` |

### HttpMessageConverter

`@RequestBody`면 JSON을 객체로, `@ResponseBody`면 객체를 JSON으로 바꾼다. Spring Boot의 기본 Converter는 Jackson이다.

## Filter, Interceptor, AOP의 위치

```
HTTP 요청 → Filter → DispatcherServlet → Interceptor → AOP → Controller
```

계층별 비교, 코드 예제, 고르는 기준은 [[filter-interceptor-aop]]에 있다.

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

`@ExceptionHandler`는 Controller에서 난 예외만 처리한다. Filter는 DispatcherServlet 앞에 있어서 거기서 난 예외는 잡지 못하고 따로 처리해야 한다.

## 자주 깨지는 곳

- **`@RequestBody` 대상에 기본 생성자가 없다.** 바인딩이 실패한다.
- **Filter 예외를 `@ExceptionHandler`로 잡으려 한다.** 잡히지 않는다.
- **`preHandle()`이 `false`를 반환한 뒤를 모른다.** Controller가 실행되지 않는다.
- **`@Controller`에서 JSON을 반환하면서 `@ResponseBody`를 빠뜨린다.** 반환값이 View 이름으로 해석된다.
- **Filter와 Interceptor를 구분 없이 쓴다.** 같은 처리가 두 곳에 흩어진다.

## 면접에서 말하기

> Spring MVC는 DispatcherServlet이 모든 요청을 받아 HandlerMapping으로 Controller를 찾고, 결과를 ViewResolver나 MessageConverter로 응답에 씁니다. 실행 순서는 Filter, Interceptor, AOP, Controller입니다. `@ExceptionHandler`는 Controller 쪽 예외만 잡기 때문에, Filter에서 나는 예외는 따로 처리합니다.

## 꼬리 질문

> [!question]- `@Controller`와 `@RestController`의 차이는?
> `@RestController`는 `@Controller` + `@ResponseBody`입니다. `@Controller`는 View 이름을 반환하고, `@RestController`는 반환값을 JSON으로 직렬화합니다.

> [!question]- `@RequestBody` 바인딩이 실패하는 원인은?
> 기본 생성자 누락, 필드명 불일치, Content-Type(`application/json`) 미설정, Jackson 어노테이션 오류가 대표적입니다.

> [!question]- DispatcherServlet의 역할은?
> Front Controller 패턴의 구현체로, 모든 HTTP 요청을 한곳에서 받아 맞는 Handler에 넘깁니다. HandlerMapping, HandlerAdapter, ViewResolver 등을 조합해 요청을 처리합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>DispatcherServlet의 역할은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="요청을 받아 HandlerMapping, HandlerAdapter, ViewResolver/MessageConverter 등 Spring MVC 구성요소로 위임하는 front controller다." aria-pressed="false">A. Spring MVC 요청 처리의 front controller</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DispatcherServlet이 직접 모든 SQL을 실행하지 않는다." aria-pressed="false">B. 모든 Repository 메서드를 직접 호출하는 객체</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DispatcherServlet은 JVM GC를 제어하는 구성요소가 아니다." aria-pressed="false">C. GC 튜닝을 담당하는 JVM 컴포넌트</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>@RestController는 @Controller와 @ResponseBody를 합친 성격이라 보통 객체를 HTTP 응답 body로 직렬화한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="REST API는 View 이름이 아니라 MessageConverter가 body를 써서 응답한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@RestController는 View 렌더링 중심 컨트롤러와 응답 처리 방식이 다르다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@RequestBody 바인딩이 실패하는 대표 원인은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="잘못된 JSON 형식, Content-Type 누락, 기본 생성자/생성자 매핑 문제, 타입 불일치 등이 원인이 될 수 있다." aria-pressed="false">A. JSON 형식, Content-Type, DTO 생성/타입 매핑 문제</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="GET만 바인딩 가능한 것이 아니다." aria-pressed="false">B. @RequestBody는 GET 요청에서만 동작하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Controller 이름 길이와 직접적인 관계는 없다." aria-pressed="false">C. Controller 클래스명이 너무 길기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[filter-interceptor-aop]]
- [[validation-and-exception-handling]]