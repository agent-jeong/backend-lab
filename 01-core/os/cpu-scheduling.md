---
title: "CPU 스케줄링 알고리즘"
description: CPU 스케줄링 알고리즘과 서버 성능에 미치는 영향
---

# CPU 스케줄링 알고리즘

## 한 줄 정의

CPU 스케줄링은 실행 대기 중인 여러 프로세스/스레드 중 다음에 CPU를 할당할 대상을 결정하는 OS의 메커니즘이다.

## 실무에서 왜 중요한가

CPU 스케줄링을 이해하지 못하면 다음 문제가 생긴다.

- CPU 사용률이 100%인데 어떤 스레드가 점유하는지 모른다.
- 특정 요청의 응답 시간이 불규칙하게 늘어나는 원인을 모른다.
- I/O 대기와 CPU 대기를 구분하지 못한다.
- 컨테이너 환경에서 CPU 제한이 애플리케이션 성능에 미치는 영향을 모른다.

## 주요 스케줄링 알고리즘

| 알고리즘 | 방식 | 특징 |
|---|---|---|
| FCFS (First-Come First-Served) | 먼저 온 순서대로 | 단순하지만, 긴 작업이 앞에 있으면 뒤가 대기 (Convoy Effect) |
| Round Robin | 시간 할당량(Time Quantum)만큼 순서대로 | 공정하고 응답 시간 균일. Time Quantum이 핵심 |
| Priority | 우선순위가 높은 것부터 | 낮은 우선순위가 계속 대기할 수 있음 (Starvation) |
| CFS (Completely Fair Scheduler) | 실행 시간이 가장 적은 것부터 | Linux 기본 스케줄러. Red-Black Tree로 공정성 보장 |

### Linux CFS

현대 Linux의 기본 스케줄러다. "모든 프로세스가 공정하게 CPU를 나눠 쓰도록" 설계되었다.

```
vruntime(가상 실행 시간)이 가장 작은 프로세스에 CPU 할당
→ 적게 실행된 프로세스가 우선 → 모든 프로세스가 공평하게 실행
```

nice 값(-20 ~ 19)으로 우선순위를 조정할 수 있다. 값이 작을수록 우선순위가 높다.

## 선점형 vs 비선점형

| 구분 | 선점형 (Preemptive) | 비선점형 (Non-preemptive) |
|---|---|---|
| 중단 | OS가 강제로 CPU 회수 가능 | 작업이 끝나거나 자발적 양보까지 대기 |
| 예시 | Round Robin, CFS | FCFS |
| 장점 | 공정, 응답 시간 예측 가능 | 컨텍스트 스위칭 비용 없음 |

현대 OS는 대부분 선점형 스케줄링을 사용한다.

## CPU 바운드 vs I/O 바운드

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

## 컨테이너 환경에서의 CPU

### CPU Limit과 Throttling

```yaml
# Kubernetes Pod CPU 설정
resources:
  requests:
    cpu: "500m"     # 0.5 코어 보장
  limits:
    cpu: "1000m"    # 1 코어 제한
```

CPU limit을 초과하면 **Throttling**이 발생한다. 프로세스가 죽지는 않지만 실행이 지연된다.

```
CPU limit = 1000m (1코어)
실제 사용 = 1500m

→ OS가 100ms 중 66ms만 실행 허용, 34ms는 강제 대기
→ 응답 시간 증가, GC 시간 증가
```

```bash
# Throttling 확인
cat /sys/fs/cgroup/cpu/cpu.stat
# nr_throttled: 발생 횟수
# throttled_time: 총 throttle 시간 (ns)
```

CPU Throttling은 로그에 남지 않아서 발견하기 어렵다. 응답 시간이 불규칙하게 늘어나면 의심해야 한다.

## 자주 나는 실수

- CPU 사용률만 보고 I/O 대기(iowait)를 무시한다.
- 컨테이너 CPU limit을 너무 낮게 설정해서 Throttling이 상시 발생한다.
- CPU 바운드 작업에 스레드를 과도하게 생성해서 컨텍스트 스위칭만 반복한다.
- 스레드 수 결정 시 CPU 바운드인지 I/O 바운드인지 구분하지 않는다.
- GC가 CPU를 점유하는 것을 애플리케이션 로직의 문제로 오해한다.

## 핵심 요약

CPU 스케줄링은 Linux CFS가 기본이며, vruntime 기반으로 공정하게 CPU를 분배합니다.
CPU 바운드와 I/O 바운드를 구분해야 적절한 스레드 수를 설정할 수 있습니다.

컨테이너 환경에서 CPU limit 초과 시 Throttling이 발생하며, 응답 시간이 불규칙하게 늘어나는 원인이 됩니다.
`top`, `/sys/fs/cgroup/cpu/cpu.stat`으로 CPU 사용 패턴과 Throttling을 확인합니다.

## 꼬리 질문

> [!question]- CPU Throttling은 어떻게 발견하는가?
> 애플리케이션 로그에는 남지 않습니다. cgroup의 `cpu.stat`에서 `nr_throttled`와 `throttled_time`을 확인하거나, Kubernetes에서는 `container_cpu_cfs_throttled_periods_total` 메트릭으로 모니터링합니다.

> [!question]- nice 값은 언제 조정하는가?
> 배치 작업처럼 우선순위가 낮아도 되는 프로세스의 nice 값을 높이면(예: 19), 실시간 요청 처리 프로세스에 CPU를 더 많이 할당할 수 있습니다. 실무에서 직접 조정하는 경우는 드물고, 컨테이너 환경에서는 CPU request/limit으로 관리합니다.

> [!question]- Context Switching 비용은 얼마나 되는가?
> 일반적으로 수 마이크로초(µs) 수준이지만, 캐시 무효화(Cache Invalidation)까지 고려하면 간접 비용이 더 큽니다. 스레드가 너무 많으면 이 비용이 누적되어 처리량이 오히려 떨어집니다.

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[system-resource-monitoring]]