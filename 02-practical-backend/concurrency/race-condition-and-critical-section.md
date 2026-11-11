---
title: Race Condition과 Critical Section
description: 실행 순서에 따라 결과가 바뀌는 구간을 찾아 막는 방법
tags: [concept, concurrency]
---

# Race Condition과 Critical Section

Race Condition(경쟁 조건)은 요청이 어떤 순서로 실행되느냐에 따라 결과가 달라지는 상태다. Critical Section(임계 구역)은 공유 자원을 건드리는 구간 가운데 동시에 실행되면 안 되는 부분이다.

선착순 쿠폰을 예로 들면, 남은 수량을 확인한 뒤 발급하기 전에 다른 요청이 끼어들면 방금 한 확인은 쓸모가 없어진다. 카운터, 재고, 쿠폰, 포인트처럼 값을 읽고, 계산하고, 다시 쓰는 흐름에서 자주 생긴다. 드물게 일어나서 재현하기 어렵고, 운영에서는 숫자가 안 맞는 데이터로 드러난다. 임계 구역은 코드 몇 번째 줄이 아니라 어떤 DB 행, 어떤 업무 키(business key), 어떤 상태 전이를 두고 다투는지로 찾는다.

## 동작

1. 요청 A가 현재 값을 읽는다.
2. 요청 B도 같은 값을 읽는다.
3. 요청 A가 새 값을 계산해 저장한다.
4. 요청 B가 처음 읽은 값으로 계산한 결과를 저장한다.
5. 요청 A의 변경이 사라지거나, 같은 일이 두 번 처리된다.

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

선착순 쿠폰 발급에서 발급 수를 조회하고, 수량을 확인하고, 하나 늘리는 일을 따로따로 실행하면 경쟁 조건이 생긴다. 조건부 update는 확인과 변경을 SQL 한 문장으로 처리해서 임계 구역을 줄인다.

## 무엇으로 보호하나

| 상황 | 보호 방식 | 이유 |
|---|---|---|
| 같은 row 수량 차감 | 조건부 update | 검증과 변경을 하나의 SQL로 묶는다 |
| 복잡한 상태 검증 | 비관적 락 | 조회 후 판단 동안 다른 변경을 막는다 |
| 충돌이 드묾 | 낙관적 락 | 충돌 시 실패시키고 재시도한다 |
| 중복 생성 방지 | unique key | 최종 중복은 DB가 막는다 |
| 다중 서버 임계 구역 | DB 락 또는 분산 락 | JVM lock은 서버 밖을 보호하지 못한다 |

방법마다 치르는 값이 있다. 임계 구역을 좁히면 성능 영향은 줄지만, 지켜야 할 구간을 정확히 알아야 한다. SQL 한 문장으로 묶으면 경쟁 조건은 줄지만, 로직이 복잡하면 SQL이 어려워진다. 락은 어디를 지키는지 분명한 대신 기다림과 데드락이 생긴다.

## 자주 깨지는 곳

- 임계 구역을 코드 블록으로만 보면, 실제로 다투는 DB 행이나 업무 키를 놓친다.
- 확인하는 쿼리와 바꾸는 쿼리를 따로 날리면, 그 사이가 바로 경쟁 조건이 된다.
- 락을 잡은 채 외부 API를 부르면, 외부가 느린 만큼 락을 오래 쥔다.
- 코드 전체를 큰 락으로 감싸면, 처리량이 크게 떨어지고 한 곳의 지연이 전체로 번진다.
- 재현이 안 됐다고 문제가 없다고 판단하면, 운영 트래픽에서 같은 문제를 만난다.

## 운영에서 볼 것

- `CountDownLatch`나 부하 도구로 같은 자원에 요청을 동시에 보낸다.
- 같은 자원 id에 대해 요청 시작, 읽은 값, 저장 결과를 시간순으로 본다.
- 실패율보다 최종 데이터가 규칙을 어긴 건수를 본다.
- DB에서 update 조건, unique key, lock wait 로그를 확인한다.

## 한 번에 설명하기

> Race Condition은 요청이 실행되는 순서에 따라 결과가 달라지는 문제이고, Critical Section은 공유 자원을 건드리는 구간 가운데 동시에 실행되면 안 되는 부분입니다.
>
> 저는 임계 구역을 코드 줄이 아니라 어떤 DB 행, 업무 키, 상태 전이를 두고 다투는지로 찾습니다.
>
> 확인과 변경을 따로 하면 그 사이에 다른 요청이 끼어들기 때문에 조건부 update로 묶습니다. 임계 구역 안에는 외부 API나 오래 걸리는 작업을 넣지 않습니다.

## 꼬리 질문

- Race Condition과 Critical Section은 어떻게 다른가?
- 확인과 변경을 SQL 한 문장으로 묶으면 무엇이 좋아지나?
- 임계 구역을 넓게 잡으면 어떤 문제가 생기나?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 잔액 검사와 사용 사이의 틈

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: java.util.concurrent.atomic](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/package-summary.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[unique-constraint-and-state-transition]]
- [[01-core/database/lock|lock]]
