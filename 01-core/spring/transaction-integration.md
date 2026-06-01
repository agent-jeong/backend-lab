---
title: Transaction Integration
description: Spring의 트랜잭션 관리와 @Transactional 동작 원리
---

# Transaction Integration

## 한 줄 정의

Spring은 `@Transactional`을 통해 AOP 기반으로 트랜잭션을 관리하며, 프록시가 메서드 실행 전후에 트랜잭션 시작, 커밋, 롤백을 자동으로 처리한다.

## 실무에서 왜 중요한가

Spring 트랜잭션을 제대로 이해하지 못하면 다음 문제가 생긴다.

- `@Transactional`을 붙였는데 롤백이 되지 않는다.
- 같은 클래스 내부 호출에서 트랜잭션이 적용되지 않는다.
- checked 예외가 발생했는데 롤백되지 않는 이유를 모른다.
- 트랜잭션 전파 설정을 잘못해서 의도하지 않은 커밋이나 롤백이 발생한다.
- readOnly 트랜잭션의 의미와 효과를 모른다.

## @Transactional 동작 원리

`@Transactional`은 AOP 프록시 기반으로 동작한다.

```
외부 호출 → 프록시 → 트랜잭션 시작 → 실제 메서드 실행 → 커밋 or 롤백
```

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        paymentService.pay(request.getPaymentInfo());
        // 예외 발생 시 전체 롤백
    }
}
```

프록시가 메서드 시작 전에 트랜잭션을 열고, 정상 완료 시 커밋, 예외 발생 시 롤백한다.

## 롤백 규칙

```java
// 기본: unchecked 예외(RuntimeException)만 롤백
@Transactional
public void process() {
    throw new RuntimeException(); // 롤백 O
}

@Transactional
public void process() throws IOException {
    throw new IOException(); // 롤백 X (checked 예외)
}

// checked 예외도 롤백하려면 명시
@Transactional(rollbackFor = Exception.class)
public void process() throws IOException {
    throw new IOException(); // 롤백 O
}
```

| 예외 타입 | 기본 롤백 | 변경 방법 |
|---|---|---|
| RuntimeException (unchecked) | O | `noRollbackFor`로 제외 가능 |
| Exception (checked) | X | `rollbackFor`로 롤백 대상 추가 |
| Error | O | - |

## 트랜잭션 전파 (Propagation)

```java
@Transactional(propagation = Propagation.REQUIRED)
public void outerMethod() {
    innerService.innerMethod();
}
```

| 전파 옵션 | 동작 | 실무 사용 |
|---|---|---|
| `REQUIRED` (기본값) | 기존 트랜잭션이 있으면 참여, 없으면 새로 생성 | 대부분 |
| `REQUIRES_NEW` | 항상 새 트랜잭션 생성, 기존 트랜잭션 일시 중지 | 독립 로깅, 알림 |
| `SUPPORTS` | 기존 트랜잭션이 있으면 참여, 없으면 트랜잭션 없이 실행 | 드물게 사용 |
| `NOT_SUPPORTED` | 트랜잭션 없이 실행, 기존 트랜잭션 일시 중지 | 드물게 사용 |

### REQUIRES_NEW 활용

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(OrderRequest request) {
        orderRepository.save(new Order(request));
        notificationService.sendNotification(request); // 알림 실패해도 주문은 유지
    }
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification(OrderRequest request) {
        // 별도 트랜잭션 → 실패해도 주문 트랜잭션에 영향 없음
    }
}
```

## readOnly 트랜잭션

```java
@Transactional(readOnly = true)
public List<OrderResponse> getOrders() {
    return orderRepository.findAll().stream()
        .map(OrderResponse::from)
        .toList();
}
```

- JPA에서 변경 감지(dirty checking)를 생략해서 성능이 향상된다.
- DB에 따라 읽기 전용 쿼리 최적화가 적용될 수 있다.
- 조회 전용 메서드에는 `readOnly = true`를 습관적으로 붙인다.

## @Transactional이 동작하지 않는 경우

`@Transactional`은 AOP 프록시 기반이므로 다음 경우에 동작하지 않는다.

- **내부 호출**: 같은 클래스에서 `this.method()`로 호출하면 프록시를 거치지 않는다.
- **private 메서드**: CGLIB 프록시가 오버라이드할 수 없다.
- **final 클래스/메서드**: CGLIB은 상속 기반이므로 프록시를 생성할 수 없다.

해결 방법은 메서드를 별도 클래스로 분리하는 것이 가장 권장된다. 자세한 동작 원리는 [[aop|AOP]] 문서에서 다룬다.

## 자주 나는 실수

- checked 예외에서 롤백이 안 되는 것을 모르고 `rollbackFor`를 설정하지 않는다.
- 같은 클래스 내부 호출에서 `@Transactional`이 무시되는 것을 모른다.
- `readOnly = true`를 조회 메서드에 붙이지 않는다.
- `REQUIRES_NEW`를 내부 호출로 사용해서 별도 트랜잭션이 생성되지 않는다.
- 트랜잭션 범위를 너무 넓게 잡아서 DB 커넥션 점유 시간이 길어진다.

## 핵심 요약

Spring의 `@Transactional`은 AOP 프록시 기반으로 동작합니다.
프록시가 메서드 실행 전에 트랜잭션을 시작하고, 정상 완료 시 커밋, 예외 발생 시 롤백합니다.

기본적으로 unchecked 예외(RuntimeException)만 롤백합니다.
checked 예외도 롤백하려면 `rollbackFor = Exception.class`를 설정해야 합니다.

내부 호출과 private 메서드에서는 프록시를 거치지 않아서 트랜잭션이 적용되지 않습니다.
조회 전용 메서드에는 `readOnly = true`를 설정해서 변경 감지를 생략하는 것이 좋습니다.

## 꼬리 질문

> [!question]- checked 예외에서 롤백되지 않는 이유는?
> Spring의 기본 롤백 정책이 unchecked 예외(RuntimeException)와 Error만 대상이기 때문입니다. checked 예외는 호출자가 복구할 수 있다는 가정으로 롤백하지 않습니다. `rollbackFor`로 변경할 수 있습니다.

> [!question]- `REQUIRED`와 `REQUIRES_NEW`의 차이는?
> `REQUIRED`는 기존 트랜잭션에 참여하고, `REQUIRES_NEW`는 항상 새 트랜잭션을 생성합니다. `REQUIRES_NEW`는 외부 트랜잭션이 롤백되어도 내부 트랜잭션이 독립적으로 커밋됩니다. 알림, 로그 저장 등에 사용합니다.

> [!question]- `readOnly = true`의 효과는?
> JPA 영속성 컨텍스트에서 변경 감지(dirty checking)를 생략해서 스냅샷 비교 비용이 줄어듭니다. DB에 따라 읽기 전용 최적화가 추가로 적용될 수 있습니다.

> [!question]- 트랜잭션 범위를 어떻게 설정해야 하는가?
> 꼭 필요한 범위만 트랜잭션으로 묶어야 합니다. 외부 API 호출이나 파일 I/O는 트랜잭션 밖에서 처리하고, DB 작업만 트랜잭션 안에 포함시키는 것이 좋습니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[aop]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[01-core/database/transaction-and-isolation|transaction-and-isolation]]
- [[01-core/jpa/transaction-and-flush|transaction-and-flush]]