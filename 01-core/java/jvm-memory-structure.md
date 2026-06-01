---
title: JVM Memory Structure
description: JVM 메모리 구조와 실무 트러블슈팅 연결
---

# JVM Memory Structure

## 한 줄 정의

JVM은 Java 코드를 바이트코드로 컴파일한 뒤, class loading, 메모리 할당, 실행, GC를 거쳐 프로그램을 실행하는 가상 머신이다.

## 실무에서 왜 중요한가

JVM 구조를 모르면 다음 상황에서 원인을 파악할 수 없다.

- `OutOfMemoryError: Java heap space` 발생 시 heap 크기와 객체 생존 패턴을 분석해야 한다.
- `StackOverflowError` 발생 시 재귀 호출 깊이와 스택 크기의 관계를 알아야 한다.
- `OutOfMemoryError: Metaspace` 발생 시 class loading 구조를 이해해야 한다.
- 메모리 누수가 의심될 때 heap dump를 분석할 수 있어야 한다.
- JVM 옵션(`-Xmx`, `-Xms`, `-XX:MetaspaceSize`)을 설정할 때 각 영역의 의미를 알아야 한다.

## Runtime Data Area 구조

JVM이 프로그램을 실행하면서 사용하는 메모리 영역이다.

```
┌───────────────────────────────────────┐
│         Method Area (Metaspace)       │  ← 클래스 정보, static 변수
├───────────────────────────────────────┤
│              Heap                     │  ← 객체 인스턴스, 배열
│  ┌─────────────┬─────────────────┐    │
│  │   Young Gen  │    Old Gen      │    │
│  │ Eden│S0│S1  │                  │    │
│  └─────────────┴─────────────────┘    │
├───────────────────────────────────────┤
│   Stack (스레드마다 독립)              │  ← 메서드 호출 프레임, 지역 변수
├───────────────────────────────────────┤
│   PC Register (스레드마다 독립)        │  ← 현재 실행 중인 명령어 주소
├───────────────────────────────────────┤
│   Native Method Stack                 │  ← JNI 네이티브 메서드 호출
└───────────────────────────────────────┘
```

## 각 영역과 실무 연결

### Heap

모든 객체가 생성되는 영역이다. GC의 대상이 된다.

| 구분 | 설명 | 실무 관련 |
|---|---|---|
| Young Generation | 새로 생성된 객체 | Minor GC 대상, 대부분 여기서 사라짐 |
| Old Generation | Young에서 살아남은 객체 | Major GC/Full GC 대상, 크기가 크면 GC 시간 증가 |

```bash
# Heap 크기 설정
java -Xms512m -Xmx2g -jar app.jar

# -Xms: 초기 heap 크기
# -Xmx: 최대 heap 크기
```

`-Xms`와 `-Xmx`를 같은 값으로 설정하면 heap 확장/축소에 따른 오버헤드를 줄일 수 있다. 컨테이너 환경에서는 이렇게 설정하는 경우가 많다.

### Stack

스레드마다 독립적으로 존재하며, 메서드 호출 시 프레임이 push되고 반환 시 pop된다.

| 상황 | 증상 |
|---|---|
| 재귀 호출이 너무 깊다 | `StackOverflowError` |
| 스레드 수가 너무 많다 | 메모리 부족 (스레드당 stack 메모리 소비) |

```bash
# 스레드 스택 크기 설정
java -Xss512k -jar app.jar
```

### Method Area (Metaspace)

클래스 메타데이터, static 변수가 저장되는 영역이다.

Java 8부터 PermGen이 Metaspace로 대체되었다. Metaspace는 Native Memory를 사용하므로 heap과 별도로 관리된다.

| 상황 | 증상 |
|---|---|
| 동적 클래스 생성이 많다 (리플렉션, 프록시) | `OutOfMemoryError: Metaspace` |
| 클래스 로더가 해제되지 않는다 | Metaspace 누수 |

```bash
# Metaspace 크기 설정
java -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m -jar app.jar
```

## Class Loading 과정

```
.java → javac → .class → ClassLoader → JVM 메모리
```

1. **Loading**: .class 파일을 읽어서 Method Area에 클래스 정보를 저장한다.
2. **Linking**: 검증(Verify) → 준비(Prepare, static 변수 기본값) → 해석(Resolve, 심볼릭 참조를 실제 참조로)
3. **Initialization**: static 초기화 블록과 static 변수에 실제 값 할당

ClassLoader 계층 구조:

| ClassLoader | 역할 |
|---|---|
| Bootstrap | `java.lang` 등 JDK 핵심 클래스 로딩 |
| Platform (Extension) | JDK 확장 모듈 로딩 |
| Application | classpath의 애플리케이션 클래스 로딩 |

## JIT Compiler

JVM은 바이트코드를 인터프리터로 실행하다가, 자주 호출되는 코드(hot spot)를 네이티브 코드로 컴파일한다.

| 관점 | 실무 영향 |
|---|---|
| 워밍업 | 애플리케이션 시작 직후에는 JIT 최적화가 안 되어 있어 느릴 수 있다 |
| 최적화 해제 | 런타임 조건이 바뀌면 최적화가 해제(deoptimization)될 수 있다 |
| 컨테이너 환경 | 짧은 생명주기의 컨테이너에서는 JIT 효과를 못 볼 수 있다 |

## 실무 트러블슈팅 도구

| 도구 | 용도 |
|---|---|
| `jps` | 실행 중인 JVM 프로세스 목록 |
| `jstat -gc <pid>` | GC 통계 실시간 모니터링 |
| `jmap -dump:format=b,file=heap.hprof <pid>` | heap dump 생성 |
| `jstack <pid>` | thread dump 생성 |
| Eclipse MAT, VisualVM | heap dump 분석 |
| Arthas | 운영 중인 JVM에 붙어서 실시간 진단 |

## 자주 나는 실수

- `-Xmx`를 컨테이너 메모리 한도와 같게 설정해서 OOM Killer에 의해 프로세스가 죽는다.
- heap dump 분석 없이 `-Xmx`만 올려서 메모리 누수를 임시로 가린다.
- 스레드 수를 과도하게 늘려서 스택 메모리 전체 합이 시스템 메모리를 넘긴다.
- Metaspace 크기를 설정하지 않아서 동적 프록시 생성 시 무한 증가한다.

## 핵심 요약

JVM의 Runtime Data Area는 크게 Heap, Stack, Method Area(Metaspace)로 나뉩니다.
Heap은 모든 객체가 생성되는 영역으로 GC의 대상이 되고, Stack은 스레드마다 독립적으로 메서드 호출 프레임을 관리합니다.
Metaspace는 Java 8부터 PermGen을 대체한 영역으로 클래스 메타데이터를 저장합니다.

실무에서는 `-Xmx`로 Heap 크기를, `-Xss`로 스레드 스택 크기를, `-XX:MaxMetaspaceSize`로 Metaspace 크기를 설정합니다.
컨테이너 환경에서는 JVM 메모리 총합이 컨테이너 한도를 넘지 않도록 주의해야 하고, 메모리 문제 발생 시 heap dump와 `jstat` 같은 도구로 분석합니다.

## 꼬리 질문

> [!question]- Heap과 Stack에 각각 어떤 데이터가 저장되는가?
> Heap에는 객체 인스턴스와 배열이, Stack에는 메서드 호출 프레임과 지역 변수, 매개변수가 저장됩니다. Stack은 스레드마다 독립적입니다.

> [!question]- `OutOfMemoryError`의 종류와 각각의 원인은?
> `Java heap space`는 heap 부족, `Metaspace`는 클래스 메타데이터 공간 부족, `unable to create new native thread`는 OS 스레드 한도 초과입니다.

> [!question]- PermGen이 Metaspace로 바뀐 이유는?
> PermGen은 고정 크기라 `OutOfMemoryError`가 자주 발생했습니다. Metaspace는 Native Memory를 사용해 필요에 따라 확장되므로 관리가 유연합니다.

> [!question]- 컨테이너 환경에서 JVM 메모리를 어떻게 설정하는가?
> `-Xmx`를 컨테이너 메모리 한도의 70~80%로 설정합니다. heap 외에 Metaspace, Stack, Direct Buffer 등이 추가로 필요하기 때문입니다.

> [!question]- JIT Compiler의 워밍업이 실무에서 문제가 되는 경우는?
> 배포 직후 트래픽이 몰리면 JIT 최적화가 안 된 상태에서 응답이 느려집니다. 짧은 생명주기의 컨테이너에서는 JIT 효과를 못 볼 수도 있습니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[gc-and-tuning]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]