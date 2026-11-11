---
title: 객체지향 설계 원칙
description: SOLID 다섯 원칙을 외우지 않고 자주 바뀌는 코드를 떼어 내는 기준으로 쓰는 법
tags: [concept, architecture]
---

# 객체지향 설계 원칙

객체지향 설계 원칙은 자주 바뀌는 코드와 잘 안 바뀌는 코드를 어디서 떼어 낼지 정하는 규칙 묶음이다. 흔히 SOLID라는 다섯 글자로 부르지만, 다섯 개를 외우는 것보다 "이 코드는 무엇 때문에 바뀌는가"를 묻는 습관이 더 쓸모 있다.

결제 수단이 카드 하나일 때 만든 결제 서비스는 간편결제와 포인트가 붙으면서 if문이 하나씩 늘어난다. 새 수단을 붙일 때마다 이미 잘 돌던 카드 결제 코드까지 다시 테스트해야 한다. 원칙은 이런 변경이 한곳에 머물게 하려고 쓴다.

## 결제 수단마다 늘어나는 if문

원칙을 어긴 코드는 대개 이런 모양으로 시작한다.

```java
@Service
public class PaymentService {

    public PaymentResult pay(Order order, PaymentMethod method) {
        if (method == PaymentMethod.CARD) {
            return payByCard(order);      // 카드사 승인, 할부 개월 검증
        } else if (method == PaymentMethod.EASY_PAY) {
            return payByEasyPay(order);   // 간편결제 토큰 검증, 승인
        } else if (method == PaymentMethod.POINT) {
            return payByPoint(order);     // 포인트 잔액 확인, 차감
        }
        throw new IllegalArgumentException("unsupported method: " + method);
    }
}
```

이 클래스는 결제 수단이 늘 때도, 카드 할부 규칙이 바뀔 때도, 포인트 정책이 바뀔 때도 고쳐진다. 바뀌는 이유가 셋이다. 결제 수단마다 바뀌는 부분을 인터페이스 뒤로 옮기면 이렇게 된다.

```java
public interface PaymentProcessor {
    PaymentMethod method();
    PaymentResult pay(Order order);
}

@Component
class CardPaymentProcessor implements PaymentProcessor {
    public PaymentMethod method() { return PaymentMethod.CARD; }
    public PaymentResult pay(Order order) { /* 카드 승인 */ return PaymentResult.approved(); }
}

@Service
public class PaymentService {
    private final Map<PaymentMethod, PaymentProcessor> processors;

    public PaymentService(List<PaymentProcessor> processors) {
        this.processors = processors.stream()
                .collect(Collectors.toUnmodifiableMap(PaymentProcessor::method, p -> p));
    }

    public PaymentResult pay(Order order, PaymentMethod method) {
        PaymentProcessor processor = processors.get(method);
        if (processor == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return processor.pay(order);
    }
}
```

Spring은 같은 타입의 Bean을 모두 `List`로 주입해 준다. 이제 계좌이체를 붙일 때는 `PaymentProcessor` 구현 클래스 하나만 추가하고 `PaymentService`는 고치지 않는다. 같은 수단을 맡은 구현이 둘이면 `toUnmodifiableMap`이 기동 시점에 예외를 던져서 실수가 바로 드러난다.

## 원칙마다 어기면 아픈 곳

| 원칙 | 한 줄 | 어기면 생기는 일 |
|---|---|---|
| SRP 단일 책임 | 바뀌는 이유가 같은 코드끼리 모은다 | 할부 규칙을 고쳤는데 포인트 결제가 깨진다 |
| OCP 개방 폐쇄 | 새 경우는 코드 추가로 붙인다 | 수단이 늘 때마다 기존 분기를 고치고 전부 다시 테스트한다 |
| LSP 리스코프 치환 | 하위 타입은 상위 타입 약속을 지킨다 | 호출하는 쪽이 `instanceof`로 구현을 골라 피한다 |
| ISP 인터페이스 분리 | 쓰지 않는 메서드에 기대지 않게 쪼갠다 | 구현마다 지원하지 않는 메서드가 예외를 던진다 |
| DIP 의존 역전 | 업무 코드가 정한 인터페이스에 기술 코드가 맞춘다 | PG사를 바꾸거나 테스트할 때 HTTP 클라이언트가 따라온다 |

SRP를 Robert C. Martin은 "같은 이유로 바뀌는 것은 모으고, 다른 이유로 바뀌는 것은 떼어 놓는다"로 다시 설명했다. "클래스가 한 가지 일만 한다"로 읽으면 메서드 하나짜리 클래스만 잔뜩 생긴다. 기준은 일의 개수가 아니라 변경을 요구하는 사람이나 정책이다.

LSP와 ISP는 한 장면에서 같이 깨진다. 결제 취소를 `PaymentProcessor`에 넣었는데 즉시 취소가 안 되는 수단이 생겼다고 하자.

```java
// PaymentProcessor에 cancel(Order)이 있다고 하자
class BankTransferProcessor implements PaymentProcessor {
    // method(), pay()는 생략
    public void cancel(Order order) {
        throw new UnsupportedOperationException("계좌이체는 환불 요청으로 처리");
    }
}
```

이제 `processor.cancel()`을 부르는 쪽은 어떤 구현이 올지 알아야 안전하다. 상위 타입만 보고 쓸 수 없으니 치환이 깨진 것이다. 고칠 때는 취소를 할 수 있는 수단만 구현하는 `CancelablePayment` 같은 인터페이스를 따로 둔다. 할 수 없는 일을 예외로 막지 않고, 처음부터 그 메서드를 갖지 않게 한다.

DIP는 [[dependency-direction]]에서 다루는 참조 방향을 클래스 단위로 지키는 방법이다. `OrderService`가 특정 PG사 HTTP 클라이언트를 직접 알면, PG사를 바꿀 때 주문 코드가 바뀐다. 주문 쪽이 `PaymentGateway` 인터페이스를 정하고 PG사 어댑터가 그 인터페이스를 구현하면, 주문 코드는 PG사 교체를 모른다. 테스트에서는 가짜 구현을 넣어 HTTP 없이 돈다.

## 상속보다 조합

공통 코드를 모으려고 상속을 쓰면 부모 클래스가 바뀔 때 모든 자식이 같이 흔들린다.

```java
abstract class AbstractPaymentProcessor {
    public PaymentResult pay(Order order) {
        validate(order);
        PaymentResult result = request(order);
        saveHistory(result);
        return result;
    }
    protected abstract PaymentResult request(Order order);
}
```

포인트 결제만 이력을 다른 테이블에 남겨야 하면 `saveHistory`를 덮어쓰거나 부모에 플래그를 넣게 된다. 자식이 셋을 넘으면 부모의 어느 메서드를 누가 덮어썼는지 따라가기 어렵다. 검증, 요청, 이력 저장을 각각 객체로 두고 필요한 것을 생성자로 받으면, 포인트 결제는 다른 이력 저장 객체만 끼우면 된다. 상속은 "A는 B다"가 업무에서도 성립하고 부모가 잘 안 바뀔 때만 쓴다.

## getter와 setter를 열어 두면 캡슐화가 없다

필드를 `private`으로 두고 getter와 setter를 모두 열면, 규칙은 객체 밖으로 흩어진다.

```java
// 서비스 여러 곳에 같은 검사가 복사된다
if (order.getStatus() == OrderStatus.PAID) {
    order.setStatus(OrderStatus.CANCELED);
}

// 규칙을 객체 안에 둔다
public void cancel() {
    if (status != OrderStatus.PAID) {
        throw new IllegalStateException("결제 완료 주문만 취소할 수 있다: " + status);
    }
    this.status = OrderStatus.CANCELED;
}
```

상태를 꺼내서 밖에서 판단하지 말고, 객체에게 하라고 시킨다. 이 원칙을 Tell, Don't Ask라고 부르고, Andy Hunt와 Dave Thomas(The Pragmatic Programmers)가 널리 알렸다. 취소 규칙이 바뀌면 `cancel()` 하나만 고친다. JPA Entity도 같다. setter를 열어 두면 변경 감지 때문에 어디서 값을 바꿨는지 추적하기 어려워진다.

## 원칙을 과하게 쓰면 생기는 일

원칙은 변경이 실제로 잦은 곳에만 쓴다. 바뀔지도 모른다는 추측으로 쓰면 읽을 코드만 늘어난다.

- 구현이 하나뿐인 `OrderService` 인터페이스와 `OrderServiceImpl`을 모든 서비스에 만들면, 기능 하나를 따라갈 때 파일을 두 번씩 연다. Spring Boot는 기본으로 CGLIB 프록시를 쓰기 때문에 `@Transactional`을 쓰려고 인터페이스를 만들 필요도 없다.
- 결제 수단이 둘이고 몇 년째 안 바뀌었다면 if문 두 개가 전략 패턴보다 읽기 쉽다.
- 메서드 하나짜리 인터페이스를 잘게 쪼개면, 구현 클래스가 인터페이스 다섯 개를 구현하고 어느 조합이 쓰이는지 찾기 어렵다.

두 번째 변형이 실제로 나타났을 때 떼어 내도 늦지 않다. 그때는 무엇이 바뀌는지 이미 보이기 때문에 경계를 더 정확히 긋는다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 일을 하는 방법이 셋 이상이고 계속 늘어난다 | 인터페이스와 전략 | 새 방법은 클래스 추가로 끝난다 |
| 분기가 둘이고 잘 안 바뀐다 | if문이나 `switch` | 간접 호출보다 읽기 쉽다 |
| 외부 시스템이나 저장소를 바꿀 가능성이 있고 테스트가 느리다 | 업무 쪽이 정한 인터페이스와 어댑터 | 업무 코드가 기술 교체와 테스트에서 자유로워진다 |
| 구현마다 지원하는 기능이 다르다 | 기능별로 인터페이스를 나눈다 | 지원하지 않는 메서드를 예외로 막지 않는다 |
| 공통 흐름을 여러 구현이 나눠 쓴다 | 조합 | 부모 변경이 모든 자식을 흔들지 않는다 |

## 자주 깨지는 곳

- 전략을 나눠 놓고 고르는 코드에 다시 if문을 쓰면, 수단이 늘 때 고르는 코드를 또 고치게 된다.
- 하위 구현이 상위 메서드를 `UnsupportedOperationException`으로 막으면, 호출하는 쪽이 구현 타입을 확인하는 코드가 퍼진다.
- 인터페이스를 기술 쪽에서 정하면, 시그니처에 HTTP 응답 타입이나 PG사 전용 코드가 들어가서 바꿔 끼울 수 없게 된다.
- 모든 필드에 setter를 열어 두면, 상태 전이 규칙이 서비스마다 복사되고 한 곳만 고쳐서 버그가 난다.
- 바뀔지 모른다는 이유로 미리 추상화하면, 실제로 바뀐 방향이 예상과 달라서 추상화를 다시 뜯게 된다.

## 한 번에 설명하기

> 객체지향 설계 원칙은 자주 바뀌는 코드를 어디서 떼어 낼지 정하는 기준으로 씁니다. 저는 원칙 이름보다 이 코드가 무엇 때문에 바뀌는지를 먼저 봅니다.
>
> 예를 들어 결제 수단이 늘 때마다 if문이 늘어나는 서비스는 결제 수단별 구현을 인터페이스 뒤로 옮겨서, 새 수단은 클래스 추가로 끝나게 바꿉니다. 외부 PG사 같은 기술 세부는 업무 쪽이 정한 인터페이스 뒤에 둡니다.
>
> 다만 구현이 하나뿐이거나 분기가 둘뿐인 곳에 인터페이스를 만들면 읽을 파일만 늘어납니다. 그래서 두 번째 변형이 실제로 나타났을 때 떼어 냅니다.

## 꼬리 질문

> [!question]- SRP를 "클래스는 한 가지 일만 한다"로 이해하면 무엇이 문제인가?
> 한 가지 일의 크기가 사람마다 달라서 기준이 되지 못합니다. 그렇게 읽으면 메서드 하나짜리 클래스가 늘어납니다. 저는 같은 이유로 바뀌는 코드를 모으고, 다른 정책 때문에 바뀌는 코드는 떼어 놓는 기준으로 씁니다.

> [!question]- 인터페이스는 언제 만드나?
> 구현이 둘 이상이거나, 테스트에서 외부 시스템을 가짜로 바꿔야 하거나, 업무 코드가 기술 세부를 몰라야 할 때 만듭니다. 구현이 하나뿐인 서비스에 `Impl`을 붙여 인터페이스를 만드는 것은 하지 않습니다. Spring Boot는 기본으로 클래스를 상속하는 CGLIB 프록시를 써서 트랜잭션 때문에 인터페이스가 필요하지도 않습니다.

> [!question]- 리스코프 치환 원칙이 깨진 걸 코드에서 어떻게 알아보나?
> 상위 타입으로 받아 놓고 `instanceof`로 구현을 확인하는 코드가 보이면 의심합니다. 하위 구현이 상위 메서드를 `UnsupportedOperationException`으로 막는 것도 같은 신호입니다. 보통 그 기능을 지원하는 구현만 갖는 인터페이스로 나눠서 고칩니다.

> [!question]- 상속 대신 조합을 쓰는 이유는?
> 상속하면 자식이 부모의 내부 흐름에 묶여서, 부모를 고칠 때 모든 자식이 같이 흔들립니다. 조합은 바뀌는 부분만 다른 객체로 바꿔 끼울 수 있습니다. 업무에서도 "A는 B다"가 성립하고 부모가 잘 안 바뀌는 경우에만 상속을 씁니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Robert C. Martin: The Single Responsibility Principle](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)
- [Robert C. Martin: The Principles of OOD](http://butunclebob.com/ArticleS.UncleBob.PrinciplesOfOod)
- [Martin Fowler: Tell Don't Ask](https://martinfowler.com/bliki/TellDontAsk.html)

## 관련 문서

- [[02-practical-backend/architecture/architecture|architecture]]
- [[dependency-direction]]
- [[service-responsibility]]
- [[layered-architecture]]
- [[ioc-and-di]]
