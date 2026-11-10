---
title: "CPU 스케줄링 알고리즘"
description: CPU 스케줄링 알고리즘과 서버 성능에 미치는 영향
tags: [concept, os]
---

# CPU 스케줄링 알고리즘

CPU 스케줄링은 실행을 기다리는 여러 프로세스나 스레드 중 다음에 누구에게 CPU를 줄지 정하는 OS의 메커니즘이다.

서버에서 이게 드러나는 순간은 대개 두 가지다. 응답 시간이 불규칙하게 늘어나는데 이유를 모를 때, 그리고 컨테이너 CPU limit 때문에 실행이 멈추는 Throttling이 생길 때다. 둘 다 I/O 대기와 CPU 대기를 구분할 줄 알아야 원인을 찾는다.

## 주요 알고리즘

| 알고리즘 | 방식 | 특징 |
|---|---|---|
| FCFS (First-Come First-Served) | 먼저 온 순서대로 | 단순하지만, 긴 작업이 앞에 있으면 뒤가 대기 (Convoy Effect) |
| Round Robin | 시간 할당량(Time Quantum)만큼 순서대로 | 공정하고 응답 시간 균일. 성능은 Time Quantum 크기에 달려 있다 |
| Priority | 우선순위가 높은 것부터 | 낮은 우선순위가 계속 대기할 수 있음 (Starvation) |
| CFS (Completely Fair Scheduler) | 실행 시간이 가장 적은 것부터 | Linux 6.5까지의 기본 스케줄러. Red-Black Tree로 공정성 보장 (6.6부터 EEVDF로 교체) |

### Linux CFS와 EEVDF

CFS는 커널 2.6.23부터 6.5까지 Linux의 기본 스케줄러였고, 모든 프로세스가 CPU를 공평하게 나눠 쓰도록 설계됐다. 커널 6.6부터는 EEVDF가 대체했다. 다만 vruntime 기반 공정 분배라는 큰 틀은 같아서 아래 설명은 그대로 유효하다. EEVDF는 여기에 "지연 허용 한도(deadline)"를 더해, 짧게 자주 깨어나는 작업의 응답성을 높였다.

```
vruntime(가상 실행 시간)이 가장 작은 프로세스에 CPU 할당
→ 적게 실행된 프로세스가 우선 → 모든 프로세스가 공평하게 실행
```

우선순위는 nice 값(-20 ~ 19)으로 조정한다. 값이 작을수록 우선순위가 높다.

## 선점형과 비선점형

| 구분 | 선점형 (Preemptive) | 비선점형 (Non-preemptive) |
|---|---|---|
| 중단 | OS가 강제로 CPU 회수 가능 | 작업이 끝나거나 자발적 양보까지 대기 |
| 예시 | Round Robin, CFS | FCFS |
| 장점 | 공정, 응답 시간 예측 가능 | 컨텍스트 스위칭 비용 없음 |

현대 OS는 대부분 선점형이다.

## CPU 바운드와 I/O 바운드

스레드 수는 작업이 어느 쪽인지 보고 정한다.

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

CPU limit을 넘으면 **Throttling**이 걸린다. 프로세스가 죽지는 않지만 실행이 지연된다.

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

Throttling은 로그에 남지 않아 찾기 어렵다. 응답 시간이 불규칙하게 늘어나면 먼저 의심한다.

## 자주 깨지는 곳

- **CPU 사용률만 보고 iowait를 놓친다.** CPU가 한가해 보여도 I/O 대기로 느릴 수 있다.
- **컨테이너 CPU limit을 너무 낮게 잡는다.** Throttling이 상시 걸려 응답 시간이 들쭉날쭉해진다.
- **CPU 바운드 작업에 스레드를 많이 만든다.** 코어 수 이상은 컨텍스트 스위칭만 반복한다.
- **CPU 바운드인지 I/O 바운드인지 보지 않고 스레드 수를 정한다.** 위 표의 공식이 완전히 다르다.
- **GC가 CPU를 쓰는 걸 애플리케이션 로직 문제로 본다.** `top -H`로 어떤 스레드가 쓰는지 먼저 확인한다.

## 면접에서 말하기

> Linux는 CFS, 6.6부터는 후속인 EEVDF로 vruntime 기반 공정 분배를 합니다. 저는 스레드 수를 정할 때 먼저 작업이 CPU 바운드인지 I/O 바운드인지 구분합니다. 컨테이너에서는 CPU limit을 넘으면 Throttling이 걸려 응답 시간이 불규칙해지는데 로그에는 안 남기 때문에, `top`과 `/sys/fs/cgroup/cpu/cpu.stat`으로 사용 패턴과 Throttling을 확인합니다.

## 꼬리 질문

> [!question]- CPU Throttling은 어떻게 발견하는가?
> 애플리케이션 로그에는 남지 않습니다. cgroup의 `cpu.stat`에서 `nr_throttled`와 `throttled_time`을 확인하거나, Kubernetes에서는 `container_cpu_cfs_throttled_periods_total` 메트릭으로 모니터링합니다.

> [!question]- nice 값은 언제 조정하는가?
> 배치 작업처럼 우선순위가 낮아도 되는 프로세스의 nice 값을 높이면(예: 19), 실시간 요청 처리 프로세스에 CPU를 더 많이 할당할 수 있습니다. 실무에서 직접 조정하는 경우는 드물고, 컨테이너 환경에서는 CPU request/limit으로 관리합니다.

> [!question]- Context Switching 비용은 얼마나 되는가?
> 일반적으로 수 마이크로초(µs) 수준이지만, 캐시 무효화(Cache Invalidation)까지 고려하면 간접 비용이 더 큽니다. 스레드가 너무 많으면 이 비용이 누적되어 처리량이 오히려 떨어집니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Linux kernel: EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html)
- [sched(7)](https://man7.org/linux/man-pages/man7/sched.7.html)

## 관련 문서

- [[01-core/os/os|os]]
- [[process-and-thread]]
- [[context-switching]]
- [[system-resource-monitoring]]
