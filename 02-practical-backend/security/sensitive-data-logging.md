---
title: 민감 정보 로깅 방지
description: 로그, 이벤트, 에러 응답에서 민감 정보 노출을 줄이는 기준
tags: [concept, security]
---

# 민감 정보 로깅 방지

비밀번호, 토큰, 개인정보, 결제 관련 값처럼 새어 나가면 피해가 큰 데이터를 로그와 에러 응답에 남기지 않게 막는 일이다. 로그는 장애 분석에 필요하지만, 애플리케이션 데이터보다 오래 보관되고 더 많은 도구로 복제된다. 민감 정보가 로그에 남으면 그 자체가 또 하나의 유출 경로가 된다.

## 막는 순서

1. 민감 정보로 볼 필드와 header를 정한다.
2. 요청/응답 로깅, 예외 로깅, 이벤트 발행 지점에서 마스킹하거나 뺀다.
3. 식별이 필요하면 원문 대신 내부 id, hash, trace id를 남긴다.
4. 로그 수집기와 APM 전송 설정에서도 민감 필드를 제거한다.
5. 로그 보관 기간과 접근 권한을 제한한다.

```java
private static final Set<String> SENSITIVE_HEADERS = Set.of(
    "authorization",
    "cookie",
    "set-cookie"
);

public String maskHeader(String name, String value) {
    if (SENSITIVE_HEADERS.contains(name.toLowerCase())) {
        return "[REDACTED]";
    }
    return value;
}
```

민감 정보는 일부만 가리기보다 아예 남기지 않는 편이 안전할 때가 많다.

## 데이터별 처리

| 데이터 | 처리 | 이유 |
|---|---|---|
| password, token | 로깅 금지 | 노출되는 즉시 계정 탈취로 이어진다 |
| Authorization header | 제거 또는 마스킹 | bearer token이 들어 있을 수 있다 |
| 개인정보 | 최소화 또는 부분 마스킹 | 식별 가능성을 줄인다 |
| 결제 관련 값 | 저장 기준 별도 검토 | 규제와 보안 요구가 강하다 |
| trace id | 적극 로깅 | 민감 정보 없이 요청을 추적할 수 있다 |

비밀번호, 토큰, 쿠키, 개인정보, 결제 관련 값은 기본적으로 로그에서 뺀다. 요청 body를 꼭 남겨야 한다면 통째로 남기지 말고 필드 단위 allowlist로 남긴다.

이렇게 하면 사고가 났을 때 노출 범위가 줄고 로그 접근 권한 관리 부담도 줄어든다. 대신 디버깅에 쓸 정보가 줄고, 마스킹 규칙을 계속 관리해야 한다. 이미 남아 있는 과거 로그는 따로 정리해야 한다.

## 자주 깨지는 곳

- **디버깅 편하자고 request body 전체를 로그로 남긴다.** 장애 분석 중 남긴 body와 header에 토큰과 개인정보가 그대로 들어간다.
- **예외 메시지에 토큰, 이메일, 전화번호를 넣는다.** 에러 응답으로 나가면 외부 사용자가 내부 구조나 민감 값을 본다.
- **access log와 application log의 마스킹 기준이 다르다.** 서비스마다, 로그 종류마다 다른 구멍이 생긴다.
- **APM, log shipper, error tracker로 나가는 데이터를 확인하지 않는다.** 애플리케이션 로그만 막고 다른 경로로 샌다.
- **운영 로그 접근 권한과 보관 기간을 관리하지 않는다.**

## 확인하는 법

- 코드 리뷰: request/response logging filter와 exception handler를 본다.
- 테스트: 샘플 요청을 보내 민감 필드가 로그에 남지 않는지 검증한다.
- 운영 점검: 로그 수집, APM, error tracker에 같은 마스킹 기준이 적용되는지 본다.
- 권한 점검: 로그 조회 권한과 보관 기간이 필요한 만큼만 열려 있는지 확인한다.

## 면접에서 말하기

> 로그는 애플리케이션 데이터보다 오래 남고 여러 도구로 복제되기 때문에, 민감 정보가 들어가면 그 자체가 유출 경로가 됩니다. 저는 비밀번호, 토큰, 쿠키, 개인정보, 결제 값을 기본적으로 빼고, 요청 body는 통째로 남기지 않고 필드 단위 allowlist로 남깁니다. 추적은 trace id와 내부 id로 하고, 로그 수집기, APM, error tracker까지 같은 기준이 적용되는지 확인합니다.

## 꼬리 질문

- 장애 분석을 위해 어떤 정보는 남기고 어떤 정보는 빼나?
- Authorization header를 로그에 남기면 어떤 위험이 생기나?
- request body 로깅을 해야 한다면 어떤 기준으로 제한하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [OWASP: Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

## 관련 문서

- [[security]]
- [[password-storage]]
- [[02-practical-backend/observability/logging|logging]]
- [[02-practical-backend/observability/trace-id-and-correlation-id|trace-id-and-correlation-id]]
