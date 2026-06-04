---
title: Distributed Tracing
description: 분산 시스템에서 요청 흐름과 의존성 지연을 추적하는 방법
---

# Distributed Tracing

## 한 줄 정의

Distributed Tracing은 하나의 요청이 여러 서비스와 의존성을 거치는 과정을 span 단위로 기록해 전체 흐름과 지연 구간을 보여주는 방식이다.

## 실무에서 왜 문제 되는가

- 마이크로서비스나 외부 API 호출이 많으면 전체 지연 원인을 로그만으로 찾기 어렵다.
- DB 쿼리, Redis, HTTP 호출 중 어느 구간이 느린지 분리해야 한다.
- 같은 장애라도 서비스별 로그 시간이 흩어져 있으면 요청 흐름을 재구성하기 어렵다.
- sampling 정책이 없으면 비용이 커지고, 과도한 sampling은 장애 trace를 놓칠 수 있다.

## 동작 원리

1. 요청이 들어오면 trace id를 생성하거나 전달받는다.
2. 서비스 내부 작업과 외부 호출을 span으로 기록한다.
3. 각 span은 시작 시간, 종료 시간, parent span, tag를 가진다.
4. HTTP header나 message metadata로 trace context를 전파한다.
5. 수집된 trace를 통해 전체 요청 경로와 지연 구간을 분석한다.

## 실무 판단 기준

| 상황 | 확인할 것 | 이유 |
|---|---|---|
| API p99 증가 | slow trace 상위 span | 가장 긴 구간을 찾는다 |
| 외부 API 장애 | HTTP client span | timeout, retry, status를 확인한다 |
| DB 지연 | DB span, query tag | 쿼리 시간과 횟수를 확인한다 |
| 메시지 처리 지연 | producer/consumer span | 비동기 경계를 연결한다 |
| 비용 증가 | sampling rate, tag 수 | 저장량과 cardinality를 줄인다 |

## 자주 나는 실수

- trace id는 남기지만 외부 호출로 전파하지 않는다.
- span에 민감정보나 긴 query parameter를 그대로 넣는다.
- 모든 요청을 100% 저장해 비용을 크게 만든다.
- sampling 때문에 중요한 error trace가 빠지는지 확인하지 않는다.
- trace만 보고 전체 영향 범위를 판단한다.

## 확인 방법

- 테스트: 서비스 간 호출에서 trace id가 끊기지 않는지 확인한다.
- 로그: trace id로 애플리케이션 로그와 trace를 연결한다.
- 메트릭: p95/p99가 증가한 시간대의 slow trace를 확인한다.
- 프로파일링: trace가 애플리케이션 내부 CPU 병목까지 모두 설명하지는 않는지 구분한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 요청 흐름과 의존성 지연을 한눈에 본다 | 전체 영향 범위는 메트릭이 더 적합하다 |
| 병목 구간을 빠르게 좁힌다 | sampling과 계측 누락의 영향을 받는다 |
| 서비스 경계 문제를 분석하기 좋다 | span tag 설계와 비용 관리가 필요하다 |

## 짧은 예제

```text
Trace:
- POST /orders 820ms
  - validate request 8ms
  - SELECT user 12ms
  - POST payment-api 690ms
  - INSERT order 18ms
```

이 경우 주문 저장보다 결제 API 호출 구간을 먼저 확인해야 한다.

## 핵심 요약

Distributed Tracing은 한 요청의 서비스 간 흐름을 span 단위로 보여준다.

느린 API에서는 가장 긴 span과 반복 호출되는 span을 먼저 본다.

trace context는 HTTP, messaging, async boundary를 넘어 전파되어야 한다.

trace는 원인 위치를 좁히는 데 강하지만 장애 규모 판단은 메트릭이 필요하다.

비용과 민감정보를 고려해 sampling과 tag를 설계해야 한다.

## 꼬리 질문

- trace와 log는 어떻게 함께 사용하는가?
- span과 trace의 차이는 무엇인가?
- sampling 때문에 생길 수 있는 문제는 무엇인가?

## 관련 문서

- [[observability]]
- [[trace-id-and-correlation-id]]
- [[metrics]]
- [[02-practical-backend/performance/bottleneck-analysis|bottleneck-analysis]]
