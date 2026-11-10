---
title: 메모리 누수와 OOM 원인 분석
description: Java 메모리 누수와 OOM 실무 원인 분석 및 대응
---

# 메모리 누수와 OOM 원인 분석

메모리 누수는 더 이상 필요 없는 객체가 GC에 회수되지 않고 heap에 계속 남는 현상이다. OOM(OutOfMemoryError)은 JVM이 더 이상 메모리를 할당하지 못할 때 나는 에러이고, 누수가 쌓인 끝에 오는 경우가 많다.

누수는 바로 장애가 나지 않아서 늦게 발견된다. 배포 며칠 뒤에야 OOM이 나 원인 추적이 어렵고, 그 전에는 GC가 점점 잦아지며 응답 시간이 서서히 나빠진다. 컨테이너에서는 OOM Killer가 프로세스를 갑자기 죽인다. 그리고 heap dump가 없으면 어떤 객체가 문제인지 알 방법이 없다.

## OOM 메시지별 원인

| 에러 메시지 | 원인 |
|---|---|
| `Java heap space` | heap에 객체를 할당할 공간이 없다 |
| `GC overhead limit exceeded` | GC에 전체 시간의 98% 이상을 쓰면서 heap의 2% 미만만 회수 |
| `Metaspace` | 클래스 메타데이터 공간 부족 (동적 프록시, 리플렉션 과다) |
| `unable to create new native thread` | OS 스레드 생성 한도 초과 |
| `Direct buffer memory` | NIO Direct Buffer 할당 실패 |

## 흔한 누수 패턴

### 컬렉션에 넣기만 하고 빼지 않는다

```java
// static Map에 계속 추가만 한다
private static final Map<String, Object> cache = new HashMap<>();

public void process(String key, Object value) {
    cache.put(key, value); // 제거 로직이 없으면 계속 쌓인다
}
```

static 컬렉션은 애플리케이션이 살아 있는 동안 GC 대상이 아니다. 크기 제한이 없으면 시간이 갈수록 메모리를 먹는다. 캐시가 목적이라면 크기 제한과 만료 정책이 있는 구현체(Caffeine, Guava Cache 등)를 쓴다.

### 리소스를 닫지 않는다

```java
// Connection, Stream 등을 닫지 않으면 관련 객체가 회수되지 않을 수 있다
public String readFile(String path) throws IOException {
    BufferedReader reader = new BufferedReader(new FileReader(path));
    return reader.readLine();
    // reader가 닫히지 않는다
}
```

```java
// try-with-resources로 해결
public String readFile(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.readLine();
    }
}
```

DB Connection, HTTP Connection, InputStream이 대표적이다.

### 리스너·콜백을 등록하고 해제하지 않는다

```java
// 이벤트 리스너를 등록만 하고 해제하지 않으면
// 리스너가 참조하는 객체도 GC 대상에서 제외된다
eventBus.register(this);
// unregister를 하지 않으면 this가 GC되지 않는다
```

### ThreadLocal을 정리하지 않는다

```java
private static final ThreadLocal<UserContext> context = new ThreadLocal<>();

public void process() {
    context.set(new UserContext(...));
    // 처리 로직
    // context.remove()를 하지 않으면 스레드 풀에서 재사용 시 누수
}
```

스레드 풀에서는 스레드가 반환돼도 `remove()`하지 않은 값이 그대로 남는다.

### 큰 객체를 필요 이상 오래 잡고 있다

```java
public class ReportGenerator {

    private List<ReportData> allData; // 수십만 건

    public void generate() {
        this.allData = fetchAllData(); // 메서드가 끝나도 필드에 남아있다
        // ...
    }
}
```

지역 변수로 충분한 데이터를 필드에 두면 객체가 쓸데없이 오래 산다.

## 분석 순서

### 1. 증상 확인

```bash
# GC 상태 확인
jstat -gc <pid> 1000

# 주요 확인 항목
# - Old Generation 사용률이 계속 올라가는가
# - Full GC가 반복되는가
# - GC 후에도 사용률이 줄지 않는가
```

### 2. Heap dump 생성

```bash
# 수동 생성
jmap -dump:format=b,file=heap.hprof <pid>

# OOM 발생 시 자동 생성 (운영 환경에서 반드시 설정)
java -XX:+HeapDumpOnOutOfMemoryError \
     -XX:HeapDumpPath=/var/log/app/ \
     -jar app.jar
```

운영에서는 `-XX:+HeapDumpOnOutOfMemoryError`를 미리 켜 둔다. OOM이 난 뒤에는 dump를 뜰 기회가 없다.

### 3. Heap dump 분석

Eclipse MAT이나 VisualVM으로 연다.

| 확인 항목 | 의미 |
|---|---|
| Dominator Tree | 가장 많은 메모리를 차지하는 객체 트리 |
| Leak Suspects | 도구가 추정하는 누수 후보 |
| Histogram | 클래스별 인스턴스 수와 크기 |
| GC Roots | 특정 객체가 왜 GC되지 않는지 참조 경로 추적 |

## 컨테이너에서 메모리 잡기

```bash
# 잘못된 설정: JVM이 컨테이너 한도를 넘길 수 있다
# 컨테이너 메모리: 2GB
# -Xmx=2g → heap 외 메모리(Metaspace, Stack, Direct Buffer 등)가 추가되어 OOM Kill

# 권장: 컨테이너 한도의 70~80%를 -Xmx로 설정
# 컨테이너 메모리: 2GB
java -Xmx1400m -jar app.jar
```

Java 10+에서는 `-XX:MaxRAMPercentage`로 비율을 줄 수 있다.

```bash
java -XX:MaxRAMPercentage=75.0 -jar app.jar
```

## 자주 깨지는 곳

- **`-XX:+HeapDumpOnOutOfMemoryError`를 켜 두지 않는다.** OOM이 나도 분석할 dump가 없다.
- **heap dump 없이 `-Xmx`만 올린다.** 누수는 그대로고 터지는 시점만 미뤄진다.
- **`ThreadLocal`을 `remove()`하지 않는다.** 재사용된 스레드에 이전 요청 값이 남는다.
- **static 컬렉션에 크기 제한 없이 계속 넣는다.** 시간이 지날수록 heap을 다 차지한다.
- **Connection, Stream을 try-with-resources 없이 쓴다.** 예외 경로에서 닫히지 않는다.
- **컨테이너 한도와 JVM 메모리 설정을 따로 본다.** heap 밖 메모리까지 합쳐 한도를 넘는다.

## 면접에서 말하기

> 메모리 누수는 필요 없는 객체가 GC에 회수되지 않고 heap에 남는 현상이고, 쌓이면 GC가 점점 잦아지다 OOM으로 끝납니다. 흔한 원인은 제거 없는 static 컬렉션, 닫지 않은 리소스, remove하지 않은 ThreadLocal입니다. 그래서 운영에는 HeapDumpOnOutOfMemoryError를 미리 켜 두고, 문제가 나면 Eclipse MAT에서 Dominator Tree와 GC Roots로 무엇이 왜 안 지워지는지 추적합니다. 컨테이너에서는 heap 밖 메모리를 감안해 `-Xmx`를 한도의 70~80% 이하로 둡니다.

## 꼬리 질문

> [!question]- 메모리 누수와 메모리 부족의 차이는?
> 메모리 부족은 단순히 데이터가 많아서 heap이 모자란 것이고, 메모리 누수는 필요 없는 객체가 GC되지 않고 계속 쌓여서 결국 OOM에 이르는 것입니다.

> [!question]- `OutOfMemoryError: Java heap space`와 `GC overhead limit exceeded`의 차이는?
> `heap space`는 할당할 공간 자체가 없는 것이고, `GC overhead limit exceeded`는 GC에 98% 이상 시간을 쓰면서 2% 미만만 회수하는 상태입니다.

> [!question]- heap dump에서 메모리 누수를 어떻게 찾는가?
> Eclipse MAT에서 Dominator Tree로 가장 큰 객체를 찾고, GC Roots 경로를 추적해서 어떤 참조가 회수를 막고 있는지 확인합니다.

> [!question]- ThreadLocal이 스레드 풀 환경에서 누수를 일으키는 이유는?
> 스레드 풀의 스레드는 재사용되므로 `remove()`를 호출하지 않으면 이전 요청의 값이 남아있습니다. 스레드 수만큼 값이 계속 유지됩니다.

> [!question]- 컨테이너 환경에서 JVM 메모리를 어떻게 설정하는가?
> `-Xmx`를 컨테이너 한도의 70~80%로 설정합니다. heap 외에 Metaspace, Stack, Direct Buffer 등이 필요하므로 한도와 같게 설정하면 OOM Kill됩니다.

## 점검 퀴즈

아래 문항은 개념을 실제로 설명할 수 있는지 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>메모리 누수와 단순 메모리 부족을 구분하는 관찰 포인트는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="GC 후에도 Old 영역 사용량이 계속 상승하면 누수를 의심할 수 있다." aria-pressed="false">A. Full GC 후에도 사용량이 줄지 않고 계속 증가하는지 본다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="순간 피크만으로 누수라고 단정할 수 없다." aria-pressed="false">B. 요청이 많은 순간 메모리가 올라가면 항상 누수다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="CPU 사용률만으로 heap 객체 보존 여부를 판단하기 어렵다." aria-pressed="false">C. CPU 사용률이 낮으면 누수가 아니다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>ThreadLocal은 스레드 풀 환경에서 remove를 누락하면 누수 원인이 될 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="스레드가 재사용되므로 요청이 끝난 뒤에도 값이 남아 다음 요청까지 보존될 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="스레드 풀에서는 스레드 수명이 길어 ThreadLocal 값이 오래 남을 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>OOM 발생 시 heap dump를 분석할 때 먼저 볼 만한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="큰 객체 자체보다 어떤 참조 경로가 객체를 살려두는지 확인해야 누수 원인을 찾을 수 있다." aria-pressed="false">A. dominator tree와 GC root로부터의 참조 경로</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="파일명만으로 원인을 알 수 없다." aria-pressed="false">B. heap dump 파일명의 길이</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="클래스 이름 정렬만으로 보존 원인을 알기 어렵다." aria-pressed="false">C. 클래스 이름의 알파벳 순서</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[gc-and-tuning]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]