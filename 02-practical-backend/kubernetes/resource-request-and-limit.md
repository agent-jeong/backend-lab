---
title: Resource Request와 Limit
description: Kubernetes에서 CPU와 메모리 자원 예약과 제한을 설정하는 기준
---

# Resource Request와 Limit

## 한 줄 정의

Resource request는 Pod 스케줄링을 위한 최소 예약 자원이고, limit은 container가 사용할 수 있는 최대 자원 제한이다.

## 실무에서 왜 문제 되는가

- request가 없으면 노드에 과밀 배치되어 부하 시 성능이 급격히 나빠질 수 있다.
- memory limit을 넘으면 container가 OOMKilled 될 수 있다.
- CPU limit이 낮으면 throttling으로 latency가 증가할 수 있다.
- request를 과도하게 잡으면 클러스터 자원이 남아도 Pod가 스케줄링되지 않을 수 있다.

## 동작 원리

1. Scheduler는 request를 기준으로 Pod를 배치할 Node를 고른다.
2. container는 limit 범위 안에서 CPU와 memory를 사용한다.
3. CPU 사용이 limit에 의해 제한되면 throttling이 발생할 수 있다.
4. memory limit을 넘으면 container가 종료될 수 있다.
5. 실제 사용량 메트릭을 보고 request와 limit을 조정한다.

## 실무 판단 기준

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| Pod Pending | request와 node allocatable | 요청 자원이 커서 배치가 안 될 수 있다 |
| 응답 지연 증가 | CPU throttling | CPU limit 설정이 병목일 수 있다 |
| 재시작 반복 | OOMKilled | memory limit 초과를 확인한다 |
| 비용 최적화 | 실제 사용량 p95 | 과도한 request를 줄인다 |
| 안정성 우선 서비스 | request 명확히 설정 | 필요한 자원을 예약한다 |

## 자주 나는 실수

- request와 limit의 차이를 모른 채 같은 값으로만 설정한다.
- CPU limit으로 인한 throttling을 애플리케이션 성능 문제로만 본다.
- memory limit 없이 배포해 노드 전체에 영향을 준다.
- 로컬 평균 사용량만 보고 운영 peak를 반영하지 않는다.
- JVM heap과 container memory limit의 관계를 확인하지 않는다.

## 확인 방법

- 명령: `kubectl describe pod`로 request, limit, OOMKilled 이벤트를 확인한다.
- 메트릭: CPU usage, CPU throttling, memory working set, restart count를 본다.
- 테스트: peak 트래픽에서 latency와 resource 사용량을 같이 확인한다.
- 리뷰: JVM heap, metaspace, native memory를 포함해 limit을 잡았는지 본다.

## 장점과 한계

| 설정 | 장점 | 한계 |
|---|---|---|
| Request | 스케줄링과 자원 예약 기준이 된다 | 과하면 배치 효율이 떨어진다 |
| CPU Limit | 특정 container의 CPU 사용을 제한한다 | throttling으로 지연이 늘 수 있다 |
| Memory Limit | 메모리 폭주를 격리한다 | 초과 시 OOMKilled가 발생한다 |

## 짧은 예제

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1"
    memory: "1Gi"
```

값은 감으로 정하기보다 실제 사용량과 부하 테스트 결과를 기준으로 조정한다.

## 핵심 요약

Request는 스케줄링 기준이고 limit은 사용 가능한 최대 자원 제한이다.

CPU limit 설정은 throttling으로 latency에 영향을 줄 수 있다.

Memory limit을 넘으면 OOMKilled가 발생할 수 있다.

request를 과도하게 잡으면 클러스터 활용률이 떨어지고 Pod가 Pending될 수 있다.

JVM 애플리케이션은 heap뿐 아니라 native memory까지 고려해야 한다.

자원 설정은 실제 메트릭과 peak 부하를 기준으로 조정한다.

## 꼬리 질문

- Request와 limit의 차이는 무엇인가?
- CPU throttling은 어떤 증상으로 나타나는가?
- Java 애플리케이션의 memory limit을 잡을 때 무엇을 고려할 것인가?

## 관련 문서

- [[kubernetes]]
- [[01-core/java/jvm-memory-structure|jvm-memory-structure]]
- [[02-practical-backend/performance/latency-and-throughput|latency-and-throughput]]
