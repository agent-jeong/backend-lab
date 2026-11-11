---
title: Observability가 필요한 이유
description: 장애가 났을 때 원인을 빨리 찾으려면 로그, 메트릭, 트레이스를 미리 남겨 둬야 하는 이유
tags: [concept, observability]
---

# Observability가 필요한 이유

Observability는 시스템이 밖으로 남기는 신호만 보고도 안에서 무슨 일이 벌어지는지, 장애 원인이 어디인지 알아낼 수 있게 해 두는 것이다.

주문 생성이 느려졌는데 로그가 부족하면 원인을 짐작할 수밖에 없다. 우리 API가 느린지, DB가 느린지, 결제 API가 느린지 가르지 못하면 복구도 늦어진다. 그 짐작을 확인 가능한 증거로 바꾸려고 미리 신호를 남겨 두는 일이 Observability다.

## 신호를 보는 순서

1. 서비스가 요청을 처리하며 로그, 메트릭, 트레이스를 남긴다.
2. 메트릭으로 무엇이 이상한지, 얼마나 퍼졌는지 빠르게 본다.
3. 트레이스로 요청이 어느 구간에서 느려졌는지 본다.
4. 로그로 그 요청의 입력, 상태, 예외, 코드가 어떤 분기를 탔는지 본다.
5. 원인을 좁혀 조치하고, 다음에 더 빨리 찾도록 계측과 알림을 보완한다.

```text
증상:
- 주문 생성 API p95 2초 초과

확인:
- 메트릭: error rate 정상, latency 증가
- 트레이스: 외부 결제 API 구간에서 1.7초 사용
- 로그: retry 2회 발생

판단:
- 애플리케이션 로직보다 외부 의존성 지연과 retry 정책을 먼저 확인한다.
```

## 질문별로 먼저 볼 신호

| 질문 | 먼저 볼 신호 | 이유 |
|---|---|---|
| 장애인가 | SLI, error rate, latency | 사용자가 영향을 받는지 본다 |
| 어디가 느린가 | trace, dependency latency | 지연 구간을 나눈다 |
| 왜 실패했나 | error log, exception, event log | 실패 조건을 확인한다 |
| 얼마나 퍼졌나 | endpoint, region, instance metric | 영향 범위를 좁힌다 |
| 재발할 수 있나 | saturation, queue, retry metric | 구조에서 온 원인인지 본다 |

계측은 설계하는 데도 운영하는 데도 품이 든다. 지표를 잘못 고르면 판단도 틀리고, 지표가 많아도 무엇을 할지 정하는 데 쓰이지 않으면 소용없다. 계측을 해 둔다고 모든 문제가 저절로 설명되지도 않는다.

## 자주 깨지는 곳

- 로그만 잔뜩 남기고 메트릭과 트레이스가 없으면, 어디가 문제인지부터 막힌다.
- 평균 latency만 보면, 일부 사용자가 겪는 큰 지연이 평균에 묻혀 장애를 작게 본다.
- 모든 이벤트에 알림을 걸면, 알림에 지쳐 진짜 장애를 놓친다. 반대로 알림이 없으면 장애를 고객 문의로 알게 된다.
- request id 없이 로그를 남기면, 한 요청이 어디를 거쳤는지 따라갈 수 없다.
- 장애 뒤 코드만 고치고 계측을 보완하지 않으면, 다음 분석도 사람 경험에 기대게 되고 같은 문제가 반복된다.

## 운영에서 볼 것

- 장애 상황을 가정하고, 어떤 지표와 로그로 원인을 찾을지 미리 점검한다.
- 로그에 request id, endpoint, 사용자를 특정하지 않는 식별자, 예외 원인이 있는지 본다.
- 메트릭은 latency, traffic, error, saturation을 본다.
- 트레이스에서 DB, Redis, 외부 API, queue 구간 시간이 나뉘어 보이는지 확인한다.

## 한 번에 설명하기

> Observability는 장애 원인을 짐작하지 않고 증거로 좁히려고 미리 해 두는 준비입니다.
>
> 장애가 나면 메트릭으로 장애인지, 얼마나 퍼졌는지 먼저 봅니다. 그다음 트레이스로 어느 구간이 느린지 나누고, 로그로 어떤 조건에서 실패했는지 확인합니다.
>
> 장애가 끝나면 코드만 고치지 않고, 이번에 모자랐던 계측과 알림도 같이 채웁니다.

## 꼬리 질문

- Monitoring과 Observability는 어떻게 다른가?
- 로그, 메트릭, 트레이스는 각각 어떤 질문에 답하나?
- 장애 후 계측을 보완해야 하는 이유는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OpenTelemetry: Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

## 관련 문서

- [[observability]]
- [[logging]]
- [[metrics]]
- [[distributed-tracing]]
- [[02-practical-backend/performance/performance|performance]]
