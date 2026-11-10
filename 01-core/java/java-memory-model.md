---
title: Java 메모리 모델
description: Java 동시성에서 visibility, atomicity, happens-before를 이해하는 기준
tags: [concept, java]
---

# Java 메모리 모델과 happens-before

Java Memory Model(JMM)은 여러 스레드가 공유 변수를 읽고 쓸 때 값이 언제 보이는지, 어떤 순서로 보이는지, 동기화가 무엇을 보장하는지를 정한 규칙이다. 코드가 순서대로 실행되는 것처럼 보여도, 다른 스레드가 바뀐 값을 바로 본다는 보장은 없다.

이걸 모르면 한 스레드가 바꾼 값을 다른 스레드가 계속 못 보고, `volatile`이면 다 해결된다고 믿고, `count++`가 원자적이라고 착각하고, double-checked locking을 잘못 만든다. 이런 버그는 재현이 잘 안 돼서 테스트는 통과하고 운영에서 간헐적으로 터진다.

## Visibility와 Atomicity

visibility는 한 스레드의 변경이 다른 스레드에 보이느냐의 문제다.

```java
class StopFlag {
    private boolean running = true;

    void stop() {
        running = false;
    }

    void run() {
        while (running) {
            // work
        }
    }
}
```

`running`을 바꿔도 다른 스레드가 바로 본다는 보장이 없다. 이럴 때 `volatile`을 붙인다.

```java
private volatile boolean running = true;
```

하지만 `volatile`은 복합 연산의 atomicity를 보장하지 않는다.

```java
volatile int count = 0;

void increment() {
    count++; // read, add, write 세 단계
}
```

카운터처럼 원자성이 필요하면 `AtomicInteger`, `LongAdder`, `synchronized`, lock 중에서 고른다.

## happens-before

happens-before는 한 작업의 결과가 다른 작업에 보이도록 보장하는 관계다. 동시성 코드에서 "다른 스레드가 이 값을 언제 볼 수 있나"를 판단하는 기준이 이것이다.

| 관계 | 의미 |
|---|---|
| 같은 스레드 내 앞선 작업 | 뒤 작업에서 앞 작업 결과를 볼 수 있다 |
| `volatile` write 후 read | read한 스레드는 write 이전 변경을 볼 수 있다 |
| `synchronized` unlock 후 lock | 같은 monitor를 잡은 스레드가 변경을 볼 수 있다 |
| thread start | 시작 전 설정한 값을 새 thread가 볼 수 있다 |
| thread join | 종료한 thread의 결과를 join한 thread가 볼 수 있다 |

## synchronized와 volatile

| 구분 | `volatile` | `synchronized` |
|---|---|---|
| visibility | 보장 | 보장 |
| atomicity | 단일 read/write 중심 | 임계 영역 전체 보장 |
| lock | 사용하지 않음 | monitor lock 사용 |
| 용도 | 상태 플래그, 단순 publish | 복합 상태 변경, 불변식 보호 |

`volatile`은 상태 플래그처럼 단순한 공유 값에 쓴다. 여러 값을 함께 바꾸거나 read-modify-write가 필요하면 lock이나 atomic class를 쓴다.

## 상황별로 무엇을 쓰나

| 상황 | 먼저 볼 것 |
|---|---|
| stop flag | `volatile boolean` |
| 단순 카운터 | `AtomicLong`, `LongAdder` |
| 여러 필드 불변식 보호 | `synchronized` 또는 lock |
| 읽기 위주 공유 데이터 | 불변 객체, copy-on-write |
| 요청 단위 상태 | 공유하지 않고 지역 변수로 유지 |

가장 좋은 방법은 공유 상태 자체를 줄이는 것이다.

## 자주 깨지는 곳

- **`volatile`로 `count++`가 안전해진다고 생각한다.** 읽기와 쓰기 사이에 다른 스레드가 끼어들어 증가분이 사라진다.
- **mutable 객체를 동기화 없이 여러 스레드가 공유한다.** 반쯤 바뀐 상태가 다른 스레드에 보인다.
- **`HashMap`을 여러 스레드가 동시에 수정한다.** 값이 유실된다.
- **lazy initialization을 동기화 없이 만든다.** 객체가 두 번 만들어지거나 초기화가 덜 된 객체가 보인다.
- **테스트에서 재현되지 않으니 문제없다고 본다.** 동시성 버그는 운영 부하에서 간헐적으로만 드러난다.

## 확인하는 방법

- 코드 리뷰에서 static mutable state와 singleton의 mutable field를 찾는다.
- 공유 변수에 read-modify-write 연산이 있는지 본다.
- 동시성 테스트는 `CountDownLatch`로 스레드 시작 시점을 맞춘다.
- thread dump와 메트릭으로 lock contention이나 blocked thread를 본다.

## 면접에서 말하기

> Java Memory Model은 여러 스레드가 공유 데이터를 볼 때 visibility와 실행 순서를 정하는 규칙입니다. volatile은 변경이 보이는 것은 보장하지만 count++ 같은 복합 연산의 원자성은 보장하지 않고, synchronized는 같은 monitor 기준으로 가시성과 임계 영역의 원자성을 함께 줍니다. 한 스레드의 변경이 언제 다른 스레드에 보이는지는 happens-before 관계로 설명합니다. 실무에서는 공유 상태부터 줄이고, 필요한 곳에만 atomic class, lock, 불변 객체를 골라 씁니다.

## 꼬리 질문

> [!question]- visibility와 atomicity의 차이는 무엇인가?
> visibility는 한 스레드의 변경이 다른 스레드에 보이는지이고, atomicity는 작업이 중간 상태 없이 하나의 단위로 수행되는지입니다.

> [!question]- `volatile`은 어떤 문제를 해결하고 어떤 문제를 해결하지 못하는가?
> visibility와 일부 ordering을 보장하지만, `count++` 같은 read-modify-write 연산의 atomicity는 보장하지 못합니다.

> [!question]- happens-before란 무엇인가?
> 한 작업의 결과가 다른 작업에 보이도록 보장하는 관계입니다. `volatile`, `synchronized`, `start`, `join` 등이 대표적인 happens-before 관계를 만듭니다.

> [!question]- `synchronized`는 어떤 보장을 제공하는가?
> 같은 monitor를 기준으로 한 번에 하나의 스레드만 임계 영역에 들어가게 하고, unlock 이후 lock한 스레드가 이전 변경을 볼 수 있게 합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>visibility와 atomicity의 차이로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="visibility는 변경을 다른 스레드가 볼 수 있는가, atomicity는 연산이 쪼개지지 않는가의 문제다." aria-pressed="false">A. 보이는 문제와 쪼개지지 않는 문제는 다르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="volatile은 모든 복합 연산을 원자적으로 만들지 않는다." aria-pressed="false">B. visibility가 보장되면 모든 증가 연산도 안전하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="atomicity만으로 최신 값 관찰이 항상 보장되는 것은 아니다." aria-pressed="false">C. atomicity와 visibility는 완전히 같은 말이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>volatile int count에 count++을 하면 멀티스레드에서도 안전한 카운터가 된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="count++은 읽기, 증가, 쓰기의 복합 연산이라 volatile만으로 원자성이 보장되지 않는다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="volatile은 가시성에는 도움되지만 복합 연산의 원자성은 보장하지 않는다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>synchronized가 보장하는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="동일 모니터 기준으로 상호 배제와 happens-before에 따른 가시성을 제공한다." aria-pressed="false">A. 상호 배제와 가시성 보장을 함께 제공한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="synchronized가 모든 비동기 작업을 병렬로 만드는 것은 아니다." aria-pressed="false">B. 모든 코드를 자동 병렬화한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="락 범위와 대상이 중요하며 모든 객체 변경을 전역으로 보호하지 않는다." aria-pressed="false">C. JVM 전체 객체 변경을 자동으로 직렬화한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [JLS 21: Threads and Locks (Memory Model)](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)

## 관련 문서

- [[java]]
- [[java-concurrency-basics]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/concurrency/concurrency-test|concurrency-test]]
