---
title: "OS 메모리 관리 (가상 메모리, 페이징)"
description: 가상 메모리와 페이징, Swap, OOM Killer, 그리고 컨테이너에서 JVM 메모리를 잡는 법
tags: [concept, os]
---

# OS 메모리 관리 (가상 메모리, 페이징)

OS는 프로세스마다 자기만 쓰는 것처럼 보이는 가상 주소 공간을 주고, 실제 물리 메모리는 페이지 단위로 나눠 연결해 준다. 그래서 한 프로세스가 다른 프로세스의 메모리를 건드리지 못하고, 물리 메모리도 아껴 쓸 수 있다.

서버에서 메모리 문제는 대개 세 가지로 드러난다. Swap이 돌면서 응답이 갑자기 느려지거나, OOM Killer가 프로세스를 죽이거나, 컨테이너 limit과 JVM 힙을 잘못 맞춰서 OOM으로 계속 재시작된다. 반대로 `free`가 0으로 나오는 정상 상태를 장애로 잘못 보는 일도 흔하다.

## 가상 메모리 (Virtual Memory)

프로세스마다 자기만의 가상 주소 공간이 있고, OS가 가상 주소를 물리 주소로 바꿔 준다.

```
Process A                   Physical Memory
┌──────────┐               ┌──────────┐
│ 0x0000   │──── Page Table ──→│ 0x5000   │
│ 0x1000   │──────────────────→│ 0x8000   │
└──────────┘               └──────────┘

Process B                   
┌──────────┐               ┌──────────┐
│ 0x0000   │──── Page Table ──→│ 0x3000   │  ← 같은 가상주소, 다른 물리주소
│ 0x1000   │──────────────────→│ 0xA000   │
└──────────┘               └──────────┘
```

이렇게 하면 프로세스끼리 메모리가 섞이지 않고, 물리 메모리보다 큰 주소 공간을 쓸 수 있고, 메모리 단편화도 줄어든다.

## 페이징 (Paging)

가상 메모리를 고정 크기 블록(Page, 보통 4KB)으로 나눠 다룬다.

### Page Fault

읽으려는 Page가 물리 메모리에 없을 때 일어난다.

```
프로세스가 가상 주소 접근
→ Page Table 확인
→ 물리 메모리에 없음 (Page Fault)
→ 디스크에서 해당 Page를 메모리로 로드
→ Page Table 업데이트
→ 접근 재시도
```

Page Fault가 잦으면 그만큼 디스크를 읽느라 느려진다.

## Swap

물리 메모리가 모자라면 잘 안 쓰는 Page를 디스크(Swap 영역)로 내보낸다.

```bash
# Swap 사용량 확인
free -h
              total    used    free    shared  buff/cache  available
Mem:           16G     12G     200M    100M    3.8G        3.5G
Swap:           4G     1.5G    2.5G
```

Swap이 활발하게 돌면 서버 응답이 갑자기 느려진다. 디스크는 메모리보다 수만 배 느리기 때문이다.

```bash
# Swap 발생 모니터링
vmstat 1
# si(swap in), so(swap out) 값이 지속적으로 높으면 메모리 부족
procs  memory       swap    io
 r  b  swpd  free   si  so  bi  bo
 2  1  1500  200    50  30  10  20   ← si, so가 0이 아니면 Swap 발생
```

### Swappiness

```bash
# Swap 사용 경향 (0~100, 기본 60)
cat /proc/sys/vm/swappiness

# DB 서버처럼 Swap을 최소화해야 하는 경우
sysctl vm.swappiness=10
```

## OOM Killer

물리 메모리와 Swap이 다 모자라면 OS의 OOM Killer가 프로세스를 강제로 죽인다. 프로세스가 이유 없이 사라졌다면 이 로그부터 본다.

```bash
# OOM Killer 발생 확인
dmesg | grep -i "oom\|killed"
# Out of memory: Killed process 1234 (java) total-vm:8192000kB
```

```bash
# 프로세스별 OOM 점수 확인 (높을수록 먼저 kill)
cat /proc/<PID>/oom_score
cat /proc/<PID>/oom_score_adj  # -1000 ~ 1000, 낮을수록 보호
```

### 컨테이너에서의 OOM

```yaml
# Kubernetes 메모리 설정
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"   # 초과 시 OOM Killed
```

컨테이너가 메모리 limit을 넘으면 cgroup OOM Killer가 프로세스를 죽이고, Pod는 `OOMKilled` 상태로 재시작된다.

### JVM + 컨테이너 메모리 설정

```
Container limit: 1Gi
├── JVM Heap (-Xmx): 512m  (작은 컨테이너라 50%)
├── JVM Metaspace: ~100m
├── JVM Thread Stack: 스레드 수 × 1MB
├── JVM 내부 (GC, JIT, NIO 등): ~100~200m
└── OS/기타: 나머지
```

JVM 힙은 컨테이너 limit의 70~80%에서 시작한다. 나머지는 Metaspace, 스레드 스택, NIO Direct Buffer 같은 힙 밖 메모리가 쓴다. 힙 밖 메모리는 limit이 얼마든 수백 MB가 들어서, 위 예시처럼 limit이 1Gi 정도로 작으면 50~60%로 낮춘다. 스레드가 많거나 Direct Buffer나 네이티브 메모리를 많이 쓰는 앱도 비율을 낮춘다.

```bash
# JVM이 컨테이너 메모리를 인식하도록 (Java 10+)
java -XX:MaxRAMPercentage=75.0 -jar app.jar
```

## Linux 메모리 확인

```bash
free -h
              total    used    free    shared  buff/cache  available
Mem:           16G     12G     200M    100M    3.8G        3.5G
```

| 항목 | 의미 |
|---|---|
| used | 실제 사용 중인 메모리 |
| free | 완전히 비어있는 메모리 |
| buff/cache | 디스크 캐시 (필요 시 즉시 해제 가능) |
| available | 실제로 사용 가능한 메모리 (free + 해제 가능한 cache) |

free가 0이어도 available이 넉넉하면 정상이다. Linux는 놀고 있는 메모리를 디스크 캐시로 쓰기 때문이다.

## 자주 깨지는 곳

- free가 0이라고 메모리가 모자란다고 판단하면 틀린다. 봐야 할 값은 available이다.
- 컨테이너 limit과 JVM 힙을 같은 값으로 잡으면, 힙 밖 메모리가 들어갈 자리가 없어 컨테이너 OOM이 난다.
- `-Xmx`만 정하고 Metaspace나 Direct Buffer를 계산에서 빼먹으면, 같은 이유로 OOM이 난다.
- Swap이 도는데 메모리는 그대로 두고 애플리케이션만 튜닝하면, 디스크로 밀려난 페이지 때문에 계속 느리다.
- OOM Killer 로그를 안 보면 프로세스가 왜 죽었는지 끝내 모른다. `dmesg`부터 확인한다.

## 한 번에 설명하기

> OS는 가상 메모리와 페이징으로 프로세스끼리 메모리를 나눠 씁니다. 물리 메모리가 모자라면 Swap을 쓰고, Swap까지 모자라면 OOM Killer가 프로세스를 죽입니다.
>
> 메모리를 확인할 때는 `free -h`에서 free가 아니라 available을 봅니다.
>
> 컨테이너에서는 JVM 힙을 limit의 70~80%에서 시작해서, Metaspace나 스레드 스택 같은 힙 밖 메모리가 들어갈 자리를 남겨 둡니다.

## 꼬리 질문

> [!question]- available이 충분한데 OOM이 발생할 수 있는가?
> 날 수 있습니다. cgroup은 그 컨테이너가 만든 페이지 캐시도 메모리 사용량에 넣습니다. 캐시는 부족하면 회수되지만, 서버 전체로 본 available과 컨테이너 안에서 쓸 수 있는 양은 다릅니다. 그래서 컨테이너 기준 메모리 사용량을 따로 봐야 합니다.

> [!question]- JVM에서 -Xmx를 컨테이너 limit과 같게 하면 안 되는 이유는?
> JVM은 힙 말고도 Metaspace, Thread Stack, GC가 쓰는 메모리, NIO Direct Buffer 같은 곳에 메모리를 씁니다. 힙이 limit을 다 차지하면, 힙 밖에서 메모리를 더 쓰는 순간 컨테이너 OOM이 납니다.

> [!question]- Swap을 아예 비활성화하면 안 되는가?
> 끌 수는 있지만, 그러면 메모리가 모자라는 순간 바로 OOM Killer가 움직입니다. DB 서버처럼 Swap으로 느려지는 게 치명적인 곳은 swappiness를 낮추거나 Swap을 끄기도 합니다. 일반 애플리케이션 서버는 Swap을 조금 남겨 두는 편이 안전합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Linux kernel: Control Group v2 (memory)](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [proc_meminfo(5)](https://man7.org/linux/man-pages/man5/proc_meminfo.5.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[system-resource-monitoring]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]
- [[01-core/java/memory-leak-and-oom|memory-leak-and-oom]]