---
title: Resource Request와 Limit
description: Kubernetes에서 CPU와 메모리를 얼마나 예약하고 어디까지 쓰게 할지 정하는 법
tags: [concept, kubernetes]
---

# Resource Request와 Limit

Resource request는 Pod를 어느 Node에 배치할지 정할 때 쓰는 최소 예약량이다. limit은 container가 쓸 수 있는 자원의 상한이다.

둘 다 잘못 잡으면 바로 장애로 드러난다. CPU limit이 낮으면 throttling 때문에 응답이 느려지고, memory limit을 넘으면 container가 OOMKilled로 죽는다. 그래서 값은 감으로 넣지 않고, 실제 사용량과 부하 테스트 결과를 보고 정한다.

## 동작

1. Scheduler는 request를 보고 Pod를 배치할 Node를 고른다.
2. container는 limit 안에서 CPU와 memory를 쓴다.
3. CPU 사용량이 limit에 걸리면 throttling이 생긴다.
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

- request와 limit이 무엇이 다른지 모르고 같은 값만 넣으면, 둘을 따로 둔 의미가 없어진다. request는 배치 기준이고 limit은 상한이다.
- CPU throttling을 애플리케이션 성능 문제로만 보면, 코드를 아무리 고쳐도 지연이 그대로다. limit이 그대로이기 때문이다.
- memory limit 없이 배포하면, container 하나의 메모리 폭주가 노드 전체로 번진다.
- 로컬에서 잰 평균 사용량으로 값을 정하면, 운영 peak에서 자원이 모자란다.
- JVM heap과 container memory limit을 따로 계산하면, heap은 남는데 container가 OOMKilled 된다. heap 말고도 metaspace와 native memory가 limit 안에 들어가야 한다.

## 운영에서 볼 것

- `kubectl describe pod`로 request, limit, OOMKilled 이벤트를 본다.
- 메트릭으로는 CPU usage, CPU throttling, memory working set, restart count를 본다.
- peak 트래픽에서 latency와 자원 사용량을 같이 본다.
- limit 안에 JVM heap, metaspace, native memory가 다 들어가는지 리뷰한다.

## 한 번에 설명하기

> Request는 스케줄링 기준이고, limit은 쓸 수 있는 최대치입니다. CPU limit에 걸리면 throttling으로 지연이 늘고, memory limit을 넘으면 OOMKilled가 나고, request를 너무 크게 잡으면 Pod가 Pending에 걸립니다.
>
> 그래서 저는 값을 실제 메트릭과 peak 부하를 보고 정합니다. JVM 애플리케이션이면 heap뿐 아니라 native memory까지 limit 안에 들어가게 계산합니다.

## 꼬리 질문

- Request와 limit은 어떻게 다른가?
- CPU throttling은 어떤 증상으로 나타나나?
- Java 애플리케이션의 memory limit을 잡을 때 무엇을 따지나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

## 관련 문서

- [[kubernetes]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
