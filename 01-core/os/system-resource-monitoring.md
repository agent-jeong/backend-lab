---
title: "시스템 자원 모니터링"
description: CPU, memory, disk, network 지표로 서버 병목을 좁히는 방법
tags: [concept, os]
---

# 시스템 자원 모니터링 (CPU, 메모리, 디스크)

시스템 자원 모니터링은 CPU, memory, disk, network, process 지표를 함께 보며 서버 병목과 장애 원인을 좁히는 작업이다.

애플리케이션 로그에 에러가 없는데 서버가 느리다면 답은 대개 여기 있다. 첫 질문은 "CPU가 높은가 낮은가"다. 높으면 계산, GC, busy loop를 의심하고, 낮은데 느리면 I/O wait, lock wait, 외부 의존성 대기를 본다.

## 주요 지표

| 영역 | 지표 | 의미 |
|---|---|---|
| CPU | usage, load average, run queue | 실행 가능 작업과 일부 I/O 대기 작업이 얼마나 쌓였는지 확인 |
| Memory | used, available, swap, OOM kill | 메모리 부족과 swap 발생 여부 확인 |
| Disk | IOPS, throughput, await, util, iowait | 디스크 대기와 포화 여부 확인 |
| Network | throughput, error, retransmit, connection | 네트워크 품질과 연결 상태 확인 |
| Process | thread count, fd count, open files | 프로세스 리소스 누수와 제한 확인 |

Linux의 load average는 CPU 실행 대기뿐 아니라 일부 uninterruptible I/O wait도 포함한다. 그래서 load average가 높다고 곧 CPU 병목은 아니고, CPU 사용률과 같이 봐야 한다.

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

OS 지표만으로는 heap, native memory, thread, GC 문제를 구분하지 못한다. JVM 지표를 옆에 놓고 본다.

| OS 지표 | JVM/애플리케이션 지표 | 판단 |
|---|---|---|
| CPU usage 높음 | GC time, thread CPU | GC 문제인지 애플리케이션 CPU 문제인지 구분 |
| memory available 낮음 | heap, non-heap, direct buffer | JVM 내부/외부 메모리 사용 구분 |
| thread count 증가 | thread dump, pool queue | 스레드 누수나 blocking 대기 확인 |
| disk iowait 높음 | log write, file processing | 로그/파일 처리 병목 확인 |
| network retransmit 증가 | external API latency | 네트워크 품질 문제 가능성 확인 |

## 자주 깨지는 곳

- **CPU 사용률 하나로 서버 상태를 판단한다.** CPU가 낮아도 I/O나 락 대기로 느릴 수 있다.
- **load average를 CPU 사용률과 같은 뜻으로 읽는다.** I/O 대기도 섞여 있다.
- **평균 latency만 본다.** p95/p99 지연과 순간 포화가 평균에 묻힌다.
- **컨테이너 limit과 호스트 OS 지표를 섞어 본다.** 호스트는 여유가 있어도 컨테이너는 limit에 걸려 있을 수 있다.
- **JVM heap만 본다.** native memory, thread stack, direct buffer를 놓쳐 OOM 원인을 못 찾는다.
- **로그와 OS 지표의 시간을 맞추지 않는다.** 원인과 결과의 선후를 잘못 읽는다.
- **포화된 뒤의 결과 지표만 본다.** 맨 처음 무엇이 튀었는지가 원인이다.

## 운영에서 볼 것

- 부하 테스트 중에 CPU, memory, disk, network 지표를 같이 수집한다.
- 장애 시간대의 API latency, dependency latency, GC pause, error rate를 시간축에 맞춰 본다.
- 메트릭은 p95/p99 latency, CPU, memory available, iowait, network retransmit, fd count. 장애 판단에는 평균보다 p95/p99, 순간 포화, error rate, queue 대기 시간이 더 쓸모 있을 때가 많다.
- 명령어는 `top`, `vmstat 1`, `iostat -x 1`, `sar`, `ss`, `lsof`, `dmesg`.

## 면접에서 말하기

> 서버가 느리면 저는 먼저 CPU가 높은지 낮은지 봅니다. 높으면 계산, GC, busy loop를 의심하고, 낮은데 느리면 I/O wait, lock wait, 외부 의존성 대기를 봅니다. load average는 일부 I/O 대기도 포함하니 CPU 사용률과 같이 해석하고, Java 서버라면 heap, native memory, GC 지표를 OS 지표와 같은 시간축에 놓고 비교합니다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느리다면 무엇을 확인하나?
- load average가 높으면 항상 CPU 병목인가?
- OOMKilled가 났을 때 heap과 native memory를 어떻게 나눠 보나?
- p99 latency가 나빠질 때 어떤 OS 지표를 같이 보나?
- thread dump와 OS 지표를 같이 봐야 하는 상황은?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

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
