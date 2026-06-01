---
title: File I/O
description: 파일 읽기/쓰기, page cache, disk wait가 서버 성능에 미치는 영향
---

# File I/O

## 한 줄 정의

File I/O는 애플리케이션이 디스크의 파일을 읽거나 쓰는 작업이며, OS page cache와 디스크 성능에 따라 서버 응답 시간이 달라질 수 있다.

## 실무에서 왜 중요한가

File I/O를 이해하지 못하면 다음 문제가 생긴다.

- 로그 쓰기, 파일 업로드, 대용량 CSV 처리 때문에 API 응답이 느려지는 원인을 놓친다.
- CPU 사용률은 낮은데 요청이 밀리는 상황을 설명하지 못한다.
- page cache 덕분에 빠른 조회를 디스크가 항상 빠른 것으로 오해한다.
- 컨테이너나 VM 환경에서 disk throttling, volume 성능 제한을 놓친다.

## 동작 원리

1. 애플리케이션이 파일 read/write system call을 호출한다.
2. OS는 먼저 page cache에 데이터가 있는지 확인한다.
3. cache hit이면 메모리에서 빠르게 반환한다.
4. cache miss이면 디스크에서 데이터를 읽고 page cache에 올린다.
5. 일반적인 write는 page cache에 먼저 반영되고, 이후 OS가 디스크에 flush한다.
6. `fsync`나 동기 쓰기를 사용하면 디스크 반영을 기다리므로 응답 지연이 커질 수 있다.
7. 디스크가 느리거나 flush가 밀리면 I/O wait가 증가한다.

## Page Cache

Linux는 남는 메모리를 page cache로 활용한다. 그래서 `free`가 낮아도 `available`이 충분하면 정상일 수 있다.

| 상황 | 의미 |
|---|---|
| 첫 파일 조회가 느림 | 디스크에서 읽어 page cache에 올리는 중일 수 있다 |
| 두 번째 조회가 빠름 | page cache hit일 가능성이 있다 |
| 메모리 압박 증가 | page cache가 줄어들고 disk read가 늘 수 있다 |
| 대용량 순차 읽기 | page cache를 밀어내 다른 파일 접근이 느려질 수 있다 |

## 실무 판단 기준

| 상황 | 판단 | 이유 |
|---|---|---|
| 작은 설정 파일 읽기 | 부담 낮음 | page cache로 대부분 처리된다 |
| 요청마다 큰 파일 읽기 | 주의 | disk I/O와 memory pressure를 만들 수 있다 |
| 대용량 파일 업로드 | 비동기/스트리밍 검토 | 메모리 적재와 요청 스레드 점유를 줄여야 한다 |
| 로그 동기 flush | 주의 | 디스크 지연이 API 지연으로 전파될 수 있다 |
| 배치 파일 처리 | 별도 worker 검토 | API 서버 리소스와 분리하는 편이 안전하다 |

## 자주 나는 실수

- 파일 전체를 메모리에 올려 OOM을 만든다.
- API 요청 스레드에서 대용량 파일 변환을 수행한다.
- 로그 쓰기 비용을 무시한다.
- CPU만 보고 disk I/O wait를 확인하지 않는다.
- 로컬 개발 환경의 SSD 성능을 운영 볼륨 성능으로 착각한다.
- write가 반환되면 항상 디스크에 안전하게 저장됐다고 오해한다.

## 확인 방법

- 테스트: 대용량 파일 읽기/쓰기, 동시 업로드, 로그 폭증 상황을 재현한다.
- 로그: 파일 크기, 처리 시간, 실패 원인을 남긴다.
- 메트릭: disk read/write throughput, IOPS, await, util, iowait를 본다.
- 명령어: `iostat -x 1`, `vmstat 1`, `pidstat -d 1`, `df -h`로 확인한다.

## 핵심 요약

File I/O는 CPU 계산보다 느리고, page cache와 디스크 상태에 따라 성능이 크게 달라진다. page cache hit이면 파일 접근이 빠르지만, cache miss나 flush 지연이 발생하면 API 응답 시간이 증가할 수 있다. 일반적인 write는 page cache 반영 후 반환될 수 있으므로, 디스크 내구성이 필요하면 fsync 같은 동기화 비용을 고려해야 한다. CPU 사용률이 낮아도 disk wait가 높으면 서버는 느릴 수 있다. 대용량 파일 처리는 스트리밍, 비동기 처리, 별도 worker 분리를 검토해야 한다. 운영에서는 CPU뿐 아니라 disk throughput, IOPS, await, iowait를 함께 봐야 한다.

## 꼬리 질문

- CPU 사용률은 낮은데 API가 느릴 때 disk I/O를 어떻게 의심할 수 있는가?
- page cache는 파일 읽기 성능에 어떤 영향을 주는가?
- 대용량 파일을 요청 스레드에서 처리하면 어떤 문제가 생기는가?
- `iowait`가 높다는 것은 무엇을 의미하는가?
- write 반환과 디스크 내구성 보장은 어떤 차이가 있는가?

## 관련 문서

- [[os]]
- [[memory]]
- [[performance]]
- [[batch-processing]]
