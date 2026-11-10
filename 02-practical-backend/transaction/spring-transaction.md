---
title: Spring 트랜잭션
description: Spring @Transactional 동작 방식과 실무 주의점
---

# Spring 트랜잭션

일반적인 Spring Boot 기본 설정에서 `@Transactional`은 프록시가 메서드 호출을 감싸고, 트랜잭션 시작·commit·rollback을 대신 처리하는 기능이다.

프록시 기반이라는 점에서 대부분의 사고가 난다. self-invocation이면 붙였는데도 적용되지 않고, 기본 rollback 규칙을 모르면 checked exception에서 commit되고, 전파 옵션을 잘못 쓰면 의도와 다르게 같은 트랜잭션에 참여하거나 따로 commit된다. 옵션 목록보다 트랜잭션 경계, 예외 전파, 독립 commit 여부를 정확히 아는 게 먼저다.

## 동작

1. Spring이 `@Transactional`이 붙은 Bean을 프록시로 감싼다.
2. 외부에서 프록시 메서드를 호출하면 트랜잭션 인터셉터가 먼저 실행된다.
3. 기존 트랜잭션이 있으면 propagation 규칙에 따라 참여하거나 새로 만든다.
4. 메서드가 정상 종료되면 commit한다.
5. rollback 대상 예외가 밖으로 전파되면 rollback한다.

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

`createOrder`는 runtime exception이 나면 rollback된다. `importOrders`는 checked exception에서도 rollback이 필요하다고 보고 `rollbackFor`를 명시한 예다.

## 주요 설정

| 설정 | 의미 | 메모 |
|---|---|---|
| `propagation = REQUIRED` | 기존 트랜잭션 참여, 없으면 생성 | 기본값이며 가장 흔하다 |
| `propagation = REQUIRES_NEW` | 기존 트랜잭션을 잠시 중단하고 새 트랜잭션 생성 | 감사 로그, 실패 기록에 쓰지만 독립 commit에 주의한다 |
| `propagation = NESTED` | savepoint 기반 중첩 트랜잭션 | DB/트랜잭션 매니저 지원 여부를 확인해야 한다 |
| `readOnly = true` | 읽기 전용 힌트 | DB 쓰기를 절대 막는 보안장치는 아니지만 ORM flush 전략과 DB 최적화 힌트에 영향을 줄 수 있다 |
| `rollbackFor` | rollback할 checked exception 지정 | 기본 규칙을 바꿔야 할 때만 명시한다 |

propagation, isolation, timeout을 메서드 단위로 조정할 수 있지만, 옵션을 남발하면 호출 흐름을 따라가기 어려워진다. read-only, timeout, isolation도 근거 없이 붙이면 성능이나 정합성 문제가 생긴다.

## rollback 규칙

| 예외 | 기본 동작 |
|---|---|
| `RuntimeException` | rollback |
| `Error` | rollback |
| checked exception | commit |

checked exception에서도 rollback해야 하면 `rollbackFor = Exception.class`처럼 명시한다. 반대로 예외를 catch하고 밖으로 던지지 않으면 Spring은 정상 종료로 보고 commit할 수 있다. 어느 쪽이든 rollback되는 건 DB 변경뿐이고 외부 부작용은 그대로 남는다.

## 자주 깨지는 곳

- **같은 클래스 안에서 `this.save()`처럼 호출한다.** 프록시를 거치지 않아 트랜잭션이 적용되지 않는다.
- **`private` 메서드에 `@Transactional`을 붙인다.** 적용되지 않는다.
- **예외를 잡고 로그만 남긴다.** 실패했는데 commit된다.
- **`REQUIRES_NEW`도 전체와 함께 rollback된다고 오해한다.** 안쪽 메서드가 정상 종료했다면 그 시점에 이미 독립적으로 commit됐고, 바깥이 rollback돼도 되돌아가지 않는다.
- **읽기 메서드 전체에 긴 트랜잭션을 연다.** 커넥션을 오래 쥐고 있게 된다.

## 운영에서 볼 것

- 의도한 예외에서 rollback되는지 DB 상태로 검증하는 테스트를 둔다.
- transaction interceptor와 SQL commit/rollback 로그를 켜서 실제 경계를 본다.
- transaction duration, connection pool active count를 본다.
- 코드 리뷰에서 self-invocation, private method, catch 후 미전파 패턴을 찾는다.

## 면접에서 말하기

> Spring의 `@Transactional`은 기본 설정에서 프록시가 메서드 호출을 감싸는 선언적 트랜잭션입니다. 기본 전파는 `REQUIRED`라 기존 트랜잭션이 있으면 참여하고, 기본 rollback 대상은 runtime exception과 error라서 checked exception은 rollback되지 않습니다. 기대와 다르게 동작하는 대표 원인은 self-invocation, private method, 예외를 잡고 다시 던지지 않는 경우이고, 저는 이 셋을 먼저 확인합니다.

## 꼬리 질문

- `@Transactional`이 붙었는데 적용되지 않는 경우는 무엇인가?
- checked exception이 발생하면 기본적으로 rollback되는가?
- `REQUIRES_NEW`를 사용하면 어떤 장점과 위험이 있는가?
- 예외를 catch하고 반환하면 트랜잭션은 어떻게 되는가?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: `REQUIRES_NEW`로 상태 변경만 따로 커밋

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[transaction-boundary]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
