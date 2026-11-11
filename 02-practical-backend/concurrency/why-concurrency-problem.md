---
title: 동시성 문제가 생기는 이유
description: 여러 요청이 같은 데이터를 동시에 바꾸면 왜 숫자가 틀어지는지
tags: [concept, concurrency]
---

# 동시성 문제가 생기는 이유

동시성 문제는 요청 둘 이상이 같은 데이터를 동시에 읽고 쓰면서, 어떤 순서로 실행됐느냐에 따라 결과가 달라지는 문제다.

재고가 1개 남았는데 주문 두 건이 모두 성공하거나, 같은 쿠폰이 여러 번 발급되거나, 같은 사용자가 두 번 가입되는 식이다. 요청을 하나씩 보내는 테스트는 통과하고, 운영 트래픽에서만 가끔 터진다. 그래서 먼저 "어떤 데이터를 여러 요청이 같이 쓰는가"와 "어떤 규칙이 깨지는가"를 찾는다.

## 동작

1. 요청 A와 B가 같은 데이터를 거의 동시에 조회한다.
2. 두 요청 모두 지금 상태로는 처리해도 된다고 판단한다.
3. 각자 바꿀 값을 따로 계산한다.
4. 나중에 저장한 요청이 먼저 저장한 결과를 덮어쓰거나, 같은 변경이 두 번 들어간다.
5. 재고가 음수가 되는 식으로 업무 규칙이 깨진다.

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

요청이 하나일 때는 멀쩡해 보이는 코드다. 하지만 두 요청이 동시에 같은 재고를 조회하면 둘 다 검사를 통과한다. 이런 흐름은 조건부 update, 비관적 락, 낙관적 락 중 하나로 막는다.

## 먼저 확인할 것

| 상황 | 먼저 확인할 것 | 이유 |
|---|---|---|
| 같은 row를 여러 요청이 수정 | lost update 가능성 | 조회 후 저장 패턴이 위험하다 |
| 중복 생성이 문제 | unique key | 애플리케이션 if문보다 DB 제약이 강하다 |
| 상태가 순서대로 바뀌어야 함 | 상태 전이 조건 | 이미 처리된 상태를 다시 처리하면 안 된다 |
| 외부 요청 재시도 포함 | 멱등성 key | 재시도와 동시 요청이 함께 온다 |
| 다중 인스턴스 환경 | JVM lock 한계 | `synchronized`는 한 프로세스 안에서만 보호한다 |

## 해결 방법마다 치르는 값

| 해결 접근 | 장점 | 한계 |
|---|---|---|
| DB 제약 조건 | 최종 방어선이 강하다 | 예외 처리와 사용자 응답 설계가 필요하다 |
| 조건부 update | 단일 SQL로 경쟁 조건을 줄인다 | 복잡한 검증에는 한계가 있다 |
| 락 | 임계 구역을 명확히 보호한다 | 대기, 데드락, 처리량 저하가 생긴다 |
| 멱등성 | 중복 요청과 재시도에 강하다 | key 저장과 만료 정책이 필요하다 |

어느 것을 쓸지는 데이터가 얼마나 정확해야 하는지, 충돌이 얼마나 자주 나는지, 재시도가 들어오는지를 보고 정한다.

## 자주 깨지는 곳

- 조회한 뒤 저장하는 코드가 늘 안전하다고 생각하면, 동시에 들어온 요청 하나의 변경이 사라진다.
- `if (stock > 0)` 검사만으로 재고를 지킨다고 생각하면, 검사와 차감 사이에 다른 요청이 끼어든다.
- 서버가 여러 대인데 `synchronized`나 메모리 안의 락으로 막으려 하면, 다른 서버에서 들어온 요청은 그대로 통과한다.
- DB 제약 없이 애플리케이션 코드로만 중복을 막으면, 동시에 들어온 요청이 같이 검사를 통과한다.
- 요청을 하나씩 보내는 테스트만 쓰면, 동시성 문제는 운영에서 처음 보게 된다.

## 운영에서 볼 것

- 같은 API를 동시에 여러 번 불러서 최종 DB 상태를 확인한다.
- 요청 id, 대상 자원 id, 읽은 값, 바꾼 값, 저장 결과를 로그로 남긴다.
- lock wait, deadlock, 재시도 횟수, 중복으로 실패한 횟수를 본다.
- unique key, version 컬럼, check constraint가 있는지 확인한다.

## 한 번에 설명하기

> 동시성 문제는 여러 요청이 같은 데이터를 동시에 바꿀 때 생깁니다. 저는 먼저 어떤 데이터를 여러 요청이 같이 쓰는지, 그리고 어떤 규칙이 깨지는지부터 찾습니다.
>
> 막는 방법은 락만 보지 않습니다. DB 제약, 조건부 update, 상태 전이, 멱등성을 함께 놓고, 데이터가 얼마나 정확해야 하는지, 충돌이 얼마나 잦은지, 재시도가 들어오는지에 따라 고릅니다.

## 꼬리 질문

- 동시성 문제는 왜 단위 테스트에서 잘 안 보이나?
- 서버가 여러 대면 `synchronized`로 왜 안 되나?
- 조회한 뒤 저장하는 코드가 위험한 경우는?

## 참고

2026년 11월에 확인한 공식 문서다.

- [JLS 21: Threads and Locks](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)
- [MySQL 8.4: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[02-practical-backend/transaction/transaction|transaction]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
