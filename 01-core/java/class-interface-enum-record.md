---
title: Class Interface Enum Record
description: Java 타입 선택 기준과 실무 설계 판단
---

# Class Interface Enum Record

## 한 줄 정의

`class`, `interface`, `enum`, `record`는 Java에서 타입을 정의하는 대표적인 방법이며, 각각 다른 설계 의도를 표현한다.

## 실무에서 왜 중요한가

문법 자체보다 중요한 것은 "이 타입이 무엇을 표현하는가"이다. 타입 선택을 잘못하면 다음 문제가 생긴다.

- DTO를 `class`로 만들어 getter, 생성자, `equals`, `hashCode`를 반복 작성한다.
- 값 전달 객체가 가변 객체가 되어 의도치 않은 변경이 발생한다.
- 상수를 `static final String`으로 흩뿌려 오타와 잘못된 값이 런타임까지 숨어 있다.
- interface와 abstract class를 혼동해서 상속 구조가 꼬인다.
- enum에 로직을 넣을 수 있다는 것을 모르고 호출부마다 if-else 분기를 반복한다.
- record를 JPA Entity처럼 생명주기가 있는 객체에 사용하려다 실패한다.

## 타입별 설계 의도

| 타입 | 설계 의도 | 핵심 질문 |
|---|---|---|
| `class` | 상태와 행위를 가진 객체 | 이 객체는 식별자, 생명주기, 변경 가능한 상태를 가지는가? |
| `interface` | 행위의 계약 | 구현체를 교체하거나 테스트에서 대체해야 하는가? |
| `enum` | 고정된 선택지 | 가능한 값의 집합이 코드 수준에서 닫혀 있는가? |
| `record` | 불변 데이터 묶음 | 데이터를 전달하거나 비교하는 것이 주 목적에 가까운가? |

## 실무 선택 기준

### 빠른 판단 흐름

1. 가능한 값이 정해진 상태, 유형, 분류인가? → `enum`
2. 데이터 전달이 목적이고 불변이어도 되는가? → `record`
3. 여러 구현체를 같은 계약으로 다뤄야 하는가? → `interface`
4. 식별자, 생명주기, 가변 상태, 도메인 행위가 필요한가? → `class`
5. 공통 상태와 구현을 하위 타입에 제공해야 하는가? → `abstract class`

### DTO / 값 전달 객체 → record

```java
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
- 좌표, 기간, 금액 범위처럼 값 자체가 의미를 가지는 작은 객체

record가 적합하지 않은 경우:

- JPA Entity
- 내부 필드를 단계적으로 변경해야 하는 객체
- 일부 필드만 equals 기준에서 제외해야 하는 경우
- 상속이 필요한 경우
- 필드에 mutable 객체가 들어가고 외부 변경을 막아야 하는 경우

record는 얕은 불변이다. 컴포넌트 참조는 final이지만, 참조 대상이 mutable이면 내부 값은 바뀔 수 있다.

```java
public record UserGroup(List<String> names) {
    public UserGroup {
        names = List.copyOf(names);
    }
}
```

위처럼 compact constructor에서 방어적 복사를 하면 외부에서 넘긴 리스트 변경이 record 내부 상태에 영향을 주지 않는다.

### 고정된 분류와 상태 → enum

상태, 유형, 카테고리처럼 값이 정해져 있는 경우 enum을 사용한다.

```java
public static final String STATUS_PENDING = "PENDING";
public static final String STATUS_APPROVED = "APPROVED";

public void process(String status) {
    if (status.equals("PENDING")) {
        // ...
    }
}

public enum OrderStatus {
    PENDING, APPROVED, REJECTED, COMPLETED
}

public void process(OrderStatus status) {
    // 컴파일 타임에 잘못된 값 방지
}
```

문자열 상수는 `"PENDNG"` 같은 오타도 컴파일된다. enum은 허용 가능한 값을 타입으로 제한하기 때문에 잘못된 값이 훨씬 빨리 드러난다.

### enum에 로직 넣기

enum은 단순 상수가 아니라 메서드와 필드를 가질 수 있다. if-else 분기를 줄이는 데 효과적이다.

```java
public long calculateFee(PaymentType type, long amount) {
    if (type == PaymentType.CARD) {
        return (long) (amount * 0.03);
    } else if (type == PaymentType.BANK_TRANSFER) {
        return 500L;
    } else {
        return 0L;
    }
}

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

새로운 결제 수단이 추가되면 enum 상수를 추가하면서 `calculateFee`를 반드시 구현해야 하므로, 누락을 컴파일러가 잡아준다. 단, enum에 너무 많은 비즈니스 흐름을 넣으면 상수가 도메인 서비스처럼 비대해질 수 있다. 상수별 작은 정책 차이를 표현할 때 적합하다.

### enum + DB 매핑 주의점

JPA에서 enum을 DB에 저장할 때 `@Enumerated`의 기본값은 `ORDINAL`이다. 실무에서는 대부분 `STRING`을 명시한다.

```java
@Enumerated(EnumType.ORDINAL)
private OrderStatus status; // 0, 1, 2...

@Enumerated(EnumType.STRING)
private OrderStatus status; // "PENDING", "APPROVED"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 기존 DB 데이터와 매핑이 깨진다. `STRING`은 순서 변경에는 안전하지만 enum 이름을 바꾸면 DB 값과 매핑이 깨질 수 있다.

DB에 저장되는 코드가 오래 유지되어야 하거나 외부 시스템과 계약된 값이면 enum 이름을 그대로 저장하기보다 별도 code 필드와 converter를 두는 편이 낫다.

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
- 포트/어댑터 구조에서 애플리케이션 코드가 외부 기술에 직접 의존하지 않게 할 때

단, 구현체가 하나뿐이고 교체 가능성도 낮다면 무조건 interface를 만들 필요는 없다. 테스트 가능성, 의존 방향, 확장 가능성이 실제로 필요할 때 사용한다.

### interface vs abstract class

| 기준 | interface | abstract class |
|---|---|---|
| 다중 구현 | 가능 | 불가능 (단일 상속) |
| 상태 (필드) | 없음 (상수만) | 가질 수 있음 |
| 생성자 | 없음 | 있음 |
| 사용 시점 | "무엇을 할 수 있는가" 정의 | "무엇인가" + 공통 구현 제공 |

실무에서는 interface를 우선 검토하고, 공통 상태나 템플릿 메서드처럼 하위 클래스가 공유해야 하는 구현이 있을 때만 abstract class를 사용한다.

### class는 언제?

class는 가장 일반적인 타입이지만, 실무에서는 특히 식별자와 생명주기, 변경 가능한 상태, 도메인 행위를 함께 표현할 때 적합하다.

- 가변 상태와 행위를 함께 가지는 도메인 객체
- JPA Entity
- 상속 구조가 필요한 경우
- 빌더 패턴 등 복잡한 생성 로직이 필요한 경우
- 캡슐화된 상태 변경 메서드가 필요한 경우

```java
public class Order {
    private Long id;
    private OrderStatus status;

    public void approve() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Only pending orders can be approved.");
        }
        this.status = OrderStatus.APPROVED;
    }
}
```

이런 객체는 단순 데이터 묶음이 아니라 상태 전이 규칙을 가진다. 이 경우 record보다 class가 더 자연스럽다.

### record를 JPA Entity로 쓰기 어려운 이유

JPA Entity는 보통 다음 조건을 필요로 한다.

- 기본 생성자
- final이 아닌 클래스
- final이 아닌 영속 필드
- 프록시 생성을 위한 상속 가능성
- 영속성 컨텍스트 안에서 상태 변경 가능성

record는 final class이고, 컴포넌트가 final이며, canonical constructor 중심으로 동작한다. 그래서 Entity보다는 DTO, projection, 값 전달 객체에 적합하다.

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
| DB에 장기 저장되는 상태 코드 | `enum` + stable code/converter |

## 자주 나는 실수

- DTO를 class로 만들어서 getter, equals, hashCode를 수동으로 관리한다.
- `@Enumerated(ORDINAL)`을 사용해서 enum 순서 변경 시 DB 데이터가 깨진다.
- `@Enumerated(STRING)`이면 완전히 안전하다고 생각하고 enum 이름을 쉽게 변경한다.
- interface 하나에 구현체가 하나인데 불필요하게 추상화한다.
- enum을 단순 상수로만 쓰고, 분기 로직을 호출부에 if-else로 작성한다.
- record를 JPA Entity로 사용하려다 프록시 생성 실패가 발생한다.
- record 안에 mutable collection을 그대로 보관해서 불변이라고 착각한다.
- abstract class를 남용해서 상속 계층이 깊어지고 변경이 어려워진다.

## 핵심 요약

Java에서 타입을 정의할 때는 먼저 표현하려는 의도를 정해야 한다.

데이터 전달이 목적이면 record가 불변성과 `equals`/`hashCode`/`toString` 자동 생성을 제공하므로 DTO에 적합하다. 다만 record는 얕은 불변이므로 mutable 필드를 받을 때는 방어적 복사를 고려해야 한다.

고정된 상수 집합은 enum을 사용하고, 상수별로 다른 작은 정책이 필요하면 enum에 메서드를 둘 수 있다. JPA에 저장할 때는 `ORDINAL`을 피하고, 이름 변경 가능성이 있거나 외부 계약 값이면 stable code와 converter를 고려한다.

행위의 계약을 정의할 때는 interface를 사용한다. class는 JPA Entity처럼 식별자, 생명주기, 가변 상태, 도메인 행위를 함께 가지는 객체에 적합하다.

## 꼬리 질문

> [!question]- record를 JPA Entity로 사용할 수 없는 이유는?
> record는 final class이고, 컴포넌트가 final이며, 기본 생성자와 상태 변경 구조가 JPA Entity 요구사항과 맞지 않습니다. JPA 프록시 생성에도 불리하므로 Entity보다는 DTO나 projection에 적합합니다.

> [!question]- enum에 로직을 넣으면 어떤 장점이 있는가?
> 호출부의 if-else 분기를 줄일 수 있고, 새 상수 추가 시 추상 메서드 구현을 컴파일러가 강제해서 누락 실수를 방지합니다. 다만 큰 비즈니스 흐름은 서비스나 정책 객체로 분리하는 것이 낫습니다.

> [!question]- `@Enumerated(ORDINAL)`이 위험한 이유는?
> enum 상수의 선언 순서(0, 1, 2...)로 저장되기 때문에, 중간에 상수를 추가하거나 순서를 바꾸면 기존 DB 데이터와 매핑이 깨집니다.

> [!question]- `@Enumerated(STRING)`이면 항상 안전한가?
> 순서 변경에는 안전하지만 enum 이름 변경에는 취약합니다. 장기 저장 값이나 외부 시스템과 계약된 값은 별도 code 필드와 converter를 고려해야 합니다.

> [!question]- interface와 abstract class를 선택하는 기준은?
> 다중 구현이 필요하거나 행위 계약만 정의하면 interface, 공통 상태나 구현을 자식에게 제공해야 하면 abstract class를 사용합니다.

> [!question]- sealed class는 이 네 가지와 어떤 관계가 있는가?
> sealed class는 상속 가능한 하위 타입을 `permits`로 제한합니다. interface나 abstract class에 적용해서 타입 안전한 계층 구조를 만들 수 있습니다.

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[java-version-features]]
- [[01-core/jpa/jpa|jpa]]