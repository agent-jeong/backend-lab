---
title: 락과 데드락
description: 트랜잭션에서 발생하는 락 경합과 데드락 대응 기준
---

# 락과 데드락

## 한 줄 정의

락은 동시에 같은 데이터를 변경할 때 정합성을 지키기 위한 동시성 제어 장치이고, 데드락은 서로가 가진 락을 기다리며 더 이상 진행하지 못하는 상태다.

## 실무에서 왜 문제 되는가

- 락 대기가 길어지면 API 응답 시간이 급격히 증가한다.
- 데드락이 발생하면 DB가 한 트랜잭션을 강제로 rollback시킨다.
- 인기 상품 재고, 쿠폰 발급, 포인트 차감처럼 같은 row에 쓰기가 몰리면 경합이 커진다.
- 락 문제는 단일 요청 테스트에서는 잘 드러나지 않고 운영 트래픽에서 갑자기 나타난다.

## 동작 원리

1. 트랜잭션이 특정 row나 index range를 읽거나 수정한다.
2. DB는 정합성을 위해 필요한 락을 획득한다.
3. 다른 트랜잭션이 같은 자원을 수정하려 하면 대기한다.
4. 서로 상대가 가진 락을 기다리는 순환 대기가 생기면 데드락이 발생한다.
5. DB는 보통 한쪽 트랜잭션을 victim으로 선택해 rollback한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 같은 row를 반드시 순차 변경 | pessimistic lock | 명시적으로 선점해 lost update를 막는다 |
| 충돌이 드물고 재시도 가능 | optimistic lock | 락 점유를 줄이고 버전 충돌만 감지한다 |
| 단순 수량 차감 | 조건부 update | 원자적 SQL로 락 범위를 줄일 수 있다 |
| 여러 자원을 함께 수정 | 락 획득 순서 고정 | 데드락 가능성을 낮춘다 |
| 긴 처리 포함 | 트랜잭션 밖에서 선처리 | 락 보유 시간을 줄인다 |

## 자주 나는 실수

- 락을 잡은 뒤 외부 API를 호출한다.
- 여러 테이블을 요청마다 다른 순서로 수정한다.
- 조건 없는 대량 update/delete로 넓은 범위에 락을 건다.
- 인덱스가 없어 불필요하게 많은 row나 range를 스캔한다.
- 데드락은 버그가 아니므로 무조건 무시해도 된다고 생각한다.

## 확인 방법

- 테스트: 동시에 여러 요청을 보내 lost update, lock wait, deadlock을 재현한다.
- 로그: DB deadlock log, lock wait timeout, transaction rollback 로그를 확인한다.
- 메트릭: lock wait time, deadlock count, slow query, active transaction 수를 본다.
- 실행 계획: update/delete 조건이 인덱스를 타는지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 락은 동시 변경에서 정합성을 지킨다 | 대기와 데드락으로 성능 문제가 생길 수 있다 |
| pessimistic lock은 충돌을 사전에 막는다 | 락 보유 시간이 길면 처리량이 떨어진다 |
| optimistic lock은 경합이 낮을 때 효율적이다 | 충돌 시 재시도나 사용자 안내가 필요하다 |
| 조건부 update는 단순하고 빠르다 | 복잡한 업무 검증에는 한계가 있다 |

## 짧은 예제

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

재고 차감은 먼저 조회하고 나중에 저장하는 방식보다 조건부 update가 단순할 수 있다. DB가 한 SQL 안에서 조건 확인과 변경을 처리하므로 경쟁 조건을 줄일 수 있다.

## 핵심 요약

락은 동시에 같은 데이터를 수정할 때 정합성을 지키기 위한 장치다.

락 문제는 응답 지연, lock wait timeout, deadlock rollback으로 드러난다.

데드락은 여러 트랜잭션이 서로의 락을 기다리는 순환 대기 상태다.

실무에서는 트랜잭션을 짧게 유지하고, 인덱스를 맞추고, 자원 접근 순서를 고정해 위험을 줄인다.

경합이 높은 기능은 pessimistic lock, optimistic lock, 조건부 update, 큐잉 중 어떤 방식이 적합한지 업무 특성으로 판단한다.

## 꼬리 질문

- 락 대기와 데드락은 어떻게 다른가?
- optimistic lock과 pessimistic lock은 언제 선택하는가?
- 조건부 update가 동시성 문제를 줄이는 이유는 무엇인가?
- 데드락이 발생했을 때 애플리케이션은 재시도해야 하는가?

## 관련 문서

- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[lock]]
- [[db-index]]
