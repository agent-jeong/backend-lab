---
title: 인증과 인가
description: 사용자가 누구인지 확인하는 인증과, 그 사용자가 해도 되는 일인지 따지는 인가의 차이
tags: [concept, security]
---

# 인증과 인가

인증은 요청을 보낸 사람이 누구인지 확인하는 일이고, 인가는 그 사람이 이 주문이나 이 기능에 손대도 되는지 따지는 일이다. 로그인했는지만 보는 것은 인가가 아니다.

둘을 한 덩어리로 생각하면 로그인만 한 사용자가 주문 id를 바꿔 보내는 것만으로 남의 주문을 열어 보게 된다.

## 요청 하나가 지나가는 순서

1. 요청에서 세션, 토큰, API key 같은 인증 정보를 읽는다.
2. 인증 정보를 검증해 사용자 식별자와 기본 권한 정보를 만든다.
3. 요청한 리소스의 소유자, 상태, 조직, 역할 같은 접근 조건을 확인한다.
4. 조건에 맞으면 처리하고, 아니면 왜 실패했는지 알 수 있는 응답을 돌려준다.
5. 권한 실패는 감사 로그나 보안 이벤트로 남긴다.

```java
public OrderDetail getOrder(long orderId, AuthenticatedUser user) {
    Order order = orderRepository.findById(orderId)
        .orElseThrow(() -> new NotFoundException("order not found"));

    if (!order.isOwnedBy(user.id()) && !user.hasRole("ORDER_ADMIN")) {
        throw new ForbiddenException("order access denied");
    }

    return OrderDetail.from(order);
}
```

요청에 담겨 온 `userId`는 믿지 않는다. 인증으로 알아낸 사용자와 DB에서 읽은 리소스의 소유자를 서버에서 비교한다.

## 상황별 판단

| 상황 | 선택 | 이유 |
|---|---|---|
| 로그인하지 않은 요청 | 401 Unauthorized | 신원을 확인할 수 없다 |
| 로그인했지만 권한 부족 | 403 Forbidden | 신원은 확인했지만 접근 권한이 없다 |
| 본인 리소스 접근 | 사용자 id와 리소스 소유자 비교 | role만으로 소유권을 보장할 수 없다 |
| 관리자 기능 | role + 기능 단위 권한 | 관리자 role 하나에 모든 권한을 몰면 위험하다 |
| 내부 API | 호출 주체와 사용 목적 검증 | 내부망에 있다는 이유만으로 신뢰하면 안 된다 |

401과 403을 나눠 두면 클라이언트는 다시 로그인시킬지 막을지를 고를 수 있고, 로그를 볼 때도 어느 쪽 문제인지 바로 보인다. 다만 실패 사유를 너무 자세히 돌려주면 공격자에게 힌트가 된다. 관리자, 소유자, 참여자처럼 역할이 섞이는 서비스는 role만 봐서는 부족하고, 리소스마다 권한 조건이 복잡해진다.

## 자주 깨지는 곳

- 로그인 여부만 보고 리소스 소유자를 확인하지 않으면, 로그인한 사용자가 남의 데이터를 조회하고 수정한다.
- 프론트엔드에서 메뉴를 숨긴 것을 권한 검증으로 여기면, API를 직접 호출하는 순간 그대로 뚫린다.
- 요청 body나 path로 받은 `userId`를 그대로 믿으면, id만 바꿔 보내도 남의 계정으로 동작한다.
- 401과 403을 구분하지 않으면, 권한 실패가 인증 실패처럼 보여서 장애를 분석하거나 보안 로그를 읽기 어려워진다.
- 관리자 권한을 넓게 주고 사용 이력을 남기지 않으면, 누가 무엇을 바꿨는지 나중에 알 수 없다.
- 소유권 검증을 조회 경로 일부에만 넣으면, 서버에서 막고 있어도 빠진 경로 하나로 우회된다.

## 확인하는 법

- 테스트: 다른 사용자의 리소스 id로 조회, 수정, 삭제가 막히는지 본다.
- 테스트: 권한 없는 role이 관리자 API를 호출하면 403이 나오는지 본다.
- 로그: 사용자 id, 요청 리소스, 거부 사유, trace id를 남긴다. 권한 실패는 보안 이벤트로 다룬다.
- 리뷰: Controller, Service, Query 조건 중 어디서 권한을 막고 있는지 따라가 본다.

## 한 번에 설명하기

> 인증은 사용자가 누구인지 확인하는 것이고, 인가는 그 사용자가 이 리소스에 접근해도 되는지 따지는 것입니다. 로그인했는지만 보는 건 인가가 아닙니다.
>
> 그래서 본인 데이터 접근은 role로 판단하지 않고, 리소스 소유자와 인증된 사용자 id를 서버에서 비교해서 막습니다. 화면에서 메뉴를 숨겼는지와 상관없이 API는 매번 권한을 검사합니다.
>
> 응답은 401과 403을 나눠서 돌려주고, 권한 실패는 trace id와 거부 사유를 로그로 남깁니다.

## 꼬리 질문

- 인증과 인가의 차이를 실무 예시로 설명할 수 있나?
- 로그인한 사용자가 다른 사용자의 주문을 조회하지 못하게 하려면 어디서 검증하나?
- 401과 403은 각각 언제 반환하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

## 관련 문서

- [[02-practical-backend/security/security|security]]
- [[session-and-token]]
- [[authorization-check-location]]
- [[01-core/spring/filter-interceptor-aop|filter-interceptor-aop]]
- [[spring-security-flow]]
