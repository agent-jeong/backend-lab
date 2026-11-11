---
title: GC 동작 원리와 튜닝
description: GC가 안 쓰는 객체를 찾아 치우는 방식과, 응답이 튀거나 메모리가 찰 때 무엇부터 볼지
tags: [concept, java]
---

# GC 동작 원리와 튜닝

GC(Garbage Collection)는 더 이상 아무도 가리키지 않는 객체를 JVM이 알아서 찾아 메모리를 돌려받는 일이다. 대부분은 기본 설정으로 충분하다. 하지만 응답 시간이 가끔 튀거나 메모리가 계속 차오르면, GC가 어떻게 도는지 알아야 원인을 가려낼 수 있다.

GC 원리가 필요해지는 때는 대개 이렇다. 주문 API 응답이 가끔 1~2초씩 튀는데 알고 보니 GC pause 때문일 때. Full GC가 반복되면서 서비스가 몇 초씩 멈출 때. 메모리 사용량이 계속 올라가면서 GC가 점점 자주 돌 때. 컨테이너 메모리 한도를 넘어 프로세스가 kill될 때. 그리고 GC 로그를 읽고 원인을 판단해야 할 때다.

## 안 쓰는 객체를 어떻게 찾나

GC가 먼저 풀어야 하는 문제는 "어떤 객체가 더 이상 쓰이지 않는가"를 가려내는 것이다.

### 도달성 분석(Reachability Analysis)

지금의 JVM은 GC Root에서 출발해 참조를 따라가며 닿는 객체에 표시를 한다. 끝까지 닿지 못한 객체가 치울 대상이다.

```
GC Roots
  ├── Stack 지역변수 → 객체A → 객체B (도달 가능 → 생존)
  ├── Static 변수 → 객체C (도달 가능 → 생존)
  └── (참조 끊김)
                         객체D → 객체E (도달 불가 → 수거 대상)
```

GC Root가 되는 것은 이렇다.

| GC Root | 예시 |
|---|---|
| Stack의 지역변수/매개변수 | 현재 실행 중인 메서드의 변수 |
| Static 변수 | 클래스의 static 필드가 참조하는 객체 |
| JNI 참조 | 네이티브 코드에서 참조하는 객체 |
| 활성 스레드 | Thread 객체 자체 |
| Synchronized lock 대상 | 현재 모니터를 잡고 있는 객체 |

### Reference Counting을 쓰지 않는 이유

예전 방식인 Reference Counting(참조 횟수 세기)은 서로를 가리키는 객체(순환 참조)를 치우지 못한다.

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

도달성 분석은 서로 가리키고 있어도 GC Root에서 닿지 않으면 치우기 때문에 이 문제가 없다.

### 수거 방식마다 얻는 것과 잃는 것

| 방식 | 장점 | 단점 |
|---|---|---|
| Reference Counting | 즉시 수거, 구현 단순 | 순환 참조 미해결, 카운트 갱신 오버헤드 |
| Mark-and-Sweep | 순환 참조 해결, 정확 | STW 필요, 단편화 |
| Mark-and-Compact | 단편화 해결 | 이동 비용 |
| Copying (세대별) | Young Gen에서 빠름 | 메모리 2배 필요 |

JVM은 이 방식들을 섞어 쓴다. Young Gen은 Copying, Old Gen은 Mark-Compact 계열이다.

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

GC가 도는 동안 애플리케이션 스레드가 멈추는 것을 말한다. Minor GC의 STW는 짧지만 Full GC의 STW는 몇 초까지 가기도 한다. 실무에서 "GC 튜닝"이라고 하면 대부분 이 멈추는 시간을 줄이는 일이다.

## GC 알고리즘

| GC | 특성 | 맞는 상황 |
|---|---|---|
| Serial GC | 싱글 스레드 GC | 작은 heap, 테스트 환경 |
| Parallel GC | 멀티 스레드 GC, 처리량 우선 | 배치, 데이터 처리 |
| G1 GC | region 기반, STW 목표 시간 설정 가능 | 일반 웹 서비스 (Java 9+ 기본) |
| ZGC | 매우 짧은 STW (< 1ms 목표) | 대용량 heap, 지연 민감 서비스 |
| Shenandoah | ZGC와 유사, OpenJDK 제공 | ZGC 대안 |

## G1 GC

Java 9부터 기본 GC이고, 대부분의 웹 서비스에서 무난하게 쓴다.

다만 JVM은 "서버급 머신"이라고 판단할 때만 G1을 고른다. CPU가 2개 미만이거나 메모리가 약 1.8GB 미만이면 Serial GC가 기본이다. CPU 1개, 메모리 1GB짜리 컨테이너에서 GC pause가 유난히 길다면 이것부터 의심한다. `java -XX:+PrintCommandLineFlags -version`으로 실제로 어떤 GC가 골라졌는지 확인하고, 필요하면 `-XX:+UseG1GC`를 직접 적는다.

Heap을 같은 크기의 region으로 나누고, 치울 객체가 많은 region부터 치운다(Garbage First).

```
┌───┬───┬───┬───┬───┬───┬───┬───┐
│ E │ E │ S │   │ O │ O │ O │ H │
└───┴───┴───┴───┴───┴───┴───┴───┘
E: Eden  S: Survivor  O: Old  H: Humongous  (빈칸: Free)
```

자주 만지는 옵션은 이렇다.

```bash
java \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \       # STW 목표 시간 (기본 200ms)
  -XX:G1HeapRegionSize=4m \        # region 크기
  -XX:InitiatingHeapOccupancyPercent=45 \  # Old 사용률이 이 값을 넘으면 Mixed GC 시작
  -jar app.jar
```

`MaxGCPauseMillis`는 지켜진다는 약속이 아니라 목표일 뿐이다. 너무 낮게 잡으면 GC가 자주 돌고, 너무 높게 잡으면 한 번 멈출 때 오래 멈춘다.

## ZGC

ZGC는 Java 15부터 운영 환경에서 쓸 수 있게 됐다. 초기 ZGC는 Young과 Old를 나누지 않아서 객체를 많이 만드는 서비스에서 CPU를 많이 썼다. Java 21에서 generational 모드가 들어오면서 이 약점이 줄었다.

```bash
# Java 21~22: generational 모드를 명시해야 한다
java -XX:+UseZGC -XX:+ZGenerational -jar app.jar

# Java 23+: generational이 기본, Java 24+는 non-generational 모드가 제거됨
java -XX:+UseZGC -jar app.jar
```

멈추는 시간은 아주 짧지만, GC 작업을 애플리케이션과 동시에 돌리기 때문에 CPU를 더 쓰고 처리량은 G1보다 낮을 수 있다. CPU 여유가 적은 작은 컨테이너에서는 얻는 게 적다.

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

- GC 로그를 남기지 않으면, 장애가 나도 무엇을 보고 분석할지가 없다.
- Full GC가 반복되는데 `-Xmx`만 올리면, 누수였을 경우 터지는 시점만 늦어진다.
- 코드보다 옵션을 먼저 만지면, 쓸데없이 객체를 많이 만드는 진짜 원인을 놓친다. 객체 생성을 줄이는 게 튜닝보다 먼저다.
- `MaxGCPauseMillis`를 너무 낮게 잡으면, GC가 지나치게 자주 돈다.
- 운영 중인 서비스의 GC 알고리즘을 충분히 테스트하지 않고 바꾸면, 처리량과 CPU 사용량까지 함께 바뀐다.

## 한 번에 설명하기

> GC는 GC Root에서 참조를 따라가 닿지 않는 객체를 찾아 메모리를 돌려받습니다. Heap은 Young과 Old로 나뉘는데, 대부분의 객체는 Young에서 Minor GC로 금방 치워집니다. Old를 감당하지 못하게 되면 Full GC가 돌면서 오래 멈춥니다(Stop-the-World).
>
> 기본 GC인 G1은 heap을 region으로 나눠 치울 게 많은 곳부터 치우고, 멈추는 시간의 목표를 정해 줄 수 있습니다.
>
> 튜닝이 필요하면 GC 로그로 얼마나 자주, 얼마나 오래 멈추는지부터 확인합니다. 옵션을 만지기 전에 쓸데없이 객체를 많이 만드는 코드부터 줄입니다.

## 꼬리 질문

> [!question]- Minor GC와 Full GC는 뭐가 다른가?
> Minor GC는 Young Generation만 치워서 빠릅니다. Full GC는 Heap 전체를 치우느라 오래 멈춰서, 서비스 응답이 늦어지는 흔한 원인이 됩니다.

> [!question]- Stop-the-World가 서비스에 어떤 영향을 주나?
> GC가 도는 동안 애플리케이션 스레드가 전부 멈춥니다. Full GC로 몇 초씩 멈추면 요청이 타임아웃 나거나 헬스체크가 실패할 수 있습니다.

> [!question]- G1 GC와 ZGC는 뭐가 다른가?
> G1은 멈추는 시간의 목표를 정해 줄 수 있는, 두루 쓰는 GC입니다. ZGC는 멈추는 시간을 1ms 이하로 유지해서, heap이 아주 크거나 응답 지연에 민감한 서비스에 맞습니다.

> [!question]- GC 튜닝보다 먼저 할 일은?
> 애플리케이션 코드에서 쓸데없이 객체를 많이 만드는 곳부터 줄입니다. 필요 없는 String 연결이나 반복문 안에서 객체를 만드는 코드 같은 것을 봅니다.

> [!question]- GC 로그에서 무엇을 보나?
> GC가 얼마나 자주 도는지, 한 번에 얼마나 멈추는지, Full GC가 났는지, GC가 끝난 뒤 heap 사용량이 어떻게 변하는지를 봅니다. GC를 해도 메모리가 줄지 않으면 누수를 의심합니다.

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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21: HotSpot GC Tuning Guide](https://docs.oracle.com/en/java/javase/21/gctuning/)
- [JEP 439: Generational ZGC](https://openjdk.org/jeps/439)
- [JEP 474: ZGC Generational Mode by Default](https://openjdk.org/jeps/474)

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[memory-leak-and-oom]]
- [[02-practical-backend/performance/performance|performance]]