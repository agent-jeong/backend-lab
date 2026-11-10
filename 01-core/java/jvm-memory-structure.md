---
title: JVM 메모리 구조와 각 영역의 역할
description: JVM 메모리 구조와 실무 트러블슈팅 연결
---

# JVM 메모리 구조와 각 영역의 역할

JVM은 `javac`가 만든 바이트코드를 class loading, 메모리 할당, 실행, GC를 거쳐 실행하는 가상 머신이다. 메모리 영역마다 터지는 에러가 달라서, 어느 영역이 무엇을 담는지 알아야 에러 메시지만 보고 방향을 잡는다.

`OutOfMemoryError: Java heap space`면 heap 크기와 객체 생존 패턴을, `StackOverflowError`면 재귀 깊이와 스택 크기를, `OutOfMemoryError: Metaspace`면 class loading 구조를 봐야 한다. 누수가 의심되면 heap dump를 읽어야 하고, `-Xmx`, `-Xms`, `-XX:MetaspaceSize` 같은 옵션도 각 영역의 의미를 알아야 제대로 잡는다.

## Runtime Data Area

JVM이 프로그램을 실행하며 쓰는 메모리 영역이다.

```
┌───────────────────────────────────────┐
│         Method Area (Metaspace)       │  ← 클래스 메타데이터, 상수 풀
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

## Heap

모든 객체가 만들어지는 곳이고, GC 대상이다.

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

`-Xms`와 `-Xmx`를 같은 값으로 두면 heap이 늘고 줄며 생기는 오버헤드가 없다. 컨테이너 환경에서 흔히 이렇게 둔다.

## Stack

스레드마다 따로 있다. 메서드를 호출하면 프레임이 push되고, 반환하면 pop된다.

| 상황 | 증상 |
|---|---|
| 재귀 호출이 너무 깊다 | `StackOverflowError` |
| 스레드 수가 너무 많다 | 메모리 부족 (스레드당 stack 메모리 소비) |

```bash
# 스레드 스택 크기 설정
java -Xss512k -jar app.jar
```

## Method Area (Metaspace)

클래스 메타데이터와 런타임 상수 풀이 들어간다. Java 8+에서 static 변수의 참조는 Heap의 `java.lang.Class` 객체에 저장된다.

Java 8부터 PermGen이 Metaspace로 바뀌었다. Metaspace는 Native Memory를 쓰므로 heap과 따로 관리된다.

| 상황 | 증상 |
|---|---|
| 동적 클래스 생성이 많다 (리플렉션, 프록시) | `OutOfMemoryError: Metaspace` |
| 클래스 로더가 해제되지 않는다 | Metaspace 누수 |

```bash
# Metaspace 크기 설정
java -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=256m -jar app.jar
```

## Class Loading

```
.java → javac → .class → ClassLoader → JVM 메모리
```

1. **Loading**: .class 파일을 읽어 Method Area에 클래스 정보를 저장한다.
2. **Linking**: 검증(Verify) → 준비(Prepare, static 변수 기본값) → 해석(Resolve, 심볼릭 참조를 실제 참조로). Resolution은 필요한 시점까지 미뤄질 수 있다.
3. **Initialization**: static 초기화 블록을 실행하고 static 변수에 실제 값을 넣는다.

| ClassLoader | 역할 |
|---|---|
| Bootstrap | `java.lang` 등 JDK 핵심 클래스 로딩 |
| Platform (Extension) | JDK 확장 모듈 로딩 |
| Application | classpath의 애플리케이션 클래스 로딩 |

## JIT Compiler

JVM은 바이트코드를 인터프리터로 실행하다가, 자주 호출되는 코드(hot spot)를 네이티브 코드로 컴파일한다.

| 관점 | 실무 영향 |
|---|---|
| 워밍업 | 시작 직후에는 JIT 최적화 전이라 느릴 수 있다 |
| 최적화 해제 | 런타임 조건이 바뀌면 최적화가 풀린다(deoptimization) |
| 컨테이너 환경 | 생명주기가 짧은 컨테이너는 JIT 효과를 못 볼 수 있다 |

## 문제를 볼 때 쓰는 도구

| 도구 | 용도 |
|---|---|
| `jps` | 실행 중인 JVM 프로세스 목록 |
| `jstat -gc <pid>` | GC 통계 실시간 모니터링 |
| `jmap -dump:format=b,file=heap.hprof <pid>` | heap dump 생성 |
| `jstack <pid>` | thread dump 생성 |
| Eclipse MAT, VisualVM | heap dump 분석 |
| Arthas | 운영 중인 JVM에 붙어서 실시간 진단 |

## 자주 깨지는 곳

- **`-Xmx`를 컨테이너 메모리 한도와 같게 잡는다.** heap 밖 메모리까지 더해져 OOM Killer가 프로세스를 죽인다.
- **heap dump 없이 `-Xmx`만 올린다.** 누수는 그대로고 터지는 시점만 늦어진다.
- **스레드 수를 과하게 늘린다.** 스레드별 스택 메모리 합이 시스템 메모리를 넘긴다.
- **Metaspace 상한을 두지 않는다.** 동적 프록시가 계속 생기면 끝없이 늘어난다.

## 면접에서 말하기

> JVM 메모리는 크게 Heap, Stack, Method Area(Metaspace)로 나뉩니다. Heap은 객체가 생기는 GC 대상 영역이고, Stack은 스레드마다 메서드 호출 프레임을 관리하며, Metaspace는 Java 8부터 PermGen을 대체해 클래스 메타데이터를 Native Memory에 둡니다. 각각 `-Xmx`, `-Xss`, `-XX:MaxMetaspaceSize`로 크기를 정하는데, 컨테이너에서는 이 합이 한도를 넘지 않게 잡고, 문제가 생기면 heap dump와 jstat으로 먼저 확인합니다.

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

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Heap과 Stack의 차이로 맞는 설명은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="객체는 주로 Heap에 저장되고, 메서드 호출 프레임과 지역 변수 참조는 Stack에 저장된다." aria-pressed="false">A. 객체는 주로 Heap, 호출 프레임은 Stack에 저장된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="클래스 메타데이터는 Metaspace와 관련이 깊다." aria-pressed="false">B. 클래스 메타데이터는 항상 Stack에 저장된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 데이터가 Heap에만 저장되는 것은 아니다." aria-pressed="false">C. 지역 변수와 호출 프레임도 모두 Heap에 저장된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>컨테이너에서 -Xmx를 컨테이너 메모리 한도와 같게 잡으면 안전하다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Heap 외에도 Metaspace, Stack, Direct Buffer 등이 있어 컨테이너 OOM Kill 위험이 커진다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="컨테이너 한도보다 낮게 잡고 heap 외 메모리 여유를 둬야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JIT 워밍업이 실무에서 문제가 되는 상황은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="배포 직후나 짧게 실행되는 배치처럼 코드가 충분히 최적화되기 전 성능이 낮게 보일 수 있다." aria-pressed="false">A. 배포 직후 지연 시간이 일시적으로 높아지는 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JIT은 컴파일 에러를 해결하는 기능이 아니다." aria-pressed="false">B. 컴파일 에러가 런타임에 자동 수정되는 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="GC 로그 포맷과 직접적인 관련은 없다." aria-pressed="false">C. GC 로그가 JSON으로 바뀌는 경우</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[gc-and-tuning]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]