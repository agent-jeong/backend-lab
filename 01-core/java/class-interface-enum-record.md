---
title: 클래스·인터페이스·이넘·레코드
description: class, interface, enum, record 중 무엇을 고를지와 고를 때 자주 하는 실수
tags: [concept, java]
---

# 클래스·인터페이스·이넘·레코드 선택 기준

`class`, `interface`, `enum`, `record`는 모두 타입을 만드는 문법이지만, 각각 나타내려는 것이 다르다. 그래서 문법을 고르기 전에 "이 타입이 무엇을 나타내는가"부터 정한다.

잘못 고르면 티가 난다. DTO를 class로 만들면 getter와 equals를 손으로 쓰게 되고, 주문 상태를 문자열 상수로 두면 `"PENDNG"` 같은 오타가 운영에서야 드러나고, 상태가 계속 바뀌는 Entity를 record로 만들려다 막힌다.

## 무엇을 고르나

| 상황 | 선택 | 이유 |
|---|---|---|
| 데이터 전달이 목적 | `record` | 필드, 생성자, `equals`, `hashCode`, `toString`을 짧게 표현 |
| 고정된 상태·유형·분류 | `enum` | 허용되는 값을 타입으로 제한 |
| 여러 구현체를 같은 방식으로 사용 | `interface` | 구현체 교체, 테스트 대체, DI에 유리 |
| 식별자와 변경 가능한 상태가 있음 | `class` | Entity, 도메인 객체처럼 생명주기와 행위를 표현 |
| 공통 상태와 구현을 상속해야 함 | `abstract class` | 하위 클래스에 공통 로직 제공 |

먼저 `enum`이나 `record`로 나타낼 수 있는지 보고, 생명주기가 있고 상태가 바뀌어야 하면 `class`로 만든다. `interface`는 구현체를 바꿔 끼우거나 의존성을 떼어 내야 할 일이 실제로 있을 때 만든다.

## 데이터를 옮기는 객체는 record

데이터를 옮기기만 하는 객체는 `record`로 쓰면 읽기 쉽다.

```java
public record UserResponse(
    Long id,
    String name,
    String email
) {
}
```

record는 필드를 다시 대입할 수 없을 뿐, 필드가 가리키는 객체까지 불변으로 만들지는 않는다. `List` 같은 mutable 객체를 담으면 그 안의 내용은 바뀐다. 막아야 하면 `List.copyOf()`로 복사해 둔다.

```java
public record UserGroup(List<String> names) {
    public UserGroup {
        names = List.copyOf(names);
    }
}
```

API 요청·응답 DTO, 메서드 사이에 넘기는 객체, 캐시 key, 작은 값 객체에 맞는다. JPA Entity, 단계마다 상태가 바뀌는 객체, 상속이 필요한 객체에는 맞지 않는다.

## 정해진 값만 오는 상태와 분류는 enum

상태, 유형, 카테고리처럼 올 수 있는 값이 정해져 있으면 enum을 쓴다. 문자열 상수로는 "이 값들만 허용한다"를 타입으로 막을 수 없다.

```java
process("PENDNG"); // 오타가 있어도 컴파일된다.
```

enum이면 잘못된 값을 쓰는 순간 컴파일 에러가 난다.

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

결제 수단마다 수수료 계산이 조금씩 다른 것처럼 상수마다 작은 규칙 차이가 있으면, 그 로직을 enum 안에 둔다. 호출하는 쪽의 if-else가 줄어든다.

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

새 결제 수단을 추가하면 `calculateFee`를 구현하지 않는 한 컴파일되지 않는다. 다만 업무 흐름이 커지면 enum에 넣지 말고 서비스나 정책 객체로 빼는 편이 낫다.

### enum을 DB에 저장할 때

JPA `@Enumerated`의 기본값은 `ORDINAL`이다. 실무에서는 대부분 `STRING`을 직접 적어 준다.

```java
// 위험: enum 선언 순서가 DB 값이 된다.
@Enumerated(EnumType.ORDINAL)
private OrderStatus status; // 0, 1, 2...

// 일반적으로 더 안전: enum 이름이 DB 값이 된다.
@Enumerated(EnumType.STRING)
private OrderStatus status; // "PENDING", "APPROVED"...
```

`ORDINAL`은 상수 선언 순서가 바뀌면 이미 저장된 숫자가 다른 상태를 가리키게 된다. `STRING`은 순서를 바꿔도 괜찮지만, enum 이름을 바꾸면 저장된 값과 맞지 않게 된다.

DB에 오래 남는 값이거나 외부 시스템과 미리 정해 둔 값이면, enum 이름을 그대로 저장하지 말고 code 필드를 따로 두고 converter로 바꾼다.

## 구현을 바꿔 끼울 자리는 interface

구현체를 바꿔 끼우거나 테스트에서 가짜로 바꿔야 하면 interface를 쓴다.

```java
public interface NotificationSender {
    void send(String to, String message);
}

public class EmailSender implements NotificationSender { ... }
public class SlackSender implements NotificationSender { ... }
```

이럴 때 쓴다.

- 구현체가 여럿이거나 앞으로 여럿이 될 수 있다.
- 외부 의존성을 감싸서 테스트할 때 바꿔 끼우고 싶다.
- Spring에서 DI로 주입받는다.
- 포트/어댑터 구조에서 애플리케이션 코드가 외부 기술을 직접 알지 않게 한다.

구현체가 하나뿐이고 바뀔 일도 없으면 interface를 만들 필요가 없다. 테스트, 의존 방향, 확장 때문에 실제로 필요해졌을 때 만든다.

## 식별자가 있고 상태가 바뀌는 객체는 class

class는 식별자가 있고, 생명주기 동안 상태가 바뀌고, 그 상태를 바꾸는 행위까지 함께 가진 객체에 맞는다.

- 바뀌는 상태와 그 상태를 다루는 메서드를 함께 가진 도메인 객체
- JPA Entity
- 상속 구조가 필요한 경우
- 빌더 패턴처럼 생성 로직이 복잡한 경우
- 상태를 바꾸는 메서드를 외부에 열어 두고 필드는 숨겨야 하는 경우

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

이 주문 객체는 데이터를 묶어 둔 것이 아니라 "대기 중일 때만 승인할 수 있다"는 상태 전이 규칙을 가진다. 그래서 record보다 class가 자연스럽다.

## 자주 깨지는 곳

- DTO를 class로 만들면, getter, equals, hashCode를 손으로 관리하게 된다.
- `@Enumerated(ORDINAL)`을 쓰면, enum 순서가 바뀌는 순간 DB에 저장된 숫자가 다른 상태를 뜻하게 된다.
- `STRING`이면 완전히 안전하다고 믿으면, enum 이름을 바꾸는 순간 저장된 값을 읽지 못한다.
- 구현체가 하나뿐인 interface를 습관처럼 만들면, 파일과 간접 호출만 늘어난다.
- enum을 상수 목록으로만 쓰면, 상수별 분기가 호출하는 곳마다 if-else로 흩어진다.
- record를 JPA Entity로 쓰려 하면, 프록시를 만들지 못해 실패한다.

## 한 번에 설명하기

> 데이터만 옮기면 record, 선택지가 정해져 있으면 enum, 구현을 바꿔 끼워야 하면 interface, 식별자가 있고 상태가 바뀌면 class를 먼저 떠올립니다.
>
> JPA Entity는 생명주기가 있고 상태가 바뀌어서 class로 만들고, record는 DTO나 값 객체에 씁니다.
>
> enum을 DB에 저장할 때는 ORDINAL을 피합니다. STRING도 이름을 바꾸면 깨지기 때문에, 오래 남는 값이면 code 필드를 따로 두고 converter로 바꿉니다.

## 꼬리 질문

> [!question]- record를 JPA Entity로 못 쓰는 이유는?
> record는 final class이고 필드도 전부 final입니다. 기본 생성자나 만든 뒤에 상태를 바꾸는 방식이 JPA Entity가 요구하는 조건과 맞지 않습니다. JPA가 프록시를 만들기도 어렵습니다. 그래서 Entity보다는 DTO나 projection에 씁니다.

> [!question]- enum에 로직을 넣으면 뭐가 좋나?
> 호출하는 쪽의 if-else가 줄어듭니다. 그리고 새 상수를 추가할 때 추상 메서드를 구현하지 않으면 컴파일이 안 되니까 빠뜨릴 일이 없습니다. 다만 업무 흐름이 커지면 서비스나 정책 객체로 빼는 게 낫습니다.

> [!question]- `@Enumerated(ORDINAL)`은 왜 위험한가?
> enum 상수를 선언한 순서(0, 1, 2...)로 저장합니다. 그래서 중간에 상수를 끼워 넣거나 순서를 바꾸면, 이미 저장된 숫자가 다른 상수를 가리키게 됩니다.

> [!question]- `@Enumerated(STRING)`이면 항상 안전한가?
> 순서를 바꾸는 건 괜찮은데 enum 이름을 바꾸면 깨집니다. 오래 저장할 값이나 외부 시스템과 미리 정해 둔 값이면 code 필드를 따로 두고 converter를 쓰는 걸 검토합니다.

> [!question]- interface와 abstract class는 어떻게 고르나?
> 여러 구현이 필요하거나 메서드 계약만 정하면 되면 interface를 씁니다. 공통 상태나 구현을 자식 클래스에 물려줘야 하면 abstract class를 씁니다.

> [!question]- sealed class는 이 네 가지와 어떤 관계인가?
> sealed는 상속할 수 있는 하위 타입을 `permits`로 정해 둡니다. interface나 abstract class에 붙여서, 하위 타입이 정해진 것 말고는 생길 수 없는 계층을 만들 수 있습니다.

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

2026년 11월에 확인한 공식 문서다.

- [JEP 395: Records](https://openjdk.org/jeps/395)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [JLS 21: Enum Classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.9)

## 관련 문서

- [[01-core/java/java|java]]
- [[equals-and-hashcode]]
- [[java-version-features]]
- [[01-core/jpa/jpa|jpa]]