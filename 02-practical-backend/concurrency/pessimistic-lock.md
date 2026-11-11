---
title: 비관적 락
description: 충돌이 잦은 곳에서 행을 먼저 잠가 다른 수정이 기다리게 하는 방식
tags: [concept, concurrency]
---

# 비관적 락

비관적 락은 충돌이 잦을 거라고 보고, 트랜잭션이 도는 동안 대상 행을 잠가서 다른 트랜잭션의 수정을 기다리게 하는 방식이다.

재고, 쿠폰, 포인트처럼 한 행에 쓰기가 몰리는 곳에서 충돌을 미리 막는다. 대신 lock wait, timeout, 데드락을 감수해야 한다. 그래서 설계할 때 신경 쓰는 일의 대부분은 락을 쥐는 시간을 짧게 만드는 것이다.

> [!tip] 함께 읽기
> - [[lock]]: DB 락의 종류와 동작
> - [[optimistic-lock]]: 충돌을 저장 시점에 감지하는 반대 선택

## 동작

1. 트랜잭션이 `select ... for update`나 JPA lock mode로 행 락을 얻는다.
2. 같은 행을 고치려는 다른 트랜잭션은 기다린다.
3. 첫 번째 트랜잭션이 commit하거나 rollback하면 락이 풀린다.
4. 기다리던 트랜잭션이 이어서 실행된다.
5. 기다림이 길어지면 lock wait timeout이나 데드락이 난다.

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

`PESSIMISTIC_WRITE`는 대상 행에 쓰기 락을 걸어, 같은 행을 고치려는 다른 트랜잭션을 기다리게 한다. 트랜잭션은 짧게 두고, 그 안에서 외부 API를 부르지 않는다. 쓰는 DB와 JPA 설정에 맞춰 lock timeout, `NOWAIT`, `SKIP LOCKED` 같은 대기 방식을 검토한다.

## 언제 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row 경합이 높음 | 비관적 락 | 충돌을 사전에 막는다 |
| 작업 시간이 짧음 | 비관적 락 가능 | 락 보유 시간이 짧으면 비용이 낮다 |
| 외부 API 포함 | 비관적 락을 피하거나 분리 | 락 보유 시간이 길어진다 |
| 여러 row를 함께 잠금 | 접근 순서 고정 | 데드락을 줄인다 |
| 단순 수량 차감 | 조건부 update 우선 검토 | 락 범위를 더 줄일 수 있다 |
| 대기 시간이 사용자 경험에 직결됨 | lock timeout 설정 | 무한 대기와 connection 고갈을 막는다 |

낙관적 락 재시도가 너무 많아 처리량이 떨어지는 곳도 비관적 락으로 바꿔 볼 만하다. 경합이 심할 때 재시도가 몰리는 걸 줄이고, 트랜잭션 안에서 잠근 값을 기준으로 판단하기 쉽다.

## 자주 깨지는 곳

- 락을 잡은 뒤 결제나 알림 API를 부르면, 외부 장애가 락 대기로 번져 모든 요청이 느려진다.
- 인덱스 없는 조건으로 조회하면 생각보다 넓은 범위가 잠긴다. 잠그는 조회가 인덱스를 타는지 실행 계획에서 확인한다.
- 여러 테이블을 요청마다 다른 순서로 잠그면 데드락이 난다.
- lock timeout 없이 오래 기다리게 두면, 응답 시간이 늘고 커넥션이 바닥난다.
- lock wait timeout을 일시적인 장애로만 보고 재현해 보지 않으면, 같은 경합이 계속 반복된다.
- 비관적 락을 쓰면 데드락이 없다고 생각하면 틀린다. 잠그는 순서가 엇갈리면 그대로 난다.
- "없으면 insert"를 `select ... for update`로 막으려 하면 데드락이 난다. MySQL InnoDB `REPEATABLE READ`에서 존재하지 않는 행을 잠그면 gap lock이 걸리는데, 두 트랜잭션이 같은 gap을 잡은 뒤 서로 insert하면 데드락이 된다. 중복 생성은 unique 제약으로 막는다.

## 운영에서 볼 것

- 같은 행을 동시에 고치는 테스트로 대기와 timeout을 확인한다.
- lock wait timeout, deadlock, 트랜잭션 지속 시간 로그를 본다.
- lock wait time, 활성 트랜잭션 수, DB 커넥션 active 수를 본다.

## 한 번에 설명하기

> 비관적 락은 행을 먼저 잠가서 다른 수정이 기다리게 하는 방식입니다. 경합이 심하고, 충돌했을 때 잃는 게 큰 곳에 씁니다.
>
> 대신 lock wait와 데드락이 생깁니다. 그래서 저는 트랜잭션을 짧게 두고, 인덱스를 타는 조건으로 잠그고, 여러 자원은 늘 같은 순서로 잠급니다.
>
> 단순히 수량만 깎는 거라면 조건부 update가 더 간단합니다.

## 꼬리 질문

- 비관적 락이 낙관적 락보다 나은 경우는?
- 비관적 락을 쓸 때 데드락을 줄이는 방법은?
- `select for update`를 쓸 때 인덱스가 중요한 이유는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Locking](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#locking)
- [MySQL 8.4: Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[optimistic-lock]]
- [[01-core/database/lock|lock]]
