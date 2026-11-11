---
title: 파일 I/O
description: 파일을 읽고 쓸 때 page cache와 디스크 대기가 API 응답 시간을 어떻게 바꾸는지
tags: [concept, os]
---

# 파일 I/O

File I/O는 애플리케이션이 디스크에 있는 파일을 읽거나 쓰는 일이다. 같은 코드라도 데이터가 OS page cache에 있느냐, 디스크가 얼마나 빠르냐에 따라 응답 시간이 크게 달라진다.

CPU 사용률은 낮은데 요청이 밀린다면 디스크를 기다리고 있는 건 아닌지 본다. 로그를 너무 많이 쓰거나, 파일 업로드를 받거나, 큰 CSV를 처리하다 API가 느려지는 일이 흔하다.

## 동작

1. 애플리케이션이 파일 read/write system call을 호출한다.
2. OS는 먼저 page cache에 데이터가 있는지 본다.
3. 있으면(cache hit) 메모리에서 바로 돌려준다.
4. 없으면(cache miss) 디스크에서 읽어 page cache에 올린다.
5. 일반적인 write는 page cache에 먼저 반영되고, 나중에 OS가 디스크로 flush한다.
6. `fsync`나 동기 쓰기를 쓰면 디스크에 실제로 써질 때까지 기다리니 응답이 늦어진다.
7. 디스크가 느리거나 flush가 밀리면 I/O wait가 늘어난다.

write가 돌아왔다고 디스크에 안전하게 저장된 건 아니다. 서버가 꺼져도 남아 있어야 하는 데이터라면 `fsync`처럼 기다리는 비용을 감수해야 한다.

## Page Cache

Linux는 남는 메모리를 page cache로 쓴다. 그래서 `free`가 낮게 나와도 `available`이 넉넉하면 정상일 수 있다.

| 상황 | 의미 |
|---|---|
| 첫 파일 조회가 느림 | 디스크에서 읽어 page cache에 올리는 중일 수 있다 |
| 두 번째 조회가 빠름 | page cache hit일 가능성이 높다 |
| 메모리 압박 증가 | page cache가 줄고 disk read가 는다 |
| 대용량 순차 읽기 | page cache를 밀어내 다른 파일 접근이 느려진다 |

page cache 덕분에 빨랐던 조회를 보고 디스크가 빠르다고 판단하면 안 된다.

## 상황별 판단

| 상황 | 판단 | 이유 |
|---|---|---|
| 작은 설정 파일 읽기 | 부담 낮음 | 대부분 page cache에서 처리된다 |
| 요청마다 큰 파일 읽기 | 주의 | disk I/O가 늘고 메모리도 빠듯해진다 |
| 대용량 파일 업로드 | 비동기/스트리밍 검토 | 파일을 통째로 메모리에 올리지 않고, 요청 스레드도 오래 붙잡지 않는다 |
| 로그 동기 flush | 주의 | 디스크 지연이 API 지연으로 번진다 |
| 배치 파일 처리 | 별도 worker 검토 | API 서버와 자원을 나눠 쓰지 않는 편이 안전하다 |

## 자주 깨지는 곳

- 파일 전체를 메모리에 올리면 큰 파일 하나로 OOM이 난다.
- API 요청 스레드에서 대용량 파일을 변환하면 그동안 요청 스레드가 묶인다.
- 로그 쓰는 비용을 무시하면, 로그가 폭증할 때 디스크 대기가 그대로 API 지연이 된다.
- CPU만 보고 disk I/O wait를 보지 않으면 병목을 엉뚱한 곳에서 찾는다.
- 로컬 SSD에서 잰 성능을 운영 볼륨도 낼 거라 생각하면 틀린다. 컨테이너나 VM에서는 disk throttling과 volume 성능 제한이 걸린다.

## 운영에서 볼 것

- 대용량 파일 읽기/쓰기, 동시 업로드, 로그 폭증 상황을 재현해 본다.
- 로그에 파일 크기, 처리 시간, 실패 원인을 남긴다.
- 메트릭은 disk read/write throughput, IOPS, await, util, iowait를 본다.
- 명령어는 `iostat -x 1`, `vmstat 1`, `pidstat -d 1`, `df -h`를 쓴다.

## 한 번에 설명하기

> 파일 읽기는 page cache에 있으면 빠르지만, cache miss가 나거나 flush가 밀리면 API 응답 시간이 늘어납니다. 그래서 CPU 사용률은 낮은데 느리면 disk throughput, IOPS, await, iowait를 같이 봅니다.
>
> 보통 write는 page cache에만 쓰고 돌아올 수 있어서, 꼭 남아야 하는 데이터라면 fsync 비용을 따로 따져 봅니다.
>
> 대용량 파일은 스트리밍이나 별도 worker로 돌려서 요청 스레드에서 떼어 냅니다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느릴 때 disk I/O를 어떻게 의심하나?
- page cache는 파일 읽기 성능에 어떤 영향을 주나?
- 대용량 파일을 요청 스레드에서 처리하면 어떤 문제가 생기나?
- `iowait`가 높다는 것은 무엇을 뜻하나?
- write 반환과 디스크 내구성 보장은 어떻게 다른가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [read(2)](https://man7.org/linux/man-pages/man2/read.2.html)
- [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[memory]]
- [[02-practical-backend/performance/performance|performance]]
- [[batch-processing]]
