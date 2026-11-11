---
title: 분산 락
description: 서버가 여러 대일 때 같은 작업이 동시에 돌지 않게 막는 방법과 그 한계
tags: [concept, concurrency]
---

# 분산 락

분산 락은 여러 서버가 같은 작업이나 자원에 동시에 들어가지 못하게, Redis 같은 외부 저장소에 잠금을 두고 서로 확인하는 방식이다.

서버가 여러 대면 `synchronized`나 메모리 안의 락은 각 서버 안에서만 통한다. 스케줄러, 쿠폰 발급, 재고 예약, 배치처럼 전체에서 한 번만 돌아야 하는 작업에 분산 락을 쓴다. 다만 락을 얻었다고 DB 데이터가 맞는다는 보장은 없다. 분산 락은 동시에 도는 일을 줄여 줄 뿐이고, 마지막에 막아 주는 건 DB다.

> [!tip] 함께 읽기
> - [[redis-distributed-lock]]: Redis로 구현할 때의 동작과 실패 모드

## 동작

1. Redis 같은 외부 저장소에 lock key를 원자적으로 만든다.
2. 만드는 데 성공한 요청만 임계 구역을 실행한다.
3. lock key에는 TTL을 둬서, 락을 쥔 프로세스가 죽어도 영원히 잠기지 않게 한다.
4. 작업이 끝나면 자기가 잡은 락인지 확인하고 푼다.
5. 락을 못 얻은 요청은 기다리거나, 다시 시도하거나, 실패로 응답한다.

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

풀 때는 owner token을 확인한다. TTL이 지나 다른 요청이 같은 key로 락을 잡았는데 앞선 요청이 그냥 delete하면 남의 락을 지운다. 하지만 owner token은 남의 락을 지우지 않게 할 뿐, TTL이 지난 뒤 앞선 작업이 늦게 쓰는 것까지 막지는 못한다. 그런 경우가 걱정되면 계속 커지는 번호(fencing token)를 저장소 쓰기 조건에 넣는 방법을 검토한다.

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

- 분산 락이 있으니 DB 데이터도 맞을 거라고 믿으면, 두 실행이 겹친 날 데이터가 틀어진다. DB 제약이나 조건부 update로 한 번 더 막아야 한다.
- TTL 없이 락을 잡으면, 프로세스가 죽었을 때 영원히 잠긴다.
- TTL이 너무 짧으면 작업 중에 락이 풀려 두 번 돌고, 너무 길면 장애 뒤 다시 돌기까지 오래 걸린다.
- value를 확인하지 않고 지우면, 다른 요청의 락을 풀어 버린다.
- TTL이 지난 뒤의 늦은 쓰기를 잊으면, 앞선 작업이 계속 돌다가 나중 작업의 결과를 덮어쓴다.
- 락을 못 얻었을 때 끝없이 기다리거나 너무 자주 다시 시도하면, 요청이 쌓이고 Redis 부하가 커진다.
- Redis 복제가 비동기라는 걸 놓치면 락이 사라지는 경우를 못 본다. primary가 락을 쓴 직후 죽고 replica가 승격되면 락이 없어져, 두 요청이 동시에 임계 구역에 들어간다. Redlock도 GC pause나 시계 오차가 있으면 안전하다고 단정하기 어렵다. 데이터가 맞아야 하는 곳은 DB 제약이나 fencing token으로 한 번 더 막는다.
- 외부 저장소 장애를 생각하지 않으면, Redis가 느려지거나 죽었을 때 락을 쓰는 기능이 전부 멈춘다.

## 운영에서 볼 것

- lock key, owner token, TTL, 획득 성공 여부, 해제 결과를 로그로 남긴다.
- 락 획득 latency, 실패 횟수, timeout 횟수를 본다.
- 여러 인스턴스나 스레드에서 동시에 락을 잡으려는 테스트를 둔다.
- 작업 중 프로세스 종료, Redis timeout, TTL 만료를 장애 실험으로 확인한다.

## 한 번에 설명하기

> 분산 락은 여러 서버에서 같은 작업이 동시에 도는 걸 줄이는 장치입니다. 원자적으로 잡고, TTL을 두고, 풀 때 owner token을 확인하는 게 기본입니다.
>
> 그래도 TTL 만료, Redis failover, GC pause 때문에 두 실행이 겹칠 수 있습니다. 그래서 저는 분산 락에 DB 정합성을 맡기지 않습니다.
>
> unique 제약, 조건부 update, fencing token으로 한 번 더 막습니다.

## 꼬리 질문

- 분산 락과 DB 락은 무엇이 다른가?
- Redis 락을 풀 때 owner token을 확인해야 하는 이유는?
- 락 TTL은 어떻게 정하나?
- 분산 락이 있어도 멱등성이 필요한 이유는?

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: `GET_LOCK`과 ShedLock 비교
- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: 분산 락의 틈

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- [Martin Kleppmann: How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[01-core/redis/redis-distributed-lock|redis-distributed-lock]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
