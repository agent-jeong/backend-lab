---
title: Blocking과 Non-blocking
description: Blocking I/O와 Non-blocking I/O의 차이와 서버 스레드 모델
tags: [concept, os]
---

# Blocking과 Non-blocking

Blocking은 작업을 끝낼 수 있을 때까지 호출한 스레드가 기다리는 방식이다. Non-blocking은 지금 처리할 수 없으면 바로 반환해서, 호출자가 다른 일을 계속하게 하는 방식이다.

Non-blocking은 DB나 외부 API를 빠르게 만들지 않는다. 바뀌는 것은 기다리는 동안 스레드를 붙잡아 두느냐 놓아 주느냐다. 그래서 선택 기준은 유행이 아니라 요청 패턴, 쓰는 라이브러리, 팀의 운영 경험이다.

## 동작

### Blocking I/O

```
Thread-1 → 외부 API 호출 → 응답 올 때까지 대기 → 다음 작업
Thread-2 → DB 조회       → 응답 올 때까지 대기 → 다음 작업
```

구현이 단순하다. 대신 호출 중에는 스레드가 대기하므로, 동시 요청이 많고 I/O 대기가 길면 스레드가 그만큼 많이 필요하다. 외부 API가 느려지면 웹 서버 스레드가 전부 대기 상태로 묶여 고갈되는 이유가 이것이다.

### Non-blocking I/O

```
Event Loop → 요청 등록 → 즉시 반환
Event Loop → 다른 작업 처리
응답 도착 → callback/reactive pipeline 실행
```

적은 스레드로 많은 I/O 대기를 다룬다. 대신 코드 흐름과 디버깅이 복잡해진다. event loop에서 blocking 작업을 실행하면 그 loop에 걸린 요청 전체가 늦어진다.

Non-blocking I/O 자체와 async/reactive 프로그래밍 모델은 별개다. 하나는 I/O 호출 방식이고, 다른 하나는 코드를 짜는 방식이다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD API | Blocking으로 충분 | DB connection pool과 thread pool만 맞게 잡으면 단순하다 |
| 외부 API 호출이 많고 대기가 김 | Non-blocking 검토 | 스레드가 대기하는 비용을 줄인다 |
| CPU 계산이 많음 | Non-blocking 이점 작음 | CPU는 결국 코어 수만큼만 실행된다 |
| 팀이 reactive 운영 경험 없음 | 신중하게 | 디버깅, 트랜잭션, 라이브러리 호환성 비용이 있다 |
| event loop 사용 중 | blocking 호출 금지 | event loop가 막히면 많은 요청이 같이 지연된다 |

스레드 수를 늘리는 것과 I/O 모델을 바꾸는 것은 다른 처방이다. 앞의 것은 단순하지만 스레드마다 메모리와 context switching 비용이 붙는다.

## 자주 깨지는 곳

- **Non-blocking이면 DB나 외부 API도 빨라진다고 믿는다.** 상대 쪽 응답 시간은 그대로다.
- **event loop 안에서 blocking 호출을 한다.** blocking JDBC, 파일 I/O, `Thread.sleep()` 하나가 loop 전체를 멈춘다.
- **WebFlux와 JPA를 섞으면서 JPA가 blocking이라는 걸 잊는다.** 결국 event loop에서 blocking 호출을 하는 것과 같다.
- **blocking 서버에서 스레드 수만 늘린다.** context switching과 메모리 사용량이 같이 커진다.
- **Non-blocking 호출을 제한 없이 늘린다.** timeout, backpressure, connection pool 제한이 없으면 downstream이 감당할 수 있는 양을 넘는다. Non-blocking API를 써도 downstream 처리량 한계는 사라지지 않는다.

## 운영에서 볼 것

- 외부 API를 일부러 느리게 만들고 thread pool, event loop, queue 대기가 어떻게 변하는지 테스트한다.
- 로그에 thread name, 요청 처리 시간, 외부 호출 대기 시간을 남긴다.
- 메트릭은 active threads, event loop latency, pending tasks, connection pool usage를 본다.
- thread dump, async profiler, event loop blocked 경고로 어디서 막히는지 찾는다.

## 한 번에 설명하기

> Blocking은 I/O가 끝날 때까지 스레드가 기다리고, Non-blocking은 바로 반환해서 그 스레드가 다른 일을 하게 합니다. 일반 CRUD API라면 저는 blocking 모델에 pool 크기를 맞추는 것으로 충분하다고 보고, 대기가 긴 외부 호출이 많을 때 Non-blocking을 검토합니다. Non-blocking을 쓸 때는 event loop에서 blocking 호출이 섞이지 않게 하고, timeout과 backpressure로 downstream에 보내는 양을 제한합니다.

## 꼬리 질문

- Blocking I/O에서 외부 API 지연이 스레드 고갈로 이어지는 이유는?
- Non-blocking을 쓰면 항상 처리량이 좋아지나?
- event loop에서 blocking 호출을 하면 어떤 문제가 생기나?
- CPU-bound 작업과 I/O-bound 작업은 스레드 전략이 어떻게 다른가?
- Non-blocking I/O와 async/reactive 프로그래밍은 어떻게 다른가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[socket-io]]
- [[02-practical-backend/performance/performance|performance]]
