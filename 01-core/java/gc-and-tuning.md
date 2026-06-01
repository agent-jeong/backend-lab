---
title: GC And Tuning
description: Java GC 동작 원리와 실무 튜닝 관점
---

# GC And Tuning

## 한 줄 정의

GC(Garbage Collection)는 JVM이 더 이상 참조되지 않는 객체의 메모리를 자동으로 회수하는 메커니즘이다.

## 실무에서 왜 중요한가

대부분의 상황에서 GC는 기본 설정으로 충분하다. 하지만 다음 상황에서는 GC 원리를 알아야 문제를 분석할 수 있다.

- 응답 지연이 간헐적으로 튀는데 원인이 GC pause인 경우
- Full GC가 반복되면서 서비스가 수 초간 멈추는 경우
- 메모리 사용량이 계속 올라가서 GC가 점점 자주 발생하는 경우
- 컨테이너 환경에서 메모리 한도를 넘겨 프로세스가 kill되는 경우
- GC 로그를 보고 원인을 판단해야 하는 경우

## GC 기본 동작

### 세대별 구조

JVM Heap은 Young Generation과 Old Generation으로 나뉜다.

```
Young Generation              Old Generation
┌──────┬────┬────┐     ┌──────────────────┐
│ Eden │ S0 │ S1 │     │                  │
│      │    │    │     │                  │
└──────┴────┴────┘     └──────────────────┘
```

| 단계 | 동작 |
|---|---|
| 객체 생성 | Eden에 할당 |
| Minor GC | Eden + 사용 중인 Survivor에서 살아남은 객체를 다른 Survivor로 복사 |
| 나이 증가 | GC를 살아남을 때마다 age 증가 |
| Promotion | age가 임계값을 넘으면 Old Generation으로 이동 |
| Major GC / Full GC | Old Generation이 가득 차면 발생, 시간이 오래 걸림 |

### Stop-the-World

GC가 실행되는 동안 애플리케이션 스레드가 일시 정지되는 현상이다.

Minor GC의 STW는 짧지만, Full GC의 STW는 수 초에 달할 수 있다. 실무에서 "GC 튜닝"이라 하면 대부분 이 STW 시간을 줄이는 것이 목표다.

## GC 알고리즘 비교

| GC | 특성 | 적합한 상황 |
|---|---|---|
| Serial GC | 싱글 스레드 GC | 작은 heap, 테스트 환경 |
| Parallel GC | 멀티 스레드 GC, 처리량 우선 | 배치, 데이터 처리 |
| G1 GC | region 기반, STW 목표 시간 설정 가능 | 일반 웹 서비스 (Java 9+ 기본) |
| ZGC | 매우 짧은 STW (< 1ms 목표) | 대용량 heap, 지연 민감 서비스 |
| Shenandoah | ZGC와 유사, OpenJDK 제공 | ZGC 대안 |

## G1 GC 실무 포인트

Java 9부터 기본 GC이며, 대부분의 웹 서비스에서 적절한 선택이다.

### 동작 방식

Heap을 고정 크기의 region으로 나누고, 가비지가 많은 region부터 우선 수집(Garbage First)한다.

```
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ E │ E │ S │   │ O │ O │ O │ H │
└───┴───┴───┴───┴───┴───┴───┴───┘
E: Eden  S: Survivor  O: Old  H: Humongous  (빈칸: Free)
```

### 주요 옵션

```bash
java \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \       # STW 목표 시간 (기본 200ms)
  -XX:G1HeapRegionSize=4m \        # region 크기
  -XX:InitiatingHeapOccupancyPercent=45 \  # Old 사용률이 이 값을 넘으면 Mixed GC 시작
  -jar app.jar
```

`MaxGCPauseMillis`는 "보장"이 아니라 "목표"다. 너무 낮게 설정하면 GC가 자주 발생하고, 너무 높으면 한 번에 긴 STW가 발생한다.

## ZGC - 지연 민감 서비스

Java 21에서 generational ZGC가 도입되어 실무에서도 사용할 수 있는 수준이 되었다.

```bash
java -XX:+UseZGC -XX:+ZGenerational -jar app.jar
```

| 특성 | 값 |
|---|---|
| STW 시간 | < 1ms 목표 |
| Heap 크기 | 수 TB까지 지원 |
| 실무 적합성 | 지연 시간이 매우 중요한 서비스 (결제, 실시간 처리) |

## GC 로그 분석

```bash
# GC 로그 활성화
java \
  -Xlog:gc*:file=gc.log:time,uptime,level,tags \
  -jar app.jar
```

GC 로그에서 확인할 것:

| 항목 | 의미 |
|---|---|
| GC 빈도 | 너무 자주 발생하면 객체 생성이 과도하거나 heap이 작다 |
| Pause 시간 | STW 시간이 응답 지연의 원인인지 확인 |
| Full GC 발생 여부 | Full GC가 반복되면 메모리 누수 의심 |
| Heap 사용량 추이 | GC 후에도 줄어들지 않으면 누수 가능성 |

## 실무 튜닝 판단 기준

| 상황 | 조치 |
|---|---|
| Full GC가 반복된다 | 메모리 누수 확인, heap dump 분석 |
| Minor GC가 너무 자주 발생한다 | Young Generation 크기 확인, 과도한 객체 생성 점검 |
| STW가 길다 | G1의 `MaxGCPauseMillis` 조정, ZGC 검토 |
| GC 후에도 메모리가 줄지 않는다 | 메모리 누수 의심, heap dump 분석 |
| 컨테이너에서 OOM Kill | `-Xmx`를 컨테이너 한도의 70~80% 이하로 설정 |

## 자주 나는 실수

- GC 로그를 남기지 않아서 장애 시 분석이 불가능하다.
- Full GC가 반복되는데 `-Xmx`만 올려서 문제를 미룬다.
- GC 튜닝 전에 애플리케이션 코드의 과도한 객체 생성을 먼저 줄이지 않는다.
- `MaxGCPauseMillis`를 너무 낮게 설정해서 GC가 과도하게 자주 발생한다.
- 운영 환경에서 GC 알고리즘을 변경할 때 충분한 테스트 없이 적용한다.

## 핵심 요약

GC는 JVM이 참조되지 않는 객체의 메모리를 자동으로 회수하는 메커니즘입니다.
Heap은 Young과 Old Generation으로 나뉘고, 대부분의 객체는 Young에서 Minor GC로 빠르게 회수됩니다.
Old Generation이 가득 차면 Full GC가 발생하는데, 이때 Stop-the-World로 인해 응답 지연이 생길 수 있습니다.

Java 9부터 기본인 G1 GC는 Heap을 region으로 나누어 가비지가 많은 영역부터 수집하며, STW 목표 시간을 설정할 수 있습니다.

실무에서 GC 튜닝은 대부분 STW 시간을 줄이는 것이 목표이고, 튜닝 전에 애플리케이션 코드의 과도한 객체 생성을 줄이는 것이 먼저입니다.
운영에서는 GC 로그를 반드시 남겨야 장애 시 원인 분석이 가능합니다.

## 꼬리 질문

> [!question]- Minor GC와 Full GC의 차이는?
> Minor GC는 Young Generation만 수집하며 빠릅니다. Full GC는 전체 Heap을 수집하며 STW 시간이 길어 서비스 응답 지연의 주요 원인이 됩니다.

> [!question]- Stop-the-World가 서비스에 미치는 영향은?
> GC 실행 중 모든 애플리케이션 스레드가 멈춥니다. Full GC의 STW가 수 초에 달하면 요청 타임아웃이나 헬스체크 실패가 발생할 수 있습니다.

> [!question]- G1 GC와 ZGC의 차이는?
> G1은 STW 목표 시간을 설정할 수 있는 범용 GC입니다. ZGC는 STW를 1ms 이하로 유지하며 대용량 heap과 지연 민감 서비스에 적합합니다.

> [!question]- GC 튜닝 전에 먼저 해야 할 것은?
> 애플리케이션 코드에서 과도한 객체 생성을 줄이는 것이 먼저입니다. 불필요한 String 연결, 반복문 안의 객체 생성 등을 점검합니다.

> [!question]- GC 로그에서 어떤 항목을 확인하는가?
> GC 빈도, STW pause 시간, Full GC 발생 여부, GC 후 heap 사용량 추이를 확인합니다. GC 후에도 메모리가 줄지 않으면 누수를 의심합니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]