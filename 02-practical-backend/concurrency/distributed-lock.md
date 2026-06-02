---
title: 분산 락
description: 다중 인스턴스 환경에서 특정 작업의 동시 실행을 제한하는 기준
---

# 분산 락

## 한 줄 정의

분산 락은 여러 서버 인스턴스가 같은 작업이나 자원에 동시에 접근하지 못하도록 외부 저장소를 사용해 잠금을 조정하는 방식이다.

## 실무에서 왜 문제 되는가

- 서버가 여러 대면 `synchronized`나 in-memory lock은 각 서버 안에서만 동작한다.
- 스케줄러, 쿠폰 발급, 재고 예약, 배치 실행처럼 동시에 한 번만 실행되어야 하는 작업이 있다.
- 락 만료 시간이 짧으면 작업 중 락이 풀리고, 길면 장애 후 복구가 늦어진다.
- 락을 얻었더라도 DB 정합성까지 자동으로 보장되는 것은 아니다.

## 동작 원리

1. 애플리케이션이 Redis 같은 외부 저장소에 lock key를 원자적으로 생성한다.
2. 성공한 요청만 임계 구역을 실행한다.
3. lock key에는 TTL을 둬 장애 시 영구 잠금을 막는다.
4. 작업이 끝나면 자신이 획득한 락인지 확인하고 해제한다.
5. 락 획득 실패 요청은 대기, 재시도, 실패 응답 중 하나를 선택한다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 다중 서버에서 한 번만 실행 | 분산 락 | JVM lock으로는 보호할 수 없다 |
| DB row 정합성 보호 | DB 락 또는 제약 조건 우선 | 분산 락은 DB 불변식의 최종 방어선이 아니다 |
| 작업 시간이 예측 가능 | TTL 설정 가능 | 만료 전 완료 가능성을 판단해야 한다 |
| 작업 시간이 길거나 불확실 | lease 연장 또는 다른 설계 | TTL 만료 후 중복 실행 위험이 있다 |
| 중복 실행 가능하지만 결과 중복 금지 | 멱등성 우선 | 락 실패보다 결과 정합성이 중요하다 |
| 락 이후 외부 저장소에 쓰기 | fencing token 검토 | TTL 만료 후 늦게 끝난 작업의 stale write를 막는다 |

## 자주 나는 실수

- Redis 분산 락을 쓰면 DB 정합성이 자동으로 보장된다고 생각한다.
- TTL 없이 락을 잡아 장애 시 영구 잠금이 생긴다.
- 락 value를 확인하지 않고 삭제해 다른 요청의 락을 해제한다.
- 락 만료 시간보다 작업 시간이 길어 중복 실행이 발생한다.
- TTL 만료 후 이전 작업이 계속 실행되어 뒤늦게 결과를 덮어쓰는 상황을 고려하지 않는다.
- 락 획득 실패 시 무한 대기하거나 과도하게 재시도한다.

## 확인 방법

- 테스트: 여러 인스턴스 또는 여러 스레드에서 동시에 락 획득을 시도한다.
- 로그: lock key, owner token, TTL, 획득 성공/실패, 해제 결과를 남긴다.
- 메트릭: lock acquire latency, failure count, timeout count를 본다.
- 장애 실험: 작업 중 프로세스 종료, Redis timeout, TTL 만료 상황을 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 다중 서버의 동시 실행을 제한할 수 있다 | 외부 저장소 장애에 영향을 받는다 |
| 스케줄러와 배치 중복 실행 방지에 유용하다 | DB 정합성 보장을 대체하지 못한다 |
| TTL로 영구 잠금을 줄일 수 있다 | TTL 설정이 잘못되면 중복 실행이나 장기 대기가 생긴다 |

## 짧은 예제

```java
boolean locked = redisLock.tryLock("coupon:issue:" + couponId, ownerToken, Duration.ofSeconds(5));
if (!locked) {
    throw new LockAcquireFailedException();
}

try {
    couponService.issue(userId, couponId);
} finally {
    redisLock.unlock("coupon:issue:" + couponId, ownerToken);
}
```

락 해제 시에는 owner token을 확인해야 한다. TTL이 만료된 뒤 다른 요청이 같은 key로 락을 획득했는데, 이전 요청이 단순 delete를 실행하면 다른 요청의 락을 지울 수 있다. 다만 owner token은 안전한 해제를 위한 값이지, TTL 만료 후 이전 작업의 늦은 쓰기까지 막아주지는 않는다. 그런 상황에서는 단조 증가하는 fencing token을 저장소 쓰기 조건에 포함하는 방식도 검토한다.

## 핵심 요약

분산 락은 다중 서버 환경에서 특정 작업의 동시 실행을 제한한다.

Redis 같은 외부 저장소를 사용하므로 원자적 획득, TTL, 안전한 해제가 중요하다.

분산 락은 DB 정합성의 최종 방어선이 아니며 unique key, 상태 전이, 트랜잭션과 함께 설계해야 한다.

TTL은 장애 복구와 중복 실행 위험 사이의 균형이다.

TTL 만료 후에도 이전 작업이 계속 실행될 수 있으므로 stale write 방어가 필요한지 확인해야 한다.

락 획득 실패 시 대기, 재시도, 실패 응답 정책을 명확히 정해야 한다.

## 꼬리 질문

- 분산 락과 DB 락은 어떤 차이가 있는가?
- Redis 락을 해제할 때 owner token을 확인해야 하는 이유는 무엇인가?
- 락 TTL은 어떻게 정해야 하는가?
- 분산 락이 있어도 멱등성이 필요한 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/redis/redis-distributed-lock|redis-distributed-lock]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
