---
title: Spring MVC 요청 처리 흐름
description: HTTP 요청 하나가 DispatcherServlet에서 Controller를 거쳐 응답이 되기까지
tags: [concept, spring]
---

# Spring MVC 요청 처리 흐름

Spring MVC에서는 DispatcherServlet이 모든 HTTP 요청을 먼저 받는다. 어느 Controller 메서드로 보낼지 고르고, 메서드가 돌려준 결과를 View나 JSON 응답으로 바꿔 내보낸다.

주문 조회 API가 404를 내거나, 주문 생성 요청의 body가 null로 들어오거나, 만들어 둔 `@ExceptionHandler`가 어떤 예외는 못 잡을 때가 있다. 이럴 때 "요청이 지금 어느 단계까지 왔나"를 따지면 원인이 Filter인지, 매핑인지, 바인딩인지 금방 좁혀진다.

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
   - ReturnValueHandler: 반환값 처리
     @ResponseBody(JSON)면 여기서 HttpMessageConverter가 응답 본문을 바로 쓴다
7. HandlerInterceptor.postHandle()
8. ViewResolver → View 렌더링 (뷰 이름을 반환했을 때만)
9. HandlerInterceptor.afterCompletion()
10. Filter (응답)
11. 클라이언트 ← HTTP 응답
```

## 단계별 컴포넌트

### DispatcherServlet

모든 HTTP 요청이 처음 들어오는 곳이다. Front Controller 패턴으로, 요청을 한곳에서 받아 맞는 핸들러에 넘긴다.

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

HTTP 요청에서 값을 꺼내 Controller 메서드 파라미터에 채워 넣는다.

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
HTTP 요청 → Filter → DispatcherServlet → Interceptor → Controller → AOP 프록시 → Service
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

REST API(`@RestController`)에서는 6단계에서 JSON이 이미 응답에 쓰인다. 그래서 `postHandle()`에서 응답 본문이나 헤더를 바꾸려 해도 늦다. 응답을 손봐야 하면 `ResponseBodyAdvice`나 Filter를 쓴다.

`@ExceptionHandler`는 Controller 쪽에서 난 예외만 잡는다. Filter는 DispatcherServlet보다 앞에 있어서, 거기서 난 예외는 여기까지 오지 않는다. Filter 안에서 따로 처리해야 한다. `Exception` 핸들러 하나가 Spring MVC 표준 예외까지 500으로 바꾸는 문제는 [[validation-and-exception-handling]]에 있다.

## 자주 깨지는 곳

- `@RequestBody`로 받는 클래스를 Jackson이 만들 방법(기본 생성자, record, `@JsonCreator`, `-parameters`로 컴파일한 생성자)이 하나도 없으면, 바인딩이 실패한다.
- Filter에서 난 예외를 `@ExceptionHandler`로 잡으려 하면, 잡히지 않는다.
- `preHandle()`이 `false`를 반환하면 Controller가 실행되지 않는데, 이걸 모르고 응답을 안 쓰면 클라이언트는 빈 응답을 받는다.
- `@Controller`에서 JSON을 반환하면서 `@ResponseBody`를 빠뜨리면, 반환값이 View 이름으로 해석된다.
- Filter와 Interceptor를 기준 없이 섞어 쓰면, 같은 처리가 두 곳에 흩어진다.

## 한 번에 설명하기

> Spring MVC에서는 DispatcherServlet이 모든 요청을 받아 HandlerMapping으로 Controller를 찾고, 결과를 ViewResolver나 MessageConverter로 응답에 씁니다. 요청은 Filter, Interceptor, Controller 순서로 지나가고, Service 메서드 앞에서 AOP 프록시가 끼어듭니다.
>
> `@ExceptionHandler`는 Controller 쪽 예외만 잡아서, Filter에서 나는 예외는 따로 처리합니다.

## 꼬리 질문

> [!question]- `@Controller`와 `@RestController`의 차이는?
> `@RestController`는 `@Controller`에 `@ResponseBody`를 합친 것입니다. `@Controller`가 돌려준 문자열은 View 이름으로 쓰이고, `@RestController`가 돌려준 객체는 JSON으로 바뀌어 응답 본문에 들어갑니다.

> [!question]- `@RequestBody` 바인딩이 실패하는 원인은?
> 자주 보는 건 넷입니다. Jackson이 객체를 만들 생성자를 찾지 못하거나, JSON 필드 이름과 클래스 필드 이름이 다르거나, Content-Type을 `application/json`으로 안 보냈거나, Jackson 어노테이션을 잘못 단 경우입니다.

> [!question]- DispatcherServlet의 역할은?
> Front Controller 패턴을 구현한 것으로, 모든 HTTP 요청을 한곳에서 받아 맞는 Handler에 넘깁니다. 직접 일을 다 하지는 않고 HandlerMapping, HandlerAdapter, ViewResolver 같은 부품을 불러서 요청을 처리합니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: DispatcherServlet](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[filter-interceptor-aop]]
- [[validation-and-exception-handling]]
- [[request-journey]]
