---
title: Race Condition과 Critical Section
description: 실행 순서에 따라 결과가 달라지는 코드 구간을 찾고 보호하는 기준
---

# Race Condition과 Critical Section

## 한 줄 정의

Race Condition은 실행 순서에 따라 결과가 달라지는 경쟁 상태이고, Critical Section은 동시에 실행되면 안 되는 공유 자원 접근 구간이다.

## 실무에서 왜 문제 되는가

- 검증과 변경 사이에 다른 요청이 끼어들면 검증 결과가 무효가 된다.
- 카운터, 재고, 쿠폰, 포인트처럼 읽기-계산-쓰기 흐름이 있는 기능에서 자주 발생한다.
- 문제 발생 빈도가 낮아 재현이 어렵고, 운영에서는 데이터 정합성 문제로 드러난다.
- 임계 구역을 너무 넓게 보호하면 성능 저하와 장애 전파가 커진다.

## 동작 원리

1. 요청 A가 현재 값을 읽는다.
2. 요청 B도 같은 값을 읽는다.
3. 요청 A가 값을 계산하고 저장한다.
4. 요청 B가 이전 값을 기준으로 계산한 값을 저장한다.
5. 요청 A의 변경이 사라지거나 중복 처리가 발생한다.

## 실무 판단 기준

| 상황 | 보호 방식 | 이유 |
|---|---|---|
| 같은 row 수량 차감 | 조건부 update | 검증과 변경을 하나의 SQL로 묶는다 |
| 복잡한 상태 검증 | 비관적 락 | 조회 후 판단 동안 다른 변경을 막는다 |
| 충돌이 드묾 | 낙관적 락 | 충돌 시 실패시키고 재시도한다 |
| 중복 생성 방지 | unique key | 최종 중복은 DB가 막는다 |
| 다중 서버 임계 구역 | DB 락 또는 분산 락 | JVM lock은 서버 밖을 보호하지 못한다 |

## 자주 나는 실수

- 임계 구역을 코드 블록 기준으로만 생각하고 DB row나 business key를 놓친다.
- 검증 쿼리와 변경 쿼리를 분리해 경쟁 조건을 만든다.
- lock을 잡은 상태에서 외부 API를 호출한다.
- 모든 코드를 큰 lock으로 감싸 처리량을 크게 떨어뜨린다.
- race condition을 재현하지 못했다고 문제가 없다고 판단한다.

## 확인 방법

- 테스트: `CountDownLatch`나 동시 요청 도구로 같은 자원에 요청을 동시에 보낸다.
- 로그: 같은 자원 id에 대한 요청 시작, 조회 값, 저장 결과를 시간순으로 본다.
- 메트릭: 실패율보다 최종 데이터 불변식 위반 count를 확인한다.
- DB: update 조건, unique key, lock wait 로그를 확인한다.

## 장점과 한계

| 접근 | 장점 | 한계 |
|---|---|---|
| 임계 구역 최소화 | 성능 영향을 줄인다 | 보호해야 할 구간을 정확히 알아야 한다 |
| 단일 SQL 처리 | 경쟁 조건을 줄인다 | 로직이 복잡하면 SQL이 어려워진다 |
| 락 사용 | 보호 범위가 명확하다 | 대기와 데드락 위험이 생긴다 |

## 짧은 예제

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

선착순 쿠폰 발급에서는 "발급 수 조회 → 수량 확인 → 증가"를 분리하면 race condition이 생긴다. 조건부 update는 조건 확인과 변경을 하나의 SQL로 처리해 임계 구역을 줄인다.

## 핵심 요약

Race Condition은 요청 실행 순서에 따라 결과가 달라지는 문제다.

Critical Section은 동시에 실행되면 안 되는 공유 자원 접근 구간이다.

실무에서는 코드 줄보다 DB row, business key, 상태 전이 기준으로 임계 구역을 찾는다.

검증과 변경을 분리하면 그 사이에 다른 요청이 끼어들 수 있다.

임계 구역은 정확히 보호하되, 외부 API나 긴 작업까지 포함하지 않도록 최소화한다.

## 꼬리 질문

- Race Condition과 Critical Section은 어떻게 다른가?
- 검증과 변경을 하나의 SQL로 묶으면 어떤 장점이 있는가?
- 임계 구역을 넓게 잡으면 어떤 문제가 생기는가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[unique-constraint-and-state-transition]]
- [[01-core/database/lock|lock]]
