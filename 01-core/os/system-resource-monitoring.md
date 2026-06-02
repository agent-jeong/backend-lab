---
title: System Resource Monitoring
description: CPU, memory, disk, network 지표로 서버 병목을 좁히는 방법
---

# System Resource Monitoring

## 한 줄 정의

System Resource Monitoring은 CPU, memory, disk, network, process 지표를 함께 보며 서버 병목과 장애 원인을 좁히는 작업이다.

## 실무에서 왜 중요한가

System resource를 보지 못하면 다음 문제가 생긴다.

- 애플리케이션 로그에 에러가 없는데 서버가 느린 이유를 찾지 못한다.
- CPU, memory, disk, network 중 어느 자원이 병목인지 구분하지 못한다.
- JVM 지표만 보고 OS OOM, disk wait, network retransmission을 놓친다.
- 평균 지표만 보고 p95/p99 지연과 순간적인 리소스 포화를 놓친다.

## 주요 지표

| 영역 | 지표 | 의미 |
|---|---|---|
| CPU | usage, load average, run queue | 실행 가능 작업과 일부 I/O 대기 작업이 얼마나 쌓였는지 확인 |
| Memory | used, available, swap, OOM kill | 메모리 부족과 swap 발생 여부 확인 |
| Disk | IOPS, throughput, await, util, iowait | 디스크 대기와 포화 여부 확인 |
| Network | throughput, error, retransmit, connection | 네트워크 품질과 연결 상태 확인 |
| Process | thread count, fd count, open files | 프로세스 리소스 누수와 제한 확인 |

## 장애 증상별 확인 순서

| 증상 | 먼저 볼 것 | 다음 확인 |
|---|---|---|
| API 전체 지연 | CPU, load average, thread dump | DB/API 대기, GC, disk wait |
| 특정 API만 지연 | 애플리케이션 metric, DB/API latency | thread dump, external dependency |
| 서버 재시작 | OOM kill, container event | heap/native memory, limit 설정 |
| CPU 높음 | top process, thread CPU | 무한 루프, GC, serialization, compression |
| CPU 낮은데 느림 | iowait, network wait, lock wait | disk, external API, DB connection pool |
| 간헐적 timeout | p99 latency, retransmit, pool usage | 네트워크 품질, connection pool, LB |

## Java 서버에서 같이 볼 것

| OS 지표 | JVM/애플리케이션 지표 | 판단 |
|---|---|---|
| CPU usage 높음 | GC time, thread CPU | GC 문제인지 애플리케이션 CPU 문제인지 구분 |
| memory available 낮음 | heap, non-heap, direct buffer | JVM 내부/외부 메모리 사용 구분 |
| thread count 증가 | thread dump, pool queue | 스레드 누수나 blocking 대기 확인 |
| disk iowait 높음 | log write, file processing | 로그/파일 처리 병목 확인 |
| network retransmit 증가 | external API latency | 네트워크 품질 문제 가능성 확인 |

## 자주 나는 실수

- CPU 사용률만 보고 서버 상태를 판단한다.
- load average를 항상 CPU 사용률과 같은 의미로 해석한다.
- 평균 latency만 보고 p99 지연을 놓친다.
- 컨테이너 limit과 호스트 OS 지표를 구분하지 않는다.
- JVM heap만 보고 native memory, thread stack, direct buffer를 놓친다.
- 애플리케이션 로그와 OS 지표의 시간을 맞춰 보지 않는다.
- 리소스가 포화된 뒤의 결과 지표만 보고 최초 원인을 놓친다.

## 확인 방법

- 테스트: 부하 테스트 중 CPU, memory, disk, network 지표를 함께 수집한다.
- 로그: 장애 시간대의 API latency, dependency latency, GC pause, error rate를 맞춰 본다.
- 메트릭: p95/p99 latency, CPU, memory available, iowait, network retransmit, fd count를 본다.
- 명령어: `top`, `vmstat 1`, `iostat -x 1`, `sar`, `ss`, `lsof`, `dmesg`를 사용한다.

## 핵심 요약

System Resource Monitoring은 서버가 느릴 때 어떤 자원이 병목인지 좁히는 기본 작업이다. CPU가 높으면 계산, GC, busy loop를 의심하고, CPU가 낮은데 느리면 I/O wait, lock wait, 외부 의존성 대기를 봐야 한다. Linux의 load average는 CPU 실행 대기뿐 아니라 일부 uninterruptible I/O wait도 포함할 수 있어 CPU 사용률과 함께 해석해야 한다. Java 서버에서는 OS 지표와 JVM 지표를 함께 봐야 heap, native memory, thread, GC 문제를 구분할 수 있다. 평균값보다 p95/p99, 순간 포화, error rate, queue 대기 시간이 장애 판단에 더 중요할 때가 많다. 운영에서는 애플리케이션 로그, JVM 지표, OS 지표의 시간을 맞춰 보는 습관이 중요하다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느리다면 무엇을 확인할 것인가?
- load average가 높다는 것은 항상 CPU 병목을 의미하는가?
- OOMKilled가 발생했을 때 heap과 native memory를 어떻게 나눠 볼 것인가?
- p99 latency가 나빠질 때 어떤 OS 지표를 함께 볼 것인가?
- thread dump와 OS 지표를 같이 봐야 하는 상황은 언제인가?

## 관련 문서

- [[01-core/os/os|os]]
- [[cpu-scheduling]]
- [[memory]]
- [[file-io]]
- [[socket-io]]
- [[02-practical-backend/performance/performance|performance]]
- [[02-practical-backend/observability/observability|observability]]
