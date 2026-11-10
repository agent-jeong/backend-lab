---
title: Resource Request와 Limit
description: Kubernetes에서 CPU와 메모리 자원 예약과 제한을 설정하는 기준
---

# Resource Request와 Limit

Resource request는 Pod를 어디에 배치할지 정할 때 쓰는 최소 예약 자원이다. limit은 container가 쓸 수 있는 자원의 상한이다.

둘 다 잘못 잡으면 바로 장애로 드러난다. CPU limit이 낮으면 throttling으로 지연이 늘고, memory limit을 넘으면 container가 OOMKilled 된다. 값은 감이 아니라 실제 사용량과 부하 테스트 결과로 정한다.

## 동작

1. Scheduler는 request를 기준으로 Pod를 배치할 Node를 고른다.
2. container는 limit 안에서 CPU와 memory를 쓴다.
3. CPU 사용이 limit에 걸리면 throttling이 생긴다.
4. memory limit을 넘으면 container가 종료된다.
5. 실제 사용량 메트릭을 보고 request와 limit을 조정한다.

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1"
    memory: "1Gi"
```

| 설정 | 역할 | 잘못 잡으면 |
|---|---|---|
| Request | 스케줄링과 자원 예약의 기준 | 없으면 노드에 과밀 배치돼 부하 시 성능이 급격히 나빠진다. 과하면 자원이 남아도 Pod가 배치되지 않는다 |
| CPU Limit | 특정 container의 CPU 사용 제한 | throttling으로 지연이 는다 |
| Memory Limit | 메모리 폭주를 격리 | 넘으면 OOMKilled가 난다 |

## 상황별로 볼 것

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| Pod Pending | request와 node allocatable | 요청 자원이 커서 배치가 안 될 수 있다 |
| 응답 지연 증가 | CPU throttling | CPU limit 설정이 병목일 수 있다 |
| 재시작 반복 | OOMKilled | memory limit 초과를 확인한다 |
| 비용 최적화 | 실제 사용량 p95 | 과도한 request를 줄인다 |
| 안정성 우선 서비스 | request 명확히 설정 | 필요한 자원을 예약한다 |

## 자주 깨지는 곳

- **request와 limit의 차이를 모른 채 같은 값만 넣는다.** 하나는 배치 기준, 하나는 상한이라 의도가 다르다.
- **CPU throttling을 애플리케이션 성능 문제로만 본다.** 코드를 아무리 고쳐도 limit이 그대로면 지연도 그대로다.
- **memory limit 없이 배포한다.** 한 container의 메모리 폭주가 노드 전체에 번진다.
- **로컬 평균 사용량으로 값을 정한다.** 운영 peak에서 모자란다.
- **JVM heap과 container memory limit을 따로 본다.** heap 외에 metaspace와 native memory도 limit 안에 들어가야 한다.

## 운영에서 볼 것

- `kubectl describe pod`로 request, limit, OOMKilled 이벤트를 본다.
- 메트릭은 CPU usage, CPU throttling, memory working set, restart count.
- peak 트래픽에서 latency와 자원 사용량을 같이 본다.
- limit에 JVM heap, metaspace, native memory가 다 들어가는지 리뷰한다.

## 면접에서 말하기

> Request는 스케줄링 기준이고, limit은 쓸 수 있는 최대치입니다. CPU limit은 throttling으로 지연을 늘리고, memory limit을 넘으면 OOMKilled가 나며, request를 과하게 잡으면 Pod가 Pending에 걸립니다. 저는 값을 실제 메트릭과 peak 부하 기준으로 잡고, JVM 애플리케이션이면 heap뿐 아니라 native memory까지 limit 안에 넣어 계산합니다.

## 꼬리 질문

- Request와 limit은 어떻게 다른가?
- CPU throttling은 어떤 증상으로 나타나나?
- Java 애플리케이션의 memory limit을 잡을 때 무엇을 따지나?

## 관련 문서

- [[kubernetes]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
