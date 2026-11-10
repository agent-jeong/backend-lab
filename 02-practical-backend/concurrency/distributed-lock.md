---
title: 분산 락
description: 다중 인스턴스 환경에서 특정 작업의 동시 실행을 제한하는 기준
---

# 분산 락

분산 락은 여러 서버 인스턴스가 같은 작업이나 자원에 동시에 들어가지 못하도록, Redis 같은 외부 저장소로 잠금을 조정하는 방식이다.

서버가 여러 대면 `synchronized`나 in-memory lock은 각 서버 안에서만 동작한다. 스케줄러, 쿠폰 발급, 재고 예약, 배치처럼 한 번만 돌아야 하는 작업에 분산 락을 쓴다. 다만 락을 얻었다고 DB 정합성까지 보장되지는 않는다. 분산 락은 동시 실행을 줄이는 장치이지 최종 방어선이 아니다.

## 동작

1. Redis 같은 외부 저장소에 lock key를 원자적으로 만든다.
2. 성공한 요청만 임계 구역을 실행한다.
3. lock key에는 TTL을 둬서, 락을 쥔 프로세스가 죽어도 영구 잠금이 되지 않게 한다.
4. 작업이 끝나면 자신이 잡은 락인지 확인하고 해제한다.
5. 락을 못 얻은 요청은 대기, 재시도, 실패 응답 중 하나를 고른다.

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

해제할 때는 owner token을 확인한다. TTL이 만료된 뒤 다른 요청이 같은 key로 락을 잡았는데 이전 요청이 단순 delete를 하면 남의 락을 지운다. 그러나 owner token은 안전한 해제를 위한 값일 뿐, TTL 만료 후 이전 작업이 늦게 쓰는 것까지 막지는 못한다. 그런 상황이면 단조 증가하는 fencing token을 저장소 쓰기 조건에 넣는 방식도 검토한다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 다중 서버에서 한 번만 실행 | 분산 락 | JVM lock으로는 보호할 수 없다 |
| DB row 정합성 보호 | DB 락 또는 제약 조건 우선 | 분산 락은 DB 불변식의 최종 방어선이 아니다 |
| 작업 시간이 예측 가능 | TTL 설정 가능 | 만료 전에 끝나는지 판단할 수 있다 |
| 작업 시간이 길거나 불확실 | lease 연장 또는 다른 설계 | TTL 만료 후 중복 실행 위험이 있다 |
| 중복 실행은 되지만 결과 중복은 안 됨 | 멱등성 우선 | 락 실패보다 결과 정합성이 우선이다 |
| 락 이후 외부 저장소에 쓰기 | fencing token 검토 | TTL 만료 후 늦게 끝난 작업의 stale write를 막는다 |

## 자주 깨지는 곳

- **분산 락이면 DB 정합성도 지켜진다고 믿는다.** 두 실행이 겹치는 경우가 있어서 DB 제약이나 조건부 update로 한 번 더 막아야 한다.
- **TTL 없이 락을 잡는다.** 프로세스가 죽으면 영구 잠금이 된다.
- **TTL을 잘못 잡는다.** 짧으면 작업 중에 락이 풀려 중복 실행되고, 길면 장애 후 복구가 늦어진다.
- **value를 확인하지 않고 삭제한다.** 다른 요청의 락을 해제한다.
- **TTL 만료 뒤의 늦은 쓰기를 잊는다.** 이전 작업이 계속 돌다가 뒤늦게 결과를 덮어쓴다.
- **획득 실패 시 무한 대기하거나 과하게 재시도한다.**
- **Redis 복제가 비동기라는 점을 놓친다.** primary가 락을 쓴 직후 죽고 replica가 승격되면 락이 사라져 두 요청이 동시에 임계 구역에 들어갈 수 있다. Redlock도 GC pause나 시계 오차 앞에서는 안전하다고 단정하기 어렵다. 정합성이 걸린 곳은 DB 제약이나 fencing token으로 한 번 더 막는다.
- **외부 저장소 장애를 생각하지 않는다.** Redis가 느려지거나 죽으면 락을 쓰는 기능 전체가 영향을 받는다.

## 운영에서 볼 것

- lock key, owner token, TTL, 획득 성공/실패, 해제 결과를 로그로 남긴다.
- lock acquire latency, failure count, timeout count를 본다.
- 여러 인스턴스나 스레드에서 동시에 락 획득을 시도하는 테스트를 둔다.
- 작업 중 프로세스 종료, Redis timeout, TTL 만료 상황을 장애 실험으로 확인한다.

## 면접에서 말하기

> 분산 락은 여러 서버에서 같은 작업이 동시에 도는 것을 줄이는 장치입니다. 원자적 획득, TTL, owner token을 확인한 뒤 해제하는 것이 기본입니다. 다만 TTL 만료, Redis failover, GC pause 때문에 두 실행이 겹칠 수 있어서, 저는 분산 락을 DB 정합성의 최종 방어선으로 보지 않습니다. unique 제약, 조건부 update, fencing token으로 한 번 더 막습니다.

## 꼬리 질문

- 분산 락과 DB 락은 어떤 차이가 있는가?
- Redis 락을 해제할 때 owner token을 확인해야 하는 이유는 무엇인가?
- 락 TTL은 어떻게 정해야 하는가?
- 분산 락이 있어도 멱등성이 필요한 이유는 무엇인가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/redis/redis-distributed-lock|redis-distributed-lock]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
