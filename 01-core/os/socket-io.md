---
title: Socket I/O
description: 네트워크 소켓, connection backlog, socket buffer와 서버 지연
---

# Socket I/O

## 한 줄 정의

Socket I/O는 프로세스가 네트워크 연결을 통해 데이터를 주고받는 작업이며, connection backlog, socket buffer, timeout, 네트워크 대기 상태가 서버 처리량에 영향을 준다.

## 실무에서 왜 중요한가

Socket I/O를 이해하지 못하면 다음 문제가 생긴다.

- 외부 API 지연 때문에 애플리케이션 스레드가 고갈되는 원인을 놓친다.
- connection refused, connection reset, timeout의 차이를 구분하지 못한다.
- 서버는 살아 있는데 요청 연결이 실패하는 상황을 backlog나 connection pool 관점에서 보지 못한다.
- 네트워크 대기 시간이 CPU 사용률보다 응답 시간에 더 큰 영향을 주는 상황을 설명하지 못한다.

## 동작 원리

1. 클라이언트가 서버 IP와 port로 TCP 연결을 요청한다.
2. 연결 수립 전 요청은 SYN queue에 머물 수 있다.
3. TCP handshake가 끝난 연결은 accept queue에서 애플리케이션의 `accept()`를 기다린다.
4. 애플리케이션이 accept하면 연결 socket이 생성된다.
5. 데이터는 socket buffer를 거쳐 애플리케이션으로 전달된다.
6. 애플리케이션이 느리게 읽거나 쓰면 buffer가 차고 송수신이 지연된다.
7. 연결 수, backlog, timeout, 네트워크 상태에 따라 실패 방식이 달라진다.

## 주요 개념

| 개념 | 의미 | 실무 영향 |
|---|---|---|
| SYN queue | handshake가 끝나기 전 연결 요청 큐 | 폭주나 공격 상황에서 연결 지연/실패가 발생할 수 있다 |
| accept queue | handshake 완료 후 accept 대기 큐 | 애플리케이션 accept가 늦으면 연결 실패나 지연이 발생할 수 있다 |
| socket buffer | 송수신 데이터를 임시 저장하는 OS 버퍼 | 느린 소비자가 있으면 buffer가 차고 지연된다 |
| connection timeout | 연결 수립까지 기다리는 시간 | 서버 장애, 방화벽, 네트워크 단절 확인에 중요하다 |
| read timeout | 연결 후 응답을 기다리는 시간 | 외부 API 처리 지연과 연결된다 |
| connection reset | 연결이 중간에 강제로 끊김 | 서버 종료, LB, 방화벽, peer reset 등을 의심한다 |

## 실무 판단 기준

| 상황 | 확인할 것 | 이유 |
|---|---|---|
| connection refused | port listen 여부, backlog, 서버 상태 | 연결 자체가 거절된 상태다 |
| connection timeout | 방화벽, 라우팅, 서버 도달성 | SYN 응답을 받지 못했을 수 있다 |
| read timeout | 상대 서버 처리 시간, thread pool | 연결은 됐지만 응답이 늦다 |
| connection reset | 서버/LB 종료, keep-alive mismatch | 기존 연결이 중간에 끊긴 상황이다 |
| 요청 폭증 | SYN queue, accept queue, thread pool | 연결 수락과 처리 속도를 함께 봐야 한다 |

## 자주 나는 실수

- connection timeout과 read timeout을 같은 문제로 본다.
- connection pool만 늘리고 상대 서버 처리량을 고려하지 않는다.
- keep-alive 연결이 오래 유지될수록 항상 좋다고 생각한다.
- 서버 thread pool 고갈을 네트워크 장애로만 오해한다.
- SYN queue, accept queue, client timeout을 함께 보지 않는다.

## 확인 방법

- 테스트: 외부 API 지연, 연결 거부, 연결 폭증 상황을 재현한다.
- 로그: timeout 종류, remote address, connection reset, pool 대기 시간을 남긴다.
- 메트릭: active connections, connection pool usage, accept count, socket errors를 본다.
- 명령어: `ss -tan`, `netstat`, `lsof -i`, `sar -n TCP,ETCP 1`로 확인한다.

## 핵심 요약

Socket I/O는 네트워크 연결과 데이터 송수신을 OS socket을 통해 처리하는 작업이다. 연결 실패는 connection refused, connection timeout, read timeout, connection reset처럼 원인이 다르므로 구분해야 한다. 서버가 살아 있어도 SYN queue, accept queue, thread pool, connection pool, LB 설정 때문에 요청이 실패할 수 있다. 외부 API 호출이 많은 Java 서버는 socket I/O 대기 시간이 스레드 고갈로 이어질 수 있다. 장애 분석에서는 네트워크 지표와 애플리케이션 thread/pool 지표를 함께 봐야 한다.

## 꼬리 질문

- connection timeout과 read timeout은 어떻게 다른가?
- connection refused와 connection reset은 어떤 상황에서 발생하는가?
- SYN queue와 accept queue는 어떤 차이가 있는가?
- accept queue가 가득 차면 어떤 증상이 나타날 수 있는가?
- 외부 API 지연이 서버 스레드 고갈로 이어지는 이유는 무엇인가?

## 관련 문서

- [[os]]
- [[tcp-connection]]
- [[timeout]]
- [[network]]
- [[performance]]
