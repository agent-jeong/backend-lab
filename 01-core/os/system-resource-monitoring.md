---
title: "시스템 자원 모니터링"
description: 서버가 느릴 때 CPU, 메모리, 디스크, 네트워크 지표를 어떤 순서로 보며 원인을 좁히는지
tags: [concept, os]
---

# 시스템 자원 모니터링 (CPU, 메모리, 디스크)

CPU, memory, disk, network, process 지표를 나란히 놓고 보면서, 서버가 어디서 막혔는지와 장애 원인을 좁혀 가는 일이다.

애플리케이션 로그에 에러가 하나도 없는데 주문 API가 느리다면, 원인은 대개 이 지표들에서 보인다. 가장 먼저 CPU가 높은지 낮은지를 본다. 높으면 계산, GC, busy loop를 의심하고, 낮은데 느리면 I/O나 락을 기다리거나 DB, 외부 API를 기다리고 있는 쪽을 본다.

## 주요 지표

| 영역 | 지표 | 의미 |
|---|---|---|
| CPU | usage, load average, run queue | 실행을 기다리는 작업과 일부 I/O 대기 작업이 얼마나 쌓였는지 |
| Memory | used, available, swap, OOM kill | 메모리가 모자란지, swap이 도는지 |
| Disk | IOPS, throughput, await, util, iowait | 디스크를 기다리는지, 디스크가 한계에 닿았는지 |
| Network | throughput, error, retransmit, connection | 패킷이 유실되거나 재전송되는지, 연결 상태는 어떤지 |
| Process | thread count, fd count, open files | 스레드나 파일이 계속 늘어나는지, 제한에 걸렸는지 |

Linux의 load average에는 CPU를 기다리는 작업뿐 아니라 일부 uninterruptible I/O wait도 들어간다. 그래서 load average가 높다고 바로 CPU 병목이라고 볼 수는 없고, CPU 사용률과 같이 봐야 한다.

## 증상별 확인 순서

| 증상 | 먼저 볼 것 | 다음 확인 |
|---|---|---|
| API 전체 지연 | CPU, load average, thread dump | DB/API 대기, GC, disk wait |
| 특정 API만 지연 | 애플리케이션 metric, DB/API latency | thread dump, external dependency |
| 서버 재시작 | OOM kill, container event | heap/native memory, limit 설정 |
| CPU 높음 | top process, thread CPU | 무한 루프, GC, serialization, compression |
| CPU 낮은데 느림 | iowait, network wait, lock wait | disk, external API, DB connection pool |
| 간헐적 timeout | p99 latency, retransmit, pool usage | 네트워크 품질, connection pool, LB |

## Java 서버에서 같이 볼 것

OS 지표만 봐서는 heap, native memory, thread, GC 중 어디가 문제인지 가릴 수 없다. 그래서 JVM 지표를 옆에 놓고 본다.

| OS 지표 | JVM/애플리케이션 지표 | 판단 |
|---|---|---|
| CPU usage 높음 | GC time, thread CPU | GC가 CPU를 쓰는지 애플리케이션 코드가 쓰는지 |
| memory available 낮음 | heap, non-heap, direct buffer | JVM 힙에서 쓰는지 힙 밖에서 쓰는지 |
| thread count 증가 | thread dump, pool queue | 스레드가 새고 있는지, blocking으로 묶여 있는지 |
| disk iowait 높음 | log write, file processing | 로그 쓰기나 파일 처리가 막고 있는지 |
| network retransmit 증가 | external API latency | 네트워크 품질이 나빠진 건 아닌지 |

## 자주 깨지는 곳

- CPU 사용률 하나로 서버 상태를 판단하면 틀린다. CPU가 낮아도 I/O나 락을 기다리느라 느릴 수 있다.
- load average를 CPU 사용률과 같은 뜻으로 읽으면 틀린다. load average에는 I/O 대기도 섞여 있다.
- 평균 latency만 보면 p95/p99 지연과 잠깐씩 꽉 차는 순간이 평균에 묻힌다.
- 컨테이너 limit과 호스트 OS 지표를 섞어 보면 판단이 어긋난다. 호스트는 여유가 있어도 컨테이너는 limit에 걸려 있을 수 있다.
- JVM heap만 보면 native memory, thread stack, direct buffer를 놓쳐서 OOM 원인을 못 찾는다.
- 로그와 OS 지표의 시간을 맞추지 않으면 무엇이 먼저 일어났는지를 거꾸로 읽는다.
- 모든 게 꽉 찬 뒤의 지표만 보면 원인을 놓친다. 맨 처음 무엇이 튀었는지가 원인이다.

## 운영에서 볼 것

- 부하 테스트 중에 CPU, memory, disk, network 지표를 같이 수집한다.
- 장애 시간대의 API latency, dependency latency, GC pause, error rate를 시간축에 맞춰 본다.
- 메트릭은 p95/p99 latency, CPU, memory available, iowait, network retransmit, fd count를 본다. 장애인지 판단할 때는 평균보다 p95/p99, 순간적으로 꽉 차는지, error rate, queue 대기 시간이 더 쓸모 있을 때가 많다.
- 명령어는 `top`, `vmstat 1`, `iostat -x 1`, `sar`, `ss`, `lsof`, `dmesg`를 쓴다.

## 한 번에 설명하기

> 서버가 느리면 먼저 CPU가 높은지 낮은지 봅니다. 높으면 계산, GC, busy loop를 의심하고, 낮은데 느리면 I/O나 락, DB나 외부 API를 기다리고 있는지 봅니다.
>
> load average에는 일부 I/O 대기도 들어가서 CPU 사용률과 같이 봅니다.
>
> Java 서버라면 heap, native memory, GC 지표를 OS 지표와 같은 시간축에 놓고 비교합니다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느리다면 무엇을 확인하나?
- load average가 높으면 항상 CPU 병목인가?
- OOMKilled가 났을 때 heap과 native memory를 어떻게 나눠 보나?
- p99 latency가 나빠질 때 어떤 OS 지표를 같이 보나?
- thread dump와 OS 지표를 같이 봐야 하는 상황은?

## 참고

2026년 11월에 확인한 공식 문서다.

- [vmstat(8)](https://man7.org/linux/man-pages/man8/vmstat.8.html)
- [top(1)](https://man7.org/linux/man-pages/man1/top.1.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[cpu-scheduling]]
- [[memory]]
- [[file-io]]
- [[socket-io]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]
