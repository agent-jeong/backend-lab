---
title: Redis 운영 모니터링
description: Redis가 흔들리는 걸 일찍 알아채려면 어떤 지표를 무엇과 같이 봐야 하는지
tags: [concept, redis]
---

# Redis 운영 모니터링

Redis 지표와 애플리케이션 지표를 나란히 놓고, latency나 메모리, eviction, connection, 느린 명령 문제를 장애가 커지기 전에 찾는 일이다.

Redis가 살아 있는지만 봐서는 모자라다. 상품 조회 API가 느려졌을 때 알고 싶은 건 Redis 지연이 API와 DB로 어떻게 번졌는지다. Redis는 원래 빨라서 조금만 느려져도 API latency에 바로 드러나고, Redis가 흔들리면 캐시 miss가 늘어 DB 부하가 오른다. hit ratio만 봐서는 timeout, eviction, DB fallback, connection pool 고갈을 놓친다.

## Redis 지표

| 지표 | 의미 | 확인할 문제 |
|---|---|---|
| latency | Redis 명령 응답 시간 | hot key, big key, slow command, 네트워크 문제 |
| memory usage | Redis 메모리 사용량 | 지워지지 않고 계속 늘어나는 key, maxmemory에 가까워짐 |
| evicted keys | 메모리 부족으로 제거된 key 수 | 캐시 손실, hit ratio 하락, DB 부하 증가 |
| expired keys | TTL 만료 key 수 | TTL 동작, 대량 동시 만료 가능성 |
| connected clients | 연결된 클라이언트 수 | connection leak, pool 설정 문제 |
| blocked clients | blocking command로 대기 중인 클라이언트 | list pop, stream 같은 blocking 명령을 잘못 쓰는 곳 |
| command stats | 명령별 호출량/비용 | 비싼 명령, 트래픽 패턴 변화 |
| slowlog | 느린 명령 기록 | big key, 비싼 명령, 서버 부하 |

## 애플리케이션 지표와 짝지어 보기

장애가 나면 Redis가 느린 건지, DB로 돌린 요청이 몰린 건지부터 가려야 한다. 그러려면 Redis 지표 옆에 애플리케이션 지표를 둔다.

| Redis 지표 | 같이 볼 애플리케이션 지표 | 무엇을 확인하나 |
|---|---|---|
| Redis latency 증가 | API p95/p99 latency | 사용자 응답 지연으로 이어졌는지 |
| timeout 증가 | Redis client pool usage | 클라이언트 대기와 스레드 고갈이 시작됐는지 |
| evicted keys 증가 | cache hit ratio, DB QPS | eviction이 DB 부하로 번지는지 |
| expired keys 급증 | DB QPS, error rate | 대량 만료가 cache stampede를 만드는지 |
| connected clients 증가 | 인스턴스 수, pool 설정 | 배포나 leak으로 연결이 늘었는지 |
| fallback count 증가 | API latency, DB latency | fallback이 동작하는 중에도 장애가 번지는지 |

## 증상별 확인 순서

| 증상 | 먼저 볼 것 | 다음 확인 |
|---|---|---|
| API 응답 지연 | Redis latency, API p99 | slowlog, hot key, DB fallback |
| DB QPS 급증 | hit ratio, expired keys | TTL 동시 만료, Redis timeout |
| Redis 메모리 증가 | memory usage, key count | TTL 없는 key, big key, prefix별 증가 |
| timeout 증가 | Redis latency, client pool | 네트워크, 서버 CPU, connection pool |
| 특정 기능만 느림 | key prefix, command stats | hot key, big key, 자료구조 크기 |

느린 명령, big key, hot key는 Redis 서버 지표만 봐서는 어디서 생겼는지 바로 안 보인다. key prefix와 command stats로 범위를 좁힌다.

## 자주 깨지는 곳

- hit ratio만 보고 정상이라고 판단하면 안 된다. hit ratio가 높아도 timeout, eviction, p99 latency가 나쁘면 사용자에게는 장애다.
- Redis 서버 지표만 보고 fallback count와 DB QPS를 안 보면, 장애가 어디로 번지는지 모른다.
- eviction을 "캐시라서 괜찮다"고 넘기면, 그사이 hit ratio가 떨어지고 DB 부하가 오른다.
- slowlog를 모아 두지 않으면 장애가 지난 뒤에 어떤 명령이 느렸는지 알 수 없다.
- client timeout과 pool 지표를 안 보면, Redis 문제가 애플리케이션으로 번지는 순간을 놓친다.
- 평균 latency만 보면 p95/p99 지연이 가려진다.

## 운영에서 볼 것

- 테스트: Redis 지연, 연결 실패, 대량 key 만료, big key 조회를 재현한다.
- 로그: Redis timeout, fallback 실행, 느린 명령으로 의심되는 것, key prefix를 남긴다.
- 메트릭: Redis latency, memory usage, evicted keys, expired keys, connected clients, blocked clients를 본다.
- 대시보드: Redis 지표와 API latency, DB QPS, error rate, fallback count를 한 화면에 둔다.
- 알림: 평균값이 아니라 timeout 급증, evicted keys 증가, memory threshold 초과, p99 latency 상승에 건다.

## 한 번에 설명하기

> Redis를 모니터링할 때는 Redis가 살아 있는지보다, Redis 지연이 애플리케이션과 DB로 어떻게 번지는지를 봅니다. 그래서 Redis latency, eviction, timeout을 API p99, DB QPS, fallback count와 한 화면에 둡니다.
>
> hit ratio가 높아도 timeout이나 p99가 나쁘면 장애로 보고, 원인은 slowlog, hot key, big key, memory usage로 좁혀 갑니다.
>
> 알림도 평균값이 아니라 p99, timeout, eviction이 늘어날 때 울리게 겁니다.

## 꼬리 질문

- Redis 장애를 감지하려면 어떤 지표를 봐야 하나?
- cache hit ratio가 높아도 API가 느릴 수 있는 이유는?
- eviction이 발생하면 사용자에게 어떤 영향이 생기나?
- Redis timeout 증가와 DB QPS 증가는 어떻게 연결되나?
- slowlog에서 느린 명령을 찾은 뒤 무엇을 확인할 것인가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: INFO](https://redis.io/docs/latest/commands/info/)
- [Redis Docs: SLOWLOG GET](https://redis.io/docs/latest/commands/slowlog-get/)

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[redis-key-and-memory]]
- [[redis-failure-and-fallback]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]
