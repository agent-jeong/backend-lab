---
title: Class Interface Enum Record
description: Java 타입 선택 기준과 실무에서의 설계 판단
---

# Class Interface Enum Record

## 한 줄 정의

class, interface, enum, record는 Java에서 타입을 정의하는 네 가지 방법이며, 각각 다른 설계 의도를 표현한다.

## 실무에서 왜 중요한가

문법 자체는 쉽지만, 실무에서는 "이 상황에서 어떤 타입을 써야 하는가"를 잘못 판단하면 다음 문제가 생긴다.

- DTO를 class로 만들어서 boilerplate가 넘치고, 불변성이 깨진다.
- 상수를 `static final String`으로 흩뿌려서 타입 안전성이 없다.
- interface와 abstract class를 혼동해서 상속 구조가 꼬인다.
- enum에 로직을 넣을 수 있다는 것을 모르고 if-else 분기를 반복한다.
- record를 Entity에 사용하려다 실패한다.

## 타입별 설계 의도

| 타입 | 설계 의도 | 핵심 특성 |
|---|---|---|
| `class` | 상태와 행위를 가진 객체 | 가변, 상속 가능, 가장 유연 |
| `interface` | 행위의 계약 정의 | 구현 강제, 다중 구현 가능 |
| `enum` | 고정된 상수 집합 | 인스턴스가 정해져 있음, 싱글턴 보장 |
| `record` | 불변 데이터 전달 | 모든 필드 final, equals/hashCode/toString 자동 |

## 실무 선택 기준

### DTO / 응답 객체 → record

```java
// before: class로 DTO를 만들면 boilerplate가 많다
public class UserResponse {
    private final Long id;
    private final String name;
    private final String email;

    public UserResponse(Long id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }

    // getter, equals, hashCode, toString...
}

// after: record로 한 줄
public record UserResponse(Long id, String name, String email) {
}
```

record가 적합한 경우:
- API 응답/요청 DTO
- 메서드 간 데이터 전달 객체
- Map key, 캐시 key 같은 값 객체

record가 적합하지 않은 경우:
- JPA Entity (final class라 프록시 생성 불가, setter 없음)
- 일부 필드만 equals 기준에서 제외해야 하는 경우
- 상속이 필요한 경우

### 고정된 분류 → enum

상태, 유형, 카테고리처럼 값이 정해져 있는 경우 enum을 사용한다.

```java
// 나쁜 예: 문자열 상수
public static final String STATUS_PENDING = "PENDING";
public static final String STATUS_APPROVED = "APPROVED";

public void process(String status) {
    if (status.equals("PENDING")) { ... } // 오타 가능, 타입 안전성 없음
}

// 좋은 예: enum
public enum OrderStatus {
    PENDING, APPROVED, REJECTED, COMPLETED
}

public void process(OrderStatus status) {
    // 컴파일 타임에 잘못된 값 방지
}
```

### enum에 로직 넣기

enum은 단순 상수가 아니라 메서드와 필드를 가질 수 있다. if-else 분기를 줄이는 데 효과적이다.

```java
// before: if-else 분기
public long calculateFee(PaymentType type, long amount) {
    if (type == PaymentType.CARD) {
        return (long) (amount * 0.03);
    } else if (type == PaymentType.BANK_TRANSFER) {
        return 500L;
    } else {
        return 0L;
    }
}

// after: enum에 로직 위임
public enum PaymentType {

    CARD {
        @Override
        public long calculateFee(long amount) {
            return (long) (amount * 0.03);
        }
    },
    BANK_TRANSFER {
        @Override
        public long calculateFee(long amount) {
            return 500L;
        }
    },
    CASH {
        @Override
        public long calculateFee(long amount) {
            return 0L;
        }
    };

    public abstract long calculateFee(long amount);
}
```

새로운 결제 수단이 추가되면 enum 상수를 추가하면서 `calculateFee`를 반드시 구현해야 하므로, 빠뜨리는 실수를 컴파일러가 잡아준다.

### enum + DB 매핑 주의점

JPA에서 enum을 DB에 저장할 때 `@Enumerated`의 기본값은 `ORDINAL`이다.

```java
// 위험: 순서가 바뀌면 DB 값이 달라진다
@Enumerated(EnumType.ORDINAL)
private OrderStatus status; // 0, 1, 2...

// 안전: 이름으로 저장
@Enumerated(EnumType.STRING)
private OrderStatus status; // "PENDING", "APPROVED"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 기존 DB 데이터와 매핑이 깨진다. 반드시 `STRING`을 사용해야 한다.

### 행위 계약 → interface

```java
public interface NotificationSender {
    void send(String to, String message);
}

public class EmailSender implements NotificationSender { ... }
public class SlackSender implements NotificationSender { ... }
```

interface가 적합한 경우:
- 여러 구현체가 존재하거나 존재할 수 있는 경우
- 외부 의존성을 추상화해서 테스트 가능하게 만들 때
- Spring에서 DI 대상으로 사용할 때

### interface vs abstract class

| 기준 | interface | abstract class |
|---|---|---|
| 다중 구현 | 가능 | 불가능 (단일 상속) |
| 상태 (필드) | 없음 (상수만) | 가질 수 있음 |
| 생성자 | 없음 | 있음 |
| 사용 시점 | "무엇을 할 수 있는가" 정의 | "무엇인가" + 공통 구현 제공 |

실무에서는 interface를 우선하고, 공통 상태나 구현이 필요한 경우에만 abstract class를 사용한다. Spring 환경에서는 거의 대부분 interface로 충분하다.

### class는 언제?

위 세 가지(record, enum, interface)로 해결되지 않을 때 class를 사용한다.

- 가변 상태와 행위를 함께 가지는 도메인 객체
- JPA Entity
- 상속 구조가 필요한 경우
- 빌더 패턴 등 복잡한 생성 로직이 필요한 경우

## 실무 판단 요약

| 상황 | 선택 |
|---|---|
| API 요청/응답 DTO | `record` |
| 메서드 간 데이터 전달 | `record` |
| 고정된 상태, 유형, 카테고리 | `enum` |
| 상수별로 다른 로직이 필요 | `enum` + 추상 메서드 |
| 구현체 교체, DI, 테스트 추상화 | `interface` |
| JPA Entity | `class` |
| 가변 상태 + 행위를 가진 도메인 객체 | `class` |
| 공통 구현 + 상태 공유가 필요한 상속 | `abstract class` |

## 자주 나는 실수

- DTO를 class로 만들어서 getter, equals, hashCode를 수동으로 관리한다.
- `@Enumerated`를 `ORDINAL`로 사용해서 enum 순서 변경 시 DB 데이터가 깨진다.
- interface 하나에 구현체가 하나인데 불필요하게 추상화한다.
- enum을 단순 상수로만 쓰고, 분기 로직을 호출부에 if-else로 작성한다.
- record를 JPA Entity로 사용하려다 프록시 생성 실패가 발생한다.
- abstract class를 남용해서 상속 계층이 깊어지고 변경이 어려워진다.

## 핵심 요약

Java에서 타입을 정의할 때는 용도에 따라 적절한 종류를 선택해야 합니다.

데이터 전달이 목적이면 record가 불변성과 equals/hashCode를 자동으로 보장해서 DTO에 적합합니다.
고정된 상수 집합은 enum을 사용하고, 상수별로 다른 로직이 필요하면 enum에 추상 메서드를 넣어서 if-else 분기를 제거할 수 있습니다.

행위의 계약을 정의할 때는 interface를 사용하며, Spring 환경에서 DI와 테스트 추상화에 주로 활용됩니다.
class는 JPA Entity처럼 가변 상태와 행위를 함께 가지는 경우에 사용합니다.

주의할 점으로 enum을 JPA에서 사용할 때 `@Enumerated(STRING)`을 써야 순서 변경에 안전하고, record는 final class이므로 JPA Entity로는 사용할 수 없습니다.

## 꼬리 질문

> [!question]- record를 JPA Entity로 사용할 수 없는 이유는?
> record는 final class라 프록시 생성이 불가능하고, setter가 없어 필드 변경이 안 되며, 기본 생성자도 없어서 JPA 스펙을 충족하지 못합니다.

> [!question]- enum에 로직을 넣으면 어떤 장점이 있는가?
> 호출부의 if-else 분기를 제거할 수 있고, 새 상수 추가 시 추상 메서드 구현을 컴파일러가 강제해서 누락 실수를 방지합니다.

> [!question]- `@Enumerated(ORDINAL)`이 위험한 이유는?
> enum 상수의 선언 순서(0, 1, 2...)로 저장되기 때문에, 중간에 상수를 추가하거나 순서를 바꾸면 기존 DB 데이터와 매핑이 깨집니다.

> [!question]- interface와 abstract class를 선택하는 기준은?
> 다중 구현이 필요하거나 행위 계약만 정의하면 interface, 공통 상태나 구현을 자식에게 제공해야 하면 abstract class를 사용합니다.

> [!question]- sealed class는 이 네 가지와 어떤 관계가 있는가?
> sealed class는 상속 가능한 하위 타입을 `permits`로 제한합니다. interface나 abstract class에 적용해서 타입 안전한 계층 구조를 만들 수 있습니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[java-version-features]]
- [[01-core/jpa/jpa|jpa]]