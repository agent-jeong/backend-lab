---
title: GC 동작 원리와 튜닝
description: Java GC 동작 원리와 실무 튜닝 관점
---

# GC 동작 원리와 튜닝

GC(Garbage Collection)는 더 이상 참조되지 않는 객체의 메모리를 JVM이 자동으로 회수하는 장치다. 대부분은 기본 설정으로 충분하지만, 응답 지연이 튀거나 메모리가 계속 차오르면 원리를 알아야 원인을 가를 수 있다.

GC 원리가 필요해지는 순간은 대개 이렇다. 응답 지연이 간헐적으로 튀는데 원인이 GC pause일 때, Full GC가 반복되며 서비스가 수 초씩 멈출 때, 메모리 사용량이 계속 올라 GC가 점점 잦아질 때, 컨테이너 메모리 한도를 넘겨 프로세스가 kill될 때, 그리고 GC 로그를 보고 원인을 판단해야 할 때다.

## 안 쓰는 객체를 어떻게 찾나

GC의 근본 문제는 "어떤 객체가 더 이상 쓰이지 않는가"를 가려내는 것이다.

### 도달성 분석(Reachability Analysis)

현대 JVM은 GC Root에서 참조 체인을 따라가며 도달 가능한 객체를 표시한다. 도달하지 못한 객체가 수거 대상이다.

```
GC Roots
  ├── Stack 지역변수 → 객체A → 객체B (도달 가능 → 생존)
  ├── Static 변수 → 객체C (도달 가능 → 생존)
  └── (참조 끊김)
                         객체D → 객체E (도달 불가 → 수거 대상)
```

GC Root가 되는 것은 다음과 같다.

| GC Root | 예시 |
|---|---|
| Stack의 지역변수/매개변수 | 현재 실행 중인 메서드의 변수 |
| Static 변수 | 클래스의 static 필드가 참조하는 객체 |
| JNI 참조 | 네이티브 코드에서 참조하는 객체 |
| 활성 스레드 | Thread 객체 자체 |
| Synchronized lock 대상 | 현재 모니터를 잡고 있는 객체 |

### Reference Counting을 쓰지 않는 이유

초기 방식인 Reference Counting(참조 횟수 세기)은 순환 참조를 풀지 못한다.

```java
// 순환 참조 예시 - Reference Counting으로는 수거 불가
class Node {
    Node next;
}

Node a = new Node();
Node b = new Node();
a.next = b;  // b의 참조 카운트: 1
b.next = a;  // a의 참조 카운트: 1
a = null;    // a 참조 카운트: 1 (b.next가 여전히 참조)
b = null;    // b 참조 카운트: 1 (a.next가 여전히 참조)
// → 둘 다 카운트가 0이 아니라 수거 불가, 하지만 실제로는 접근 불가
```

도달성 분석은 GC Root에서 닿지 않으면 수거하므로 순환 참조 문제가 없다.

### 수거 방식의 트레이드오프

| 방식 | 장점 | 단점 |
|---|---|---|
| Reference Counting | 즉시 수거, 구현 단순 | 순환 참조 미해결, 카운트 갱신 오버헤드 |
| Mark-and-Sweep | 순환 참조 해결, 정확 | STW 필요, 단편화 |
| Mark-and-Compact | 단편화 해결 | 이동 비용 |
| Copying (세대별) | Young Gen에서 빠름 | 메모리 2배 필요 |

JVM은 이들을 섞어 쓴다. Young Gen은 Copying, Old Gen은 Mark-Compact 계열이다.

## 세대별 구조

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
| Old 영역 회수 | Old가 차면 회수한다. G1은 평소 concurrent marking + Mixed GC로 나눠 치우고, 그걸로 따라가지 못할 때만 Full GC(전체 STW)로 떨어진다 |

### Stop-the-World

GC가 도는 동안 애플리케이션 스레드가 멈추는 현상이다. Minor GC의 STW는 짧지만 Full GC의 STW는 수 초에 이르기도 한다. 실무에서 "GC 튜닝"이라고 하면 대부분 이 STW 시간을 줄이는 일이다.

## GC 알고리즘

| GC | 특성 | 맞는 상황 |
|---|---|---|
| Serial GC | 싱글 스레드 GC | 작은 heap, 테스트 환경 |
| Parallel GC | 멀티 스레드 GC, 처리량 우선 | 배치, 데이터 처리 |
| G1 GC | region 기반, STW 목표 시간 설정 가능 | 일반 웹 서비스 (Java 9+ 기본) |
| ZGC | 매우 짧은 STW (< 1ms 목표) | 대용량 heap, 지연 민감 서비스 |
| Shenandoah | ZGC와 유사, OpenJDK 제공 | ZGC 대안 |

## G1 GC

Java 9부터 기본 GC이고, 대부분의 웹 서비스에서 무난하다.

단, JVM은 "서버급 머신"일 때만 G1을 고른다. CPU가 2개 미만이거나 메모리가 약 1.8GB 미만이면 Serial GC가 기본이다. CPU 1개, 메모리 1GB짜리 컨테이너에서 GC pause가 유독 길다면 이것부터 의심한다. `java -XX:+PrintCommandLineFlags -version`으로 실제 선택된 GC를 확인하고, 필요하면 `-XX:+UseG1GC`를 명시한다.

Heap을 고정 크기 region으로 나누고, 가비지가 많은 region부터 수집한다(Garbage First).

```
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ E │ E │ S │   │ O │ O │ O │ H │
└───┴───┴───┴───┴───┴───┴───┴───┘
E: Eden  S: Survivor  O: Old  H: Humongous  (빈칸: Free)
```

주요 옵션:

```bash
java \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \       # STW 목표 시간 (기본 200ms)
  -XX:G1HeapRegionSize=4m \        # region 크기
  -XX:InitiatingHeapOccupancyPercent=45 \  # Old 사용률이 이 값을 넘으면 Mixed GC 시작
  -jar app.jar
```

`MaxGCPauseMillis`는 보장이 아니라 목표다. 너무 낮으면 GC가 잦아지고, 너무 높으면 한 번에 긴 STW가 생긴다.

## ZGC

ZGC는 Java 15부터 운영용(production)으로 쓸 수 있었다. 초기 ZGC는 세대 구분이 없어 할당이 많은 서비스에서 CPU를 많이 썼는데, Java 21에서 generational 모드가 들어오며 이 약점이 줄었다.

```bash
# Java 21~22: generational 모드를 명시해야 한다
java -XX:+UseZGC -XX:+ZGenerational -jar app.jar

# Java 23+: generational이 기본, Java 24+는 non-generational 모드가 제거됨
java -XX:+UseZGC -jar app.jar
```

STW는 매우 짧지만, GC 작업을 애플리케이션과 동시에 돌리므로 CPU를 더 쓰고 처리량은 G1보다 낮을 수 있다. CPU 여유가 적은 작은 컨테이너에서는 이점이 작다.

| 특성 | 값 |
|---|---|
| STW 시간 | < 1ms 목표 |
| Heap 크기 | 수 TB까지 지원 |
| 맞는 서비스 | 지연 시간이 매우 중요한 서비스 (결제, 실시간 처리) |

## GC 로그 보기

```bash
# GC 로그 활성화
java \
  -Xlog:gc*:file=gc.log:time,uptime,level,tags \
  -jar app.jar
```

| 항목 | 의미 |
|---|---|
| GC 빈도 | 너무 잦으면 객체 생성이 과하거나 heap이 작다 |
| Pause 시간 | STW 시간이 응답 지연의 원인인지 본다 |
| Full GC 발생 여부 | Full GC가 반복되면 메모리 누수를 의심한다 |
| Heap 사용량 추이 | GC 후에도 줄지 않으면 누수 가능성이 있다 |

## 증상별로 무엇을 하나

| 상황 | 조치 |
|---|---|
| Full GC가 반복된다 | 메모리 누수 확인, heap dump 분석 |
| Minor GC가 너무 잦다 | Young Generation 크기 확인, 과도한 객체 생성 점검 |
| STW가 길다 | G1의 `MaxGCPauseMillis` 조정, ZGC 검토 |
| GC 후에도 메모리가 줄지 않는다 | 메모리 누수 의심, heap dump 분석 |
| 컨테이너에서 OOM Kill | `-Xmx`를 컨테이너 한도의 70~80% 이하로 설정 |

## 자주 깨지는 곳

- **GC 로그를 남기지 않는다.** 장애가 나도 분석할 근거가 없다.
- **Full GC가 반복되는데 `-Xmx`만 올린다.** 누수라면 터지는 시점만 미뤄진다.
- **코드보다 옵션을 먼저 만진다.** 과도한 객체 생성을 줄이는 게 튜닝보다 먼저다.
- **`MaxGCPauseMillis`를 너무 낮게 잡는다.** GC가 지나치게 자주 돈다.
- **운영에서 GC 알고리즘을 충분한 테스트 없이 바꾼다.** 처리량과 CPU 사용 패턴이 함께 바뀐다.

## 면접에서 말하기

> GC는 GC Root에서 닿지 않는 객체를 찾아 메모리를 회수하는 장치입니다. Heap은 Young과 Old로 나뉘어 대부분의 객체는 Young에서 Minor GC로 빨리 회수되고, Old가 감당이 안 되면 Full GC로 긴 Stop-the-World가 생깁니다. 기본인 G1은 region 단위로 가비지가 많은 곳부터 치우고 STW 목표 시간을 줄 수 있습니다. 튜닝이 필요하면 GC 로그로 빈도와 pause를 먼저 확인하고, 옵션보다 과도한 객체 생성을 줄이는 쪽을 먼저 봅니다.

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

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>GC 튜닝 전에 먼저 할 일은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="GC 로그, heap 사용량, 지연 시간, allocation rate를 보고 병목인지 확인해야 한다." aria-pressed="false">A. 로그와 지표로 GC가 실제 병목인지 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="근거 없이 heap을 키우면 문제를 숨기거나 컨테이너 OOM을 만들 수 있다." aria-pressed="false">B. 우선 -Xmx를 최대한 크게 올린다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="알고리즘 변경은 측정 후 선택해야 한다." aria-pressed="false">C. 무조건 최신 GC로 바꾼다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Stop-the-World는 GC 종류와 관계없이 애플리케이션 스레드가 멈추는 구간을 의미한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="STW 시간이 길어지면 API 지연 시간과 타임아웃에 직접 영향을 줄 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="GC가 백그라운드로 동작하더라도 STW 구간은 존재할 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>G1 GC와 ZGC 선택을 비교할 때 핵심 기준은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="ZGC는 낮은 지연 시간에 강점이 있고, G1은 일반 서버에서 균형 잡힌 기본 선택지로 많이 쓰인다." aria-pressed="false">A. 지연 시간 목표와 운영 검증 수준을 함께 본다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 서비스에 하나의 정답 GC가 있는 것은 아니다." aria-pressed="false">B. ZGC가 항상 처리량과 지연 시간 모두에서 우월하다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="GC 선택은 코드 스타일보다 지표와 서비스 특성에 좌우된다." aria-pressed="false">C. 컨트롤러 코드가 많으면 G1을 쓰면 안 된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]