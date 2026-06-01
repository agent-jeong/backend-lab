---
title: Java Version Features
description: Java 버전별 핵심 변화와 실무 적용 판단
---

# Java Version Features

## 한 줄 정의

Java 8부터 21까지의 주요 기능 변화를 실무 관점에서 정리한 문서다.

## 실무에서 왜 중요한가

면접에서 버전별 기능을 나열하는 것은 쉽지만, 실무에서 중요한 것은 "이 기능이 어떤 코드를 더 안전하고 읽기 쉽게 만드는가"다.

- 팀에서 Java 버전을 올릴 때 어떤 기능을 적용할지 판단해야 한다.
- 레거시 코드에서 최신 기능으로 리팩토링할 때 이점과 리스크를 알아야 한다.
- Java 21의 virtual thread는 동시성 모델 자체를 바꿀 수 있어 아키텍처에 영향을 준다.

## Java 8 - 실무 기반이 된 버전

Java 8은 사실상 현대 Java 코드의 기준이다.

| 기능 | 실무 의미 |
|---|---|
| Lambda | 콜백, 이벤트 핸들러, 정렬 기준 등을 간결하게 작성 |
| Stream API | 컬렉션 처리를 선언적으로 표현 |
| Optional | null 반환 대신 값의 부재를 명시 |
| `LocalDate`, `LocalDateTime` | `Date`, `Calendar`의 혼란을 해결 |
| default method | 인터페이스 확장 시 기존 구현체 호환 유지 |

대부분의 프로젝트에서 이 기능들은 이미 일상적으로 사용된다.

## Java 11 - 첫 번째 실무 LTS

| 기능 | 실무 의미 |
|---|---|
| `var` (Java 10) | 지역 변수 타입 추론, 과도한 사용 시 가독성 저하 |
| `HttpClient` | 외부 HTTP 호출 시 별도 라이브러리 없이 가능 |
| `String` 메서드 추가 | `isBlank()`, `strip()`, `lines()` 등 유틸리티 |
| `toList()` 불변 리스트 | `List.of()`, `List.copyOf()`로 불변 컬렉션 생성 |

`var` 사용 기준: 타입이 오른쪽에서 명확히 보이는 경우에만 사용한다.

```java
// 좋은 예 - 오른쪽에서 타입이 보인다
var users = new ArrayList<User>();
var response = restTemplate.getForObject(url, UserResponse.class);

// 나쁜 예 - 타입을 추론하기 어렵다
var result = process(data);
var value = getConfig();
```

## Java 17 - 두 번째 실무 LTS

| 기능 | 실무 의미 |
|---|---|
| `record` (Java 16) | 불변 데이터 전달 객체를 한 줄로 정의 |
| `sealed class` | 상속 범위를 제한해서 타입 안전성 확보 |
| pattern matching `instanceof` | 캐스팅 코드 제거 |
| text block | 여러 줄 문자열 (SQL, JSON 템플릿) |
| `switch` expression | 값을 반환하는 switch |

### record 실무 적용

```java
// DTO로 적합
public record UserResponse(Long id, String name, String email) {
}

// 주의: JPA Entity로 사용 불가 (final class, setter 없음)
```

record는 모든 필드가 `equals/hashCode` 기준에 포함된다. 특정 필드만 제외하고 싶은 경우에는 직접 구현해야 한다.

### sealed class 실무 적용

```java
public sealed interface PaymentResult
    permits PaymentSuccess, PaymentFailure, PaymentPending {
}

public record PaymentSuccess(String transactionId) implements PaymentResult {}
public record PaymentFailure(String reason) implements PaymentResult {}
public record PaymentPending(String redirectUrl) implements PaymentResult {}
```

가능한 하위 타입을 컴파일 타임에 제한할 수 있어, switch에서 빠진 케이스를 컴파일러가 경고해준다.

## Java 21 - Virtual Thread와 동시성 전환

| 기능 | 실무 의미 |
|---|---|
| Virtual Thread | OS 스레드 1:1 매핑 탈피, 경량 스레드로 동시성 확장 |
| `switch` pattern matching | 타입별 분기를 안전하게 처리 |
| sequenced collections | `getFirst()`, `getLast()` 등 순서 기반 접근 표준화 |

### Virtual Thread가 바꾸는 것

기존 Java의 스레드는 OS 스레드와 1:1로 매핑되어 수천 개 이상 생성이 어렵다. Virtual Thread는 JVM이 관리하는 경량 스레드로, 수만 개를 동시에 실행할 수 있다.

```java
// 기존: 스레드 풀 크기가 동시 처리량의 한계
ExecutorService executor = Executors.newFixedThreadPool(200);

// Virtual Thread: 요청당 스레드를 만들어도 부담이 적다
ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
```

실무에서 주의할 점:

- CPU 바운드 작업에서는 이점이 없다. I/O 바운드에서 효과적이다.
- `synchronized` 블록 안에서 blocking I/O를 하면 carrier thread가 고정(pinning)된다.
- `ThreadLocal` 사용 시 메모리 문제가 생길 수 있다 (virtual thread 수가 많으므로).
- Spring Boot 3.2+에서는 설정 한 줄로 활성화 가능하다.

```yaml
# application.yml
spring:
  threads:
    virtual:
      enabled: true
```

## 버전 선택 실무 기준

| 판단 기준 | 권장 |
|---|---|
| 신규 프로젝트 | Java 21 (최신 LTS) |
| 기존 운영 중인 프로젝트 | Java 17 이상으로 점진적 마이그레이션 |
| Java 8에 묶여 있는 프로젝트 | 라이브러리 호환성 확인 후 17로 먼저 올리기 |
| Virtual Thread 도입 | I/O 바운드 서비스에서 Java 21 + Spring Boot 3.2+ |

## 핵심 요약

Java 8은 Lambda, Stream, Optional으로 현대 Java의 기반을 만들었고, Java 17은 record와 sealed class로 타입 안전성과 불변 객체 생성을 편리하게 했습니다.

가장 큰 변화는 Java 21의 virtual thread인데, OS 스레드와 1:1 매핑이던 기존 모델에서 JVM이 관리하는 경량 스레드로 전환되어, I/O 바운드 서비스에서 수만 개의 동시 요청을 적은 리소스로 처리할 수 있게 되었습니다.
다만 CPU 바운드 작업에서는 이점이 없고, synchronized 블록이나 ThreadLocal 사용 시 주의가 필요합니다.

실무에서는 새 프로젝트는 Java 21, 기존 프로젝트는 17 이상으로 올리는 것을 기준으로 판단합니다.

## 꼬리 질문

> [!question]- virtual thread와 platform thread의 차이는?
> platform thread는 OS 스레드와 1:1 매핑되어 생성 비용이 큽니다. virtual thread는 JVM이 관리하는 경량 스레드로 수만 개를 생성해도 부담이 적습니다.

> [!question]- virtual thread에서 pinning이 발생하는 상황은?
> `synchronized` 블록 안에서 blocking I/O를 수행하면 carrier thread가 고정(pinning)됩니다. `ReentrantLock`으로 대체하면 해결됩니다.

> [!question]- record를 JPA Entity로 사용할 수 없는 이유는?
> record는 final class라 JPA가 프록시를 생성할 수 없고, setter가 없어 필드 값 변경이 불가능하며, 기본 생성자도 없습니다.

> [!question]- sealed class는 어떤 설계 문제를 해결하는가?
> 상속 가능한 하위 타입을 컴파일 타임에 제한합니다. switch에서 빠진 케이스를 컴파일러가 경고해주어 타입 안전성이 높아집니다.

> [!question]- var를 남용하면 어떤 문제가 생기는가?
> 타입이 오른쪽에서 명확히 보이지 않는 경우 코드 가독성이 떨어집니다. `var result = process(data)`처럼 타입 추론이 어려운 경우가 문제입니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[stream-and-optional]]
- [[equals-and-hashcode]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]