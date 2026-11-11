---
title: JVM 메모리 구조와 각 영역의 역할
description: JVM 메모리 영역마다 무엇을 담고, 어떤 에러가 나면 어디를 봐야 하는지
tags: [concept, java]
---

# JVM 메모리 구조와 각 영역의 역할

JVM은 `javac`가 만든 바이트코드를 읽어 들여(class loading), 메모리를 나눠 주고, 실행하고, 다 쓴 객체를 치우는(GC) 가상 머신이다. 메모리 영역마다 터지는 에러가 다르다. 그래서 어느 영역에 무엇이 담기는지 알면 에러 메시지만 보고도 어디부터 볼지 정할 수 있다.

`OutOfMemoryError: Java heap space`가 나면 heap 크기와 객체가 얼마나 오래 살아남는지를 본다. `StackOverflowError`면 재귀 깊이와 스택 크기를, `OutOfMemoryError: Metaspace`면 클래스가 어떻게 로딩되는지를 본다. 누수가 의심되면 heap dump를 열어 봐야 한다. `-Xmx`, `-Xms`, `-XX:MaxMetaspaceSize` 같은 옵션도 각 영역이 무엇인지 알아야 제대로 잡는다.

## Runtime Data Area

JVM이 프로그램을 실행하면서 쓰는 메모리 영역이다.

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

객체가 만들어지는 곳이고, GC가 치우는 대상이다.

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

`-Xms`와 `-Xmx`를 같은 값으로 두면 heap이 늘었다 줄었다 하는 비용이 없다. 컨테이너에서는 흔히 이렇게 둔다.

## Stack

스레드마다 따로 있다. 메서드를 호출하면 프레임이 하나 쌓이고(push), 반환하면 빠진다(pop).

| 상황 | 증상 |
|---|---|
| 재귀 호출이 너무 깊다 | `StackOverflowError` |
| 스레드 수가 너무 많다 | 메모리 부족 (스레드당 stack 메모리 소비) |

```bash
# 스레드 스택 크기 설정
java -Xss512k -jar app.jar
```

## Method Area (Metaspace)

클래스 메타데이터와 런타임 상수 풀이 들어간다. Java 8부터 static 변수의 참조는 Heap에 있는 `java.lang.Class` 객체에 저장된다.

Java 8부터 PermGen이 Metaspace로 바뀌었다. Metaspace는 Native Memory를 쓰기 때문에 heap과 따로 잡힌다.

| 상황 | 증상 |
|---|---|
| 동적 클래스 생성이 많다 (리플렉션, 프록시) | `OutOfMemoryError: Metaspace` |
| 클래스 로더가 해제되지 않는다 | Metaspace 누수 |

```bash
# MetaspaceSize: 클래스 메타데이터 GC를 처음 일으키는 기준선 (미리 잡아 두는 크기가 아니다)
# MaxMetaspaceSize: 상한 (기본은 무제한)
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

JVM은 처음에는 바이트코드를 인터프리터로 한 줄씩 실행하다가, 자주 호출되는 코드(hot spot)를 찾아 네이티브 코드로 컴파일한다.

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

- `-Xmx`를 컨테이너 메모리 한도와 같게 잡으면, heap 밖에서 쓰는 메모리(Metaspace, 스레드 스택, direct buffer)까지 더해져 OOM Killer가 프로세스를 죽인다. heap은 한도보다 작게 잡고, `-XX:MaxRAMPercentage`로 컨테이너 메모리의 일정 비율만 heap으로 쓰게 하면 한도가 바뀌어도 따라간다.
- heap dump를 보지 않고 `-Xmx`만 올리면, 누수는 그대로이고 터지는 시점만 늦어진다.
- 스레드 수를 지나치게 늘리면, 스레드마다 잡는 스택 메모리를 합친 양이 시스템 메모리를 넘는다.
- Metaspace에 상한을 두지 않으면, 동적 프록시가 계속 생길 때 끝없이 늘어난다.

## 한 번에 설명하기

> JVM 메모리는 크게 Heap, Stack, Method Area(Metaspace)로 나뉩니다. Heap은 객체가 만들어지고 GC가 치우는 곳이고, Stack은 스레드마다 메서드 호출 프레임을 쌓는 곳입니다. Metaspace는 Java 8부터 PermGen 대신 클래스 메타데이터를 Native Memory에 둡니다.
>
> 크기는 각각 `-Xmx`, `-Xss`, `-XX:MaxMetaspaceSize`로 정합니다. 컨테이너에서는 이걸 다 더해도 한도를 넘지 않게 잡고, 문제가 생기면 heap dump와 jstat부터 확인합니다.

## 꼬리 질문

> [!question]- Heap과 Stack에는 각각 무엇이 저장되나?
> Heap에는 객체 인스턴스와 배열이 들어가고, Stack에는 메서드 호출 프레임과 지역 변수, 매개변수가 들어갑니다. Stack은 스레드마다 따로 있습니다.

> [!question]- `OutOfMemoryError`는 어떤 종류가 있고 원인이 각각 뭔가?
> `Java heap space`는 heap이 모자란 것이고, `Metaspace`는 클래스 메타데이터를 둘 공간이 모자란 것이고, `unable to create new native thread`는 OS가 허용하는 스레드 수를 넘은 것입니다.

> [!question]- PermGen은 왜 Metaspace로 바뀌었나?
> PermGen은 상한(`-XX:MaxPermSize`)을 미리 정해 둬야 해서, 그 값을 넘으면 `OutOfMemoryError`가 났습니다. Metaspace는 Native Memory를 써서 필요한 만큼 늘어나기 때문에 다루기가 더 편합니다.

> [!question]- 컨테이너에서는 JVM 메모리를 어떻게 잡나?
> `-Xmx`를 컨테이너 메모리 한도의 70~80%로 잡습니다. heap 말고도 Metaspace, Stack, Direct Buffer 같은 곳에 메모리가 더 필요하기 때문입니다.

> [!question]- JIT 워밍업은 실무에서 언제 문제가 되나?
> 배포 직후에 트래픽이 몰리면, 아직 JIT 최적화가 안 된 상태라 응답이 느립니다. 금방 내려가는 컨테이너는 JIT 효과를 아예 못 볼 수도 있습니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [JVMS 21: Run-Time Data Areas](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html#jvms-2.5)

## 관련 문서

- [[01-core/java/java|java]]
- [[gc-and-tuning]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]