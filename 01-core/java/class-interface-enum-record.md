---
title: 클래스·인터페이스·이넘·레코드
description: Java 타입 선택 기준과 실무 설계 판단
tags: [concept, java]
---

# 클래스·인터페이스·이넘·레코드 선택 기준

`class`, `interface`, `enum`, `record`는 모두 타입을 정의하지만 표현하는 의도가 다르다. 문법보다 "이 타입이 무엇을 표현하는가"를 먼저 정해야 한다.

선택이 어긋나면 DTO에 boilerplate가 쌓이고, 문자열 상수 오타가 런타임까지 숨고, 생명주기가 있는 Entity를 record로 만들려다 실패한다.

## 무엇을 고르나

| 상황 | 선택 | 이유 |
|---|---|---|
| 데이터 전달이 목적 | `record` | 필드, 생성자, `equals`, `hashCode`, `toString`을 짧게 표현 |
| 고정된 상태·유형·분류 | `enum` | 허용되는 값을 타입으로 제한 |
| 여러 구현체를 같은 방식으로 사용 | `interface` | 구현체 교체, 테스트 대체, DI에 유리 |
| 식별자와 변경 가능한 상태가 있음 | `class` | Entity, 도메인 객체처럼 생명주기와 행위를 표현 |
| 공통 상태와 구현을 상속해야 함 | `abstract class` | 하위 클래스에 공통 로직 제공 |

먼저 `enum`이나 `record`로 표현되는지 보고, 생명주기와 상태 변경이 필요하면 `class`로 간다. `interface`는 구현체 교체나 의존성 분리가 실제로 필요할 때 만든다.

## DTO와 값 전달 객체: record

데이터를 옮기는 객체는 `record`로 쓰면 읽기 쉽다.

```java
public record UserResponse(
    Long id,
    String name,
    String email
) {
}
```

record는 얕은 불변이다. `List` 같은 mutable 객체를 담으면 그 내부는 바뀐다. 막아야 하면 `List.copyOf()`로 방어적 복사를 한다.

```java
public record UserGroup(List<String> names) {
    public UserGroup {
        names = List.copyOf(names);
    }
}
```

API 요청·응답 DTO, 메서드 간 전달 객체, 캐시 key, 작은 값 객체에 맞는다. JPA Entity, 단계적으로 상태가 바뀌는 객체, 상속이 필요한 객체에는 맞지 않는다.

## 고정된 분류와 상태: enum

상태, 유형, 카테고리처럼 값이 정해져 있으면 enum을 쓴다. 문자열 상수는 허용되는 값의 범위를 타입으로 표현하지 못한다.

```java
process("PENDNG"); // 오타가 있어도 컴파일된다.
```

enum이면 잘못된 값이 컴파일 단계에서 드러난다.

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

상수마다 작은 정책 차이가 있으면 enum 안에 로직을 둔다. 호출부의 if-else가 줄어든다.

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

새 결제 수단을 추가하면 컴파일러가 `calculateFee` 구현을 강제한다. 다만 큰 비즈니스 흐름은 enum이 아니라 서비스나 정책 객체로 빼는 편이 낫다.

### enum을 DB에 저장할 때

JPA `@Enumerated`의 기본값은 `ORDINAL`이다. 실무에서는 대부분 `STRING`을 명시한다.

```java
// 위험: enum 선언 순서가 DB 값이 된다.
@Enumerated(EnumType.ORDINAL)
private OrderStatus status; // 0, 1, 2...

// 일반적으로 더 안전: enum 이름이 DB 값이 된다.
@Enumerated(EnumType.STRING)
private OrderStatus status; // "PENDING", "APPROVED"...
```

`ORDINAL`은 상수 선언 순서가 바뀌면 기존 DB 데이터와 매핑이 깨진다. `STRING`은 순서 변경에는 안전하지만 enum 이름을 바꾸면 깨진다.

DB에 오래 남는 코드이거나 외부 시스템과 약속한 값이면, enum 이름을 그대로 저장하지 말고 별도 code 필드와 converter를 둔다.

## 행위 계약: interface

구현체를 바꿔 끼우거나 테스트에서 대체해야 하면 interface를 쓴다.

```java
public interface NotificationSender {
    void send(String to, String message);
}

public class EmailSender implements NotificationSender { ... }
public class SlackSender implements NotificationSender { ... }
```

이럴 때 쓴다.

- 구현체가 여럿이거나 여럿이 될 수 있다.
- 외부 의존성을 추상화해 테스트할 수 있게 만든다.
- Spring에서 DI 대상으로 쓴다.
- 포트/어댑터 구조에서 애플리케이션 코드가 외부 기술에 직접 의존하지 않게 한다.

구현체가 하나뿐이고 바뀔 일도 없으면 interface를 만들 필요가 없다. 테스트, 의존 방향, 확장이 실제로 필요할 때 만든다.

## 식별자와 상태가 있는 객체: class

class는 식별자와 생명주기, 변경 가능한 상태, 도메인 행위를 함께 표현할 때 맞는다.

- 가변 상태와 행위를 함께 가진 도메인 객체
- JPA Entity
- 상속 구조가 필요한 경우
- 빌더 패턴처럼 생성 로직이 복잡한 경우
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

이 객체는 데이터 묶음이 아니라 상태 전이 규칙을 가진다. 그래서 record보다 class가 자연스럽다.

## 자주 깨지는 곳

- **DTO를 class로 만든다.** getter, equals, hashCode를 손으로 관리하게 된다.
- **`@Enumerated(ORDINAL)`을 쓴다.** enum 순서가 바뀌면 DB 데이터의 의미가 바뀐다.
- **`STRING`이면 완전히 안전하다고 믿는다.** enum 이름을 바꾸는 순간 저장된 값과 매핑이 깨진다.
- **구현체 하나짜리 interface를 습관적으로 만든다.** 추상화 비용만 늘어난다.
- **enum을 상수로만 쓴다.** 분기 로직이 호출부 곳곳의 if-else로 흩어진다.
- **record를 JPA Entity로 쓰려 한다.** 프록시 생성에서 실패한다.

## 면접에서 말하기

> 데이터 전달은 record, 고정된 선택지는 enum, 행위 계약은 interface, 식별자와 상태 변경이 있는 객체는 class를 먼저 떠올립니다. JPA Entity는 생명주기와 상태 변경이 있어서 class로 만들고, record는 DTO나 값 객체에 씁니다. enum을 DB에 저장할 때는 ORDINAL을 피하고, STRING도 이름 변경에 약하기 때문에 오래 남는 값이면 별도 code 필드와 converter를 둡니다.

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

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>record를 JPA Entity로 쓰기 어려운 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="record도 메서드를 가질 수 있다. 핵심 제약은 상속/프록시와 불변 구조다." aria-pressed="false">A. record는 메서드를 정의할 수 없기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="record는 final이고 필드가 불변이라 JPA 프록시, 지연 로딩, 변경 감지 모델과 맞지 않는다." aria-pressed="false">B. final 불변 구조가 JPA 프록시와 변경 감지 방식에 맞지 않기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="record도 생성자를 가진다. 기본 생성자만의 문제가 아니다." aria-pressed="false">C. record에는 생성자가 없기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>enum에 상태 전이 검증 같은 도메인 로직을 넣으면 switch/if 분산을 줄일 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="상태별 행위를 enum 내부로 모으면 분기 로직이 흩어지는 문제를 줄일 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="enum은 단순 상수뿐 아니라 제한된 상태와 행위를 함께 표현할 수 있다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Enumerated(ORDINAL)이 위험한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="enum 순서가 바뀌거나 중간에 값이 추가되면 DB에 저장된 숫자의 의미가 바뀔 수 있다." aria-pressed="false">A. enum 선언 순서 변경이 저장 데이터 의미를 깨뜨릴 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="저장 공간보다 저장된 숫자의 의미가 바뀌는 게 문제다." aria-pressed="false">B. 문자열보다 항상 저장 공간을 많이 쓰기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="컴파일은 된다. 문제는 컴파일러가 잡지 못하는 데이터 호환성이다." aria-pressed="false">C. 컴파일 자체가 되지 않기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [JEP 395: Records](https://openjdk.org/jeps/395)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [JLS 21: Enum Classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.9)

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[java-version-features]]
- [[01-core/jpa/jpa|jpa]]