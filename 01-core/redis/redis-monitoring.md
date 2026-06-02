---
title: Redis 운영 모니터링
description: Redis 장애 징후를 보기 위한 latency, memory, command, connection 지표
---

# Redis 운영 모니터링

## 한 줄 정의

Redis 운영 모니터링은 Redis 자체 지표와 애플리케이션 지표를 함께 보면서 latency, 메모리, eviction, connection, slow command 문제를 조기에 찾는 것이다.

## 실무에서 왜 문제 되는가

- Redis는 빠른 저장소라 작은 지연 증가도 API 전체 latency에 바로 반영될 수 있다.
- cache hit ratio만 보면 Redis timeout, eviction, DB fallback, connection pool 고갈을 놓칠 수 있다.
- Redis 장애는 캐시 miss 증가를 통해 DB 부하 증가로 이어질 수 있다.
- slow command, big key, hot key는 Redis 서버 지표만 봐서는 원인을 바로 알기 어렵다.
- 운영 지표 없이 Redis를 쓰면 장애 시 "Redis가 느린지, DB fallback이 몰린 건지"를 구분하기 어렵다.

## 주요 지표

| 지표 | 의미 | 확인할 문제 |
|---|---|---|
| latency | Redis 명령 응답 시간 | hot key, big key, slow command, 네트워크 문제 |
| memory usage | Redis 메모리 사용량 | 메모리 누수형 key 증가, maxmemory 근접 |
| evicted keys | 메모리 부족으로 제거된 key 수 | 캐시 손실, hit ratio 하락, DB 부하 증가 |
| expired keys | TTL 만료 key 수 | TTL 동작, 대량 동시 만료 가능성 |
| connected clients | 연결된 클라이언트 수 | connection leak, pool 설정 문제 |
| blocked clients | blocking command 대기 클라이언트 | list pop, stream 등 blocking 사용 문제 |
| command stats | 명령별 호출량/비용 | 비싼 명령, 트래픽 패턴 변화 |
| slowlog | 느린 명령 기록 | big key, 비효율 명령, 서버 부하 |

## 애플리케이션과 함께 볼 지표

| Redis 지표 | 함께 볼 애플리케이션 지표 | 이유 |
|---|---|---|
| Redis latency 증가 | API p95/p99 latency | 사용자 응답 지연으로 이어졌는지 확인 |
| timeout 증가 | Redis client pool usage | 클라이언트 대기와 스레드 고갈 가능성 확인 |
| evicted keys 증가 | cache hit ratio, DB QPS | eviction이 DB 부하로 전파되는지 확인 |
| expired keys 급증 | DB QPS, error rate | 대량 만료가 cache stampede를 만드는지 확인 |
| connected clients 증가 | 인스턴스 수, pool 설정 | 배포나 leak으로 연결이 늘었는지 확인 |
| fallback count 증가 | API latency, DB latency | fallback이 정상 동작해도 장애 전파 중인지 확인 |

## 장애 징후별 확인 순서

| 증상 | 먼저 볼 것 | 다음 확인 |
|---|---|---|
| API 응답 지연 | Redis latency, API p99 | slowlog, hot key, DB fallback |
| DB QPS 급증 | hit ratio, expired keys | TTL 동시 만료, Redis timeout |
| Redis 메모리 증가 | memory usage, key count | TTL 없는 key, big key, prefix별 증가 |
| timeout 증가 | Redis latency, client pool | 네트워크, 서버 CPU, connection pool |
| 특정 기능만 느림 | key prefix, command stats | hot key, big key, 자료구조 크기 |

## 자주 나는 실수

- cache hit ratio만 보고 Redis가 정상이라고 판단한다.
- Redis 서버 지표만 보고 애플리케이션 fallback count와 DB QPS를 보지 않는다.
- eviction이 발생해도 캐시라서 괜찮다고 보고 넘어간다.
- slowlog를 수집하지 않아 느린 명령을 사후 분석하지 못한다.
- Redis client timeout과 pool 지표를 보지 않아 애플리케이션 장애 전파를 놓친다.
- 평균 latency만 보고 p95/p99 지연을 놓친다.

## 확인 방법

- 테스트: Redis 지연, 연결 실패, 대량 key 만료, big key 조회 상황을 재현한다.
- 로그: Redis timeout, fallback 실행, slow command 후보, key prefix를 남긴다.
- 메트릭: Redis latency, memory usage, evicted keys, expired keys, connected clients, blocked clients를 수집한다.
- 대시보드: Redis 지표와 API latency, DB QPS, error rate, fallback count를 같은 화면에서 본다.
- 알림: timeout 급증, evicted keys 증가, memory threshold 초과, p99 latency 상승에 알림을 둔다.

## 핵심 요약

Redis 운영 모니터링은 Redis가 살아 있는지만 보는 것이 아니라 Redis 지연이 애플리케이션과 DB에 어떻게 전파되는지 보는 것이다. hit ratio가 높아도 timeout, eviction, p99 latency가 나쁘면 사용자 장애가 될 수 있다. Redis 지표는 API latency, DB QPS, fallback count와 함께 봐야 한다. slowlog, hot key, big key, memory usage는 Redis 성능 문제를 좁히는 핵심 단서다. 알림은 평균값보다 p95/p99, timeout, eviction, fallback 증가 같은 장애 징후에 맞춰야 한다.

## 꼬리 질문

- Redis 장애를 감지하려면 어떤 지표를 봐야 하는가?
- cache hit ratio가 높아도 API가 느릴 수 있는 이유는 무엇인가?
- eviction이 발생하면 어떤 사용자 영향이 생길 수 있는가?
- Redis timeout 증가와 DB QPS 증가는 어떻게 연결되는가?
- slowlog에서 느린 명령을 찾은 뒤 무엇을 확인할 것인가?

## 관련 문서

- [[01-core/redis/redis|redis]]
- [[redis-key-and-memory]]
- [[redis-failure-and-fallback]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]
