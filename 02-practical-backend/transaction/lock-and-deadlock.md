---
title: 락과 데드락
description: 트랜잭션에서 발생하는 락 경합과 데드락 대응 기준
tags: [concept, transaction]
---

# 락과 데드락

락은 같은 데이터를 동시에 바꿀 때 정합성을 지키는 동시성 제어 장치다. 데드락은 트랜잭션들이 서로가 가진 락을 기다리며 더 진행하지 못하는 상태다.

락 문제는 응답 지연, lock wait timeout, deadlock rollback으로 드러난다. 인기 상품 재고, 쿠폰 발급, 포인트 차감처럼 같은 row에 쓰기가 몰리면 경합이 커지고, 단일 요청 테스트에서는 안 보이다가 운영 트래픽에서 갑자기 나타난다.

> [!tip] 함께 읽기
> - [[lock]]: DB 락의 종류와 동작
> - [[pessimistic-lock]]: 행을 먼저 잠그는 방식을 언제 고르나

## 동작

1. 트랜잭션이 특정 row나 index range를 읽거나 수정한다.
2. DB는 정합성을 위해 필요한 락을 잡는다.
3. 같은 자원을 수정하려는 다른 트랜잭션은 기다린다.
4. 서로 상대의 락을 기다리는 순환 대기가 생기면 데드락이다.
5. DB는 보통 한쪽 트랜잭션을 victim으로 골라 rollback한다.

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

재고 차감은 먼저 조회하고 나중에 저장하는 방식보다 조건부 update가 단순하다. DB가 SQL 한 문장 안에서 조건 확인과 변경을 처리해 경쟁 조건을 줄인다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row를 반드시 순차 변경 | pessimistic lock | 명시적으로 선점해 lost update를 막는다 |
| 충돌이 드물고 재시도 가능 | optimistic lock | 락 점유를 줄이고 버전 충돌만 감지한다 |
| 단순 수량 차감 | 조건부 update | 원자적 SQL로 락 범위를 줄인다 |
| 여러 자원을 함께 수정 | 락 획득 순서 고정 | 데드락 가능성을 낮춘다 |
| 긴 처리 포함 | 트랜잭션 밖에서 선처리 | 락 보유 시간을 줄인다 |

pessimistic lock은 충돌을 미리 막지만 보유 시간이 길면 처리량이 떨어진다. optimistic lock은 경합이 낮을 때 효율적이지만 충돌 시 재시도나 사용자 안내가 필요하다. 조건부 update는 단순하고 빠르지만 복잡한 업무 검증에는 한계가 있다. 경합이 높은 기능이면 큐잉까지 포함해 업무 특성으로 고른다.

## 자주 깨지는 곳

- **락을 잡은 뒤 외부 API를 호출한다.** 외부 지연만큼 락 대기가 늘어난다.
- **여러 테이블을 요청마다 다른 순서로 수정한다.** 데드락의 전형적인 원인이다.
- **조건 없는 대량 update/delete를 실행한다.** 넓은 범위에 락이 걸린다.
- **인덱스가 없다.** 불필요하게 많은 row나 range를 스캔하며 잠근다.
- **데드락은 버그가 아니니 무시해도 된다고 생각한다.** DB가 한쪽을 rollback시키므로 애플리케이션이 그 실패를 처리해야 한다.

## 운영에서 볼 것

- 동시에 여러 요청을 보내 lost update, lock wait, deadlock을 재현한다.
- DB deadlock log, lock wait timeout, transaction rollback 로그를 확인한다.
- lock wait time, deadlock count, slow query, active transaction 수를 본다.
- update/delete 조건이 인덱스를 타는지 실행 계획으로 확인한다.

## 한 번에 설명하기

> 락은 같은 데이터를 동시에 수정할 때 정합성을 지키는 장치이고, 데드락은 여러 트랜잭션이 서로의 락을 기다리는 순환 대기 상태입니다. 저는 트랜잭션을 짧게 두고, 조건이 인덱스를 타게 하고, 자원 접근 순서를 고정해서 위험을 줄입니다. 경합이 높은 기능은 pessimistic lock, optimistic lock, 조건부 update, 큐잉 중 업무 특성에 맞는 것을 고릅니다.

## 꼬리 질문

- 락 대기와 데드락은 어떻게 다른가?
- optimistic lock과 pessimistic lock은 언제 선택하는가?
- 조건부 update가 동시성 문제를 줄이는 이유는 무엇인가?
- 데드락이 발생했을 때 애플리케이션은 재시도해야 하는가?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 겹쳐 돈 스케줄러의 데드락

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[lock]]
- [[db-index]]
