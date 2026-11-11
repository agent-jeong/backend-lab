---
title: Java 메모리 모델
description: 한 스레드가 바꾼 값을 다른 스레드가 언제 보는지 정하는 Java 메모리 모델과 volatile, synchronized
tags: [concept, java]
---

# Java 메모리 모델과 happens-before

Java Memory Model(JMM)은 여러 스레드가 같은 변수를 읽고 쓸 때, 바뀐 값이 다른 스레드에 언제 보이는지, 어떤 순서로 보이는지, `volatile`이나 `synchronized`를 쓰면 무엇이 달라지는지를 정한 규칙이다. 코드가 위에서 아래로 실행되는 것처럼 보여도, 다른 스레드가 바뀐 값을 바로 본다는 보장은 없다.

이걸 모르면 이런 일이 생긴다.

- 한 스레드가 바꾼 값을 다른 스레드가 계속 옛 값으로 본다.
- `volatile`만 붙이면 다 해결된다고 믿는다.
- `count++`가 한 번에 끝나는 연산이라고 착각한다.
- double-checked locking(락을 줄이려고 null 검사를 락 안팎에서 두 번 하는 초기화 방식)을 잘못 만든다.

이런 버그는 재현이 잘 안 돼서, 테스트는 통과하고 운영에서 가끔씩 터진다.

## Visibility와 Atomicity

visibility는 한 스레드가 바꾼 값이 다른 스레드에 보이느냐의 문제다.

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

하지만 `volatile`을 붙여도 여러 단계로 된 연산이 한 번에 끝나지는(atomicity) 않는다.

```java
volatile int count = 0;

void increment() {
    count++; // read, add, write 세 단계
}
```

카운터처럼 읽고 더하고 쓰는 과정이 중간에 끊기면 안 되면 `AtomicInteger`, `LongAdder`, `synchronized`, lock 중에서 고른다.

## happens-before

happens-before는 "A 작업의 결과가 B 작업에서 반드시 보인다"는 관계다. 동시성 코드에서 "다른 스레드가 이 값을 언제 볼 수 있나"를 따질 때 이 관계가 있는지를 본다.

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

`volatile`은 멈춤 플래그처럼 단순한 공유 값에 쓴다. 여러 값을 함께 바꾸거나, 읽고 고치고 다시 쓰는(read-modify-write) 연산이면 lock이나 atomic class를 쓴다.

## 상황별로 무엇을 쓰나

| 상황 | 먼저 볼 것 |
|---|---|
| stop flag | `volatile boolean` |
| 단순 카운터 | `AtomicLong`, `LongAdder` |
| 여러 필드 불변식 보호 | `synchronized` 또는 lock |
| 읽기 위주 공유 데이터 | 불변 객체, copy-on-write |
| 요청 단위 상태 | 공유하지 않고 지역 변수로 유지 |

가장 좋은 방법은 여러 스레드가 함께 건드리는 상태를 처음부터 줄이는 것이다.

## 자주 깨지는 곳

- `volatile`을 붙이면 `count++`가 안전해진다고 생각하면, 읽기와 쓰기 사이에 다른 스레드가 끼어들어 더한 값이 사라진다.
- 바뀌는 객체를 동기화 없이 여러 스레드가 함께 쓰면, 반쯤 바뀐 상태가 다른 스레드에 보인다.
- `HashMap`을 여러 스레드가 동시에 고치면, 값이 사라진다.
- 처음 쓸 때 만드는(lazy initialization) 코드를 동기화 없이 짜면, 객체가 두 번 만들어지거나 초기화가 덜 된 객체가 보인다.
- 테스트에서 재현되지 않으니 괜찮다고 보면, 운영에서 부하가 걸릴 때 가끔씩만 터지는 버그를 놓친다.

## 확인하는 방법

- 코드 리뷰에서 바뀔 수 있는 static 필드와, singleton 객체의 바뀔 수 있는 필드를 찾는다.
- 공유 변수에 읽고 고치고 쓰는 연산이 있는지 본다.
- 동시성 테스트는 `CountDownLatch`로 스레드들이 동시에 출발하게 맞춘다.
- thread dump와 메트릭으로 lock을 서로 기다리는 경합(lock contention)이나 blocked thread를 본다.

## 한 번에 설명하기

> Java Memory Model은 여러 스레드가 같은 데이터를 볼 때, 바뀐 값이 언제 보이고 어떤 순서로 보이는지를 정한 규칙입니다. 한 스레드가 바꾼 값이 다른 스레드에 언제 보이는지는 happens-before 관계로 설명합니다.
>
> volatile은 바뀐 값이 보이게는 해 주지만, count++처럼 여러 단계로 된 연산을 한 번에 끝내 주지는 않습니다. synchronized는 같은 monitor를 잡는 스레드끼리 바뀐 값이 보이게 하고, 임계 영역 전체를 한 번에 하나만 실행하게 합니다.
>
> 실무에서는 여러 스레드가 함께 쓰는 상태부터 줄이고, 꼭 필요한 곳에만 atomic class, lock, 불변 객체를 골라 씁니다.

## 꼬리 질문

> [!question]- visibility와 atomicity는 뭐가 다른가?
> visibility는 한 스레드가 바꾼 값이 다른 스레드에 보이느냐이고, atomicity는 작업이 중간에 끊기지 않고 한 덩어리로 끝나느냐입니다.

> [!question]- `volatile`로 풀리는 문제와 안 풀리는 문제는?
> 바뀐 값이 보이는 문제와 일부 순서 문제는 풀립니다. 하지만 `count++`처럼 읽고 고치고 쓰는 연산이 한 번에 끝나게 해 주지는 못합니다.

> [!question]- happens-before가 뭔가?
> 한 작업의 결과가 다른 작업에서 반드시 보이게 해 주는 관계입니다. `volatile`, `synchronized`, `start`, `join` 같은 것들이 이 관계를 만듭니다.

> [!question]- `synchronized`를 쓰면 무엇이 보장되나?
> 같은 monitor를 쓰는 스레드 중 한 번에 하나만 임계 영역에 들어갑니다. 그리고 앞 스레드가 unlock하고 나면, 다음에 lock을 잡은 스레드가 앞에서 바꾼 값을 볼 수 있습니다.

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

2026년 11월에 확인한 공식 문서다.

- [JLS 21: Threads and Locks (Memory Model)](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[java-concurrency-basics]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/concurrency/concurrency-test|concurrency-test]]
