---
title: 메모리 누수와 OOM 원인 분석
description: Java 메모리 누수와 OOM 실무 원인 분석 및 대응
---

# 메모리 누수와 OOM 원인 분석

## 한 줄 정의

메모리 누수는 더 이상 필요하지 않은 객체가 GC에 의해 회수되지 않고 계속 heap에 남는 현상이고, OOM(OutOfMemoryError)은 JVM이 더 이상 메모리를 할당할 수 없을 때 발생하는 에러다.

## 실무에서 왜 중요한가

메모리 누수는 즉시 장애가 나지 않아서 발견이 늦다. 하지만 한번 터지면 서비스 전체가 멈출 수 있다.

- 배포 후 며칠 뒤에야 OOM이 발생해서 원인 추적이 어렵다.
- GC가 점점 자주 발생하면서 응답 시간이 서서히 나빠진다.
- 컨테이너 환경에서 OOM Killer에 의해 프로세스가 갑자기 죽는다.
- heap dump 없이는 어떤 객체가 문제인지 알 수 없다.

## OOM 종류와 원인

| 에러 메시지 | 원인 |
|---|---|
| `Java heap space` | heap에 객체를 할당할 공간이 없다 |
| `GC overhead limit exceeded` | GC에 전체 시간의 98% 이상을 쓰면서 heap의 2% 미만만 회수 |
| `Metaspace` | 클래스 메타데이터 공간 부족 (동적 프록시, 리플렉션 과다) |
| `unable to create new native thread` | OS 스레드 생성 한도 초과 |
| `Direct buffer memory` | NIO Direct Buffer 할당 실패 |

## 자주 발생하는 메모리 누수 패턴

### 1. 컬렉션에 넣고 빼지 않는다

```java
// static Map에 계속 추가만 한다
private static final Map<String, Object> cache = new HashMap<>();

public void process(String key, Object value) {
    cache.put(key, value); // 제거 로직이 없으면 계속 쌓인다
}
```

static 컬렉션은 애플리케이션이 살아있는 동안 GC 대상이 되지 않는다. 크기 제한이 없으면 시간이 지날수록 메모리를 잡아먹는다.

대응: 캐시라면 크기 제한 + 만료 정책을 가진 구현체를 사용한다 (Caffeine, Guava Cache 등).

### 2. 리소스를 닫지 않는다

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

DB Connection, HTTP Connection, InputStream 등이 대표적이다.

### 3. 리스너/콜백을 등록하고 해제하지 않는다

```java
// 이벤트 리스너를 등록만 하고 해제하지 않으면
// 리스너가 참조하는 객체도 GC 대상에서 제외된다
eventBus.register(this);
// unregister를 하지 않으면 this가 GC되지 않는다
```

### 4. ThreadLocal을 정리하지 않는다

```java
private static final ThreadLocal<UserContext> context = new ThreadLocal<>();

public void process() {
    context.set(new UserContext(...));
    // 처리 로직
    // context.remove()를 하지 않으면 스레드 풀에서 재사용 시 누수
}
```

스레드 풀 환경에서 `ThreadLocal`을 `remove()`하지 않으면 스레드가 반환되어도 값이 남아있다.

### 5. 큰 객체를 불필요하게 오래 참조한다

```java
public class ReportGenerator {

    private List<ReportData> allData; // 수십만 건

    public void generate() {
        this.allData = fetchAllData(); // 메서드가 끝나도 필드에 남아있다
        // ...
    }
}
```

지역 변수로 충분한 데이터를 필드에 저장하면 객체 생존 시간이 불필요하게 길어진다.

## 실무 분석 절차

### 1. 증상 확인

```bash
# GC 상태 확인
jstat -gc <pid> 1000

# 주요 확인 항목
# - Old Generation 사용률이 계속 올라가는가
# - Full GC가 반복되는가
# - GC 후에도 사용률이 줄지 않는가
```

### 2. Heap Dump 생성

```bash
# 수동 생성
jmap -dump:format=b,file=heap.hprof <pid>

# OOM 발생 시 자동 생성 (운영 환경에서 반드시 설정)
java -XX:+HeapDumpOnOutOfMemoryError \
     -XX:HeapDumpPath=/var/log/app/ \
     -jar app.jar
```

### 3. Heap Dump 분석

Eclipse MAT이나 VisualVM으로 분석한다.

| 확인 항목 | 의미 |
|---|---|
| Dominator Tree | 가장 많은 메모리를 차지하는 객체 트리 |
| Leak Suspects | 도구가 추정하는 누수 후보 |
| Histogram | 클래스별 인스턴스 수와 크기 |
| GC Roots | 특정 객체가 왜 GC되지 않는지 참조 경로 추적 |

## 컨테이너 환경 주의점

```bash
# 잘못된 설정: JVM이 컨테이너 한도를 넘길 수 있다
# 컨테이너 메모리: 2GB
# -Xmx=2g → heap 외 메모리(Metaspace, Stack, Direct Buffer 등)가 추가되어 OOM Kill

# 권장: 컨테이너 한도의 70~80%를 -Xmx로 설정
# 컨테이너 메모리: 2GB
java -Xmx1400m -jar app.jar
```

Java 10+에서는 `-XX:MaxRAMPercentage`를 사용할 수 있다.

```bash
java -XX:MaxRAMPercentage=75.0 -jar app.jar
```

## 자주 나는 실수

- `-XX:+HeapDumpOnOutOfMemoryError`를 설정하지 않아서 OOM 발생 시 분석이 불가능하다.
- heap dump 없이 `-Xmx`만 올려서 누수를 임시로 가린다.
- `ThreadLocal`을 `remove()`하지 않는다.
- static 컬렉션에 크기 제한 없이 데이터를 계속 추가한다.
- 리소스(Connection, Stream)를 try-with-resources 없이 사용한다.
- 컨테이너 메모리 한도와 JVM 메모리 설정의 관계를 고려하지 않는다.

## 핵심 요약

메모리 누수는 더 이상 필요 없는 객체가 GC에 의해 회수되지 않고 heap에 남는 현상입니다.
대표적인 원인으로는 static 컬렉션에 제거 없이 추가만 하는 경우, 리소스를 닫지 않는 경우, ThreadLocal을 remove하지 않는 경우가 있습니다.

누수가 쌓이면 GC가 점점 자주 발생하다가 결국 OOM이 발생합니다.
운영에서는 반드시 `-XX:+HeapDumpOnOutOfMemoryError`를 설정해서 OOM 발생 시 heap dump가 자동 생성되도록 해야 합니다.

분석은 Eclipse MAT으로 Dominator Tree와 GC Roots를 확인해서 어떤 객체가 왜 회수되지 않는지 추적합니다.
컨테이너 환경에서는 JVM 메모리 총합이 컨테이너 한도를 넘지 않도록 `-Xmx`를 한도의 70~80% 이하로 설정해야 합니다.

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

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[gc-and-tuning]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]