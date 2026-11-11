---
title: Spring 트랜잭션
description: Spring @Transactional이 프록시로 어떻게 동작하고, 어디서 기대와 다르게 도는지
tags: [concept, transaction]
---

# Spring 트랜잭션

일반적인 Spring Boot 기본 설정에서 `@Transactional`은 프록시가 메서드 호출을 감싸서 트랜잭션 시작, commit, rollback을 대신 해 주는 기능이다.

사고는 대부분 이 프록시 방식에서 난다. 같은 클래스 안에서 자기 메서드를 부르면(self-invocation) 애너테이션을 붙였는데도 트랜잭션이 걸리지 않는다. 기본 rollback 규칙을 모르면 checked exception이 났는데 commit된다. 전파 옵션을 잘못 쓰면 따로 돌 줄 알았던 작업이 같은 트랜잭션에 끼거나, 같이 돌 줄 알았던 작업이 따로 commit된다. 옵션 목록을 외우기보다 트랜잭션이 어디서 시작하고 끝나는지, 예외가 어디까지 올라가는지, 어떤 작업이 따로 commit되는지부터 정확히 알아야 한다.

> [!tip] 함께 읽기
> - [[transaction-integration]]: 프록시, 전파, 롤백 규칙까지 자세히 다룬 글
> - [[transactional-pitfalls]]: 적용되지 않을 때의 진단 체크리스트

## 동작

1. Spring이 `@Transactional`이 붙은 Bean을 프록시로 감싼다.
2. 바깥에서 프록시의 메서드를 부르면 트랜잭션 인터셉터가 먼저 돈다.
3. 이미 열린 트랜잭션이 있으면 propagation 규칙에 따라 거기에 끼거나 새로 연다.
4. 메서드가 정상으로 끝나면 commit한다.
5. rollback 대상 예외가 메서드 밖으로 던져지면 rollback한다.

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

`createOrder`는 runtime exception이 나면 rollback된다. `importOrders`는 checked exception에서도 rollback해야 한다고 보고 `rollbackFor`를 직접 적은 예다.

## 주요 설정

| 설정 | 의미 | 메모 |
|---|---|---|
| `propagation = REQUIRED` | 기존 트랜잭션 참여, 없으면 생성 | 기본값이며 가장 흔하다 |
| `propagation = REQUIRES_NEW` | 기존 트랜잭션을 잠시 중단하고 새 트랜잭션 생성 | 감사 로그, 실패 기록에 쓰지만 독립 commit에 주의한다 |
| `propagation = NESTED` | savepoint 기반 중첩 트랜잭션 | DB/트랜잭션 매니저 지원 여부를 확인해야 한다 |
| `readOnly = true` | 읽기 전용 힌트 | DB 쓰기를 절대 막는 보안장치는 아니지만 ORM flush 전략과 DB 최적화 힌트에 영향을 줄 수 있다 |
| `rollbackFor` | rollback할 checked exception 지정 | 기본 규칙을 바꿔야 할 때만 명시한다 |

propagation, isolation, timeout은 메서드마다 바꿀 수 있다. 하지만 옵션을 여기저기 붙이면 호출 흐름을 따라가기 어려워진다. read-only, timeout, isolation도 이유 없이 붙이면 성능이나 정합성 문제가 생긴다.

## rollback 규칙

| 예외 | 기본 동작 |
|---|---|
| `RuntimeException` | rollback |
| `Error` | rollback |
| checked exception | commit |

checked exception에서도 rollback해야 하면 `rollbackFor = Exception.class`처럼 적어 준다. 반대로 예외를 catch하고 밖으로 다시 던지지 않으면 Spring은 정상 종료로 보고 commit할 수 있다. 어느 경우든 rollback되는 건 DB 변경뿐이고, 이미 보낸 외부 호출 같은 부작용은 그대로 남는다.

## 자주 깨지는 곳

- 같은 클래스 안에서 `this.save()`처럼 부르면, 프록시를 거치지 않아 트랜잭션이 걸리지 않는다.
- `private` 메서드에 `@Transactional`을 붙이면 적용되지 않는다.
- 예외를 잡고 로그만 남기면, 실패한 작업이 commit된다.
- `REQUIRES_NEW`도 바깥과 함께 rollback될 거라고 생각하면 틀린다. 안쪽 메서드가 정상으로 끝났다면 그때 이미 따로 commit됐고, 바깥이 rollback돼도 되돌아가지 않는다.
- 읽기 메서드 전체를 긴 트랜잭션으로 감싸면, 커넥션을 오래 쥐게 된다.

## 운영에서 볼 것

- 의도한 예외에서 정말 rollback되는지 DB 상태로 확인하는 테스트를 둔다.
- 트랜잭션 인터셉터와 SQL commit/rollback 로그를 켜서 실제로 어디서 열리고 닫히는지 본다.
- 트랜잭션 지속 시간과 커넥션 풀의 active 수를 본다.
- 코드 리뷰에서 self-invocation, private 메서드, 예외를 잡고 다시 던지지 않는 코드를 찾는다.

## 한 번에 설명하기

> Spring의 `@Transactional`은 기본 설정에서 프록시가 메서드 호출을 감싸 트랜잭션을 열고 닫는 방식입니다.
>
> 기본 전파는 `REQUIRED`라서 이미 열린 트랜잭션이 있으면 거기에 낍니다. 기본으로 rollback되는 건 runtime exception과 error뿐이라 checked exception은 rollback되지 않습니다.
>
> 기대와 다르게 돌 때는 self-invocation, private 메서드, 예외를 잡고 다시 던지지 않은 경우를 먼저 확인합니다. 대부분 이 셋 중 하나입니다.

## 꼬리 질문

- `@Transactional`을 붙였는데 적용되지 않는 경우는?
- checked exception이 나면 기본적으로 rollback되나?
- `REQUIRES_NEW`를 쓰면 무엇이 좋아지고 무엇이 위험해지나?
- 예외를 catch하고 그냥 반환하면 트랜잭션은 어떻게 되나?

## 내 사례

- [[webhook-once-without-loss|웹훅을 잃지 않고 한 번만 처리하기]]: `REQUIRES_NEW`로 상태 변경만 따로 커밋

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html)
- [Spring Framework: Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[transaction-boundary]]
- [[01-core/spring/spring|spring]]
- [[01-core/jpa/jpa|jpa]]
