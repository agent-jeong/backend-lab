---
title: Java 메모리 모델
description: Java 동시성에서 visibility, atomicity, happens-before를 이해하는 기준
---

# Java 메모리 모델과 happens-before

## 한 줄 정의

Java Memory Model은 여러 스레드가 공유 변수를 읽고 쓸 때 값의 가시성, 실행 순서, 동기화 보장을 정의하는 규칙이다.

## 실무에서 왜 중요한가

멀티스레드 환경에서는 코드 순서대로 실행되는 것처럼 보여도 다른 스레드가 같은 값을 즉시 본다는 보장이 없다. JMM을 모르면 다음 문제가 생긴다.

- 한 스레드가 바꾼 값을 다른 스레드가 계속 보지 못한다.
- `volatile`을 쓰면 모든 동시성 문제가 해결된다고 오해한다.
- `count++` 같은 연산이 원자적이라고 생각한다.
- double-checked locking을 잘못 구현한다.
- 동시성 버그가 재현되지 않아 테스트만 통과하고 운영에서 간헐적으로 실패한다.

## Visibility와 Atomicity

visibility는 한 스레드의 변경이 다른 스레드에 보이는지의 문제다.

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

`running` 변경이 다른 스레드에 즉시 보인다는 보장이 없다. 이런 경우 `volatile`을 사용할 수 있다.

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

카운터처럼 원자성이 필요하면 `AtomicInteger`, `LongAdder`, `synchronized`, lock을 검토한다.

## happens-before

happens-before는 한 작업의 결과가 다른 작업에 보이도록 보장하는 관계다.

대표적인 예시는 다음과 같다.

| 관계 | 의미 |
|---|---|
| 같은 스레드 내 앞선 작업 | 뒤 작업에서 앞 작업 결과를 볼 수 있다 |
| `volatile` write 후 read | read한 스레드는 write 이전 변경을 볼 수 있다 |
| `synchronized` unlock 후 lock | 같은 monitor를 잡은 스레드가 변경을 볼 수 있다 |
| thread start | 시작 전 설정한 값을 새 thread가 볼 수 있다 |
| thread join | 종료한 thread의 결과를 join한 thread가 볼 수 있다 |

JMM은 동시성 코드를 작성할 때 "언제 다른 스레드가 이 값을 볼 수 있는가"를 판단하는 기준이다.

## synchronized와 volatile

| 구분 | `volatile` | `synchronized` |
|---|---|---|
| visibility | 보장 | 보장 |
| atomicity | 단일 read/write 중심 | 임계 영역 전체 보장 |
| lock | 사용하지 않음 | monitor lock 사용 |
| 용도 | 상태 플래그, 단순 publish | 복합 상태 변경, 불변식 보호 |

`volatile`은 상태 플래그처럼 단순한 공유 값에 적합하다. 여러 값을 함께 변경하거나 read-modify-write가 필요하면 lock이나 atomic class가 필요하다.

## 자주 나는 실수

- `volatile`로 `count++`를 안전하게 만들 수 있다고 생각한다.
- 동기화 없이 mutable 객체를 여러 스레드가 공유한다.
- `HashMap`을 여러 스레드가 동시에 수정한다.
- lazy initialization을 동기화 없이 구현한다.
- 테스트에서 재현되지 않는다고 동시성 문제가 없다고 판단한다.

## 실무 판단 기준

| 상황 | 우선 고려 |
|---|---|
| stop flag | `volatile boolean` |
| 단순 카운터 | `AtomicLong`, `LongAdder` |
| 여러 필드 불변식 보호 | `synchronized` 또는 lock |
| 읽기 위주 공유 데이터 | 불변 객체, copy-on-write |
| 요청 단위 상태 | 공유하지 않고 지역 변수로 유지 |

## 확인 방법

- 코드 리뷰에서 static mutable state와 singleton mutable field를 찾는다.
- 공유 변수에 read-modify-write 연산이 있는지 확인한다.
- 동시성 테스트는 `CountDownLatch`로 시작 시점을 맞춘다.
- thread dump와 메트릭으로 lock contention이나 blocked thread를 확인한다.

## 핵심 요약

Java Memory Model은 여러 스레드가 공유 데이터를 볼 때 visibility와 실행 순서를 정의하는 규칙입니다.

`volatile`은 값 변경의 가시성을 보장하지만 `count++` 같은 복합 연산의 원자성은 보장하지 않습니다.

`synchronized`는 같은 monitor를 기준으로 visibility와 임계 영역의 atomicity를 함께 제공합니다.

happens-before 관계를 이해해야 한 스레드의 변경이 다른 스레드에 언제 보이는지 설명할 수 있습니다.

실무에서는 공유 상태를 줄이고, 필요한 경우 atomic class, lock, 불변 객체를 명확한 기준으로 선택해야 합니다.

## 꼬리 질문

> [!question]- visibility와 atomicity의 차이는 무엇인가?
> visibility는 한 스레드의 변경이 다른 스레드에 보이는지이고, atomicity는 작업이 중간 상태 없이 하나의 단위로 수행되는지입니다.

> [!question]- `volatile`은 어떤 문제를 해결하고 어떤 문제를 해결하지 못하는가?
> visibility와 일부 ordering을 보장하지만, `count++` 같은 read-modify-write 연산의 atomicity는 보장하지 못합니다.

> [!question]- happens-before란 무엇인가?
> 한 작업의 결과가 다른 작업에 보이도록 보장하는 관계입니다. `volatile`, `synchronized`, `start`, `join` 등이 대표적인 happens-before 관계를 만듭니다.

> [!question]- `synchronized`는 어떤 보장을 제공하는가?
> 같은 monitor를 기준으로 한 번에 하나의 스레드만 임계 영역에 들어가게 하고, unlock 이후 lock한 스레드가 이전 변경을 볼 수 있게 합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>visibility와 atomicity의 차이로 가장 적절한 것은?</p>
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
    <p class="quiz-question"><span class="quiz-label">객관식</span>synchronized가 제공하는 보장으로 가장 적절한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="동일 모니터 기준으로 상호 배제와 happens-before에 따른 가시성을 제공한다." aria-pressed="false">A. 상호 배제와 가시성 보장을 함께 제공한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="synchronized가 모든 비동기 작업을 병렬로 만드는 것은 아니다." aria-pressed="false">B. 모든 코드를 자동 병렬화한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="락 범위와 대상이 중요하며 모든 객체 변경을 전역으로 보호하지 않는다." aria-pressed="false">C. JVM 전체 객체 변경을 자동으로 직렬화한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[java]]
- [[java-concurrency-basics]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/concurrency/concurrency-test|concurrency-test]]
