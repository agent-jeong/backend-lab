---
title: Race Condition과 Critical Section
description: 실행 순서에 따라 결과가 달라지는 코드 구간을 찾고 보호하는 기준
tags: [concept, concurrency]
---

# Race Condition과 Critical Section

Race Condition은 실행 순서에 따라 결과가 달라지는 경쟁 상태다. Critical Section은 동시에 실행되면 안 되는 공유 자원 접근 구간이다.

검증과 변경 사이에 다른 요청이 끼어들면 검증 결과는 무효가 된다. 카운터, 재고, 쿠폰, 포인트처럼 읽고-계산하고-쓰는 흐름에서 자주 생긴다. 빈도가 낮아 재현이 어렵고, 운영에서는 데이터 정합성 문제로 드러난다. 임계 구역은 코드 줄이 아니라 DB row, business key, 상태 전이를 기준으로 찾는다.

## 동작

1. 요청 A가 현재 값을 읽는다.
2. 요청 B도 같은 값을 읽는다.
3. 요청 A가 값을 계산해 저장한다.
4. 요청 B가 이전 값을 기준으로 계산한 값을 저장한다.
5. 요청 A의 변경이 사라지거나 중복 처리가 생긴다.

```java
@Modifying
@Query("""
    update Coupon c
       set c.issuedCount = c.issuedCount + 1
     where c.id = :couponId
       and c.issuedCount < c.maxIssueCount
""")
int increaseIssuedCount(Long couponId);
```

선착순 쿠폰 발급에서 "발급 수 조회 → 수량 확인 → 증가"를 따로 실행하면 race condition이 생긴다. 조건부 update는 조건 확인과 변경을 SQL 한 문장으로 처리해 임계 구역을 줄인다.

## 무엇으로 보호하나

| 상황 | 보호 방식 | 이유 |
|---|---|---|
| 같은 row 수량 차감 | 조건부 update | 검증과 변경을 하나의 SQL로 묶는다 |
| 복잡한 상태 검증 | 비관적 락 | 조회 후 판단 동안 다른 변경을 막는다 |
| 충돌이 드묾 | 낙관적 락 | 충돌 시 실패시키고 재시도한다 |
| 중복 생성 방지 | unique key | 최종 중복은 DB가 막는다 |
| 다중 서버 임계 구역 | DB 락 또는 분산 락 | JVM lock은 서버 밖을 보호하지 못한다 |

접근마다 대가가 있다. 임계 구역을 최소화하면 성능 영향이 줄지만 보호할 구간을 정확히 알아야 한다. 단일 SQL은 경쟁 조건을 줄이지만 로직이 복잡하면 SQL이 어려워진다. 락은 보호 범위가 명확한 대신 대기와 데드락 위험이 생긴다.

## 자주 깨지는 곳

- **임계 구역을 코드 블록으로만 본다.** 실제로 경쟁하는 DB row나 business key를 놓친다.
- **검증 쿼리와 변경 쿼리를 분리한다.** 그 사이가 바로 경쟁 조건이다.
- **lock을 잡은 채 외부 API를 호출한다.** 외부 지연이 락 보유 시간이 된다.
- **모든 코드를 큰 lock으로 감싼다.** 처리량이 크게 떨어지고 장애가 번진다.
- **재현하지 못했으니 문제가 없다고 판단한다.**

## 운영에서 볼 것

- `CountDownLatch`나 동시 요청 도구로 같은 자원에 요청을 동시에 보낸다.
- 같은 자원 id에 대한 요청 시작, 조회 값, 저장 결과를 시간순으로 본다.
- 실패율보다 최종 데이터 불변식 위반 count를 본다.
- DB에서 update 조건, unique key, lock wait 로그를 확인한다.

## 한 번에 설명하기

> Race Condition은 요청 실행 순서에 따라 결과가 달라지는 문제이고, Critical Section은 동시에 실행되면 안 되는 공유 자원 접근 구간입니다. 저는 임계 구역을 코드 줄이 아니라 DB row, business key, 상태 전이 기준으로 찾습니다. 검증과 변경을 분리하면 그 사이에 다른 요청이 끼어들기 때문에 조건부 update로 묶고, 임계 구역에는 외부 API나 긴 작업을 넣지 않습니다.

## 꼬리 질문

- Race Condition과 Critical Section은 어떻게 다른가?
- 검증과 변경을 하나의 SQL로 묶으면 어떤 장점이 있는가?
- 임계 구역을 넓게 잡으면 어떤 문제가 생기는가?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 잔액 검사와 사용 사이의 틈

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Java SE 21 API: java.util.concurrent.atomic](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/package-summary.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[unique-constraint-and-state-transition]]
- [[01-core/database/lock|lock]]
