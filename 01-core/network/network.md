---
title: Network
description: HTTP, timeout, retry, 네트워크 장애 분석 학습 인덱스
comments: false
---

# Network

## 운영 방식

- 이 문서는 Network 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/network/` 아래 개념별 문서로 나눈다.
- 학습한 내용은 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 요청 흐름, 장애 원인 분석, timeout/retry 판단, 면접 답변을 중심으로 작성한다.

## 학습 산출물

- 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

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

## 핵심 질문

- Network를 실무에서 왜 알아야 하는가?
- HTTP 요청은 클라이언트에서 서버까지 어떤 단계를 거치는가?
- GET, POST, PUT, DELETE의 멱등성 차이는 무엇인가?
- DNS 조회 흐름과 TTL이 실무에서 왜 중요한가?
- TCP 3-way handshake와 커넥션 풀의 관계는 무엇인가?
- Connection timeout과 Read timeout은 어떻게 다른가?
- timeout과 retry는 왜 함께 설계해야 하는가?
- 재시도 가능한 에러와 불가능한 에러를 어떻게 구분하는가?
- 로드밸런서의 헬스체크와 무중단 배포는 어떻게 연결되는가?
- CORS Preflight는 왜 발생하고 어떻게 설정하는가?
- WebSocket과 SSE는 각각 언제 사용하는가?
- HTTP method, header, status code, stateless를 API 설계와 어떻게 연결할 수 있는가?
- keep-alive, connection pool, connection reset은 장애 분석에서 어떻게 연결되는가?
- 멱등성, backoff, 중복 처리, 부하 증폭을 고려한 retry 기준은 무엇인가?
- 4xx와 5xx는 재시도 가능 여부 판단에 어떤 차이를 만드는가?
- JVM DNS cache와 DNS TTL은 장애 대응에서 왜 중요한가?
- Load Balancer의 502, 503은 어떤 원인으로 나눠 볼 수 있는가?
- 네트워크 장애는 클라이언트, DNS, LB, 애플리케이션, 외부 API 중 어떤 순서로 좁히는가?
- p95/p99 latency, timeout count, connection pool 사용률은 외부 연동 장애 판단에 어떻게 쓰는가?

## 실무 관점

- Network는 API 장애 분석, 외부 연동 안정성, timeout 설정의 기반이다.
- retry는 장애를 숨길 수도 있지만 부하를 증폭시킬 수도 있다.
- 클라이언트, 서버, DNS, LB, 방화벽, 외부 API 중 어느 구간의 문제인지 나눠서 봐야 한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
