---
title: Redis 분산 락
description: Redis 분산 락을 사용할 때의 동작 원리와 실패 모드
tags: [concept, redis]
---

# Redis 분산 락

Redis 분산 락은 Redis key 하나를 원자적으로 선점해서, 여러 서버 인스턴스가 같은 작업을 동시에 처리하지 않게 하는 방식이다. 서버가 여러 대면 JVM의 `synchronized`나 로컬 락으로는 중복 실행을 막지 못한다.

다만 분산 락은 동시 실행을 **줄이는** 도구이지, DB 정합성을 대신하지 않는다. 중복되면 안 되는 작업은 결국 DB에서 막는다.

> [!tip] 함께 읽기
> - [[distributed-lock]]: 분산 락이 필요한지부터 판단하는 기준

## 동작

1. 작업 시작 전 `SET key value NX PX milliseconds`로 lock key를 저장한다.
2. 저장에 성공한 요청만 작업을 수행한다.
3. lock key에는 TTL과 소유자 token을 함께 둔다.
4. 작업이 끝나면 Lua script 등으로 token 확인과 key 삭제를 한 번에 원자적으로 수행한다.
5. 작업 중 서버가 죽으면 TTL이 지나 lock key가 만료된다.

획득은 `NX`와 TTL을 한 명령으로 걸어야 하고, 해제는 "내 token인지 확인"과 삭제를 한 번에 해야 한다. 둘 중 하나라도 명령을 나누면 그 틈에 다른 요청이 끼어든다.

## 락이 깨지는 두 장면

`SET NX PX`와 Lua 해제를 제대로 해도 아래 두 경우는 막지 못한다.

| 장면 | 무슨 일이 생기나 | 대응 |
|---|---|---|
| 작업이 TTL보다 길어짐 (GC pause, 외부 API 지연) | 락이 만료되고 B가 락을 잡는다. A는 자기가 아직 락을 가졌다고 믿고 쓰기를 계속한다 | 쓰기 대상에 fencing token(락 획득마다 증가하는 번호)을 넘기고, DB가 더 작은 번호의 쓰기를 거부하게 한다. 또는 `UPDATE ... WHERE version = ?` 같은 조건부 쓰기 |
| master 장애 후 replica 승격 | Redis 복제는 비동기라 락 key가 replica에 복제되기 전에 master가 죽을 수 있다. 승격된 replica에는 락이 없어 B도 락을 잡는다 | 락이 잠깐 중복될 수 있다고 가정하고 DB 제약·멱등키로 최종 방어한다 |

결국 Redis 락은 "대부분의 경우 한 번만 실행"을 싸게 얻는 도구다. "절대 두 번 실행되면 안 되는" 작업의 최종 방어선은 DB에 둔다.

## 언제 쓰나

| 상황 | 분산 락 판단 | 이유 |
|---|---|---|
| 중복 실행돼도 재시도 가능 | 맞다 | 락을 못 잡으면 나중에 다시 처리하면 된다 |
| 결제 승인처럼 정합성이 매우 중요 | 보조 수단 | DB 제약, 멱등키, 상태 체크가 함께 있어야 한다 |
| 작업 시간이 예측 가능 | 맞다 | TTL을 근거 있게 정할 수 있다 |
| 작업 시간이 길고 들쭉날쭉 | 조심 | TTL 연장, 작업 분할, 큐 기반 처리를 검토한다 |
| 단일 DB row 갱신 경쟁 | DB 락 먼저 검토 | 데이터 정합성은 DB가 더 직접 보장한다 |
| Redis 장애 중에도 꼭 한 번만 실행 | 안 맞다 | 락 저장소 장애와 네트워크 분리를 완전히 없앨 수 없다 |

## 자주 깨지는 곳

- **`SETNX` 뒤에 `EXPIRE`를 따로 건다.** 그 사이 서버가 죽으면 TTL 없는 락이 영원히 남는다.
- **소유자 확인 없이 key를 지운다.** 내 락이 이미 만료됐다면 남의 락을 지운다. token 확인과 삭제를 별도 명령으로 나눠도 같은 race가 생긴다.
- **TTL을 작업 시간보다 짧게 잡는다.** 작업이 끝나기 전에 다른 요청이 락을 얻어 중복 실행된다.
- **락 획득 실패를 성공처럼 처리한다.** 락을 못 잡은 요청도 그대로 작업을 진행한다.
- **분산 락이 있으니 DB unique constraint나 상태 검증을 뺀다.** 위의 두 장면에서 중복이 그대로 DB에 들어간다.
- **failover 때 락이 어떻게 되는지 검토하지 않는다.** 승격된 replica에 락이 없을 수 있다.

## 운영에서 볼 것

- 테스트: 같은 요청을 동시에 여러 번 보내 중복 처리가 없는지 확인한다.
- 장애 실험: 락을 잡은 뒤 프로세스를 죽이고, TTL 이후 다른 요청이 처리하는지 확인한다.
- 로그: lock acquire 성공/실패, lock 대기 시간, lock release 실패.
- 메트릭: 락 획득 실패율, 대기 시간, 작업 수행 시간, TTL 초과 비율.

## 면접에서 말하기

> Redis 분산 락은 여러 인스턴스가 같은 작업을 동시에 실행하지 않게 하는 도구입니다. 획득은 `SET NX PX`로 TTL과 함께 원자적으로 걸고, 해제는 Lua로 소유자 token 확인과 삭제를 한 번에 합니다. 그래도 작업이 TTL보다 길어지거나 failover가 나면 락이 중복될 수 있어서, 저는 꼭 한 번만 실행돼야 하는 작업은 DB 제약, 멱등키, 상태 전이 조건으로 최종 방어합니다.

## 꼬리 질문

- `SETNX`와 `EXPIRE`를 따로 실행하면 어떤 문제가 생기나?
- 락 TTL보다 작업 시간이 길어지면 어떻게 되나?
- 분산 락과 DB unique constraint는 어떻게 다른가?
- 락 해제 시 소유자 token을 확인해야 하는 이유는?
- 분산 락만으로 중복 처리를 완전히 막을 수 있나?
- Redis failover 중 분산 락의 안전성은 어떻게 판단하나?

## 내 사례

- [[point-balance-and-idempotent-batch|포인트 잔액 계산과 멱등 지급 배치]]: Redisson 락 안에 넣은 잔액 검사와 남은 틈

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Redis Docs: Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[02-practical-backend/idempotency/idempotency|idempotency]]
- [[lock]]
- [[02-practical-backend/transaction/transaction|transaction]]
