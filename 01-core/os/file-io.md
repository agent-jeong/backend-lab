---
title: 파일 I/O
description: 파일 읽기/쓰기, page cache, disk wait가 서버 성능에 미치는 영향
tags: [concept, os]
---

# 파일 I/O

File I/O는 애플리케이션이 디스크의 파일을 읽거나 쓰는 작업이다. 같은 코드라도 OS page cache에 데이터가 있느냐, 디스크가 얼마나 빠르냐에 따라 응답 시간이 크게 달라진다.

CPU 사용률은 낮은데 요청이 밀린다면 디스크 대기를 의심한다. 로그 쓰기, 파일 업로드, 대용량 CSV 처리가 API를 느리게 만드는 흔한 원인이다.

## 동작

1. 애플리케이션이 파일 read/write system call을 호출한다.
2. OS는 먼저 page cache에 데이터가 있는지 본다.
3. 있으면(cache hit) 메모리에서 바로 돌려준다.
4. 없으면(cache miss) 디스크에서 읽어 page cache에 올린다.
5. 일반적인 write는 page cache에 먼저 반영되고, 나중에 OS가 디스크로 flush한다.
6. `fsync`나 동기 쓰기를 쓰면 디스크 반영까지 기다리므로 응답이 늦어진다.
7. 디스크가 느리거나 flush가 밀리면 I/O wait가 늘어난다.

write가 반환됐다고 디스크에 안전하게 저장된 것은 아니다. 내구성이 필요하면 `fsync` 같은 동기화 비용을 감수해야 한다.

## Page Cache

Linux는 남는 메모리를 page cache로 쓴다. 그래서 `free`가 낮아도 `available`이 충분하면 정상일 수 있다.

| 상황 | 의미 |
|---|---|
| 첫 파일 조회가 느림 | 디스크에서 읽어 page cache에 올리는 중일 수 있다 |
| 두 번째 조회가 빠름 | page cache hit일 가능성이 높다 |
| 메모리 압박 증가 | page cache가 줄고 disk read가 는다 |
| 대용량 순차 읽기 | page cache를 밀어내 다른 파일 접근이 느려진다 |

page cache 덕에 빨랐던 조회를 보고 디스크가 빠르다고 판단하면 안 된다.

## 상황별 판단

| 상황 | 판단 | 이유 |
|---|---|---|
| 작은 설정 파일 읽기 | 부담 낮음 | 대부분 page cache에서 처리된다 |
| 요청마다 큰 파일 읽기 | 주의 | disk I/O와 memory pressure를 만든다 |
| 대용량 파일 업로드 | 비동기/스트리밍 검토 | 메모리 적재와 요청 스레드 점유를 줄인다 |
| 로그 동기 flush | 주의 | 디스크 지연이 API 지연으로 번진다 |
| 배치 파일 처리 | 별도 worker 검토 | API 서버 리소스와 분리하는 편이 안전하다 |

## 자주 깨지는 곳

- **파일 전체를 메모리에 올린다.** 큰 파일 하나로 OOM이 난다.
- **API 요청 스레드에서 대용량 파일 변환을 한다.** 그동안 요청 스레드가 묶인다.
- **로그 쓰기 비용을 무시한다.** 로그가 폭증하면 디스크 대기가 API 지연이 된다.
- **CPU만 보고 disk I/O wait를 보지 않는다.** 병목을 엉뚱한 곳에서 찾는다.
- **로컬 SSD 성능을 운영 볼륨 성능으로 착각한다.** 컨테이너나 VM에서는 disk throttling과 volume 성능 제한이 걸린다.

## 운영에서 볼 것

- 대용량 파일 읽기/쓰기, 동시 업로드, 로그 폭증 상황을 재현해 본다.
- 로그에 파일 크기, 처리 시간, 실패 원인을 남긴다.
- 메트릭은 disk read/write throughput, IOPS, await, util, iowait를 본다.
- 명령어는 `iostat -x 1`, `vmstat 1`, `pidstat -d 1`, `df -h`.

## 면접에서 말하기

> File I/O는 page cache에 있으면 빠르지만, cache miss나 flush 지연이 생기면 API 응답 시간이 늘어납니다. 그래서 CPU 사용률이 낮은데 느리면 저는 disk throughput, IOPS, await, iowait를 같이 봅니다. 일반 write는 page cache에만 반영되고 반환될 수 있어서 내구성이 필요하면 fsync 비용을 따로 따지고, 대용량 파일은 스트리밍이나 별도 worker로 요청 스레드에서 떼어 냅니다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느릴 때 disk I/O를 어떻게 의심하나?
- page cache는 파일 읽기 성능에 어떤 영향을 주나?
- 대용량 파일을 요청 스레드에서 처리하면 어떤 문제가 생기나?
- `iowait`가 높다는 것은 무엇을 뜻하나?
- write 반환과 디스크 내구성 보장은 어떻게 다른가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [read(2)](https://man7.org/linux/man-pages/man2/read.2.html)
- [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[memory]]
- [[02-practical-backend/performance/performance|performance]]
- [[batch-processing]]
