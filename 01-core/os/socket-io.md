---
title: 소켓 I/O
description: 네트워크 소켓, connection backlog, socket buffer와 서버 지연
tags: [concept, os]
---

# 소켓 I/O

Socket I/O는 프로세스가 네트워크 연결로 데이터를 주고받는 작업이다. 처리량은 connection backlog, socket buffer, timeout, 네트워크 대기 상태에 좌우된다.

외부 API 호출이 많은 Java 서버에서는 CPU 사용률보다 네트워크 대기 시간이 응답 시간을 더 크게 흔든다. 대기가 길어지면 애플리케이션 스레드가 묶여 고갈된다. 서버가 살아 있는데도 backlog나 connection pool 때문에 연결이 실패할 수 있다.

## 동작

1. 클라이언트가 서버 IP와 port로 TCP 연결을 요청한다.
2. 연결 수립 전 요청은 SYN queue에 머문다.
3. TCP handshake가 끝난 연결은 accept queue에서 애플리케이션의 `accept()`를 기다린다.
4. 애플리케이션이 accept하면 연결 socket이 생긴다.
5. 데이터는 socket buffer를 거쳐 애플리케이션으로 간다.
6. 애플리케이션이 느리게 읽거나 쓰면 buffer가 차고 송수신이 늦어진다.
7. 연결 수, backlog, timeout, 네트워크 상태에 따라 실패하는 모습이 달라진다.

| 개념 | 의미 | 실무 영향 |
|---|---|---|
| SYN queue | handshake가 끝나기 전 연결 요청 큐 | 폭주나 공격 상황에서 연결이 지연되거나 실패한다 |
| accept queue | handshake 완료 후 accept 대기 큐 | 애플리케이션 accept가 늦으면 연결이 지연되거나 실패한다 |
| socket buffer | 송수신 데이터를 임시 저장하는 OS 버퍼 | 느린 소비자가 있으면 buffer가 차고 지연된다 |
| connection timeout | 연결 수립까지 기다리는 시간 | 서버 장애, 방화벽, 네트워크 단절을 가려낸다 |
| read timeout | 연결 후 응답을 기다리는 시간 | 외부 API 처리 지연과 연결된다 |
| connection reset | 연결이 중간에 강제로 끊김 | 서버 종료, LB, 방화벽, peer reset 등을 의심한다 |

## 실패 유형별로 볼 것

실패 메시지마다 원인이 다르다. 먼저 어떤 실패인지 구분한다.

| 상황 | 확인할 것 | 이유 |
|---|---|---|
| connection refused | port listen 여부, backlog, 서버 상태 | 연결 자체가 거절됐다 |
| connection timeout | 방화벽, 라우팅, 서버 도달성 | SYN 응답을 받지 못했을 가능성이 크다 |
| read timeout | 상대 서버 처리 시간, thread pool | 연결은 됐지만 응답이 늦다 |
| connection reset | 서버/LB 종료, keep-alive mismatch | 기존 연결이 중간에 끊겼다 |
| 요청 폭증 | SYN queue, accept queue, thread pool | 연결 수락 속도와 처리 속도를 같이 봐야 한다 |

## 자주 깨지는 곳

- **connection timeout과 read timeout을 같은 문제로 본다.** 하나는 도달성, 하나는 상대 처리 속도 문제다.
- **connection pool만 늘린다.** 상대 서버 처리량이 그대로면 대기 위치만 옮겨 간다.
- **keep-alive를 길게 잡을수록 좋다고 생각한다.** 상대나 LB가 먼저 끊으면 connection reset이 난다.
- **서버 thread pool 고갈을 네트워크 장애로만 본다.** 원인은 느린 외부 호출에 스레드가 묶인 것일 때가 많다.
- **SYN queue, accept queue, client timeout을 따로 본다.** 셋을 같이 봐야 연결이 어디서 막히는지 보인다.

## 운영에서 볼 것

- 외부 API 지연, 연결 거부, 연결 폭증 상황을 재현해 본다.
- 로그에 timeout 종류, remote address, connection reset, pool 대기 시간을 남긴다.
- 메트릭은 active connections, connection pool usage, accept count, socket errors를 본다.
- 명령어는 `ss -tan`, `netstat`, `lsof -i`, `sar -n TCP,ETCP 1`.
- 네트워크 지표와 애플리케이션 thread/pool 지표는 같이 놓고 본다.

## 한 번에 설명하기

> Socket I/O는 OS socket으로 연결을 맺고 데이터를 주고받는 작업입니다. 연결 실패는 refused, connection timeout, read timeout, reset이 각각 원인이 달라서 저는 어떤 실패인지부터 구분합니다. 서버가 살아 있어도 SYN queue, accept queue, thread pool, connection pool, LB 설정 때문에 요청이 실패할 수 있으니, 네트워크 지표와 애플리케이션 pool 지표를 같이 봅니다.

## 꼬리 질문

- connection timeout과 read timeout은 어떻게 다른가?
- connection refused와 connection reset은 어떤 상황에서 생기나?
- SYN queue와 accept queue는 어떻게 다른가?
- accept queue가 가득 차면 어떤 증상이 나타나나?
- 외부 API 지연이 서버 스레드 고갈로 이어지는 이유는?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [socket(7)](https://man7.org/linux/man-pages/man7/socket.7.html)
- [tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[tcp-connection]]
- [[timeout]]
- [[01-core/network/network|network]]
- [[02-practical-backend/performance/performance|performance]]
