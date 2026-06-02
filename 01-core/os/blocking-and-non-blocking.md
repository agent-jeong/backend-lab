---
title: Blocking과 Non-blocking
description: Blocking I/O와 Non-blocking I/O의 차이와 서버 스레드 모델
---

# Blocking과 Non-blocking

## 한 줄 정의

Blocking은 작업을 완료할 수 있을 때까지 호출 스레드가 기다리는 방식이고, Non-blocking은 지금 처리할 수 없는 경우 즉시 반환해 호출자가 다른 작업을 계속할 수 있게 하는 방식이다.

## 실무에서 왜 중요한가

Blocking과 Non-blocking을 구분하지 못하면 다음 문제가 생긴다.

- 외부 API나 DB 응답 대기 때문에 웹 서버 스레드가 고갈되는 이유를 설명하지 못한다.
- WebFlux, Netty, NIO 같은 기술을 쓰면 자동으로 성능이 좋아진다고 오해한다.
- Non-blocking 환경에서 blocking 라이브러리를 호출해 event loop를 막는다.
- 스레드 수를 늘리는 방식과 I/O 모델을 바꾸는 방식의 차이를 판단하지 못한다.

## 동작 방식

### Blocking I/O

```
Thread-1 → 외부 API 호출 → 응답 올 때까지 대기 → 다음 작업
Thread-2 → DB 조회       → 응답 올 때까지 대기 → 다음 작업
```

- 구현이 단순하다.
- 호출 중 스레드가 대기한다.
- 동시 요청이 많고 I/O 대기가 길면 많은 스레드가 필요하다.

### Non-blocking I/O

```
Event Loop → 요청 등록 → 즉시 반환
Event Loop → 다른 작업 처리
응답 도착 → callback/reactive pipeline 실행
```

- 적은 스레드로 많은 I/O 대기를 다룰 수 있다.
- 코드 흐름과 디버깅이 복잡해질 수 있다.
- event loop에서 blocking 작업을 실행하면 전체 처리 지연이 커진다.
- Non-blocking I/O 자체와 async/reactive 프로그래밍 모델은 구분해야 한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반적인 CRUD API | Blocking도 충분 | DB connection pool과 thread pool을 적절히 잡으면 단순하다 |
| 외부 API 호출이 많고 대기가 김 | Non-blocking 검토 | 스레드 대기 비용을 줄일 수 있다 |
| CPU 계산이 많음 | Non-blocking 이점 작음 | CPU는 결국 코어 수만큼 실행된다 |
| 팀이 reactive 운영 경험 없음 | 신중 | 디버깅, 트랜잭션, 라이브러리 호환성 비용이 있다 |
| event loop 사용 중 | blocking 호출 금지 | event loop가 막히면 많은 요청이 같이 지연된다 |

## 자주 나는 실수

- Non-blocking을 쓰면 DB나 외부 API 자체가 빨라진다고 생각한다.
- event loop 안에서 blocking JDBC, 파일 I/O, `Thread.sleep()`을 호출한다.
- blocking 서버에서 스레드 수만 늘려 context switching과 메모리 사용량을 키운다.
- WebFlux와 JPA를 조합하면서 blocking 특성을 고려하지 않는다.
- timeout, backpressure, connection pool 제한 없이 Non-blocking 호출을 늘린다.
- Non-blocking API를 호출하면 downstream 처리량 제한이 사라진다고 오해한다.

## 확인 방법

- 테스트: 외부 API 지연 상황에서 thread pool, event loop, queue 대기를 확인한다.
- 로그: thread name, 요청 처리 시간, 외부 호출 대기 시간을 남긴다.
- 메트릭: active threads, event loop latency, pending tasks, connection pool usage를 본다.
- 프로파일링: thread dump, async profiler, event loop blocked warning을 확인한다.

## 핵심 요약

Blocking은 호출 스레드가 I/O 완료까지 기다리는 방식이고, Non-blocking은 지금 처리할 수 없는 작업에서 즉시 반환해 스레드를 다른 작업에 사용할 수 있게 하는 방식이다. Blocking 모델은 단순하지만 I/O 대기가 많으면 스레드가 많이 필요하다. Non-blocking 모델은 대기 시간이 긴 I/O에는 유리할 수 있지만 코드와 운영 복잡도가 커진다. Non-blocking 환경에서 blocking 호출을 섞으면 event loop가 막혀 더 큰 장애가 날 수 있다. I/O 모델 선택은 성능 유행이 아니라 요청 패턴, 라이브러리, 팀 운영 역량을 보고 판단해야 한다.

## 꼬리 질문

- Blocking I/O에서 외부 API 지연이 스레드 고갈로 이어지는 이유는 무엇인가?
- Non-blocking을 사용하면 항상 처리량이 좋아지는가?
- event loop에서 blocking 호출을 하면 어떤 문제가 생기는가?
- CPU-bound 작업과 I/O-bound 작업은 스레드 전략이 어떻게 다른가?
- Non-blocking I/O와 async/reactive 프로그래밍은 어떤 차이가 있는가?

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[socket-io]]
- [[02-practical-backend/performance/performance|performance]]
