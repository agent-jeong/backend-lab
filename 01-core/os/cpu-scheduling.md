---
title: "CPU 스케줄링 알고리즘"
description: OS가 다음에 어느 스레드에 CPU를 줄지 정하는 방식과, 그게 서버 응답 시간에 드러나는 경우
tags: [concept, os]
---

# CPU 스케줄링 알고리즘

CPU 스케줄링은 실행을 기다리는 프로세스나 스레드 여럿 중에서, 다음에 어느 것에 CPU를 줄지 OS가 정하는 일이다.

서버를 운영하다 이걸 신경 쓰게 되는 건 보통 두 경우다. 주문 API 응답 시간이 이유 없이 들쭉날쭉할 때, 그리고 컨테이너 CPU limit에 걸려 실행이 잠깐씩 멈추는 Throttling이 생길 때다. 둘 다 I/O를 기다리는 건지 CPU를 기다리는 건지 가를 줄 알아야 원인이 보인다.

## 주요 알고리즘

| 알고리즘 | 방식 | 특징 |
|---|---|---|
| FCFS (First-Come First-Served) | 먼저 온 순서대로 | 단순하지만, 긴 작업이 앞에 있으면 뒤가 대기 (Convoy Effect) |
| Round Robin | 시간 할당량(Time Quantum)만큼 순서대로 | 공정하고 응답 시간이 고르다. 성능은 Time Quantum 크기에 달려 있다 |
| Priority | 우선순위가 높은 것부터 | 낮은 우선순위가 계속 대기할 수 있음 (Starvation) |
| CFS (Completely Fair Scheduler) | 실행 시간이 가장 적은 것부터 | Linux 6.5까지의 기본 스케줄러. Red-Black Tree로 공정성 보장 (6.6부터 EEVDF로 교체) |

### Linux CFS와 EEVDF

CFS는 커널 2.6.23부터 6.5까지 Linux의 기본 스케줄러였고, 모든 프로세스가 CPU를 공평하게 나눠 쓰게 만든 스케줄러다. 커널 6.6부터는 EEVDF로 바뀌었다. 그래도 vruntime을 보고 공평하게 나눠 준다는 큰 틀은 같아서 아래 설명은 그대로 통한다. EEVDF는 여기에 "얼마까지 늦어져도 되는지(deadline)"를 더해서, 짧게 자주 깨어나는 작업이 더 빨리 CPU를 받게 했다.

```
vruntime(가상 실행 시간)이 가장 작은 프로세스에 CPU 할당
→ 적게 실행된 프로세스가 우선 → 모든 프로세스가 공평하게 실행
```

우선순위는 nice 값(-20 ~ 19)으로 바꾼다. 값이 작을수록 우선순위가 높다.

## 선점형과 비선점형

| 구분 | 선점형 (Preemptive) | 비선점형 (Non-preemptive) |
|---|---|---|
| 중단 | OS가 강제로 CPU 회수 가능 | 작업이 끝나거나 자발적 양보까지 대기 |
| 예시 | Round Robin, CFS | FCFS |
| 장점 | 공정, 응답 시간 예측 가능 | 컨텍스트 스위칭 비용 없음 |

요즘 OS는 대부분 선점형이다.

## CPU 바운드와 I/O 바운드

스레드 수는 작업이 계산 위주인지 대기 위주인지 보고 정한다.

| 구분 | CPU 바운드 | I/O 바운드 |
|---|---|---|
| 특징 | 계산 위주 (암호화, 이미지 처리) | 대기 위주 (DB 조회, API 호출, 파일 읽기) |
| CPU 사용률 | 높음 | 낮음 (대기 중 CPU 반환) |
| 스레드 수 | 코어 수 + 1 | 코어 수 × (1 + 대기/처리 비율) |

```bash
# CPU 사용률 확인
top -H -p <PID>    # 스레드별 CPU 사용률

# CPU 바운드 확인: %us(user) 높으면 CPU 바운드
# I/O 바운드 확인: %wa(iowait) 높으면 I/O 대기
top
%Cpu(s): 85.3 us,  2.1 sy,  0.0 ni, 10.5 id,  2.1 wa
         ↑ CPU 바운드                           ↑ I/O 대기
```

## 컨테이너의 CPU limit과 Throttling

```yaml
# Kubernetes Pod CPU 설정
resources:
  requests:
    cpu: "500m"     # 0.5 코어 보장
  limits:
    cpu: "1000m"    # 1 코어 제한
```

CPU limit을 넘으면 Throttling이 걸린다. 프로세스가 죽지는 않지만, 한동안 실행을 못 하고 기다린다.

```
CPU limit = 1000m (1코어) → 100ms마다 CPU 시간 100ms까지 쓸 수 있다
스레드들이 1.5코어만큼 쓰려고 함

→ 약 66ms 만에 이번 100ms 몫을 다 쓴다
→ 남은 34ms 동안 컨테이너의 모든 스레드가 멈춘다
→ 그 사이 들어온 요청과 GC가 같이 늦어진다
```

```bash
# Throttling 확인 (cgroup v2)
cat /sys/fs/cgroup/cpu.stat
# nr_throttled: throttle이 걸린 구간 수
# throttled_usec: 멈춰 있던 시간 합계 (µs)
# cgroup v1이면 /sys/fs/cgroup/cpu/cpu.stat 의 throttled_time(ns)
```

Throttling은 로그에 남지 않아서 찾기 어렵다. 응답 시간이 불규칙하게 늘어나면 먼저 의심해 본다.

## 자주 깨지는 곳

- CPU 사용률만 보고 iowait를 놓치면, CPU는 한가한데 I/O를 기다리느라 느린 상황을 못 알아본다.
- 컨테이너 CPU limit을 너무 낮게 잡으면 Throttling이 늘 걸려서 응답 시간이 들쭉날쭉해진다.
- CPU 바운드 작업에 스레드를 많이 만들면, 코어 수를 넘는 스레드는 컨텍스트 스위칭만 늘린다.
- CPU 바운드인지 I/O 바운드인지 보지 않고 스레드 수를 정하면 틀린다. 위 표처럼 두 경우의 계산식이 완전히 다르다.
- GC가 CPU를 쓰는 걸 애플리케이션 로직 문제로 보면 엉뚱한 코드를 고친다. `top -H`로 어떤 스레드가 CPU를 쓰는지 먼저 확인한다.

## 한 번에 설명하기

> Linux는 CFS, 커널 6.6부터는 그 뒤를 이은 EEVDF로 vruntime을 보고 CPU를 공평하게 나눠 줍니다.
>
> 스레드 수를 정할 때는 먼저 작업이 CPU 바운드인지 I/O 바운드인지 나눠 봅니다.
>
> 컨테이너에서는 CPU limit을 넘으면 Throttling이 걸려 응답 시간이 불규칙해지는데, 로그에는 안 남습니다. 그래서 `top`과 `/sys/fs/cgroup/cpu/cpu.stat`으로 CPU를 어떻게 쓰는지와 Throttling이 걸렸는지를 확인합니다.

## 꼬리 질문

> [!question]- CPU Throttling은 어떻게 발견하는가?
> 애플리케이션 로그에는 안 남습니다. cgroup의 `cpu.stat`에서 `nr_throttled`와 `throttled_time`을 보거나, Kubernetes라면 `container_cpu_cfs_throttled_periods_total` 메트릭을 봅니다.

> [!question]- nice 값은 언제 조정하는가?
> 배치처럼 늦어도 되는 프로세스의 nice 값을 높이면(예: 19), 실시간 요청을 처리하는 프로세스가 CPU를 더 받습니다. 다만 실무에서 직접 만지는 일은 드물고, 컨테이너 환경에서는 CPU request와 limit으로 조절합니다.

> [!question]- Context Switching 비용은 얼마나 되는가?
> 전환 자체는 보통 몇 마이크로초(µs)지만, 캐시가 비워져서(Cache Invalidation) 생기는 간접 비용이 더 큽니다. 스레드가 너무 많으면 이 비용이 쌓여서 처리량이 오히려 떨어집니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Linux kernel: EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html)
- [sched(7)](https://man7.org/linux/man-pages/man7/sched.7.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[system-resource-monitoring]]
