---
title: 분산 추적
description: 요청 하나가 여러 서비스를 거치는 동안 어디서 시간이 걸렸는지 따라가는 방법
tags: [concept, observability]
---

# 분산 추적

Distributed Tracing은 요청 하나가 여러 서비스와 DB, 외부 API를 거치는 과정을 구간(span)별로 기록해서, 전체 경로와 오래 걸린 구간을 보여 준다.

주문 하나에 회원, 재고, 결제 서비스를 차례로 부르는 구조라면, 로그만으로는 어디서 시간이 새는지 찾기 어렵다. 서비스마다 로그 시각이 흩어져 있어서 요청 흐름을 다시 맞추기도 힘들다. 트레이스를 보면 DB 쿼리, Redis, HTTP 호출 중 어느 구간이 느린지 바로 나뉜다.

## 트레이스가 만들어지는 흐름

1. 요청이 들어오면 trace id를 만들거나 전달받는다.
2. 서비스 내부 작업과 외부 호출을 span으로 기록한다.
3. 각 span은 시작 시간, 종료 시간, parent span, tag를 가진다.
4. HTTP header나 message metadata로 trace context를 전파한다.
5. 모인 trace로 요청이 지나간 경로와 오래 걸린 구간을 본다.

```text
Trace:
- POST /orders 820ms
  - validate request 8ms
  - SELECT user 12ms
  - POST payment-api 690ms
  - INSERT order 18ms
```

이 경우에는 주문 저장보다 결제 API 호출 구간을 먼저 본다. 느린 API라면 가장 긴 span과 여러 번 반복되는 span부터 본다.

## 상황별로 볼 것

| 상황 | 확인할 것 | 이유 |
|---|---|---|
| API p99 증가 | slow trace 상위 span | 가장 긴 구간을 찾는다 |
| 외부 API 장애 | HTTP client span | timeout, retry, status를 확인한다 |
| DB 지연 | DB span, query tag | 쿼리 시간과 횟수를 확인한다 |
| 메시지 처리 지연 | producer/consumer span | 비동기 경계를 연결한다 |
| 비용 증가 | sampling rate, tag 수 | 저장량과 cardinality를 줄인다 |

트레이스는 원인이 어디 있는지 좁히는 데는 강하지만, 장애가 얼마나 퍼졌는지는 메트릭이 더 잘 보여 준다. sampling으로 빠진 요청이나 계측이 안 된 구간은 트레이스에 안 나오고, span tag를 어떻게 붙일지와 비용도 따로 챙겨야 한다.

## 자주 깨지는 곳

- trace id를 남기기만 하고 외부 호출로 넘기지 않으면, 서비스 경계에서 trace가 끊긴다. HTTP, messaging, async 경계를 모두 넘어가야 한다.
- span에 민감정보나 긴 query parameter를 그대로 넣으면, 트레이스 저장소로 민감정보가 새고 저장량도 는다.
- 모든 요청을 100% 저장하면, 비용이 크게 늘어난다.
- sampling 때문에 error trace가 빠지는지 확인하지 않으면, 정작 장애 난 요청의 trace가 없다.
- trace 몇 개만 보고 영향 범위를 판단하면, 장애 규모를 잘못 짚는다.

## 운영에서 볼 것

- 서비스 간 호출에서 trace id가 끊기지 않는지 테스트한다.
- trace id로 애플리케이션 로그와 trace를 연결한다.
- p95/p99가 오른 시간대의 slow trace를 확인한다.
- 애플리케이션 내부 CPU 병목은 trace만으로 다 설명되지 않는다. 그때는 프로파일링으로 넘어간다.

## 한 번에 설명하기

> Distributed Tracing은 요청 하나가 여러 서비스를 거치는 흐름을 span 단위로 보여 줍니다.
>
> 느린 API를 보면 가장 긴 span과 반복 호출되는 span부터 확인합니다. 장애 규모는 trace가 아니라 메트릭으로 따로 판단합니다.
>
> trace context가 HTTP, 메시징, 비동기 경계를 넘어 이어지는지 확인하고, 비용과 민감정보 때문에 sampling과 tag는 미리 정해 둡니다.

## 꼬리 질문

- trace와 log는 어떻게 함께 쓰나?
- span과 trace는 어떻게 다른가?
- sampling 때문에 생길 수 있는 문제는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OpenTelemetry: Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)

## 관련 문서

- [[02-practical-backend/observability/observability|observability]]
- [[trace-id-and-correlation-id]]
- [[metrics]]
- [[02-practical-backend/performance/bottleneck-analysis|bottleneck-analysis]]
