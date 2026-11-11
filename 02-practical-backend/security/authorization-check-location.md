---
title: 권한 검증 위치
description: 권한 검사를 Controller, Service, Query 중 어디에 나눠 둘지 정하는 기준
tags: [concept, security]
---

# 권한 검증 위치

"이 사용자가 이 리소스에 접근해도 되나"를 Controller, Service, Query, 공통 보안 계층 중 어디서 확인할지 정하는 문제다. 답은 한 곳이 아니다. 요청이 들어오는 입구, 업무 규칙, 조회 조건에 나눠서 둔다.

어디서 막는지 정해 두지 않으면 검사가 여기저기 흩어진다. 그러면 주문 취소 API 하나를 놓고도 정말 막혀 있는지 아무도 확신하지 못한다.

## 계층별로 무엇을 막나

1. 요청의 인증 정보는 공통 필터나 인터셉터에서 확인한다.
2. 기능 단위 권한은 Controller나 method security에서 일찍 막는다.
3. 리소스 소유권과 상태에 따른 권한은 Service에서 업무 규칙과 함께 검사한다.
4. 목록 조회나 검색은 접근할 수 있는 범위를 Query 조건에 넣는다.
5. 권한 실패는 예외 하나와 로그 형식 하나로 처리한다.

| 검증 대상 | 둘 곳 | 이유 |
|---|---|---|
| 로그인 여부 | Filter, Interceptor | 대부분의 요청에 공통으로 적용된다 |
| 기능 role | Controller, method security | API 진입 지점에서 빠르게 차단한다 |
| 리소스 소유권 | Service | 업무 규칙과 함께 판단해야 한다 |
| 목록 조회 범위 | Query 조건 | 권한 없는 데이터를 애초에 조회하지 않는다 |
| 관리자 예외 정책 | Service | role과 리소스 상태를 함께 판단한다 |

```java
public List<OrderSummary> findMyOrders(AuthenticatedUser user, OrderSearchCondition condition) {
    return orderQueryRepository.findSummaries(
        condition.withOwnerId(user.id())
    );
}
```

목록은 다 읽어 온 뒤 걸러 내지 않는다. 처음부터 볼 수 있는 범위만 query 조건으로 가져온다.

## 방식별 약한 곳

| 방식 | 장점 | 약한 곳 |
|---|---|---|
| 공통 필터 | 로그인 여부를 일관되게 확인한다 | 리소스별 권한은 모른다 |
| Controller 검증 | API 진입점에서 의도가 보인다 | 내부 호출, 배치 같은 다른 경로에서 빠진다 |
| Service 검증 | 업무 규칙과 함께 판단한다 | 반복 코드가 생긴다. 정책 메서드나 도메인 규칙으로 모은다 |
| Query 조건 | 권한 없는 데이터 조회 자체를 줄인다 | 조건이 복잡해지면 테스트로 지켜야 한다 |

## 자주 깨지는 곳

- `@PreAuthorize("isAuthenticated()")`만 붙이고 끝났다고 여기면, 소유권 검사가 빠진다. 공통 어노테이션으로는 "이 주문의 주인인가" 같은 데이터에 따른 권한을 표현하기 어렵다.
- 목록 API에서 전체를 읽은 뒤 애플리케이션에서 거르면, 거르는 과정에서 권한 없는 데이터가 새어 나갈 틈이 생긴다.
- Service 메서드를 Controller 말고 다른 곳에서도 부른다는 걸 놓치면, Controller에서만 검사한 그 경로는 무방비가 된다.
- 관리자 role이면 모든 리소스에 접근하게 두면, 관리자 계정 하나가 털렸을 때 피해가 전체로 번진다.
- 권한 실패 로그에 요청 값을 그대로 남기면, 그 로그가 민감 정보를 퍼뜨린다.

## 확인하는 법

- 테스트: 소유자가 아닌 사용자가 단건 조회, 목록 조회, 수정, 삭제에 모두 실패하는지 본다.
- 테스트: 관리자 예외가 필요한 기능과 필요 없는 기능을 나눠 검증한다.
- 코드 리뷰: 권한 조건을 Controller, Service, Query 중 어디서 막고 있는지 따라간다.
- 로그: 권한 실패 때 사용자 id, 리소스 id, 정책 이름, trace id를 남긴다.

## 한 번에 설명하기

> 권한 검사는 한 곳에 몰아 두는 게 아니라 계층마다 나눠 두는 일이라고 봅니다.
>
> 로그인 여부는 공통 필터에서, 기능 role은 Controller나 method security에서, 리소스 소유권은 업무 규칙과 함께 Service에서 확인합니다. 목록 조회는 가져온 뒤 거르지 않고 query 조건에 권한 범위를 넣습니다.
>
> 권한 실패는 403으로 응답하고, 감사에 필요한 최소한의 정보만 로그로 남깁니다.

## 꼬리 질문

- 권한 검증은 Controller와 Service 중 어디에 두는 게 좋은가?
- 목록 조회에서 권한 검증을 어떻게 보장하나?
- 공통 보안 어노테이션으로 해결하기 어려운 권한은?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Spring Security: Method Security](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[session-and-token]]
- [[01-core/spring/filter-interceptor-aop|filter-interceptor-aop]]
