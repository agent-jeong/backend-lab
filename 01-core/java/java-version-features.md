---
title: Java 버전별 핵심 변화
description: Java 8부터 21, 25까지 실무 코드를 바꾼 기능과 버전을 올릴 때 볼 것
tags: [concept, java]
---

# Java 버전별 핵심 변화

Java 8부터 21(그리고 25)까지, 실무 코드를 실제로 바꾼 기능만 골라 모았다. 기능 목록을 외우기보다, 각 기능 덕분에 어떤 코드가 더 안전하고 읽기 쉬워졌는지로 본다.

이 정리가 필요한 때는 팀에서 Java 버전을 올리면서 새 기능 중 무엇을 쓸지 정할 때, 오래된 코드를 새 기능으로 고치면서 얻는 것과 위험을 따져 볼 때다. 특히 Java 21의 virtual thread는 요청을 스레드에 어떻게 나눠 맡길지부터 바꾸기 때문에, 서버 구조를 정할 때도 영향을 준다.

## Java 8: 지금 Java 코드의 출발점

| 기능 | 실무 의미 |
|---|---|
| Lambda | 콜백, 이벤트 핸들러, 정렬 기준 등을 짧게 작성 |
| Stream API | 컬렉션 처리를 선언적으로 표현 |
| Optional | null 반환 대신 값의 부재를 명시 |
| `LocalDate`, `LocalDateTime` | `Date`, `Calendar`의 혼란을 해결 |
| default method | 인터페이스를 확장해도 기존 구현체가 깨지지 않음 |

대부분의 프로젝트가 이미 매일 쓰는 기능이다.

## Java 11 (LTS): 모듈 시스템 이후 첫 LTS

| 기능 | 실무 의미 |
|---|---|
| `var` (Java 10) | 지역 변수 타입 추론, 남용하면 읽기 어려워짐 |
| `HttpClient` | 외부 HTTP 호출에 별도 라이브러리가 필요 없음 |
| `String` 메서드 추가 | `isBlank()`, `strip()`, `lines()` 등 유틸리티 |
| 불변 컬렉션 팩토리 (Java 9~10) | `List.of()`, `Map.of()`, `List.copyOf()`로 불변 컬렉션 생성 |

`var`는 타입이 오른쪽에서 바로 보일 때만 쓴다.

```java
// 좋은 예 - 오른쪽에서 타입이 보인다
var users = new ArrayList<User>();
var response = restTemplate.getForObject(url, UserResponse.class);

// 나쁜 예 - 타입을 추론하기 어렵다
var result = process(data);
var value = getConfig();
```

## Java 17 (LTS)

| 기능 | 실무 의미 |
|---|---|
| `record` (Java 16) | 불변 데이터 전달 객체를 한 줄로 정의 |
| `sealed class` | 상속 범위를 제한해 타입 안전성 확보 |
| pattern matching `instanceof` | 캐스팅 코드 제거 |
| text block | 여러 줄 문자열 (SQL, JSON 템플릿) |
| `switch` expression | 값을 반환하는 switch |
| `Stream.toList()` (Java 16) | `collect(Collectors.toList())` 대신 쓰는 불변 리스트 반환 |

### record

```java
// DTO로 적합
public record UserResponse(Long id, String name, String email) {
}

// 주의: JPA Entity로 사용 불가 (final class, setter 없음)
```

record는 모든 필드가 `equals/hashCode` 기준에 들어간다. 특정 필드를 빼려면 직접 구현한다.

### sealed class

```java
public sealed interface PaymentResult
    permits PaymentSuccess, PaymentFailure, PaymentPending {
}

public record PaymentSuccess(String transactionId) implements PaymentResult {}
public record PaymentFailure(String reason) implements PaymentResult {}
public record PaymentPending(String redirectUrl) implements PaymentResult {}
```

올 수 있는 하위 타입을 컴파일할 때 정해 둔다. Java 21의 pattern matching switch와 같이 쓰면, 하위 타입을 하나 빠뜨렸을 때 `default` 없이도 컴파일 에러가 난다. 그래서 새 결제 상태를 추가하면, 그 상태를 처리하지 않은 switch를 컴파일러가 전부 찾아 준다.

## Java 21: Virtual Thread

| 기능 | 실무 의미 |
|---|---|
| Virtual Thread | OS 스레드 1:1 매핑에서 벗어나 경량 스레드로 동시성 확장 |
| `switch` pattern matching | 타입별 분기를 안전하게 처리 |
| sequenced collections | `getFirst()`, `getLast()` 등 순서 기반 접근 표준화 |

### Virtual Thread가 바꾸는 것

기존 스레드는 OS 스레드 하나에 하나씩 대응돼서 수천 개 넘게 만들기 어렵다. Virtual Thread는 JVM이 관리하는 가벼운 스레드라서 수만 개를 동시에 돌릴 수 있다.

```java
// 기존: 스레드 풀 크기가 동시 처리량의 한계
ExecutorService executor = Executors.newFixedThreadPool(200);

// Virtual Thread: 요청당 스레드를 만들어도 부담이 적다
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
```

도입하기 전에 알아 둘 것이 있다.

- I/O를 기다리는 시간이 긴 작업에서만 이득이 있다. CPU를 계속 쓰는 작업은 빨라지지 않는다.
- pinning은 버전마다 다르다. Java 21~23에서는 `synchronized` 블록 안에서 blocking I/O를 하면 carrier thread가 고정(pinning)된다. Java 24(JEP 491)부터 `synchronized`로 인한 pinning은 해소됐다. native 메서드 호출 중 blocking은 여전히 pinning된다.
- 외부 자원의 한도는 그대로다. 스레드가 1만 개여도 DB 커넥션이 20개면 나머지는 커넥션 풀에서 기다린다.
- `ThreadLocal`이 메모리를 잡아먹는다. virtual thread가 많은 만큼 복사본도 많아진다.
- Spring Boot 3.2+에서는 설정 한 줄로 켠다.

```yaml
# application.yml
spring:
  threads:
    virtual:
      enabled: true
```

## 어느 버전으로 가나

| 상황 | 권장 |
|---|---|
| 신규 프로젝트 | Java 21 또는 25 (2025년 9월 LTS) |
| 기존 운영 중인 프로젝트 | Java 17 이상으로 점진적 마이그레이션 |
| Java 8에 묶여 있는 프로젝트 | 라이브러리 호환성 확인 후 17로 먼저 올리기 |
| Virtual Thread 도입 | I/O 바운드 서비스에서 Java 21 + Spring Boot 3.2+ |

## 한 번에 설명하기

> 지금 Java 코드는 대부분 Java 8의 Lambda, Stream, Optional 위에 서 있습니다. Java 17에서는 record와 sealed class 덕분에 불변 객체와 하위 타입 제한을 짧게 쓸 수 있게 됐습니다.
>
> 가장 큰 변화는 Java 21의 virtual thread입니다. OS 스레드에 하나씩 대응하던 방식에서 JVM이 관리하는 가벼운 스레드로 바뀌어, I/O를 많이 기다리는 서비스가 적은 자원으로 수만 개의 동시 요청을 처리할 수 있습니다. 다만 CPU를 많이 쓰는 작업에는 이득이 없고, synchronized pinning과 ThreadLocal은 따로 확인합니다.
>
> 새 프로젝트는 Java 21 이상(최신 LTS는 25), 기존 프로젝트는 17 이상을 기준으로 올립니다.

## 꼬리 질문

> [!question]- virtual thread와 platform thread는 뭐가 다른가?
> platform thread는 OS 스레드 하나에 하나씩 대응해서 만드는 비용이 큽니다. virtual thread는 JVM이 관리하는 가벼운 스레드라서 수만 개를 만들어도 부담이 적습니다.

> [!question]- virtual thread에서 pinning은 언제 생기나?
> Java 21~23에서는 `synchronized` 블록 안에서 blocking I/O를 하면 carrier thread가 묶여 버립니다(pinning). 이 버전에서는 `ReentrantLock`으로 바꿔서 피합니다. Java 24(JEP 491)부터는 `synchronized` 때문에 생기는 pinning은 없어졌고, native 호출 중에 blocking되는 경우 정도만 남았습니다. 실제로 생기는지는 JFR `jdk.VirtualThreadPinned` 이벤트로 봅니다.

> [!question]- record를 JPA Entity로 못 쓰는 이유는?
> record는 final class라서 JPA가 프록시를 만들 수 없고, 필드가 전부 final이라 JPA가 빈 객체를 만든 뒤 값을 채워 넣을 수 없습니다. 인자 없는 생성자를 따로 선언할 수는 있지만 결국 다른 생성자를 불러 모든 필드를 정해야 해서, JPA가 쓰는 방식과 맞지 않습니다.

> [!question]- sealed class는 어떤 문제를 풀어 주나?
> 상속할 수 있는 하위 타입을 컴파일할 때 정해 둡니다. Java 21 pattern matching switch와 같이 쓰면 빠뜨린 케이스가 컴파일 에러가 되니까, 타입을 새로 추가했을 때 처리를 빠뜨리지 않습니다.

> [!question]- var를 아무 데나 쓰면 어떤 문제가 생기나?
> 오른쪽만 봐서는 타입을 알 수 없을 때 코드를 읽기 어려워집니다. `var result = process(data)`처럼 무슨 타입인지 짐작이 안 가는 경우가 문제입니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Virtual Thread 도입 시 가장 먼저 확인해야 할 작업 특성은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="blocking I/O가 많은 요청 처리에서는 이점이 크지만 CPU 바운드 작업의 성능을 마법처럼 높이지는 않는다." aria-pressed="false">A. blocking I/O 중심인지 CPU 바운드인지 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Virtual Thread가 DB 커넥션 같은 외부 리소스 한도를 없애지는 않는다." aria-pressed="false">B. DB 커넥션 풀 크기를 무시해도 되는지 확인한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문법보다 실행 모델과 blocking 여부가 달라진다." aria-pressed="false">C. var를 더 많이 쓸 수 있는지 확인한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>sealed class는 허용된 하위 타입을 제한해 도메인 상태 모델을 명확하게 만들 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="확장 가능한 타입 집합을 제한하면 switch 처리와 상태 모델링에서 누락을 줄일 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="sealed는 상속을 완전히 금지하는 것이 아니라 허용 대상을 제한한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>var를 사용할 때 실무에서 주의할 점은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="우변만 봐도 타입과 의도가 명확한 경우에 제한적으로 써야 가독성을 해치지 않는다." aria-pressed="false">A. 타입 추론이 의도를 흐리면 명시 타입을 사용한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="var는 동적 타입이 아니라 컴파일 타임 타입 추론이다." aria-pressed="false">B. 런타임에 타입이 자유롭게 바뀐다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="var 사용 여부가 null safety를 자동 보장하지 않는다." aria-pressed="false">C. null 관련 버그를 자동으로 제거한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [JDK Release Notes (OpenJDK projects)](https://openjdk.org/projects/jdk/)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- [JEP 491: Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491)

## 관련 문서

- [[01-core/java/java|java]]
- [[stream-and-optional]]
- [[equals-and-hashcode]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]