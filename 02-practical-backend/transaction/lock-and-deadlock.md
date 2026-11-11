---
title: 락과 데드락
description: 같은 행에 쓰기가 몰릴 때 생기는 락 대기와 데드락, 그리고 줄이는 방법
tags: [concept, transaction]
---

# 락과 데드락

락은 여러 요청이 같은 데이터를 동시에 바꾸려 할 때 한 번에 하나씩만 바꾸게 하는 장치다. 데드락은 트랜잭션끼리 서로가 쥔 락을 기다리느라 둘 다 멈춘 상태다.

락 문제는 느린 응답, lock wait timeout, 데드락으로 인한 rollback으로 드러난다. 인기 상품 재고, 쿠폰 발급, 포인트 차감처럼 한 행에 쓰기가 몰리는 곳에서 특히 심하다. 요청을 하나씩 보내는 테스트에서는 보이지 않다가 운영 트래픽이 들어오면 갑자기 나타난다.

> [!tip] 함께 읽기
> - [[lock]]: DB 락의 종류와 동작
> - [[pessimistic-lock]]: 행을 먼저 잠그는 방식을 언제 고르나

## 동작

1. 트랜잭션이 특정 행이나 인덱스 범위를 읽거나 고친다.
2. DB가 정합성을 지키는 데 필요한 락을 잡는다.
3. 같은 자원을 고치려는 다른 트랜잭션은 기다린다.
4. 서로 상대의 락을 기다리며 원을 그리면 데드락이다.
5. DB는 보통 한쪽 트랜잭션을 희생자(victim)로 골라 rollback한다.

```java
@Modifying
@Query("""
    update Product p
       set p.stock = p.stock - :quantity
     where p.id = :productId
       and p.stock >= :quantity
""")
int decreaseStock(Long productId, int quantity);

@Transactional
public void reserveStock(Long productId, int quantity) {
    int updated = productRepository.decreaseStock(productId, quantity);
    if (updated != 1) {
        throw new SoldOutException();
    }
}
```

재고를 먼저 조회하고 나중에 저장하는 것보다 조건부 update 한 문장이 단순하다. 재고가 충분한지 확인하는 일과 깎는 일을 DB가 SQL 한 문장 안에서 처리하니, 그 사이에 다른 요청이 끼어들 틈이 줄어든다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row를 한 번에 하나씩만 고쳐야 할 때 | pessimistic lock | 명시적으로 선점해 lost update를 막는다 |
| 충돌이 드물고 재시도 가능 | optimistic lock | 락 점유를 줄이고 버전 충돌만 감지한다 |
| 단순 수량 차감 | 조건부 update | 원자적 SQL로 락 범위를 줄인다 |
| 여러 자원을 함께 수정 | 락 획득 순서 고정 | 데드락 가능성을 낮춘다 |
| 긴 처리 포함 | 트랜잭션 밖에서 선처리 | 락 보유 시간을 줄인다 |

pessimistic lock은 충돌을 미리 막지만, 락을 오래 쥐면 처리량이 떨어진다. optimistic lock은 충돌이 드물 때 가볍지만, 충돌하면 재시도하거나 사용자에게 다시 하라고 알려야 한다. 조건부 update는 단순하고 빠르지만 검증할 규칙이 복잡하면 한 문장에 담기 어렵다. 경합이 아주 심한 기능이면 요청을 큐에 줄 세우는 방법까지 놓고 업무에 맞게 고른다.

## 교착 상태가 생기는 네 가지 조건

데드락은 네 조건이 한꺼번에 성립할 때만 생긴다. 거꾸로 하나라도 깨면 데드락은 생기지 않는다. 운영체제 교재에서 다루는 조건이지만 DB 락과 애플리케이션 락에도 그대로 들어맞는다.

| 조건 | 뜻 | DB 락에서 | 애플리케이션 락에서 |
|---|---|---|---|
| 상호 배제 | 자원을 한 번에 하나만 쥔다 | 배타 락이 걸린 행은 다른 트랜잭션이 고치지 못한다 | `synchronized`, `ReentrantLock`, 분산 락은 한 스레드나 한 서버만 쥔다 |
| 점유 대기 | 자원을 쥔 채 다른 자원을 기다린다 | 주문 행을 고친 트랜잭션이 커밋하기 전에 재고 행의 락을 기다린다 | 락 A를 쥔 스레드가 락 B의 `lock()`에서 멈춘다 |
| 비선점 | 남이 쥔 자원을 강제로 빼앗지 못한다 | 트랜잭션이 쥔 행 락은 커밋이나 롤백 전까지 풀리지 않는다 | 다른 스레드가 쥔 `synchronized` 모니터를 밖에서 풀 방법이 없다 |
| 순환 대기 | 기다림이 원을 이룬다 | T1은 A 행을 쥐고 B 행을, T2는 B 행을 쥐고 A 행을 기다린다 | 스레드 1은 계좌 A, B 순서로, 스레드 2는 B, A 순서로 잠근다 |

조건마다 깨는 비용이 다르다.

- 상호 배제는 깰 수 없다. 동시에 고쳐도 되는 데이터라면 처음부터 락이 필요 없다.
- 점유 대기는 필요한 락을 처음에 한꺼번에 잡거나, 하나라도 못 잡으면 쥔 것을 다 놓고 다시 시작하면 깨진다. `tryLock(timeout)`이 실패했을 때 쥔 락을 풀고 재시도하는 방식이 이쪽이다. 무엇을 잠글지 미리 알아야 하고, 재시도 로직이 붙는다.
- 비선점은 DB가 이미 대신 깨 준다. InnoDB 같은 DB는 데드락을 감지하면 한 트랜잭션을 희생자로 골라 롤백해서 락을 강제로 놓게 한다. 그래서 데드락이 나도 영원히 멈추지는 않지만, 롤백된 요청은 애플리케이션이 받아서 처리해야 한다.
- 순환 대기는 락을 잡는 순서를 하나로 정하면 깨진다. 모든 요청이 id가 작은 행부터 잠그면, 작은 id를 쥔 쪽이 큰 id를 기다리는 일은 있어도 그 반대는 없어서 원이 생기지 않는다.

실무에서는 주로 순환 대기를 깬다. 코드에서 잠그는 순서만 맞추면 되고, 락을 더 오래 쥐거나 재시도를 붙일 필요가 없어서 비용이 가장 적다.

```java
@Transactional
public void transfer(long fromAccountId, long toAccountId, long amount) {
    long firstId = Math.min(fromAccountId, toAccountId);
    long secondId = Math.max(fromAccountId, toAccountId);

    Account first = accountRepository.findByIdForUpdate(firstId);
    Account second = accountRepository.findByIdForUpdate(secondId);

    Account from = first.getId() == fromAccountId ? first : second;
    Account to = first.getId() == fromAccountId ? second : first;
    from.withdraw(amount);
    to.deposit(amount);
}
```

A에서 B로 보내는 요청과 B에서 A로 보내는 요청이 동시에 와도, 둘 다 id가 작은 계좌부터 잠그니 서로를 기다리는 원이 생기지 않는다. 여러 테이블을 고칠 때도 같다. 주문, 재고, 포인트처럼 테이블 순서를 정해 두고 모든 기능이 그 순서를 따르게 한다.

## 자주 깨지는 곳

- 락을 잡은 채 외부 API를 부르면, 외부가 느린 만큼 다른 요청의 락 대기가 늘어난다.
- 여러 테이블을 요청마다 다른 순서로 고치면 데드락이 난다. 가장 흔한 원인이다.
- 조건 없이 대량 update나 delete를 돌리면 넓은 범위에 락이 걸린다.
- 조건 컬럼에 인덱스가 없으면, 필요 없는 행과 범위까지 훑으면서 잠근다.
- 데드락은 버그가 아니니 무시해도 된다고 생각하면, rollback된 요청이 그냥 실패로 끝난다. DB가 한쪽을 rollback시키므로 그 실패는 애플리케이션이 처리해야 한다.

## 운영에서 볼 것

- 여러 요청을 동시에 보내 lost update, lock wait, deadlock을 재현한다.
- DB deadlock 로그, lock wait timeout, rollback 로그를 확인한다.
- lock wait time, deadlock count, slow query, 활성 트랜잭션 수를 본다.
- update/delete 조건이 인덱스를 타는지 실행 계획으로 확인한다.

## 한 번에 설명하기

> 락은 같은 데이터를 동시에 고칠 때 한 번에 하나씩만 바꾸게 하는 장치이고, 데드락은 트랜잭션끼리 서로의 락을 기다리느라 멈춘 상태입니다.
>
> 저는 트랜잭션을 짧게 두고, 조건이 인덱스를 타게 하고, 여러 자원을 건드릴 때는 잠그는 순서를 고정해서 위험을 줄입니다.
>
> 경합이 심한 기능은 pessimistic lock, optimistic lock, 조건부 update, 큐잉 가운데 업무에 맞는 것을 고릅니다.

## 꼬리 질문

- 락 대기와 데드락은 어떻게 다른가?
- optimistic lock과 pessimistic lock은 각각 언제 고르나?
- 조건부 update가 동시성 문제를 줄이는 이유는?
- 데드락이 나면 애플리케이션이 재시도해야 하나?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 겹쳐 돈 스케줄러의 데드락

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[lock]]
- [[db-index]]
