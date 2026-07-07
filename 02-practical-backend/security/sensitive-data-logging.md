---
title: 민감 정보 로깅 방지
description: 로그, 이벤트, 에러 응답에서 민감 정보 노출을 줄이는 기준
---

# 민감 정보 로깅 방지

## 한 줄 정의

민감 정보 로깅 방지는 비밀번호, 토큰, 개인정보, 결제 관련 값처럼 노출되면 피해가 큰 데이터를 로그와 에러 응답에 남기지 않도록 제어하는 것이다.

## 실무에서 왜 문제 되는가

- 로그는 애플리케이션보다 더 오래 보관되고 더 많은 도구로 복제될 수 있다.
- 장애 분석 중 요청 body나 header를 통째로 남기면 토큰과 개인정보가 노출될 수 있다.
- 에러 응답에 내부 값이 포함되면 외부 사용자가 시스템 구조나 민감 값을 볼 수 있다.
- 로그 마스킹 기준이 없으면 서비스마다 다른 방식으로 노출 위험을 만든다.

## 동작 원리

1. 민감 정보로 볼 필드와 header를 정의한다.
2. 요청/응답 로깅, 예외 로깅, 이벤트 발행 지점에서 마스킹 또는 제외한다.
3. 필요한 경우 식별 가능한 원문 대신 내부 id, hash, trace id를 남긴다.
4. 로그 수집기와 APM 전송 설정에서도 민감 필드 제거를 적용한다.
5. 로그 보관 기간과 접근 권한을 제한한다.

## 실무 판단 기준

| 데이터 | 처리 | 이유 |
|---|---|---|
| password, token | 로깅 금지 | 노출 즉시 계정 탈취로 이어질 수 있다 |
| Authorization header | 제거 또는 마스킹 | bearer token이 포함될 수 있다 |
| 개인정보 | 최소화 또는 부분 마스킹 | 식별 가능성을 줄인다 |
| 결제 관련 값 | 저장 기준 별도 검토 | 규제와 보안 요구가 강하다 |
| trace id | 적극 로깅 | 민감 정보 없이 요청 추적이 가능하다 |

## 자주 나는 실수

- 디버깅 편의를 위해 request body 전체를 로그로 남긴다.
- 예외 메시지에 토큰, 이메일, 전화번호 같은 값을 포함한다.
- access log와 application log의 마스킹 기준이 다르다.
- APM, log shipper, error tracker로 전송되는 데이터를 확인하지 않는다.
- 운영 로그 접근 권한과 보관 기간을 관리하지 않는다.

## 확인 방법

- 코드 리뷰: request/response logging filter와 exception handler를 확인한다.
- 테스트: 민감 필드가 로그에 남지 않는지 샘플 요청으로 검증한다.
- 운영 점검: 로그 수집, APM, error tracker에 같은 마스킹 기준이 적용되는지 본다.
- 권한 점검: 로그 조회 권한과 보관 기간이 필요한 수준으로 제한되어 있는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 사고 시 노출 범위를 줄인다 | 디버깅에 필요한 정보가 줄어들 수 있다 |
| 로그 접근 권한 부담을 낮춘다 | 마스킹 규칙을 계속 관리해야 한다 |
| trace id 중심 분석 습관을 만든다 | 이미 남은 과거 로그는 별도 정리가 필요하다 |

## 짧은 예제

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

민감 정보는 일부만 가리는 것보다 아예 남기지 않는 편이 안전한 경우가 많다.

## 핵심 요약

로그는 장애 분석에 필요하지만 민감 정보가 남으면 별도 유출 경로가 된다.

비밀번호, 토큰, 쿠키, 개인정보, 결제 관련 값은 기본적으로 로그에서 제외한다.

요청 body 전체 로깅은 편리하지만 위험하므로 필드 단위 allowlist가 안전하다.

에러 응답과 예외 메시지에도 내부 값이 섞이지 않게 해야 한다.

trace id와 내부 id를 남기면 민감 정보 없이도 요청 흐름을 추적할 수 있다.

로그 수집기, APM, error tracker까지 같은 기준으로 확인해야 한다.

## 꼬리 질문

- 장애 분석을 위해 어떤 정보는 남기고 어떤 정보는 남기지 않을 것인가?
- Authorization header를 로그에 남기면 어떤 위험이 생기는가?
- request body 로깅을 해야 한다면 어떤 기준으로 제한할 것인가?

## 관련 문서

- [[security]]
- [[password-storage]]
- [[02-practical-backend/observability/logging|logging]]
- [[02-practical-backend/observability/trace-id-and-correlation-id|trace-id-and-correlation-id]]
