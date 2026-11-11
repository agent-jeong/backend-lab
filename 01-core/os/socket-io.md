---
title: 소켓 I/O
description: 소켓으로 연결을 받고 데이터를 주고받는 과정과, 연결이 어디서 막히는지 가리는 법
tags: [concept, os]
---

# 소켓 I/O

Socket I/O는 프로세스가 네트워크 연결로 데이터를 주고받는 일이다. 얼마나 많이, 빨리 주고받을 수 있는지는 connection backlog, socket buffer, timeout, 네트워크 상태에 달려 있다.

결제나 배송 같은 외부 API를 많이 부르는 Java 서버에서는 CPU 사용률보다 네트워크를 기다리는 시간이 응답 시간을 더 크게 흔든다. 기다리는 시간이 길어지면 애플리케이션 스레드가 거기 묶여 바닥난다. 서버가 멀쩡히 살아 있어도 backlog나 connection pool이 차서 연결이 실패하기도 한다.

## 동작

1. 클라이언트가 서버 IP와 port로 TCP 연결을 요청한다.
2. handshake가 끝나기 전의 연결 요청은 SYN queue에 머문다.
3. TCP handshake가 끝난 연결은 accept queue에서 애플리케이션의 `accept()`를 기다린다.
4. 애플리케이션이 accept하면 그 연결을 위한 socket이 생긴다.
5. 데이터는 socket buffer를 거쳐 애플리케이션으로 간다.
6. 애플리케이션이 느리게 읽거나 쓰면 buffer가 차고 송수신이 늦어진다.
7. 연결 수, backlog, timeout, 네트워크 상태에 따라 어떤 에러로 실패하는지가 달라진다.

| 개념 | 의미 | 실무 영향 |
|---|---|---|
| SYN queue | handshake가 끝나기 전 연결 요청 큐 | 폭주나 공격 상황에서 연결이 지연되거나 실패한다 |
| accept queue | handshake 완료 후 accept 대기 큐 | 애플리케이션 accept가 늦으면 연결이 지연되거나 실패한다 |
| socket buffer | 송수신 데이터를 임시 저장하는 OS 버퍼 | 느린 소비자가 있으면 buffer가 차고 지연된다 |
| connection timeout | 연결이 맺어질 때까지 기다리는 시간 | 이게 나면 서버 장애, 방화벽, 네트워크 단절을 의심한다 |
| read timeout | 연결 후 응답을 기다리는 시간 | 이게 나면 외부 API가 처리하는 데 오래 걸리는 쪽이다 |
| connection reset | 연결이 중간에 강제로 끊김 | 서버 종료, LB, 방화벽, peer reset 등을 의심한다 |

## 실패 유형별로 볼 것

실패 메시지마다 원인이 다르다. 그래서 먼저 어떤 실패인지부터 가린다.

| 상황 | 확인할 것 | 이유 |
|---|---|---|
| connection refused | 그 port를 듣는 프로세스가 있는지, 서버 프로세스가 떠 있는지 | 듣는 곳이 없어서 OS가 바로 거절했다 |
| connection timeout | 방화벽, 라우팅, 서버 도달성 | SYN 응답을 받지 못했을 가능성이 크다 |
| read timeout | 상대 서버 처리 시간, thread pool | 연결은 됐지만 응답이 늦다 |
| connection reset | 서버/LB 종료, keep-alive mismatch | 기존 연결이 중간에 끊겼다 |
| 요청 폭증 | SYN queue, accept queue, thread pool | accept queue가 차면 Linux는 새 연결을 거절하지 않고 버린다. 그래서 refused가 아니라 connect timeout으로 보인다 |

## 자주 깨지는 곳

- connection timeout과 read timeout을 같은 문제로 보면 엉뚱한 곳을 찾는다. 앞의 것은 상대에게 닿지 못한 것이고, 뒤의 것은 닿았는데 상대가 느린 것이다.
- connection pool만 늘리면, 상대 서버가 처리하는 양이 그대로인 한 기다리는 자리만 pool에서 상대 서버로 옮겨 간다.
- keep-alive를 길게 잡을수록 좋은 건 아니다. 상대나 LB가 먼저 끊은 연결로 요청을 보내면 connection reset이 난다.
- 서버 thread pool이 바닥난 걸 네트워크 장애로만 보면 원인을 놓친다. 느린 외부 호출에 스레드가 묶인 게 원인일 때가 많다.
- SYN queue, accept queue, client timeout을 하나씩 따로 보면 연결이 어디서 막히는지 안 보인다. 셋을 같이 본다.

## 운영에서 볼 것

- 외부 API 지연, 연결 거부, 연결 폭증 상황을 재현해 본다.
- 로그에 timeout 종류, remote address, connection reset, pool 대기 시간을 남긴다.
- 메트릭은 active connections, connection pool usage, accept count, socket errors를 본다.
- 명령어는 `ss -tan`, `netstat`, `lsof -i`, `sar -n TCP,ETCP 1`을 쓴다.
- 네트워크 지표와 애플리케이션 thread/pool 지표는 같이 놓고 본다.

## 한 번에 설명하기

> Socket I/O는 OS socket으로 연결을 맺고 데이터를 주고받는 일입니다.
>
> 연결 실패는 refused, connection timeout, read timeout, reset마다 원인이 달라서, 어떤 실패인지부터 가립니다.
>
> 서버가 살아 있어도 SYN queue, accept queue, thread pool, connection pool, LB 설정 때문에 요청이 실패할 수 있어서, 네트워크 지표와 애플리케이션 pool 지표를 같이 봅니다.

## 꼬리 질문

- connection timeout과 read timeout은 어떻게 다른가?
- connection refused와 connection reset은 어떤 상황에서 생기나?
- SYN queue와 accept queue는 어떻게 다른가?
- accept queue가 가득 차면 어떤 증상이 나타나나?
- 외부 API 지연이 서버 스레드 고갈로 이어지는 이유는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [socket(7)](https://man7.org/linux/man-pages/man7/socket.7.html)
- [tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[tcp-connection]]
- [[timeout]]
- [[01-core/network/network|network]]
- [[02-practical-backend/performance/performance|performance]]
