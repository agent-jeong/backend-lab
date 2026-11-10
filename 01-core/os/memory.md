---
title: "OS 메모리 관리 (가상 메모리, 페이징)"
description: OS 메모리 관리, 가상 메모리, 페이징과 OOM
---

# OS 메모리 관리 (가상 메모리, 페이징)

OS는 물리 메모리를 프로세스마다 따로 보이는 가상 주소 공간으로 감싸고, 페이징으로 나눠 관리한다. 덕분에 프로세스끼리 메모리가 격리되고, 물리 메모리를 아껴 쓸 수 있다.

서버에서 메모리 문제는 세 모습으로 나타난다. Swap이 돌면서 응답이 급격히 느려지거나, OOM Killer가 프로세스를 죽이거나, 컨테이너 limit과 JVM 힙을 잘못 맞춰 OOM이 반복된다. 반대로 `free`가 0인 정상 상태를 장애로 오판하는 일도 흔하다.

## 가상 메모리 (Virtual Memory)

각 프로세스는 자기만의 가상 주소 공간을 가진다. OS가 가상 주소를 물리 주소로 바꿔 준다.

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

이 구조로 얻는 것은 세 가지다. 프로세스 간 메모리가 격리되고, 물리 메모리보다 큰 주소 공간을 쓸 수 있고, 메모리 단편화가 줄어든다.

## 페이징 (Paging)

가상 메모리를 고정 크기 블록(Page, 보통 4KB)으로 나눠 관리한다.

### Page Fault

접근하려는 Page가 물리 메모리에 없을 때 일어난다.

```
프로세스가 가상 주소 접근
→ Page Table 확인
→ 물리 메모리에 없음 (Page Fault)
→ 디스크에서 해당 Page를 메모리로 로드
→ Page Table 업데이트
→ 접근 재시도
```

Page Fault가 잦으면 그만큼 디스크 I/O가 늘어 성능이 떨어진다.

## Swap

물리 메모리가 부족하면 사용 빈도가 낮은 Page를 디스크(Swap 영역)로 내보낸다.

```bash
# Swap 사용량 확인
free -h
              total    used    free    shared  buff/cache  available
Mem:           16G     12G     200M    100M    3.8G        3.5G
Swap:           4G     1.5G    2.5G
```

**Swap이 활발하면 서버 응답이 급격히 느려진다.** 디스크 I/O는 메모리보다 수만 배 느리다.

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

물리 메모리와 Swap이 모두 부족하면 OS의 OOM Killer가 프로세스를 강제 종료한다. 프로세스가 이유 없이 사라졌다면 이 로그부터 본다.

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

컨테이너 메모리 limit을 넘으면 cgroup OOM Killer가 프로세스를 종료하고, Pod는 `OOMKilled` 상태로 재시작된다.

### JVM + 컨테이너 메모리 설정

```
Container limit: 1Gi
├── JVM Heap (-Xmx): 512m
├── JVM Metaspace: ~100m
├── JVM Thread Stack: 스레드 수 × 1MB
├── JVM 내부 (GC, JIT, NIO 등): ~100~200m
└── OS/기타: 나머지
```

**JVM 힙은 컨테이너 limit의 50~70%** 정도로 잡는다. 나머지는 힙 외 메모리(Metaspace, 스레드 스택, NIO Direct Buffer 등)가 쓴다.

```bash
# JVM이 컨테이너 메모리를 인식하도록 (Java 10+)
java -XX:MaxRAMPercentage=70.0 -jar app.jar
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

**free가 0이어도 available이 충분하면 정상이다.** Linux는 놀고 있는 메모리를 디스크 캐시로 쓴다.

## 자주 깨지는 곳

- **free가 0이라고 메모리 부족으로 본다.** 봐야 할 값은 available이다.
- **컨테이너 limit과 JVM 힙을 같은 값으로 잡는다.** 힙 외 메모리가 들어갈 자리가 없어 컨테이너 OOM이 난다.
- **`-Xmx`만 정하고 Metaspace, Direct Buffer를 빼먹는다.** 위와 같은 이유로 OOM이 난다.
- **Swap이 도는데 메모리는 그대로 두고 애플리케이션만 튜닝한다.** 디스크로 밀려난 페이지가 계속 느리게 만든다.
- **OOM Killer 로그를 안 본다.** 프로세스가 왜 죽었는지 끝내 모른다. `dmesg`부터 확인한다.

## 면접에서 말하기

> OS는 가상 메모리와 페이징으로 프로세스 메모리를 격리합니다. 물리 메모리가 부족하면 Swap이 생기고, Swap까지 부족하면 OOM Killer가 프로세스를 종료합니다. 저는 `free -h`에서 free가 아니라 available을 보고, 컨테이너에서는 JVM 힙을 limit의 50~70%로 잡아 Metaspace나 스레드 스택 같은 힙 외 메모리 자리를 남겨 둡니다.

## 꼬리 질문

> [!question]- available이 충분한데 OOM이 발생할 수 있는가?
> 가능합니다. cgroup 메모리 limit은 buff/cache를 포함해서 계산하므로, OS 전체 available과 컨테이너 내 available은 다를 수 있습니다. 컨테이너 기준의 메모리 사용량을 확인해야 합니다.

> [!question]- JVM에서 -Xmx를 컨테이너 limit과 같게 하면 안 되는 이유는?
> JVM은 힙 외에도 Metaspace, Thread Stack, GC 오버헤드, NIO Direct Buffer 등으로 메모리를 사용합니다. 힙만으로 전체 limit을 쓰면 힙 외 메모리 할당 시 컨테이너 OOM이 발생합니다.

> [!question]- Swap을 아예 비활성화하면 안 되는가?
> 가능하지만, 메모리 부족 시 바로 OOM Killer가 동작합니다. DB 서버처럼 Swap 성능 저하가 치명적인 경우 swappiness를 낮추거나 Swap을 비활성화하기도 합니다. 일반 애플리케이션 서버는 소량의 Swap을 유지하는 것이 안전합니다.

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[system-resource-monitoring]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]
- [[01-core/java/memory-leak-and-oom|memory-leak-and-oom]]