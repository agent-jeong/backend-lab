---
title: 동시성 문제가 생기는 이유
description: 여러 요청이 같은 공유 자원을 동시에 변경할 때 발생하는 정합성 문제
tags: [concept, concurrency]
---

# 동시성 문제가 생기는 이유

동시성 문제는 둘 이상의 요청이 같은 공유 자원을 동시에 읽고 쓰면서, 실행 순서에 따라 결과가 달라지는 문제다.

재고가 1개인데 두 주문이 모두 성공하고, 같은 쿠폰이 여러 번 발급되고, 같은 사용자가 중복 가입된다. 단일 요청 테스트는 통과하고 운영 트래픽에서만 간헐적으로 터진다. 그래서 먼저 "어떤 자원이 공유되는가"와 "어떤 불변식이 깨지는가"를 찾는다.

## 동작

1. 요청 A와 B가 같은 데이터를 거의 동시에 조회한다.
2. 두 요청 모두 현재 상태가 유효하다고 판단한다.
3. 각 요청이 따로 변경 값을 계산한다.
4. 나중에 저장한 요청이 먼저 저장한 결과를 덮어쓰거나 중복 변경을 만든다.
5. 업무 불변식이 깨진다.

```java
@Transactional
public void unsafeDecreaseStock(Long productId, int quantity) {
    Product product = productRepository.findById(productId).orElseThrow();
    if (product.getStock() < quantity) {
        throw new SoldOutException();
    }
    product.decreaseStock(quantity);
}
```

단일 요청에서는 정상으로 보이는 코드다. 두 요청이 동시에 같은 재고를 조회하면 둘 다 검증을 통과한다. 이런 흐름은 조건부 update, 비관적 락, 낙관적 락 중 하나로 보호한다.

## 먼저 확인할 것

| 상황 | 먼저 확인할 것 | 이유 |
|---|---|---|
| 같은 row를 여러 요청이 수정 | lost update 가능성 | 조회 후 저장 패턴이 위험하다 |
| 중복 생성이 문제 | unique key | 애플리케이션 if문보다 DB 제약이 강하다 |
| 상태가 순서대로 바뀌어야 함 | 상태 전이 조건 | 이미 처리된 상태를 다시 처리하면 안 된다 |
| 외부 요청 재시도 포함 | 멱등성 key | 재시도와 동시 요청이 함께 온다 |
| 다중 인스턴스 환경 | JVM lock 한계 | `synchronized`는 한 프로세스 안에서만 보호한다 |

## 해결 접근의 대가

| 해결 접근 | 장점 | 한계 |
|---|---|---|
| DB 제약 조건 | 최종 방어선이 강하다 | 예외 처리와 사용자 응답 설계가 필요하다 |
| 조건부 update | 단일 SQL로 경쟁 조건을 줄인다 | 복잡한 검증에는 한계가 있다 |
| 락 | 임계 구역을 명확히 보호한다 | 대기, 데드락, 처리량 저하가 생긴다 |
| 멱등성 | 중복 요청과 재시도에 강하다 | key 저장과 만료 정책이 필요하다 |

어느 것을 쓸지는 정합성 요구사항, 경합 빈도, 재시도 가능성으로 정한다.

## 자주 깨지는 곳

- **조회 후 저장이 항상 안전하다고 생각한다.**
- **`if (stock > 0)` 검증만으로 재고를 지킨다고 생각한다.** 검증과 차감 사이에 다른 요청이 끼어든다.
- **서버가 여러 대인데 `synchronized`나 in-memory lock으로 해결하려 한다.**
- **DB 제약 없이 애플리케이션 코드로만 중복을 막는다.**
- **단일 요청 테스트만 작성한다.**

## 운영에서 볼 것

- 같은 API를 동시에 여러 번 호출해 최종 DB 상태를 검증한다.
- 요청 id, 대상 자원 id, 조회 값, 변경 값, 저장 결과를 로그로 남긴다.
- lock wait, deadlock, retry count, 중복 실패 count를 본다.
- unique key, version column, check constraint가 있는지 확인한다.

## 면접에서 말하기

> 동시성 문제는 여러 요청이 같은 공유 자원을 동시에 바꿀 때 생깁니다. 저는 먼저 어떤 자원이 공유되고 어떤 불변식이 깨지는지를 찾습니다. 해결책은 락만 보지 않고 DB 제약, 조건부 update, 상태 전이, 멱등성을 같이 놓고, 정합성 요구사항과 경합 빈도, 재시도 가능성에 따라 고릅니다.

## 꼬리 질문

- 동시성 문제는 왜 단위 테스트에서 잘 드러나지 않는가?
- `synchronized`는 다중 서버 환경에서 왜 한계가 있는가?
- 조회 후 저장 패턴이 위험한 경우는 무엇인가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [JLS 21: Threads and Locks](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)
- [MySQL 8.4: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
