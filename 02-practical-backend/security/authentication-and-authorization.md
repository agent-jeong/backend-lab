---
title: 인증과 인가
description: 사용자를 식별하는 인증과 권한을 확인하는 인가의 차이
tags: [concept, security]
---

# 인증과 인가

인증은 사용자가 누구인지 확인하는 과정이고, 인가는 그 사용자가 특정 리소스나 기능에 접근해도 되는지 판단하는 과정이다. 로그인 여부만 확인하는 것은 권한 검증이 아니다. 둘을 섞으면 로그인만 한 사용자가 남의 데이터에 접근하게 된다.

## 요청 하나가 지나가는 순서

1. 요청에서 세션, 토큰, API key 같은 인증 정보를 읽는다.
2. 인증 정보를 검증해 사용자 식별자와 기본 권한 정보를 만든다.
3. 요청한 리소스의 소유자, 상태, 조직, 역할 같은 접근 조건을 확인한다.
4. 조건을 만족하면 처리하고, 아니면 원인이 분명한 실패 응답을 돌려준다.
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

요청에 담긴 `userId`를 믿지 않는다. 인증된 사용자와 조회한 리소스의 소유자를 서버에서 비교한다.

## 상황별 판단

| 상황 | 선택 | 이유 |
|---|---|---|
| 로그인하지 않은 요청 | 401 Unauthorized | 신원을 확인할 수 없다 |
| 로그인했지만 권한 부족 | 403 Forbidden | 신원은 확인했지만 접근 권한이 없다 |
| 본인 리소스 접근 | 사용자 id와 리소스 소유자 비교 | role만으로 소유권을 보장할 수 없다 |
| 관리자 기능 | role + 기능 단위 권한 | 관리자 role 하나에 모든 권한을 몰면 위험하다 |
| 내부 API | 호출 주체와 사용 목적 검증 | 내부망에 있다는 이유만으로 신뢰하면 안 된다 |

401과 403을 나누면 클라이언트 대응과 로그 분석이 분명해진다. 다만 실패 사유를 너무 자세히 응답하면 공격자에게 힌트가 된다. 관리자, 소유자, 참여자처럼 역할이 섞이는 서비스는 단순 role 체크로는 부족하고, 리소스별 권한 조건이 복잡해진다.

## 자주 깨지는 곳

- **로그인 여부만 보고 리소스 소유권은 확인하지 않는다.** 로그인한 사용자가 남의 데이터를 조회·수정한다.
- **프론트엔드 메뉴를 숨긴 것을 권한 검증으로 착각한다.** API를 직접 호출하면 그대로 뚫린다.
- **`userId`를 요청 body나 path에서 받은 값 그대로 믿는다.** id만 바꿔 보내면 남의 계정으로 동작한다.
- **401과 403을 구분하지 않는다.** 권한 실패가 인증 실패처럼 보여 장애 분석과 보안 로그 해석이 어려워진다.
- **관리자 권한을 넓게 주고 사용 이력을 남기지 않는다.**
- **소유권 검증을 일부 조회 경로에만 넣는다.** 서버에서 강제해도 경로 하나가 빠지면 그 경로로 우회된다.

## 확인하는 법

- 테스트: 다른 사용자의 리소스 id로 조회, 수정, 삭제가 막히는지 본다.
- 테스트: 권한 없는 role이 관리자 API를 호출하면 403이 나오는지 본다.
- 로그: 사용자 id, 요청 리소스, 거부 사유, trace id를 남긴다. 권한 실패는 보안 이벤트로 다룬다.
- 리뷰: Controller, Service, Query 조건 중 어디서 권한이 보장되는지 확인한다.

## 한 번에 설명하기

> 인증은 사용자가 누구인지 확인하는 것이고, 인가는 그 사용자가 이 리소스에 접근해도 되는지 판단하는 것입니다. 로그인 여부만 보는 것은 인가가 아니어서, 저는 본인 데이터 접근은 role이 아니라 리소스 소유자와 인증된 사용자 id를 서버에서 비교해 막습니다. 화면에서 메뉴를 숨겼는지와 상관없이 API는 항상 권한을 검증하고, 401과 403을 구분해 응답하면서 권한 실패는 trace id와 거부 사유를 로그로 남깁니다.

## 꼬리 질문

- 인증과 인가의 차이를 실무 예시로 설명할 수 있나?
- 로그인한 사용자가 다른 사용자의 주문을 조회하지 못하게 하려면 어디서 검증하나?
- 401과 403은 각각 언제 반환하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [OWASP: Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

## 관련 문서

- [[security]]
- [[session-and-token]]
- [[authorization-check-location]]
- [[01-core/spring/filter-interceptor-aop|filter-interceptor-aop]]
