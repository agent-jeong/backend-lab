---
title: 비관적 락
description: 충돌 가능성이 높은 상황에서 DB row를 선점해 동시 변경을 막는 방식
---

# 비관적 락

## 한 줄 정의

비관적 락은 충돌이 발생할 가능성이 높다고 보고, 트랜잭션 동안 대상 row를 잠가 다른 트랜잭션의 변경을 대기시키는 방식이다.

## 실무에서 왜 문제 되는가

- 재고, 쿠폰, 포인트처럼 같은 row에 쓰기가 몰리면 동시에 변경되면 안 된다.
- 낙관적 락 재시도가 너무 많으면 처리량과 사용자 경험이 나빠질 수 있다.
- 비관적 락은 정합성을 강하게 보호하지만 lock wait, timeout, deadlock을 만들 수 있다.
- 락을 잡은 상태에서 외부 API를 호출하면 장애가 전체 요청으로 전파된다.

## 동작 원리

1. 트랜잭션이 `select ... for update` 또는 JPA lock mode로 row lock을 획득한다.
2. 다른 트랜잭션은 같은 row를 수정하려 할 때 대기한다.
3. 첫 번째 트랜잭션이 commit 또는 rollback하면 락이 해제된다.
4. 대기 중인 트랜잭션이 이어서 실행된다.
5. 대기가 길어지면 lock wait timeout이나 deadlock이 발생할 수 있다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row 경합이 높음 | 비관적 락 | 충돌을 사전에 막는다 |
| 작업 시간이 짧음 | 비관적 락 가능 | 락 보유 시간이 짧으면 비용이 낮다 |
| 외부 API 포함 | 비관적 락 피하거나 분리 | 락 보유 시간이 길어진다 |
| 여러 row를 함께 잠금 | 접근 순서 고정 | 데드락을 줄인다 |
| 단순 수량 차감 | 조건부 update 우선 검토 | 락 범위를 더 줄일 수 있다 |
| 대기 시간이 사용자 경험에 중요 | lock timeout 설정 | 무한 대기와 connection 고갈을 막는다 |

## 자주 나는 실수

- 락을 잡은 뒤 결제 API나 알림 API를 호출한다.
- 인덱스 없는 조건으로 조회해 예상보다 넓은 범위를 잠근다.
- 여러 테이블을 요청마다 다른 순서로 잠근다.
- lock timeout 없이 오래 대기하게 둔다.
- lock wait timeout을 단순 장애로만 보고 재현하지 않는다.
- 비관적 락을 쓰면 데드락이 절대 없다고 생각한다.

## 확인 방법

- 테스트: 동시에 같은 row를 수정해 대기와 timeout을 확인한다.
- 로그: lock wait timeout, deadlock, transaction duration을 본다.
- 메트릭: lock wait time, active transaction, DB connection active count를 본다.
- 실행 계획: lock 대상 조회가 적절한 인덱스를 사용하는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 충돌을 사전에 막아 정합성을 강하게 보호한다 | 락 대기로 응답 시간이 증가할 수 있다 |
| 경합이 높은 상황에서 재시도 폭증을 줄인다 | 데드락과 timeout 대응이 필요하다 |
| 트랜잭션 안에서 일관된 판단이 쉽다 | 락 범위와 보유 시간을 잘못 잡으면 장애가 커진다 |

## 짧은 예제

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("select p from Product p where p.id = :productId")
Optional<Product> findByIdForUpdate(Long productId);

@Transactional
public void decreaseStock(Long productId, int quantity) {
    Product product = productRepository.findByIdForUpdate(productId)
        .orElseThrow();
    product.decreaseStock(quantity);
}
```

`PESSIMISTIC_WRITE`는 대상 row에 쓰기 락을 걸어 다른 트랜잭션의 동시 변경을 대기시킨다. 트랜잭션 범위는 짧게 유지해야 하며, 이 안에서 외부 API를 호출하지 않는 것이 중요하다. 실무에서는 DB와 JPA 설정에 맞게 lock timeout, `NOWAIT`, `SKIP LOCKED` 같은 대기 정책을 검토한다.

## 핵심 요약

비관적 락은 대상 row를 선점해 동시 변경을 막는다.

경합이 높고 충돌 실패 비용이 큰 기능에서 유용하다.

하지만 락 대기, timeout, 데드락을 만들 수 있으므로 트랜잭션을 짧게 유지해야 한다.

무한 대기를 막기 위해 lock timeout과 실패 시 응답 정책을 명확히 둔다.

락 대상 조회에는 적절한 인덱스가 필요하고, 여러 자원을 잠글 때는 순서를 고정해야 한다.

단순 수량 차감은 비관적 락보다 조건부 update가 더 단순할 수 있다.

## 꼬리 질문

- 비관적 락은 언제 낙관적 락보다 적합한가?
- 비관적 락을 사용할 때 데드락을 줄이는 방법은 무엇인가?
- `select for update`를 쓸 때 인덱스가 중요한 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[optimistic-lock]]
- [[01-core/database/lock|lock]]
