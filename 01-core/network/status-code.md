---
title: "HTTP 상태 코드 사용 기준"
description: HTTP 상태 코드를 언제 무엇으로 주고, 재시도 판단에 어떻게 쓰는지
tags: [concept, network]
---

# HTTP 상태 코드 사용 기준

HTTP 상태 코드는 서버가 요청을 어떻게 처리했는지 숫자로 알려 주는 코드다.

클라이언트, 프록시, 모니터링은 바디보다 상태 코드를 먼저 본다. 주문 조회 실패를 200으로 주고 바디에만 에러를 담으면 클라이언트는 성공으로 처리하고, 에러율 대시보드에도 잡히지 않는다. 400과 404를 섞어 쓰면 주문이 없는 건지 요청이 틀린 건지 구분이 안 되고, 아무 에러나 500으로 주면 누구 탓인지, 다시 보내도 되는지 알 수 없다.

## 분류

| 범위 | 분류 | 의미 |
|---|---|---|
| 1xx | Informational | 처리 진행 중 |
| 2xx | Success | 요청 성공 |
| 3xx | Redirection | 추가 동작 필요 |
| 4xx | Client Error | 클라이언트 요청 오류 |
| 5xx | Server Error | 서버 처리 오류 |

## 2xx: 성공

| 코드 | 의미 | 사용 시점 |
|---|---|---|
| 200 OK | 요청 성공 | GET 조회, PUT 수정 성공 |
| 201 Created | 리소스 생성 | POST로 새 리소스 생성 시 |
| 204 No Content | 성공, 응답 바디 없음 | DELETE 성공, 바디가 필요 없을 때 |

```java
@PostMapping("/api/orders")
public ResponseEntity<OrderResponse> createOrder(@RequestBody OrderRequest request) {
    OrderResponse response = orderService.create(request);
    return ResponseEntity.status(HttpStatus.CREATED)
        .header("Location", "/api/orders/" + response.getId())
        .body(response);
}

@DeleteMapping("/api/orders/{id}")
public ResponseEntity<Void> deleteOrder(@PathVariable Long id) {
    orderService.delete(id);
    return ResponseEntity.noContent().build();
}
```

## 4xx: 클라이언트 에러

| 코드 | 의미 | 사용 시점 |
|---|---|---|
| 400 Bad Request | 요청 형식/값 오류 | 검증 실패, 잘못된 파라미터 |
| 401 Unauthorized | 인증 필요 | 토큰 없음, 토큰 만료 |
| 403 Forbidden | 인가 실패 (권한 없음) | 인증은 됐지만 권한이 없음 |
| 404 Not Found | 리소스 없음 | 존재하지 않는 ID 조회 |
| 405 Method Not Allowed | 허용되지 않은 메서드 | POST만 가능한데 GET 요청 |
| 409 Conflict | 리소스 충돌 | 중복 등록, 상태 충돌 |
| 422 Unprocessable Entity | 문법은 맞지만 처리 불가 | 비즈니스 규칙 위반 |
| 429 Too Many Requests | 요청 횟수 초과 | Rate Limit 초과 |

### 401 vs 403

```
401 Unauthorized: "누구세요?" → 인증이 안 됨 (로그인 필요)
403 Forbidden:    "권한 없음"  → 인증은 됐지만 접근할 수 없음
```

### 400 vs 422

```
400 Bad Request:          요청 자체가 잘못됨 (JSON 파싱 실패, 필수 필드 누락)
422 Unprocessable Entity: 요청 형식은 맞지만 비즈니스 규칙 위반 (잔액 부족, 재고 없음)
```

실무에서는 400 하나로 통일하는 팀도 많다. 어느 쪽이든 팀 안에서는 하나로 맞춘다.

## 5xx: 서버 에러

| 코드 | 의미 | 사용 시점 |
|---|---|---|
| 500 Internal Server Error | 서버 내부 오류 | 예상치 못한 예외 |
| 502 Bad Gateway | 업스트림 서버 응답 오류 | 프록시/LB 뒤의 서버 에러 |
| 503 Service Unavailable | 서비스 일시적 불가 | 서버 과부하, 배포 중 |
| 504 Gateway Timeout | 업스트림 서버 응답 시간 초과 | 프록시/LB의 timeout |

### 502 vs 503 vs 504

```
502: LB가 백엔드 서버에 요청했는데 잘못된 응답을 받음
503: 서버가 요청을 처리할 수 없는 상태 (과부하, 점검)
504: LB가 백엔드 서버의 응답을 기다리다 timeout
```

## 재시도해도 되나

| 상태 코드 | 재시도 가능 | 이유 |
|---|---|---|
| 408 | O | 요청 시간 초과 (일시적) |
| 429 | O | Rate Limit (Retry-After 대기 후) |
| 500 | △ | 원인에 따라 다름 |
| 503 | O | 일시적 불가. `Retry-After`가 있으면 따른다 |
| 502, 504 | 멱등 요청만 O | 서버가 이미 처리했는데 응답만 못 받았을 수 있다. POST 결제를 504 후 재시도하면 이중 결제가 난다 |
| 400, 401, 403, 404 | X | 같은 요청을 보내도 결과 동일 |

## 에러 응답 형식

에러 응답은 모든 API에서 같은 모양으로 준다. 그래야 클라이언트가 에러를 한 군데에서 처리한다.

```java
// 일관된 에러 응답 형식
{
    "code": "ORDER_NOT_FOUND",
    "message": "주문을 찾을 수 없습니다.",
    "status": 404
}
```

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(EntityNotFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("NOT_FOUND", e.getMessage(), 404));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_ERROR", message, 400));
    }
}
```

## 자주 깨지는 곳

- 모든 응답을 200으로 주고 바디의 `success` 필드로 성공과 실패를 나누면, 모니터링도 캐싱도 재시도 판단도 상태 코드를 쓸 수 없다.
- 잔액 부족 같은 비즈니스 에러를 500으로 주면, 진짜 서버 에러와 섞여서 장애를 알아보기 어렵다.
- 401과 403을 섞어 쓰면, 클라이언트가 다시 로그인해야 하는지 권한이 없는 건지 모른다.
- 리소스를 만들고 201 대신 200을 주면서 `Location` 헤더까지 빠뜨리면, 클라이언트는 새로 생긴 리소스가 어디 있는지 알 수 없다.
- API마다 에러 응답 형식이 다르면 클라이언트가 에러를 한 방식으로 처리하지 못한다.

## 한 번에 설명하기

> 상태 코드는 2xx 성공, 4xx 클라이언트 에러, 5xx 서버 에러로 나뉩니다.
>
> 401은 로그인이 안 된 경우, 403은 로그인은 했지만 권한이 없는 경우로 나누고, 비즈니스 규칙 위반은 팀에서 정한 대로 400이나 422로 줍니다.
>
> 상태 코드는 재시도할지 정할 때도 씁니다. 4xx는 다시 보내지 않고, 502나 504는 멱등한 요청만 다시 보냅니다.

## 꼬리 질문

> [!question]- 모든 에러를 200으로 반환하면 안 되는 이유는?
> 프록시, CDN, 모니터링 같은 HTTP 도구들이 상태 코드를 보고 움직이기 때문입니다. 전부 200으로 주면 에러율을 잴 수도, 캐싱을 제어할 수도, 재시도할지 판단할 수도 없습니다.

> [!question]- 500 에러가 발생하면 재시도해야 하는가?
> 원인에 따라 다릅니다. NullPointerException 같은 코드 버그는 몇 번을 다시 보내도 실패합니다. DB 커넥션이 잠깐 모자랐던 거라면 다시 보냈을 때 성공할 수 있습니다. 500이 계속 나면 Circuit Breaker로 끊는 게 맞습니다.

> [!question]- 429 응답에는 어떻게 대응해야 하는가?
> `Retry-After` 헤더에 적힌 만큼 기다렸다가 다시 보냅니다. 헤더가 없으면 지수 백오프로 재시도합니다. 다만 429는 정해진 사용량을 넘겼다는 뜻이라, 애초에 요청을 덜 보내도록 고치는 것도 같이 해야 합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 9110: Status Codes](https://www.rfc-editor.org/rfc/rfc9110#name-status-codes)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[retry]]
- [[01-core/spring/validation-and-exception-handling|validation-and-exception-handling]]
- [[rest-api-design]]
