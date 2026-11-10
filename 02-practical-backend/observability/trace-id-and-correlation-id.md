---
title: traceId와 correlationId
description: 요청 흐름을 로그, 트레이스, 메시지 처리까지 연결하는 식별자 설계
tags: [concept, observability]
---

# traceId와 correlationId

traceId와 correlationId는 여러 로그, 서비스 호출, 비동기 작업을 하나의 요청이나 업무 흐름으로 묶는 식별자다.

traceId는 HTTP 요청 하나의 기술적 흐름을 따라간다. correlationId는 그보다 넓다. 재시도, 비동기 처리, 배치처럼 요청 하나보다 긴 업무 흐름을 묶을 때 쓴다. 어느 쪽이든 서비스와 큐 경계에서 끊기면 쓸모가 없다.

## 동작

1. 요청이 들어올 때 기존 trace id가 있으면 쓰고, 없으면 만든다.
2. 로그 MDC나 context에 식별자를 넣는다.
3. 내부 로그, 메트릭 tag, trace span에 식별자를 연결한다.
4. 외부 HTTP 호출, 메시지 header, async task로 식별자를 넘긴다.
5. 장애 분석 때 식별자로 관련 로그와 trace를 찾는다.

```text
HTTP Header:
- traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
- X-Correlation-Id: order-20260602-001
```

업무 식별자는 어디까지 공개해도 되는지와 얼마나 보관할지를 따져 설계한다.

## 식별자 구분

| 구분 | 용도 | 예시 |
|---|---|---|
| traceId | 기술적 요청 추적 | 한 HTTP 요청의 전체 trace |
| spanId | trace 내부 작업 구간 | DB 조회, 외부 API 호출 |
| correlationId | 업무 흐름 연결 | 주문 생성부터 결제 콜백까지 |
| idempotencyKey | 중복 처리 방지 | 결제 요청 재시도 식별 |
| requestId | API 요청 식별 | gateway에서 생성한 요청 id |

식별자가 이어지면 분산 로그가 하나의 흐름으로 묶이고, 고객 문의와 내부 분석을 연결하기도 쉽다. 대신 context 전파를 직접 구현해야 하고, 비동기와 배치에서는 경계를 어디서 끊을지 설계하기 어렵다.

## 자주 깨지는 곳

- **controller에서는 id가 있는데 async thread에서 사라진다.** MDC는 스레드를 넘어가지 않는다. 직접 넘겨야 한다.
- **HTTP header로는 넘기고 message queue header에는 안 넣는다.** consumer 쪽 로그가 따로 논다.
- **trace id를 새로 만들어 upstream trace를 끊는다.** 들어온 값이 있으면 이어 쓴다.
- **user id나 email을 correlation id처럼 쓴다.** 민감하거나 바뀔 수 있는 값이라 보안 문제와 분석 문제가 같이 생긴다.
- **모든 로그에 id가 들어갔는지 검증하지 않는다.** 정작 장애 때 빠진 로그가 나온다.

## 운영에서 볼 것

- HTTP 호출, async, message consumer에서 id가 유지되는지 테스트한다.
- 같은 trace id로 한 요청의 로그가 모두 검색되는지 확인한다.
- 메트릭에서 error exemplar나 trace link가 연결되는지 본다.
- 서비스 경계와 비동기 경계에서 trace가 끊기지 않는지 본다.

## 한 번에 설명하기

> traceId는 한 요청의 기술적 흐름을, correlationId는 여러 요청과 비동기 작업을 포함한 업무 흐름을 묶을 때 씁니다. 저는 들어온 trace id가 있으면 이어 쓰고, HTTP뿐 아니라 메시지 header와 async 작업까지 전파되는지 테스트합니다. 사용자 개인정보나 토큰은 추적 식별자로 쓰지 않습니다.

## 꼬리 질문

- traceId와 correlationId는 어떻게 다른가?
- 비동기 처리에서 trace id가 끊기는 이유는?
- request id를 로그에 남길 때 민감정보 측면에서 무엇을 조심하나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Spring Boot: Tracing](https://docs.spring.io/spring-boot/reference/actuator/tracing.html)

## 관련 문서

- [[observability]]
- [[logging]]
- [[distributed-tracing]]
- [[02-practical-backend/idempotency/idempotency-key|idempotency-key]]
