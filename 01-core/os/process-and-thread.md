---
title: Process And Thread
description: 프로세스와 스레드의 차이, 멀티스레드 모델과 실무 영향
---

# Process And Thread

## 한 줄 정의

프로세스는 실행 중인 프로그램의 독립적인 메모리 단위이고, 스레드는 프로세스 내에서 실행 흐름을 나누는 경량 단위다.

## 실무에서 왜 중요한가

프로세스와 스레드를 이해하지 못하면 다음 문제가 생긴다.

- 서버의 스레드 수를 근거 없이 설정해서 CPU 사용률이 비정상적이다.
- 멀티스레드에서 공유 자원 접근 시 동시성 문제가 발생한다.
- 스레드 덤프를 떠도 내용을 해석하지 못한다.
- 스레드 풀 고갈의 원인을 파악하지 못한다.

## 프로세스 (Process)

프로세스는 OS로부터 독립된 메모리 공간을 할당받아 실행되는 단위다.

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

- 프로세스 간에는 메모리를 공유하지 않는다.
- 프로세스 간 통신(IPC)은 파이프, 소켓, 공유 메모리 등을 사용한다.
- 한 프로세스가 죽어도 다른 프로세스에 영향이 없다.

## 스레드 (Thread)

스레드는 프로세스 내에서 Code, Data, Heap을 공유하면서 각자의 Stack만 독립적으로 가진다.

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

### 프로세스 vs 스레드

| 구분 | 프로세스 | 스레드 |
|---|---|---|
| 메모리 | 독립 | 코드/데이터/힙 공유 |
| 생성 비용 | 높음 | 낮음 |
| 통신 | IPC 필요 | 공유 메모리로 직접 |
| 안전성 | 한 프로세스 죽어도 다른 프로세스 안전 | 한 스레드 오류가 프로세스 전체에 영향 |
| 컨텍스트 스위칭 | 비용 높음 | 비용 낮음 |

## Java에서의 스레드

### 스레드 풀 (Thread Pool)

스레드를 매번 생성/소멸하면 비용이 크다. 스레드 풀은 미리 스레드를 만들어두고 작업을 큐에 넣어 재사용한다.

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

### 스레드 풀 사이즈 결정

- **CPU 바운드 작업**: 코어 수 + 1 (계산 위주)
- **I/O 바운드 작업**: 코어 수 × (1 + 대기시간/처리시간) (DB 조회, API 호출 위주)

대부분의 웹 서버는 I/O 바운드이므로 코어 수보다 많은 스레드를 설정한다. Tomcat 기본값 200은 대부분의 상황에서 적절한 시작점이다.

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

| 스레드 상태 | 의미 | 주의 사항 |
|---|---|---|
| RUNNABLE | 실행 중 또는 실행 대기 | 정상 |
| WAITING | 다른 스레드의 통지 대기 | 많으면 병목 의심 |
| TIMED_WAITING | 시간 제한 대기 | sleep, timeout 대기 |
| BLOCKED | 모니터 락 획득 대기 | 많으면 락 경합 확인 |

## 멀티프로세스 vs 멀티스레드

| 구분 | 멀티프로세스 | 멀티스레드 |
|---|---|---|
| 예시 | Nginx worker, Chrome 탭 | Tomcat, Spring MVC |
| 장점 | 프로세스 격리 (안전) | 메모리 공유 (효율) |
| 단점 | 메모리 사용량 높음, IPC 비용 | 동시성 문제 (동기화 필요) |

Java 웹 서버(Tomcat)는 하나의 프로세스 안에서 멀티스레드로 요청을 처리한다.

## 자주 나는 실수

- 스레드 풀 사이즈를 CPU 코어 수만 고려하고 I/O 대기를 무시한다.
- 스레드 안전하지 않은 객체를 멀티스레드에서 공유한다 (SimpleDateFormat 등).
- 스레드 풀을 사용하지 않고 매번 `new Thread()`로 생성한다.
- 스레드 덤프에서 BLOCKED 스레드가 많은데 원인을 분석하지 않는다.
- 스레드 로컬을 사용하고 스레드 풀 반환 시 정리하지 않는다.

## 핵심 요약

프로세스는 독립된 메모리 공간을 가지고, 스레드는 프로세스 내에서 힙을 공유하며 스택만 독립적입니다.
Java 웹 서버는 멀티스레드 모델이며, 스레드 풀로 스레드를 재사용합니다.

스레드 풀 사이즈는 CPU 바운드/I/O 바운드 특성에 따라 결정합니다.
스레드 덤프로 BLOCKED, WAITING 상태의 스레드를 분석하면 병목 원인을 찾을 수 있습니다.

## 꼬리 질문

> [!question]- 스레드가 많으면 항상 성능이 좋아지는가?
> 아닙니다. 스레드가 너무 많으면 컨텍스트 스위칭 비용이 증가하고, 메모리 사용량이 늘어납니다. CPU 코어 수 이상의 스레드가 동시에 RUNNABLE이면 컨텍스트 스위칭만 반복합니다.

> [!question]- Java에서 스레드 안전을 보장하는 방법은?
> `synchronized`, `ReentrantLock`, `AtomicInteger` 같은 동기화 도구를 사용하거나, 불변 객체나 ThreadLocal로 공유 자원 자체를 피하는 방법이 있습니다.

> [!question]- Virtual Thread(Java 21)는 기존 스레드와 무엇이 다른가?
> Virtual Thread는 OS 스레드에 1:1로 매핑되지 않고, JVM이 관리하는 경량 스레드입니다. I/O 대기 시 OS 스레드를 반환하므로, 수만 개의 동시 요청을 적은 OS 스레드로 처리할 수 있습니다.

## 관련 문서

- [[01-core/os/os|os]]
- [[context-switching]]
- [[cpu-scheduling]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]