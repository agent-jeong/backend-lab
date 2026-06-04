---
title: Class Interface Enum Record
description: Java 타입 선택 기준과 실무 설계 판단
---

# Class Interface Enum Record

## 한 줄 정의

`class`, `interface`, `enum`, `record`는 Java에서 타입을 정의하는 대표적인 방법이며, 각각 다른 설계 의도를 표현한다.

## 실무에서 왜 중요한가

문법 자체보다 중요한 것은 "이 타입이 무엇을 표현하는가"이다.

타입 선택이 어긋나면 DTO에 boilerplate가 늘어나고, 문자열 상수 오타가 런타임까지 숨어 있으며, Entity처럼 생명주기가 있는 객체를 record로 만들려다 실패한다.

## 한눈에 보는 선택 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 데이터 전달이 목적 | `record` | 필드, 생성자, `equals`, `hashCode`, `toString`을 간결하게 표현 |
| 고정된 상태/유형/분류 | `enum` | 허용 가능한 값을 타입으로 제한 |
| 여러 구현체를 같은 방식으로 사용 | `interface` | 구현체 교체, 테스트 대체, DI에 유리 |
| 식별자와 변경 가능한 상태가 있음 | `class` | Entity, 도메인 객체처럼 생명주기와 행위를 표현 |
| 공통 상태와 구현을 상속해야 함 | `abstract class` | 하위 클래스에 공통 로직 제공 |

먼저 `enum`과 `record`로 표현할 수 있는지 확인하고, 생명주기와 상태 변경이 필요하면 `class`를 선택한다. `interface`는 구현체 교체나 의존성 분리가 실제로 필요할 때 사용한다.

### DTO / 값 전달 객체 → record

DTO처럼 데이터를 옮기는 객체는 `record`가 읽기 쉽다.

```java
public record UserResponse(
    Long id,
    String name,
    String email
) {
}
```

주의할 점은 record가 얕은 불변이라는 것이다. `List` 같은 mutable 객체를 받으면 방어적 복사를 고려한다.

```java
public record UserGroup(List<String> names) {
    public UserGroup {
        names = List.copyOf(names);
    }
}
```

적합한 곳: API 요청/응답 DTO, 메서드 간 데이터 전달 객체, 캐시 key, 작은 값 객체.

피해야 할 곳: JPA Entity, 단계적으로 상태가 바뀌는 객체, 상속이 필요한 객체.

### 고정된 분류와 상태 → enum

상태, 유형, 카테고리처럼 값이 정해져 있는 경우 enum을 사용한다.

문자열 상수는 허용 가능한 값의 범위를 타입으로 표현하지 못한다.

```java
process("PENDNG"); // 오타가 있어도 컴파일된다.
```

enum을 사용하면 잘못된 값이 컴파일 단계에서 드러난다.

```java
public enum OrderStatus {
    PENDING,
    APPROVED,
    REJECTED
}

public void process(OrderStatus status) {
    if (status == OrderStatus.PENDING) {
        approve();
    }
}

process(OrderStatus.PENDNG); // 컴파일 에러: 존재하지 않는 enum 상수
```

### enum에 로직 넣기

상수별 작은 정책 차이가 있으면 enum 내부에 로직을 둘 수 있다. 호출부의 if-else를 줄이는 데 도움이 된다.

```java
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

새 결제 수단을 추가하면 `calculateFee` 구현을 컴파일러가 강제한다. 다만 큰 비즈니스 흐름은 enum이 아니라 서비스나 정책 객체로 분리하는 편이 낫다.

### enum + DB 매핑 주의점

JPA에서 enum을 DB에 저장할 때 `@Enumerated`의 기본값은 `ORDINAL`이다. 실무에서는 대부분 `STRING`을 명시한다.

```java
// 위험: enum 선언 순서가 DB 값이 된다.
@Enumerated(EnumType.ORDINAL)
private OrderStatus status; // 0, 1, 2...

// 일반적으로 더 안전: enum 이름이 DB 값이 된다.
@Enumerated(EnumType.STRING)
private OrderStatus status; // "PENDING", "APPROVED"...
```

`ORDINAL`은 enum 상수의 선언 순서가 바뀌면 기존 DB 데이터와 매핑이 깨진다. `STRING`은 순서 변경에는 안전하지만 enum 이름을 바꾸면 DB 값과 매핑이 깨질 수 있다.

DB에 저장되는 코드가 오래 유지되어야 하거나 외부 시스템과 계약된 값이면 enum 이름을 그대로 저장하기보다 별도 code 필드와 converter를 두는 편이 낫다.

### 행위 계약 → interface

구현체를 바꿔 끼우거나 테스트에서 대체해야 한다면 interface를 사용한다.

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
    private OrderStatus status = OrderStatus.PENDING;

    public void approve() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("Only pending orders can be approved.");
        }
        this.status = OrderStatus.APPROVED;
    }
}
```

이런 객체는 단순 데이터 묶음이 아니라 상태 전이 규칙을 가진다. 이 경우 record보다 class가 더 자연스럽다.

## 자주 나는 실수

- DTO를 class로 만들어서 getter, equals, hashCode를 수동으로 관리한다.
- `@Enumerated(ORDINAL)`을 사용해서 enum 순서 변경 시 DB 데이터가 깨진다.
- `@Enumerated(STRING)`이면 완전히 안전하다고 생각하고 enum 이름을 쉽게 변경한다.
- interface 하나에 구현체가 하나인데 불필요하게 추상화한다.
- enum을 단순 상수로만 쓰고, 분기 로직을 호출부에 if-else로 작성한다.
- record를 JPA Entity로 사용하려다 프록시 생성 실패가 발생한다.

## 핵심 요약

데이터 전달은 `record`, 고정된 선택지는 `enum`, 행위 계약은 `interface`, 식별자와 상태 변경을 가진 객체는 `class`를 우선 고려한다.

JPA Entity는 생명주기와 상태 변경이 있으므로 `class`가 자연스럽다. record는 DTO나 값 전달 객체에 더 적합하다.

enum을 DB에 저장할 때는 `ORDINAL`을 피한다. `STRING`도 이름 변경에는 취약하므로 장기 저장 값이면 별도 code 전략을 고려한다.

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