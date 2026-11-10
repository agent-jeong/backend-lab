---
title: "프로세스와 스레드의 차이"
description: 프로세스와 스레드의 차이, 멀티스레드 모델과 실무 영향
tags: [concept, os]
---

# 프로세스와 스레드의 차이

프로세스는 실행 중인 프로그램으로, 자기만의 메모리 공간을 가진다. 스레드는 한 프로세스 안에서 실행 흐름을 나눈 가벼운 단위다.

Java 웹 서버는 한 프로세스 안의 여러 스레드로 요청을 처리한다. 그래서 스레드 풀 크기, 공유 자원의 동시성 문제, 스레드 덤프 해석이 모두 이 차이에서 출발한다.

## 프로세스 (Process)

프로세스는 OS에게서 독립된 메모리 공간을 받아 실행되는 단위다.

```
┌─────────────────────────┐
│        Process A        │
│  ┌─────┬──────┬──────┐  │
│  │Code │ Data │ Heap │  │
│  └─────┴──────┴──────┘  │
│  ┌──────────────────┐   │
│  │   Stack (Main)   │   │
│  └──────────────────┘   │
└─────────────────────────┘
         ↕ IPC (Inter-Process Communication)
┌─────────────────────────┐
│        Process B        │  ← 별도 메모리 공간
└─────────────────────────┘
```

프로세스끼리는 메모리를 공유하지 않는다. 그래서 통신(IPC)에는 파이프, 소켓, 공유 메모리 등을 쓰고, 한 프로세스가 죽어도 다른 프로세스는 영향을 받지 않는다.

## 스레드 (Thread)

스레드는 프로세스 안에서 Code, Data, Heap을 공유하고, Stack만 각자 가진다.

```
┌─────────────────────────────────┐
│            Process              │
│  ┌─────┬──────┬──────────────┐  │
│  │Code │ Data │     Heap     │  │  ← 스레드 간 공유
│  └─────┴──────┴──────────────┘  │
│  ┌────────┐ ┌────────┐ ┌────────┐
│  │Stack-1 │ │Stack-2 │ │Stack-3 │  ← 스레드별 독립
│  │Thread-1│ │Thread-2│ │Thread-3│
│  └────────┘ └────────┘ └────────┘
└─────────────────────────────────┘
```

### 프로세스와 스레드 비교

| 구분 | 프로세스 | 스레드 |
|---|---|---|
| 메모리 | 독립 | 코드/데이터/힙 공유 |
| 생성 비용 | 높음 | 낮음 |
| 통신 | IPC 필요 | 공유 메모리로 직접 |
| 안전성 | 한 프로세스 죽어도 다른 프로세스 안전 | 한 스레드 오류가 프로세스 전체에 영향 |
| 컨텍스트 스위칭 | 비용 높음 | 비용 낮음 |

## Java에서의 스레드

### 스레드 풀 (Thread Pool)

스레드를 매번 만들고 없애면 비용이 크다. 스레드 풀은 스레드를 미리 만들어 두고, 작업을 큐에 넣어 재사용한다.

```java
// Tomcat 스레드 풀 설정
server:
  tomcat:
    threads:
      max: 200        # 최대 스레드 수
      min-spare: 10   # 최소 유지 스레드
    max-connections: 8192
    accept-count: 100  # 대기 큐 크기
```

```
요청 → Accept Queue → Thread Pool에서 스레드 할당 → 처리 → 반환

Thread Pool (max=200):
[Thread-1: 처리 중] [Thread-2: 처리 중] [Thread-3: 유휴] ... [Thread-200]

모든 스레드가 처리 중이면 → Accept Queue에서 대기
Accept Queue도 가득 차면 → 요청 거부 (Connection Refused)
```

### 스레드 풀 크기 정하기

- **CPU 바운드 작업** (계산 위주): 코어 수 + 1
- **I/O 바운드 작업** (DB 조회, API 호출 위주): 코어 수 × (1 + 대기시간/처리시간)

웹 서버는 대부분 I/O 바운드라 코어 수보다 많은 스레드를 둔다. Tomcat 기본값 200은 대부분의 상황에서 무난한 출발점이다.

### 스레드 덤프

```bash
# JVM 스레드 덤프 출력
jstack <PID>
kill -3 <PID>
```

```
"http-nio-8080-exec-5" #35 daemon prio=5 os_prio=0 tid=0x00007f
   java.lang.Thread.State: WAITING (parking)
    at sun.misc.Unsafe.park(Native Method)
    at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:162)
```

| 스레드 상태 | 의미 | 해석 |
|---|---|---|
| RUNNABLE | 실행 중 또는 실행 대기 | 정상 |
| WAITING | 다른 스레드의 통지 대기 | 많으면 병목 의심 |
| TIMED_WAITING | 시간 제한 대기 | sleep, timeout 대기 |
| BLOCKED | 모니터 락 획득 대기 | 많으면 락 경합 확인 |

## 멀티프로세스와 멀티스레드

| 구분 | 멀티프로세스 | 멀티스레드 |
|---|---|---|
| 예시 | Nginx worker, Chrome 탭 | Tomcat, Spring MVC |
| 장점 | 프로세스 격리 (안전) | 메모리 공유 (효율) |
| 단점 | 메모리 사용량 높음, IPC 비용 | 동시성 문제 (동기화 필요) |

Java 웹 서버(Tomcat)는 하나의 프로세스 안에서 멀티스레드로 요청을 처리한다. 메모리를 공유해 효율적인 대신 동기화를 직접 챙겨야 한다.

## 자주 깨지는 곳

- **스레드 풀 크기를 코어 수만 보고 정한다.** I/O 대기가 긴 서버에서는 스레드가 모자라 요청이 큐에 쌓인다.
- **스레드 안전하지 않은 객체를 공유한다.** `SimpleDateFormat` 같은 객체를 여러 스레드가 쓰면 값이 섞인다.
- **스레드 풀 없이 매번 `new Thread()`로 만든다.** 생성 비용이 쌓이고 스레드 수에 상한이 없다.
- **스레드 덤프에 BLOCKED가 많은데 그냥 넘어간다.** 락 경합이 병목인 경우가 많다.
- **ThreadLocal을 쓰고 풀에 반환할 때 정리하지 않는다.** 다음 요청이 이전 요청의 값을 본다.

## 면접에서 말하기

> 프로세스는 독립된 메모리 공간을 갖고, 스레드는 같은 프로세스 안에서 힙을 공유하며 스택만 따로 가집니다. Java 웹 서버는 멀티스레드 모델이라 스레드 풀로 스레드를 재사용하는데, 저는 풀 크기를 작업이 CPU 바운드인지 I/O 바운드인지 보고 정합니다. 병목이 의심되면 스레드 덤프에서 BLOCKED, WAITING 스레드가 어디서 멈췄는지 확인합니다.

## 꼬리 질문

> [!question]- 스레드가 많으면 항상 성능이 좋아지는가?
> 아닙니다. 스레드가 너무 많으면 컨텍스트 스위칭 비용이 증가하고, 메모리 사용량이 늘어납니다. CPU 코어 수 이상의 스레드가 동시에 RUNNABLE이면 컨텍스트 스위칭만 반복합니다.

> [!question]- Java에서 스레드 안전을 보장하는 방법은?
> `synchronized`, `ReentrantLock`, `AtomicInteger` 같은 동기화 도구를 사용하거나, 불변 객체나 ThreadLocal로 공유 자원 자체를 피하는 방법이 있습니다.

> [!question]- Virtual Thread(Java 21)는 기존 스레드와 무엇이 다른가?
> Virtual Thread는 OS 스레드에 1:1로 매핑되지 않고, JVM이 관리하는 경량 스레드입니다. I/O 대기 시 OS 스레드를 반환하므로, 수만 개의 동시 요청을 적은 OS 스레드로 처리할 수 있습니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [pthreads(7)](https://man7.org/linux/man-pages/man7/pthreads.7.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)

## 관련 문서

- [[01-core/os/os|os]]
- [[context-switching]]
- [[cpu-scheduling]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]