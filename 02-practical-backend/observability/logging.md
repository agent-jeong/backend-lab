---
title: 로깅
description: 장애가 났을 때 실제로 찾아보게 되는 로그를 남기는 방법과 주의점
tags: [concept, observability]
---

# 로깅

Logging은 요청을 처리하면서 상태가 어떻게 바뀌었는지, 코드가 어느 분기를 탔는지, 왜 실패했는지를 나중에 따라갈 수 있게 적어 두는 일이다.

로그는 적어도 문제, 많아도 문제다. 결제가 실패했는데 그때 로그가 없으면 원인을 짐작해야 하고, 너무 많으면 비용이 커지고 중요한 줄이 묻힌다. 그래서 무엇을 남길지는 "장애 때 이 필드로 검색하게 될까"를 물어서 정한다.

## 로그가 남고 쓰이는 흐름

1. 요청이 들어오면 request id나 trace id를 만들거나 전달받는다.
2. 주요 처리 단계마다 필요한 상태와 결과를 필드로 나눠 남긴다.
3. 예외가 나면 원인, 영향, 복구할 수 있는지를 나눠 남긴다.
4. 로그 수집기가 로그를 중앙 저장소로 보낸다.
5. 장애 분석 때 id, endpoint, error code, 시간 범위로 검색한다.

```java
log.info("order create completed traceId={} orderId={} elapsedMs={}",
    traceId, orderId, elapsedMs);

log.warn("payment retry traceId={} orderId={} attempt={} reason={}",
    traceId, orderId, attempt, reason);
```

운영 로그는 사람이 읽을 수 있으면서 필드로 검색도 돼야 한다. 쓸모 있는 로그에는 request id, endpoint, 상태, 결과, elapsed time이 들어간다.

## 로그 수준 정하기

| 상황 | 로그 수준 | 이유 |
|---|---|---|
| 정상 요청 요약 | INFO | 흐름과 처리 결과를 남긴다 |
| 재시도 가능 실패 | WARN | 즉시 장애는 아니지만 지켜봐야 한다 |
| 사용자 영향 실패 | ERROR | 알림과 장애 분석 대상이다 |
| 상세 내부 상태 | DEBUG | 운영 기본 로그로 남기기에는 비용이 크다 |
| 민감정보 포함 가능 | 기록 금지 또는 마스킹 | 공개 저장소와 운영 로그 모두 위험하다 |

로그는 무엇 때문에 실패했는지, 장애 당시 무슨 일이 있었는지 되짚는 데 강하고, 주문이나 결제 같은 업무 이벤트를 분석할 때도 쓴다. 하지만 로그만으로는 장애가 얼마나 퍼졌는지 안 보인다. 그건 메트릭으로 본다.

## 자주 깨지는 곳

- `e.getMessage()`만 남기면, stack trace와 앞뒤 상황이 없어 어디서 왜 실패했는지 모른다.
- user id, token, raw request body를 그대로 남기면, 로그 자체가 보안 사고가 된다.
- 로그를 통문자열로만 남기면, 필드로 검색하거나 집계하기 어렵다.
- 같은 예외를 여러 계층에서 또 남기면, 한 번 실패한 것이 여러 번처럼 보여 헷갈린다.
- 예외 로그만 있고 주문 상태 같은 업무 상태가 없으면, 무엇을 하다 실패했는지 알 수 없다.
- 실패 로그만 있고 성공 로그가 없으면, 정상일 때와 비교할 기준이 없다.
- request id가 없으면, 흩어진 로그를 한 요청의 흐름으로 묶지 못한다.

## 운영에서 볼 것

- 실패 케이스에서 원인을 찾는 데 필요한 필드가 남는지 테스트한다.
- 로그에 trace id, endpoint, status, elapsed time, error code가 있는지 본다.
- 메트릭으로는 로그량, error log rate, ingestion 실패율을 본다.
- 토큰, 비밀번호, 주민번호, 이메일 같은 민감정보가 없는지 보안 점검한다.

## 한 번에 설명하기

> 로그는 장애가 났을 때 그 요청이 어떤 상태였고 왜 실패했는지 확인하려고 남깁니다.
>
> request id, endpoint, 상태, 결과, elapsed time을 필드로 나눠 남기고, 민감정보는 아예 남기지 않거나 마스킹합니다. ERROR만 남기지 않고 정상 흐름도 짧게 남겨서 실패와 비교할 수 있게 합니다.
>
> 장애가 얼마나 퍼졌는지는 로그가 아니라 메트릭으로 봅니다.

## 꼬리 질문

- 좋은 운영 로그에는 어떤 필드가 들어가야 하나?
- 로그에 민감정보가 남으면 어떤 문제가 생기나?
- 로그와 메트릭은 역할이 어떻게 다른가?

## 내 사례

- [[inherited-access-system-incidents|이어받은 출입 시스템의 장애 추적]]: 삼켜지던 비동기 에러에 로그 붙이기

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Boot: Logging](https://docs.spring.io/spring-boot/reference/features/logging.html)
- [OWASP: Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

## 관련 문서

- [[02-practical-backend/observability/observability|observability]]
- [[trace-id-and-correlation-id]]
- [[metrics]]
- [[01-core/network/http-basics|http-basics]]
