---
title: Spring 트랜잭션
description: Spring @Transactional 동작 방식과 실무 주의점
---

# Spring 트랜잭션

## 한 줄 정의

Spring 트랜잭션은 일반적인 Spring Boot 기본 설정에서 `@Transactional`을 기준으로 프록시가 메서드 호출을 감싸고, 트랜잭션 시작, commit, rollback을 대신 처리하는 기능이다.

## 실무에서 왜 문제 되는가

- `@Transactional`을 붙였는데 self-invocation 때문에 적용되지 않을 수 있다.
- 기본 rollback 규칙을 몰라 checked exception에서 commit되는 경우가 생긴다.
- 전파 옵션을 잘못 쓰면 의도와 다르게 같은 트랜잭션에 참여하거나 독립 commit된다.
- read-only, timeout, isolation 설정을 무분별하게 쓰면 성능이나 정합성 문제가 생긴다.

## 동작 원리

1. Spring이 `@Transactional`이 붙은 Bean을 프록시로 감싼다.
2. 외부에서 프록시 메서드를 호출하면 트랜잭션 인터셉터가 먼저 실행된다.
3. 기존 트랜잭션이 있으면 propagation 규칙에 따라 참여하거나 새로 만든다.
4. 메서드가 정상 종료되면 commit한다.
5. rollback 대상 예외가 밖으로 전파되면 rollback한다.

## 주요 설정

| 설정 | 의미 | 실무 메모 |
|---|---|---|
| `propagation = REQUIRED` | 기존 트랜잭션 참여, 없으면 생성 | 기본값이며 가장 흔하다 |
| `propagation = REQUIRES_NEW` | 기존 트랜잭션을 잠시 중단하고 새 트랜잭션 생성 | 감사 로그, 실패 기록에 쓰지만 독립 commit에 주의한다 |
| `propagation = NESTED` | savepoint 기반 중첩 트랜잭션 | DB/트랜잭션 매니저 지원 여부를 확인해야 한다 |
| `readOnly = true` | 읽기 전용 힌트 | DB 쓰기를 절대 막는 보안장치는 아니지만 ORM flush 전략과 DB 최적화 힌트에 영향을 줄 수 있다 |
| `rollbackFor` | rollback할 checked exception 지정 | 기본 규칙을 바꿔야 할 때만 명시한다 |

## rollback 규칙

| 예외 | 기본 동작 |
|---|---|
| `RuntimeException` | rollback |
| `Error` | rollback |
| checked exception | commit |

checked exception에서도 rollback해야 한다면 `rollbackFor = Exception.class`처럼 명시한다. 반대로 예외를 catch하고 밖으로 던지지 않으면 Spring은 정상 종료로 보고 commit할 수 있다.

## 자주 나는 실수

- 같은 클래스 내부에서 `this.save()`처럼 호출해 트랜잭션 프록시를 거치지 않는다.
- `private` 메서드에 `@Transactional`을 붙이고 적용된다고 생각한다.
- 예외를 잡고 로그만 남긴 뒤 commit되게 만든다.
- `REQUIRES_NEW`를 쓰면 전체 작업이 함께 rollback된다고 오해한다.
- 읽기 메서드 전체에 긴 트랜잭션을 열어 커넥션을 오래 점유한다.

## 확인 방법

- 테스트: 의도한 예외에서 rollback되는지 DB 상태를 검증한다.
- 로그: transaction interceptor, SQL commit/rollback 로그를 켠다.
- 메트릭: transaction duration, connection pool active count를 본다.
- 코드 리뷰: self-invocation, private method, catch 후 미전파 패턴을 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 선언적으로 트랜잭션 경계를 표현한다 | 프록시 기반 제약을 이해해야 한다 |
| propagation, isolation, timeout을 메서드 단위로 조정할 수 있다 | 옵션 남용은 호출 흐름을 추적하기 어렵게 만든다 |
| 예외 기반 rollback 처리가 단순하다 | 외부 부작용은 rollback되지 않는다 |

## 짧은 예제

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder(CreateOrderCommand command) {
        orderRepository.save(Order.create(command.userId()));
        stockRepository.decrease(command.productId(), command.quantity());
    }

    @Transactional(rollbackFor = Exception.class)
    public void importOrders(List<OrderRow> rows) throws Exception {
        for (OrderRow row : rows) {
            orderRepository.save(row.toOrder());
        }
    }
}
```

`createOrder`는 runtime exception 발생 시 rollback된다. `importOrders`는 checked exception에서도 rollback이 필요하다고 판단해 `rollbackFor`를 명시한 예다.

## 핵심 요약

Spring의 `@Transactional`은 일반적인 Spring Boot 기본 설정에서 프록시를 통해 메서드 호출을 감싸는 선언적 트랜잭션 기능이다.

기본 전파 옵션은 `REQUIRED`이고, 기존 트랜잭션이 있으면 참여한다.

기본 rollback 대상은 runtime exception과 error이며, checked exception은 기본적으로 rollback되지 않는다.

self-invocation, private method, 예외 catch 후 미전파는 트랜잭션이 기대와 다르게 동작하는 대표 원인이다.

실무에서는 옵션을 많이 아는 것보다 경계, 예외 전파, 독립 commit 여부를 정확히 설명하는 것이 중요하다.

## 꼬리 질문

- `@Transactional`이 붙었는데 적용되지 않는 경우는 무엇인가?
- checked exception이 발생하면 기본적으로 rollback되는가?
- `REQUIRES_NEW`를 사용하면 어떤 장점과 위험이 있는가?
- 예외를 catch하고 반환하면 트랜잭션은 어떻게 되는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[transaction-boundary]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
