---
title: Network
description: HTTP, timeout, retry, 네트워크 장애 분석 학습 인덱스
comments: false
---

# Network

> 학습 인덱스다. 상세 내용은 `01-core/network/` 아래 개념 문서에 둔다.
> 초점은 요청 흐름, 장애 원인 분석, timeout/retry 판단이다. 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓰고, 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[http-basics|HTTP 기본 구조]]
2. [[tcp-connection|TCP와 연결]]
3. [[timeout|Timeout]]
4. [[retry|Retry]]
5. [[status-code|Status Code]]
6. [[dns|DNS]]
7. [[load-balancer|Load Balancer]]
8. [[cors|CORS]]
9. [[tls|TLS]]
10. [[websocket|WebSocket]]

## 스스로 답해 볼 질문

- HTTP 요청은 클라이언트에서 서버까지 어떤 단계를 거치는가?
- GET, POST, PUT, DELETE의 멱등성 차이는 무엇인가?
- TCP 3-way handshake와 커넥션 풀의 관계는 무엇인가?
- Connection timeout과 Read timeout은 어떻게 다른가?
- timeout과 retry는 왜 함께 설계해야 하는가?
- 재시도 가능한 에러와 불가능한 에러를 어떻게 구분하는가? (멱등성, backoff, 부하 증폭)
- 로드밸런서의 헬스체크와 무중단 배포는 어떻게 연결되는가?
- CORS Preflight는 왜 발생하고 어떻게 설정하는가?
- WebSocket과 SSE는 각각 언제 사용하는가?
- HTTP method, header, status code, stateless는 API 설계에 어떻게 반영되는가?
- keep-alive, connection pool, connection reset은 장애 분석에서 어떻게 연결되는가?
- 4xx와 5xx는 재시도 가능 여부 판단에 어떤 차이를 만드는가?
- DNS TTL과 JVM DNS cache가 다르면 장애 대응에서 무슨 일이 생기는가?
- Load Balancer의 502, 503은 어떤 원인으로 나눠 볼 수 있는가?
- 네트워크 장애는 클라이언트, DNS, LB, 애플리케이션, 외부 API 중 어떤 순서로 좁히는가?
- p95/p99 latency, timeout count, connection pool 사용률은 외부 연동 장애 판단에 어떻게 쓰는가?

## 실무에서 보는 순서

- retry는 일시 장애를 숨겨 주지만, 이미 느린 서버에는 부하를 몇 배로 늘린다.
- 장애가 나면 클라이언트, 서버, DNS, LB, 방화벽, 외부 API 중 어느 구간의 문제인지부터 나눈다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|technical-questions]]
