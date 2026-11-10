---
title: 권한 검증 위치
description: Controller, Service, Query 경계에서 권한 검증을 배치하는 기준
tags: [concept, security]
---

# 권한 검증 위치

권한 검증 위치는 "이 사용자가 이 리소스에 접근해도 되나"를 Controller, Service, Query, 공통 보안 계층 중 어디서 확인할지 정하는 문제다. 한 계층만의 문제가 아니다. 요청 진입, 업무 규칙, 조회 조건에 걸쳐 나눠 둔다. 검증이 여기저기 흩어지면 어떤 API가 안전한지 아무도 확인할 수 없다.

## 계층별로 무엇을 막나

1. 요청의 인증 정보는 공통 필터나 인터셉터에서 확인한다.
2. 기능 단위 권한은 Controller나 method security에서 빠르게 막는다.
3. 리소스 소유권과 상태 기반 권한은 Service에서 업무 규칙으로 검증한다.
4. 목록 조회나 검색은 접근 가능한 범위를 Query 조건에 넣는다.
5. 권한 실패는 한 가지 예외와 로그 형식으로 처리한다.

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

목록은 조회한 뒤 걸러 내지 말고, 처음부터 접근 가능한 범위만 query 조건으로 가져온다.

## 방식별 약한 곳

| 방식 | 장점 | 약한 곳 |
|---|---|---|
| 공통 필터 | 로그인 여부를 일관되게 확인한다 | 리소스별 권한은 모른다 |
| Controller 검증 | API 진입점에서 의도가 보인다 | 내부 호출, 배치 같은 다른 경로에서 빠진다 |
| Service 검증 | 업무 규칙과 함께 판단한다 | 반복 코드가 생긴다. 정책 메서드나 도메인 규칙으로 모은다 |
| Query 조건 | 권한 없는 데이터 조회 자체를 줄인다 | 조건이 복잡해지면 테스트로 지켜야 한다 |

## 자주 깨지는 곳

- **`@PreAuthorize("isAuthenticated()")`만 붙이고 소유권 검증이 끝났다고 생각한다.** 공통 어노테이션으로는 리소스 소유권 같은 데이터 기반 권한을 표현하기 어렵다.
- **목록 API에서 전체를 조회한 뒤 애플리케이션에서 필터링한다.** 필터링 과정에서 권한 없는 데이터가 새어 나갈 틈이 생긴다.
- **Service 메서드가 다른 진입점에서도 호출된다는 점을 놓친다.** Controller에서만 검증하면 그 경로는 무방비다.
- **관리자 role이면 모든 리소스 접근을 허용한다.**
- **권한 실패 로그에 민감한 요청 값을 그대로 남긴다.**

## 확인하는 법

- 테스트: 소유자가 아닌 사용자가 단건 조회, 목록 조회, 수정, 삭제에 모두 실패하는지 본다.
- 테스트: 관리자 예외가 필요한 기능과 필요 없는 기능을 나눠 검증한다.
- 코드 리뷰: 권한 조건이 Controller, Service, Query 중 어디에서 보장되는지 따라간다.
- 로그: 권한 실패 때 사용자 id, 리소스 id, 정책 이름, trace id를 남긴다.

## 면접에서 말하기

> 권한 검증은 한 곳에 두는 문제가 아니라 계층별로 나눠 두는 문제라고 봅니다. 로그인 여부는 공통 필터에서, 기능 role은 Controller나 method security에서, 리소스 소유권은 업무 규칙과 함께 Service에서 확인합니다. 목록 조회는 가져온 뒤 거르지 않고 query 조건에 권한 범위를 넣습니다. 권한 실패는 403으로 응답하고 감사에 필요한 최소 정보만 로그로 남깁니다.

## 꼬리 질문

- 권한 검증은 Controller와 Service 중 어디에 두는 게 좋은가?
- 목록 조회에서 권한 검증을 어떻게 보장하나?
- 공통 보안 어노테이션으로 해결하기 어려운 권한은?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Spring Security: Method Security](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[session-and-token]]
- [[01-core/spring/filter-interceptor-aop|filter-interceptor-aop]]
