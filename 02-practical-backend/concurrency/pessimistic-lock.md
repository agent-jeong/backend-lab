---
title: 비관적 락
description: 충돌 가능성이 높은 상황에서 DB row를 선점해 동시 변경을 막는 방식
tags: [concept, concurrency]
---

# 비관적 락

비관적 락은 충돌이 잦다고 보고, 트랜잭션 동안 대상 row를 잠가 다른 트랜잭션의 변경을 기다리게 하는 방식이다.

재고, 쿠폰, 포인트처럼 같은 row에 쓰기가 몰리는 곳에서 충돌을 미리 막는다. 대가는 lock wait, timeout, deadlock이다. 그래서 락을 잡은 시간을 짧게 유지하는 것이 설계의 대부분이다.

> [!tip] 함께 읽기
> - [[lock]]: DB 락의 종류와 동작
> - [[optimistic-lock]]: 충돌을 저장 시점에 감지하는 반대 선택

## 동작

1. 트랜잭션이 `select ... for update` 또는 JPA lock mode로 row lock을 얻는다.
2. 같은 row를 수정하려는 다른 트랜잭션은 기다린다.
3. 첫 번째 트랜잭션이 commit 또는 rollback하면 락이 풀린다.
4. 기다리던 트랜잭션이 이어서 실행된다.
5. 대기가 길어지면 lock wait timeout이나 deadlock이 난다.

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

`PESSIMISTIC_WRITE`는 대상 row에 쓰기 락을 걸어 다른 트랜잭션의 동시 변경을 기다리게 한다. 트랜잭션은 짧게 두고, 그 안에서 외부 API를 호출하지 않는다. DB와 JPA 설정에 맞춰 lock timeout, `NOWAIT`, `SKIP LOCKED` 같은 대기 정책을 검토한다.

## 언제 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row 경합이 높음 | 비관적 락 | 충돌을 사전에 막는다 |
| 작업 시간이 짧음 | 비관적 락 가능 | 락 보유 시간이 짧으면 비용이 낮다 |
| 외부 API 포함 | 비관적 락을 피하거나 분리 | 락 보유 시간이 길어진다 |
| 여러 row를 함께 잠금 | 접근 순서 고정 | 데드락을 줄인다 |
| 단순 수량 차감 | 조건부 update 우선 검토 | 락 범위를 더 줄일 수 있다 |
| 대기 시간이 사용자 경험에 직결됨 | lock timeout 설정 | 무한 대기와 connection 고갈을 막는다 |

낙관적 락 재시도가 너무 많아 처리량이 떨어지는 곳도 비관적 락으로 바꿀 후보다. 경합이 높을 때 재시도 폭증을 줄이고, 트랜잭션 안에서 일관된 판단을 하기 쉽다.

## 자주 깨지는 곳

- **락을 잡은 뒤 결제 API나 알림 API를 호출한다.** 외부 장애가 락 대기로 번져 전체 요청이 느려진다.
- **인덱스 없는 조건으로 조회한다.** 예상보다 넓은 범위가 잠긴다. 실행 계획에서 lock 대상 조회가 인덱스를 타는지 본다.
- **여러 테이블을 요청마다 다른 순서로 잠근다.** 데드락이 난다.
- **lock timeout 없이 오래 기다리게 둔다.** 응답 시간이 늘고 connection이 고갈된다.
- **lock wait timeout을 단순 장애로만 보고 재현하지 않는다.**
- **비관적 락이면 데드락이 절대 없다고 생각한다.**
- **"없으면 insert"를 `select ... for update`로 막으려 한다.** MySQL InnoDB `REPEATABLE READ`에서 존재하지 않는 row를 잠그면 gap lock이 걸리고, 두 트랜잭션이 같은 gap을 잡은 뒤 서로 insert하면 데드락이 난다. 중복 생성 방지는 unique 제약으로 한다.

## 운영에서 볼 것

- 같은 row를 동시에 수정하는 테스트로 대기와 timeout을 확인한다.
- lock wait timeout, deadlock, transaction duration 로그를 본다.
- lock wait time, active transaction, DB connection active count를 본다.

## 면접에서 말하기

> 비관적 락은 row를 먼저 잠가 동시 변경을 기다리게 하는 방식이라, 경합이 높고 충돌 시 실패 비용이 큰 곳에 씁니다. 대가는 lock wait와 데드락이어서, 저는 트랜잭션을 짧게 두고 인덱스를 타는 조건으로 잠그고 여러 자원은 같은 순서로 잠급니다. 단순 수량 차감이라면 조건부 update가 더 단순합니다.

## 꼬리 질문

- 비관적 락은 언제 낙관적 락보다 적합한가?
- 비관적 락을 사용할 때 데드락을 줄이는 방법은 무엇인가?
- `select for update`를 쓸 때 인덱스가 중요한 이유는 무엇인가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Hibernate ORM 6.6 User Guide: Locking](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#locking)
- [MySQL 8.4: Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[optimistic-lock]]
- [[01-core/database/lock|lock]]
