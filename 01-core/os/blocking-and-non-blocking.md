---
title: Blocking과 Non-blocking
description: Blocking I/O와 Non-blocking I/O가 서버 스레드를 어떻게 다르게 쓰고, 언제 무엇을 고르는지
tags: [concept, os]
---

# Blocking과 Non-blocking

Blocking은 작업이 끝날 때까지 호출한 스레드가 기다리는 방식이다. Non-blocking은 지금 처리할 수 없으면 바로 돌아와서, 호출한 쪽이 다른 일을 계속하게 하는 방식이다.

Non-blocking으로 바꾼다고 DB나 외부 API가 빨라지지는 않는다. 결제 API가 3초 걸리면 Non-blocking으로 불러도 3초다. 달라지는 건 그 3초 동안 스레드를 붙잡아 두느냐 놓아 주느냐다. 그래서 고를 때는 유행보다 요청이 어떻게 들어오는지, 쓰는 라이브러리가 지원하는지, 팀이 운영해 본 적이 있는지를 본다.

## 동작

### Blocking I/O

```
Thread-1 → 외부 API 호출 → 응답 올 때까지 대기 → 다음 작업
Thread-2 → DB 조회       → 응답 올 때까지 대기 → 다음 작업
```

구현이 단순하다. 대신 호출하는 동안 스레드가 기다리고 있으니, 동시 요청이 많고 I/O 대기가 길면 스레드가 그만큼 많이 필요하다. 외부 API가 느려졌을 때 웹 서버 스레드가 전부 기다리다 바닥나는 이유가 이것이다.

### Non-blocking I/O

```
Event Loop → 요청 등록 → 즉시 반환
Event Loop → 다른 작업 처리
응답 도착 → callback/reactive pipeline 실행
```

적은 스레드로 많은 I/O 대기를 처리한다. 대신 코드 흐름을 따라가기 어렵고 디버깅도 힘들어진다. event loop에서 blocking 작업을 돌리면 그 loop가 맡은 요청이 전부 늦어진다.

Non-blocking I/O와 async/reactive 프로그래밍은 다른 이야기다. 앞의 것은 I/O를 부르는 방식이고, 뒤의 것은 코드를 짜는 방식이다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD API | Blocking으로 충분 | DB connection pool과 thread pool 크기만 맞게 잡으면 된다 |
| 외부 API 호출이 많고 대기가 김 | Non-blocking 검토 | 스레드가 대기하는 비용을 줄인다 |
| CPU 계산이 많음 | Non-blocking 이점 작음 | CPU는 결국 코어 수만큼만 실행된다 |
| 팀이 reactive 운영 경험 없음 | 신중하게 | 디버깅이 어렵고, 트랜잭션 처리와 라이브러리 호환에서 막히는 곳이 생긴다 |
| event loop 사용 중 | blocking 호출 금지 | event loop가 막히면 많은 요청이 같이 지연된다 |

스레드 수를 늘리는 것과 I/O 모델을 바꾸는 것은 서로 다른 해법이다. 스레드를 늘리는 쪽이 단순하지만, 스레드마다 메모리를 쓰고 context switching도 늘어난다.

## 자주 깨지는 곳

- Non-blocking으로 바꾸면 DB나 외부 API도 빨라질 거라 기대하면 실망한다. 상대 쪽 응답 시간은 그대로다.
- event loop 안에서 blocking 호출을 하면, blocking JDBC나 파일 I/O, `Thread.sleep()` 하나가 loop 전체를 멈춘다.
- WebFlux에 JPA를 섞으면서 JPA가 blocking이라는 걸 잊으면, 결국 event loop에서 blocking 호출을 하는 셈이 된다.
- blocking 서버에서 스레드 수만 늘리면 context switching과 메모리 사용량이 같이 커진다.
- Non-blocking 호출을 제한 없이 늘리면, timeout과 backpressure, connection pool 제한이 없는 한 downstream이 받아 낼 수 있는 양을 넘긴다. Non-blocking으로 불러도 downstream이 처리할 수 있는 양은 그대로다.

## 운영에서 볼 것

- 외부 API를 일부러 느리게 만들어 놓고, thread pool과 event loop, queue 대기가 어떻게 변하는지 테스트한다.
- 로그에 thread name, 요청 처리 시간, 외부 호출 대기 시간을 남긴다.
- 메트릭은 active threads, event loop latency, pending tasks, connection pool usage를 본다.
- thread dump, async profiler, event loop blocked 경고로 어디서 막히는지 찾는다.

## 한 번에 설명하기

> Blocking은 I/O가 끝날 때까지 스레드가 기다리고, Non-blocking은 바로 돌아와서 그 스레드가 다른 일을 하게 합니다.
>
> 일반 CRUD API라면 blocking 모델에서 pool 크기만 잘 맞춰도 충분하다고 보고, 오래 기다려야 하는 외부 호출이 많을 때 Non-blocking을 검토합니다.
>
> Non-blocking을 쓸 때는 event loop에 blocking 호출이 섞이지 않게 하고, timeout과 backpressure로 downstream에 보내는 양을 제한합니다.

## 꼬리 질문

- Blocking I/O에서 외부 API 지연이 스레드 고갈로 이어지는 이유는?
- Non-blocking을 쓰면 항상 처리량이 좋아지나?
- event loop에서 blocking 호출을 하면 어떤 문제가 생기나?
- CPU-bound 작업과 I/O-bound 작업은 스레드 전략이 어떻게 다른가?
- Non-blocking I/O와 async/reactive 프로그래밍은 어떻게 다른가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[socket-io]]
- [[02-practical-backend/performance/performance|performance]]
