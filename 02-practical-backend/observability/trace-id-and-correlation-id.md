---
title: traceId와 correlationId
description: 요청 흐름을 로그, 트레이스, 메시지 처리까지 연결하는 식별자 설계
---

# traceId와 correlationId

## 한 줄 정의

traceId와 correlationId는 여러 로그, 서비스 호출, 비동기 작업을 하나의 요청 또는 업무 흐름으로 묶기 위한 식별자다.

## 실무에서 왜 문제 되는가

- 장애 로그가 여러 서버에 흩어지면 하나의 요청 흐름을 찾기 어렵다.
- 외부 API나 메시지 큐로 넘어가면서 식별자가 끊기면 분석이 단절된다.
- 사용자 id 같은 민감하거나 변경 가능한 값을 추적 키로 쓰면 보안과 분석 문제가 생긴다.
- 재시도, 비동기 처리, 배치에서는 하나의 HTTP 요청보다 긴 업무 흐름을 추적해야 할 수 있다.

## 동작 원리

1. 요청 진입 시 기존 trace id가 있으면 사용하고 없으면 생성한다.
2. 로그 MDC나 context에 식별자를 저장한다.
3. 내부 로그와 메트릭 tag, trace span에 식별자를 연결한다.
4. 외부 HTTP 호출, 메시지 header, async task로 식별자를 전파한다.
5. 장애 분석 시 식별자로 관련 로그와 trace를 검색한다.

## 실무 판단 기준

| 구분 | 용도 | 예시 |
|---|---|---|
| traceId | 기술적 요청 추적 | 한 HTTP 요청의 전체 trace |
| spanId | trace 내부 작업 구간 | DB 조회, 외부 API 호출 |
| correlationId | 업무 흐름 연결 | 주문 생성부터 결제 콜백까지 |
| idempotencyKey | 중복 처리 방지 | 결제 요청 재시도 식별 |
| requestId | API 요청 식별 | gateway에서 생성한 요청 id |

## 자주 나는 실수

- controller에서는 id가 있지만 async thread에서 사라진다.
- HTTP header 전파는 했지만 message queue header에는 넣지 않는다.
- trace id를 새로 생성해 기존 upstream trace를 끊는다.
- user id나 email을 correlation id처럼 사용한다.
- 모든 로그에 id가 있는지 검증하지 않는다.

## 확인 방법

- 테스트: HTTP 호출, async, message consumer에서 id가 유지되는지 확인한다.
- 로그: 같은 trace id로 한 요청의 로그가 검색되는지 확인한다.
- 메트릭: error exemplar나 trace link가 연결되는지 확인한다.
- 트레이스: 서비스 경계와 비동기 경계에서 trace가 끊기지 않는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 분산 로그를 하나의 흐름으로 묶는다 | context 전파 구현이 필요하다 |
| 장애 분석 시간이 줄어든다 | 비동기와 배치에서는 경계 설계가 어렵다 |
| 고객 문의와 내부 분석을 연결하기 쉽다 | 민감정보를 식별자로 쓰면 위험하다 |

## 짧은 예제

```text
HTTP Header:
- traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
- X-Correlation-Id: order-20260602-001
```

업무 식별자는 공개 가능한 범위와 보존 기간을 고려해 설계해야 한다.

## 핵심 요약

traceId는 한 요청의 기술적 흐름을 추적하는 데 사용한다.

correlationId는 여러 요청과 비동기 작업을 포함하는 업무 흐름을 묶을 때 사용한다.

식별자는 HTTP, 메시지, async boundary를 넘어 전파되어야 한다.

사용자 개인정보나 토큰을 추적 식별자로 쓰면 안 된다.

면접에서는 "장애 로그를 어떻게 하나의 요청 흐름으로 묶었는가"를 설명하면 좋다.

## 꼬리 질문

- traceId와 correlationId의 차이는 무엇인가?
- 비동기 처리에서 trace id가 끊기는 이유는 무엇인가?
- request id를 로그에 남길 때 민감정보 관점에서 주의할 점은 무엇인가?

## 관련 문서

- [[observability]]
- [[logging]]
- [[distributed-tracing]]
- [[02-practical-backend/idempotency/idempotency-key|idempotency-key]]
