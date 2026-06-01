---
title: Status Code
description: HTTP 상태 코드의 의미와 API 설계 시 올바른 사용법
---

# Status Code

## 한 줄 정의

HTTP 상태 코드는 서버가 클라이언트의 요청을 어떻게 처리했는지를 숫자로 나타내는 응답 코드다.

## 실무에서 왜 중요한가

상태 코드를 잘못 사용하면 다음 문제가 생긴다.

- 모든 응답을 200으로 반환하고 바디에 에러를 담아서 클라이언트가 에러 처리를 제대로 못한다.
- 404와 400을 구분하지 않아서 "리소스가 없는 것"인지 "요청이 잘못된 것"인지 모른다.
- 500을 남발해서 서버 에러인지 클라이언트 에러인지 구분이 안 된다.
- 재시도 가능 여부를 판단할 수 없다.

## 상태 코드 분류

| 범위 | 분류 | 의미 |
|---|---|---|
| 1xx | Informational | 처리 진행 중 |
| 2xx | Success | 요청 성공 |
| 3xx | Redirection | 추가 동작 필요 |
| 4xx | Client Error | 클라이언트 요청 오류 |
| 5xx | Server Error | 서버 처리 오류 |

## 자주 사용하는 상태 코드

### 2xx (성공)

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

### 4xx (클라이언트 에러)

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

실무에서는 400으로 통일하는 경우도 많다. 팀 내 컨벤션이 중요하다.

### 5xx (서버 에러)

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

## 재시도 판단 기준

| 상태 코드 | 재시도 가능 | 이유 |
|---|---|---|
| 408 | O | 요청 시간 초과 (일시적) |
| 429 | O | Rate Limit (Retry-After 대기 후) |
| 500 | △ | 원인에 따라 다름 |
| 502, 503, 504 | O | 일시적 서버 문제 |
| 400, 401, 403, 404 | X | 같은 요청을 보내도 결과 동일 |

## API 에러 응답 설계

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

## 자주 나는 실수

- 모든 응답을 200으로 반환하고 바디의 `success` 필드로 성공/실패를 구분한다.
- 비즈니스 에러를 500으로 반환해서 서버 에러와 구분이 안 된다.
- 401과 403을 혼용해서 인증 문제인지 인가 문제인지 모른다.
- 리소스 생성 시 200을 반환하면서 `Location` 헤더를 빠뜨린다.
- 에러 응답 형식이 API마다 달라서 클라이언트가 일관된 처리를 못한다.

## 핵심 요약

상태 코드는 2xx(성공), 4xx(클라이언트 에러), 5xx(서버 에러)로 구분합니다.
올바른 상태 코드를 사용해야 클라이언트가 에러를 구분하고 적절히 대응(재시도, 인증 등)할 수 있습니다.

401(인증 필요)과 403(권한 없음), 400(요청 오류)과 422(비즈니스 규칙 위반)를 구분해야 합니다.
에러 응답은 일관된 형식으로 설계하고, 재시도 가능 여부의 판단 기준으로 활용해야 합니다.

## 꼬리 질문

> [!question]- 모든 에러를 200으로 반환하면 안 되는 이유는?
> HTTP 인프라(프록시, CDN, 모니터링)가 상태 코드를 기반으로 동작합니다. 200으로 통일하면 에러율 모니터링, 캐싱 제어, 재시도 판단이 불가능합니다.

> [!question]- 500 에러가 발생하면 재시도해야 하는가?
> 원인에 따라 다릅니다. NullPointerException 같은 코드 버그는 재시도해도 실패합니다. DB 커넥션 부족 같은 일시적 문제는 재시도로 성공할 수 있습니다. 500이 반복되면 Circuit Breaker로 차단하는 것이 적절합니다.

> [!question]- 429 응답에는 어떻게 대응해야 하는가?
> `Retry-After` 헤더의 값만큼 대기한 후 재시도합니다. 헤더가 없으면 지수 백오프로 재시도합니다. Rate Limit은 API 사용량을 초과한 것이므로, 요청 빈도를 줄이는 근본적인 조치도 필요합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[retry]]
- [[01-core/spring/validation-and-exception-handling|validation-and-exception-handling]]