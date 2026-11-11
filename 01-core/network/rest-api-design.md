---
title: REST API 설계
description: 자원과 URI를 정하고, 메서드와 상태 코드와 에러 형식을 클라이언트가 예측할 수 있게 맞추는 기준
tags: [concept, network]
---

# REST API 설계

REST API 설계는 서버가 가진 자원을 URI로 이름 짓고, 그 자원에 무엇을 할지를 HTTP 메서드로 나타내는 일이다. 잘 설계한 API는 문서를 덜 읽어도 클라이언트가 동작을 짐작한다.

주문 취소를 `POST /cancelOrder?id=42`로 만들고 실패를 200과 `{"success": false}`로 돌려주면, 클라이언트는 이 요청을 다시 보내도 되는지, 실패를 어떻게 알아보는지를 API마다 따로 외워야 한다. 게이트웨이와 모니터링도 상태 코드로 에러율을 잴 수 없다. 메서드와 상태 코드를 HTTP 정의대로 쓰면 재시도, 캐싱, 에러 처리가 한 가지 규칙으로 맞춰진다.

## 자원과 URI

URI는 자원을 가리키는 명사로 짓고, 동작은 메서드로 나타낸다.

```
GET    /orders              주문 목록
POST   /orders              주문 생성
GET    /orders/42           주문 하나 조회
PATCH  /orders/42           주문 일부 수정
DELETE /orders/42           주문 삭제
GET    /users/7/orders      사용자 7의 주문 목록
```

- 컬렉션은 복수형(`/orders`)으로, 그 안의 하나는 식별자(`/orders/42`)로 쓴다.
- 하위 자원은 소유 관계가 분명할 때만 경로로 중첩한다. 두 단계를 넘기면 `/orders?userId=7`처럼 쿼리로 푸는 편이 읽기 쉽다.
- 경로는 소문자와 하이픈(`/order-items`)으로 맞추고, 확장자(`.json`)는 넣지 않는다. 형식은 `Accept` 헤더로 고른다.

주문 취소처럼 CRUD로 딱 떨어지지 않는 동작도 있다. 이때는 상태 변경으로 볼지(`PATCH /orders/42` 에 `{"status": "CANCELED"}`), 취소 자체를 자원으로 볼지(`POST /orders/42/cancellation`) 정한다. 취소에 사유, 환불 금액 같은 자기 데이터가 붙으면 자원으로 만드는 쪽이 낫다.

## 메서드와 멱등성

메서드를 고를 때 기준은 이 요청을 다시 보냈을 때 결과가 같은가이다. 메서드별 안전성과 멱등성 표는 [[http-basics]]에 있다.

| 메서드 | 멱등 | 설계에서 쓰는 곳 |
|---|---|---|
| GET | O | 조회. 서버 상태를 바꾸지 않는다 |
| POST | X | 생성, 또는 다른 메서드로 표현하기 어려운 처리 |
| PUT | O | 자원 전체를 보낸 표현으로 바꾼다. 없으면 만든다 |
| PATCH | X | 자원 일부를 바꾼다 |
| DELETE | O | 삭제. 두 번째 호출은 404가 나도 서버 상태는 같다 |

RFC 9110은 PUT이 자원을 새로 만들면 201, 기존 자원을 바꾸면 200이나 204를 주라고 정한다. 클라이언트가 식별자를 정할 수 있으면 `PUT /orders/{클라이언트가 만든 ID}`로 생성 자체를 멱등하게 만든다.

POST 주문 생성처럼 멱등하지 않은 요청을 안전하게 재시도하려면 `Idempotency-Key` 헤더를 받는다. 키를 어떻게 만들고 저장하는지는 [[idempotency-key]]에 있다.

## PUT과 PATCH

PUT은 보낸 본문이 자원의 새 상태 전체다. 본문에서 빠진 필드는 비우거나 기본값으로 돌린다.

```
현재: {"name": "kim", "phone": "010-0000-0000", "email": "a@example.com"}

PUT /users/7   {"name": "lee"}
결과: {"name": "lee", "phone": null, "email": null}

PATCH /users/7 (application/merge-patch+json)  {"name": "lee"}
결과: {"name": "lee", "phone": "010-0000-0000", "email": "a@example.com"}
```

PATCH 본문의 형식은 미디어 타입으로 정한다. JSON Merge Patch(RFC 7396)는 보낸 필드만 바꾸고 `null`을 보낸 필드는 지운다. JSON Patch(RFC 6902)는 `add`, `remove`, `replace` 같은 연산 목록을 보낸다.

PATCH는 RFC 5789에서 멱등하지 않은 메서드로 정의한다. `{"name": "lee"}`처럼 값을 덮어쓰는 PATCH는 몇 번 보내도 결과가 같지만, "재고를 1 줄여라" 같은 연산은 보낼 때마다 결과가 달라진다. 그래서 PATCH를 재시도할지는 본문이 무엇을 하는지 보고 정한다.

## 상태 코드 고르기

상태 코드는 클라이언트가 다음에 할 일을 알려 준다. 코드별 뜻과 재시도 판단은 [[status-code]]에 있고, 설계에서는 아래 질문 순서로 고른다.

1. 성공했나? 생성이면 201과 `Location`, 본문이 없으면 204, 나머지는 200.
2. 요청이 틀렸나? 형식 오류는 400, 인증이 없으면 401, 권한이 없으면 403, 대상이 없으면 404.
3. 지금 자원 상태와 부딪치나? 이미 취소된 주문을 다시 취소하는 식이면 409.
4. 서버 쪽 문제인가? 예상 못 한 예외는 500, 외부 의존성 장애로 지금 못 받으면 503.

잔액 부족 같은 업무 규칙 위반을 400으로 줄지 422로 줄지는 팀에서 하나로 정하고, 에러 본문의 코드로 구체적인 이유를 나눈다.

## 에러 응답 형식 (RFC 9457 Problem Details)

에러 본문을 API마다 다르게 만들지 말고 RFC 9457 Problem Details 형식으로 맞춘다. RFC 9457은 2023년에 RFC 7807을 대체했고, 미디어 타입은 `application/problem+json`이다.

```json
{
  "type": "https://api.example.com/problems/insufficient-balance",
  "title": "잔액이 부족합니다",
  "status": 422,
  "detail": "결제 금액 30000원이 잔액 12000원보다 큽니다.",
  "instance": "/payments/981",
  "errorCode": "PAYMENT_INSUFFICIENT_BALANCE"
}
```

| 필드 | 뜻 |
|---|---|
| `type` | 문제 종류를 가리키는 URI. 없으면 `about:blank`로 본다 |
| `title` | 문제 종류의 짧은 요약. 같은 `type`이면 같은 문장이다 |
| `status` | HTTP 상태 코드. 참고용이고 실제 판단은 응답 상태 줄로 한다 |
| `detail` | 이번 요청에서 일어난 일 |
| `instance` | 이번 발생을 가리키는 URI |

`errorCode`처럼 RFC에 없는 필드는 확장 필드로 덧붙인다. 클라이언트는 모르는 확장 필드를 무시한다.

Spring Framework 6.0부터 `ProblemDetail` 클래스를 지원한다. Spring Boot 3.x에서는 `spring.mvc.problemdetails.enabled=true`를 켜면 Spring MVC가 내는 기본 예외도 이 형식으로 나간다.

```java
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(InsufficientBalanceException.class)
    ProblemDetail handleInsufficientBalance(InsufficientBalanceException e) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.UNPROCESSABLE_ENTITY, e.getMessage());
        problem.setType(URI.create("https://api.example.com/problems/insufficient-balance"));
        problem.setTitle("잔액이 부족합니다");
        problem.setProperty("errorCode", "PAYMENT_INSUFFICIENT_BALANCE");
        return problem;
    }
}
```

예외 처리기를 어떻게 나누는지는 [[validation-and-exception-handling]]에 있다.

## 목록 조회와 페이지네이션

목록 API는 처음부터 페이지 단위로 만든다. 처음엔 데이터가 적어도, 전부 돌려주는 API는 데이터가 늘면 응답이 커지고 DB 조회가 느려진다.

| 방식 | 요청 예 | 맞는 곳 | 한계 |
|---|---|---|---|
| offset | `GET /orders?page=3&size=20` | 관리자 화면처럼 페이지 번호로 이동하는 곳 | 뒤 페이지일수록 DB가 앞 행을 읽고 버린다. 읽는 사이 행이 추가되면 중복이나 누락이 생긴다 |
| cursor | `GET /orders?after=eyJpZCI6OTgxfQ&size=20` | 무한 스크롤, 최신순 피드, 배치로 전체 훑기 | 임의 페이지로 바로 가지 못한다. 정렬 키가 유일해야 한다 |

cursor는 마지막으로 받은 행의 정렬 키를 담고, 서버는 `WHERE id < :lastId ORDER BY id DESC LIMIT 20`처럼 그 다음부터 읽는다. 정렬 키가 `created_at` 하나면 같은 시각의 행이 겹쳐서 빠지므로 `(created_at, id)`처럼 유일하게 만든다.

필터와 정렬은 쿼리 파라미터로 받는다(`?status=PAID&sort=-createdAt`). 허용할 필터와 정렬 필드는 서버가 목록으로 정해 두고 나머지는 400으로 거절한다. 아무 필드나 정렬하게 열어 두면 인덱스 없는 정렬이 운영 DB에 그대로 들어온다.

## 버전 관리

버전은 하위 호환이 깨질 때만 올린다. 필드 추가는 호환되는 변경이고, 필드 삭제와 이름 변경, 타입 변경, 필수 필드 추가는 호환을 깬다.

| 방식 | 예 | 특징 |
|---|---|---|
| URI 경로 | `/v1/orders` | 눈에 보이고 라우팅과 로그에서 나누기 쉽다. 가장 흔하다 |
| 헤더 | `X-API-Version: 2` | URI가 바뀌지 않는다. 브라우저 주소창이나 캐시 키에서 놓치기 쉽다 |
| 미디어 타입 | `Accept: application/vnd.example.v2+json` | HTTP 콘텐츠 협상을 따른다. 클라이언트가 쓰기 번거롭다 |

어느 방식이든 옛 버전을 언제 끝낼지 같이 정한다. 호출하는 클라이언트를 버전별로 로그에 남겨 두면, 끄기 전에 누가 아직 쓰는지 확인할 수 있다.

## 자주 깨지는 곳

- URI에 동사를 넣고 POST 하나로 모든 동작을 처리하면, 어떤 요청을 다시 보내도 되는지 메서드만 보고 알 수 없다.
- 실패를 200과 `success: false`로 돌려주면, 게이트웨이와 모니터링이 에러를 성공으로 센다.
- PUT을 부분 수정처럼 쓰면, 클라이언트가 빠뜨린 필드가 서버에서 비워진다.
- 에러 `detail`에 예외 메시지나 SQL을 그대로 담으면, 내부 구조가 바깥으로 새어 나간다. RFC 9457도 스택 같은 구현 정보를 내보내지 말라고 적는다.
- 목록 API에 크기 상한이 없으면, `size=100000` 요청 하나가 DB와 메모리를 다 쓴다.
- 응답 필드를 지우거나 이름을 바꾸면서 버전을 올리지 않으면, 배포 순간 옛 클라이언트가 깨진다.
- offset 페이지네이션으로 전체 데이터를 훑으면, 그 사이 들어온 행 때문에 같은 행을 두 번 읽거나 건너뛴다.

## 한 번에 설명하기

> REST API는 URI로 자원을 가리키고, 그 자원에 할 일을 HTTP 메서드로 나타냅니다. 메서드를 정의대로 쓰면 GET, PUT, DELETE는 다시 보내도 되고 POST는 멱등키가 있어야 다시 보낸다는 규칙이 API 전체에 똑같이 적용됩니다.
>
> 결과는 상태 코드로 알리고, 에러 본문은 RFC 9457 Problem Details로 맞춰서 클라이언트가 에러를 한 군데에서 처리하게 합니다.
>
> 목록은 처음부터 페이지 단위로 만들고, 전체를 훑거나 무한 스크롤이면 cursor 방식을 씁니다. 버전은 필드 삭제처럼 하위 호환이 깨질 때만 올립니다.

## 꼬리 질문

> [!question]- PUT과 PATCH는 어떻게 다른가요?
> PUT은 보낸 본문이 자원의 새 상태 전체라서, 빠진 필드는 비워집니다. 같은 요청을 여러 번 보내도 결과가 같아서 멱등합니다. PATCH는 일부만 바꾸는 요청이고, RFC 5789는 멱등하지 않은 메서드로 정의합니다. 값을 덮어쓰는 PATCH는 사실상 멱등하지만, 수량을 줄이는 연산처럼 상대값을 바꾸면 보낼 때마다 결과가 달라집니다.

> [!question]- 주문 취소 API는 어떻게 설계하나요?
> 취소가 단순히 상태만 바꾸면 `PATCH /orders/42`로 상태를 바꿉니다. 취소 사유나 환불 금액처럼 취소 자체에 데이터가 붙으면 `POST /orders/42/cancellation`으로 취소를 자원으로 만듭니다. 이미 취소된 주문이면 409를 주거나, 같은 취소 요청의 재시도라면 처음 결과를 그대로 돌려줍니다.

> [!question]- offset 페이지네이션은 왜 뒤로 갈수록 느려지나요?
> `OFFSET 100000 LIMIT 20`이면 DB가 앞의 10만 행을 읽고 버린 뒤 20행을 돌려줍니다. cursor 방식은 마지막으로 본 키보다 뒤부터 인덱스로 바로 찾아서, 몇 번째 페이지든 읽는 양이 같습니다.

> [!question]- 에러 응답에 `status`가 있는데 HTTP 상태 코드는 왜 따로 맞추나요?
> 프록시, 게이트웨이, 모니터링은 본문을 읽지 않고 상태 줄만 봅니다. RFC 9457도 본문의 `status`는 참고용이라고 적습니다. 그래서 두 값은 같게 두고, 판단은 상태 줄로 합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [Spring Framework: Error Responses](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[status-code]]
- [[idempotency-key]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[validation-and-exception-handling]]
