---
title: 민감 정보 로깅 방지
description: 로그, 이벤트, 에러 응답에 비밀번호나 토큰, 개인정보가 남지 않게 막는 방법
tags: [concept, security]
---

# 민감 정보 로깅 방지

비밀번호, 토큰, 개인정보, 결제 관련 값처럼 새어 나가면 피해가 큰 데이터를 로그와 에러 응답에 남기지 않게 막는 일이다.

장애를 분석하려면 로그가 필요하다. 그런데 로그는 애플리케이션 데이터보다 오래 보관되고, 수집기와 검색 도구, APM 같은 여러 곳으로 복사된다. 결제 요청 body를 통째로 로그에 남기면 그 순간 로그 저장소가 또 하나의 유출 경로가 된다.

## 막는 순서

1. 민감 정보로 볼 필드와 header를 정한다.
2. 요청/응답 로깅, 예외 로깅, 이벤트 발행 지점에서 가리거나 뺀다.
3. 누구의 요청인지 알아야 하면 원문 대신 내부 id, hash, trace id를 남긴다.
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

비밀번호, 토큰, 쿠키, 개인정보, 결제 관련 값은 기본적으로 로그에서 뺀다. 요청 body를 꼭 남겨야 한다면 통째로 남기지 말고, 남겨도 되는 필드만 골라 둔 allowlist로 남긴다.

이렇게 하면 사고가 났을 때 노출되는 범위가 줄고, 로그 접근 권한을 관리하는 부담도 줄어든다. 대신 디버깅에 쓸 정보가 줄고, 마스킹 규칙을 계속 손봐야 한다. 이미 쌓여 있는 과거 로그는 따로 정리해야 한다.

## 자주 깨지는 곳

- 디버깅이 편하다고 request body 전체를 로그로 남기면, 장애 분석 중에 남긴 body와 header에 토큰과 개인정보가 그대로 들어간다.
- 예외 메시지에 토큰, 이메일, 전화번호를 넣으면, 그 메시지가 에러 응답으로 나갔을 때 외부 사용자가 내부 구조나 민감 값을 본다.
- access log와 application log의 마스킹 기준이 다르면, 서비스마다, 로그 종류마다 다른 구멍이 생긴다.
- APM, log shipper, error tracker로 나가는 데이터를 확인하지 않으면, 애플리케이션 로그만 막고 다른 길로 샌다.
- 운영 로그 접근 권한과 보관 기간을 관리하지 않으면, 필요 없는 사람이 오래된 민감 정보까지 볼 수 있다.

## 확인하는 법

- 코드 리뷰: request/response logging filter와 exception handler를 본다.
- 테스트: 샘플 요청을 보내 민감 필드가 로그에 남지 않는지 검증한다.
- 운영 점검: 로그 수집, APM, error tracker에 같은 마스킹 기준이 적용되는지 본다.
- 권한 점검: 로그 조회 권한과 보관 기간이 필요한 만큼만 열려 있는지 확인한다.

## 한 번에 설명하기

> 로그는 애플리케이션 데이터보다 오래 남고 여러 도구로 복사되기 때문에, 민감 정보가 들어가면 로그 자체가 유출 경로가 됩니다.
>
> 그래서 비밀번호, 토큰, 쿠키, 개인정보, 결제 값은 기본적으로 빼고, 요청 body는 통째로 남기지 않고 필요한 필드만 allowlist로 남깁니다.
>
> 요청 추적은 trace id와 내부 id로 하고, 로그 수집기, APM, error tracker까지 같은 기준이 적용되는지 확인합니다.

## 꼬리 질문

- 장애 분석을 위해 어떤 정보는 남기고 어떤 정보는 빼나?
- Authorization header를 로그에 남기면 어떤 위험이 생기나?
- request body 로깅을 해야 한다면 어떤 기준으로 제한하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

## 관련 문서

- [[security]]
- [[password-storage]]
- [[02-practical-backend/observability/logging|logging]]
- [[02-practical-backend/observability/trace-id-and-correlation-id|trace-id-and-correlation-id]]
