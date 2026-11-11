---
title: Graceful Shutdown
description: Pod가 내려갈 때 새 요청은 그만 받고 처리 중인 요청과 작업을 마친 뒤 종료하게 하는 Kubernetes와 Spring Boot 설정
tags: [concept, kubernetes]
---

# Graceful Shutdown

Graceful shutdown은 프로세스를 끝낼 때 새 요청은 그만 받고, 처리 중인 요청과 작업을 마치고, 자원을 정리한 뒤 내려가는 것이다.

Kubernetes에서는 배포할 때마다 모든 Pod가 한 번씩 종료된다. 종료가 거칠면 배포 때마다 502가 몇 건씩 나고, 결제 승인 요청을 외부로 보낸 직후 컨테이너가 죽어 승인 결과를 DB에 적지 못하는 일이 생긴다. 그래서 무중단 배포는 새 Pod를 잘 띄우는 일과 옛 Pod를 잘 내리는 일이 같이 맞아야 된다.

> [!tip] 함께 읽기
> - [[rolling-update-and-rollback]]: 배포 중 옛 Pod가 내려가는 흐름
> - [[readiness-and-liveness-probe]]: 트래픽을 받는 Pod를 고르는 기준

## Pod가 종료되는 순서

Pod 삭제 요청(배포, 스케일 다운, 노드 drain)이 오면 두 갈래 일이 동시에 시작된다.

1. API 서버가 Pod를 Terminating으로 표시하고 grace period를 기록한다. `terminationGracePeriodSeconds` 기본값은 30초다.
2. 노드의 kubelet은 `preStop` hook(종료 직전에 실행할 명령)이 있으면 먼저 실행한다. hook이 끝나야 컨테이너의 PID 1(컨테이너 안에서 처음 뜬 프로세스)에 SIGTERM(정리하고 끝내라는 신호)을 보낸다.
3. 같은 순간 control plane은 이 Pod를 Service의 EndpointSlice(Service가 요청을 보낼 Pod 주소 목록)에서 종료 중(ready=false)으로 표시한다. kube-proxy와 Ingress controller는 이 변경을 받아 라우팅 목록에서 Pod를 뺀다.
4. grace period가 끝났는데도 컨테이너가 살아 있으면 SIGKILL(정리할 틈 없이 바로 죽이는 신호)로 강제 종료한다. 이 시간은 `preStop`이 시작되기 전부터 세며, `preStop`과 SIGTERM 이후의 종료 시간을 합친 시간이다.

```
t=0  Pod 삭제 요청
 ├─ kubelet:        preStop 실행 ──→ SIGTERM ──→ 앱 종료 처리 ──→ (grace period 끝) SIGKILL
 └─ control plane:  EndpointSlice에서 제외 ──→ kube-proxy, Ingress가 라우팅에서 뺌 (전파에 시간이 걸린다)
```

### 엔드포인트에서 빠지는 시점과의 경쟁

배포 중 502가 나는 가장 흔한 원인은 2번과 3번의 경쟁이다. 두 갈래는 순서 없이 동시에 진행되고, 라우팅 목록이 모든 노드와 Ingress에 퍼지는 데는 시간이 걸린다. `preStop`이 없으면 앱은 SIGTERM을 바로 받아 포트를 닫는데, 아직 이 Pod를 목적지로 알고 있는 Ingress나 kube-proxy가 요청을 보내면 연결이 거부되어 502가 난다.

그래서 `preStop`에서 몇 초 잠든다. 그 사이 라우팅 목록에서 Pod가 빠지고, 그다음 SIGTERM을 받은 앱은 이미 들어온 요청만 마치면 된다.

```yaml
spec:
  terminationGracePeriodSeconds: 45
  containers:
    - name: app
      image: example-service:1.0.0
      lifecycle:
        preStop:
          sleep:
            seconds: 10
```

Spring Boot 문서는 Kubernetes 1.32 이상에서 `sleep` 핸들러를 쓰고, 그보다 낮으면 `exec`로 `["sh", "-c", "sleep 10"]`을 부르라고 안내한다. `exec` 방식은 이미지에 셸이 있어야 한다. 잠드는 시간은 라우팅에서 빠지는 데 걸리는 시간보다 길게 잡고, 클러스터마다 다르니 배포하며 재 본다.

## Spring Boot 쪽 설정

`server.shutdown=graceful`이면 SIGTERM을 받은 뒤 새 요청은 받지 않고 처리 중인 요청이 끝나기를 기다린다. Spring Boot 3.4부터는 이게 기본값이고, 3.3 이하는 직접 켜야 한다. Tomcat, Jetty, Reactor Netty는 네트워크 계층에서 새 요청을 받지 않고, Undertow는 연결은 받되 503으로 바로 답한다.

```yaml
server:
  shutdown: graceful   # 3.4부터 기본값. 3.3 이하에서는 직접 켠다
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s   # 기본값 30s
```

`spring.lifecycle.timeout-per-shutdown-phase`는 종료 단계(phase) 하나를 기다리는 최대 시간이다. 이 시간이 지나도 끝나지 않은 요청은 끊긴다. Tomcat이면 로그에 `Commencing graceful shutdown. Waiting for active requests to complete`가 찍히고, 다 끝나면 `Graceful shutdown complete`, 시간이 다 돼 끊으면 `Graceful shutdown aborted with one or more requests still active`가 찍힌다.

시간은 바깥에서 안으로 맞춘다. `terminationGracePeriodSeconds`는 `preStop` 시간과 앱 종료 시간을 합친 것보다 길어야 한다. `preStop` 10초에 `timeout-per-shutdown-phase` 30초면 기본 grace period 30초로는 모자라서, 앱이 요청을 마치기 전에 SIGKILL을 맞는다. 위 예시에서 45초로 늘린 이유다.

컨텍스트를 닫기 시작하면 Spring Boot는 readiness를 `REFUSING_TRAFFIC`으로 바꾼다(3.5 기준 확인). 하지만 종료 중인 Pod는 이미 EndpointSlice에서 ready=false라서, 이것만으로 위의 경쟁이 풀리지는 않는다. 경쟁은 `preStop` 지연으로 푼다.

SIGTERM은 컨테이너의 PID 1이 받는다. `ENTRYPOINT ["java", "-jar", "app.jar"]`처럼 exec 형식으로 띄우면 자바 프로세스가 PID 1이 된다. 셸 스크립트로 띄우면서 마지막 줄에 `exec java ...`를 쓰지 않으면 셸이 신호를 받고 자바 프로세스는 받지 못해, grace period가 다 지난 뒤 SIGKILL로 죽는다.

## 처리 중인 일을 안전하게 끝내기

HTTP 요청 말고도 종료 때 끊기는 일이 있다. 일의 종류마다 멈추는 방법이 다르다.

| 일 | 종료 때 할 일 | 끊기면 생기는 일 |
|---|---|---|
| HTTP 요청 | `server.shutdown=graceful`로 처리 중인 요청을 마친다 | 클라이언트가 502나 연결 끊김을 받는다 |
| `@Async`, 스레드 풀 작업 | `spring.task.execution.shutdown.await-termination=true`와 기다릴 시간을 준다. 기본값은 false다 | 큐에 남은 작업이 조용히 버려진다 |
| `@Scheduled` 작업 | `spring.task.scheduling.shutdown.await-termination=true`로 도는 작업을 기다린다 | 작업이 중간에 끊기고 다음 실행 때까지 상태가 어긋난다 |
| 메시지 소비 | 리스너가 새 메시지를 가져오지 않게 멈추고, 처리 중인 메시지를 마친 뒤 ack나 offset commit을 한다 | ack 전에 죽으면 같은 메시지가 다시 온다 |
| 긴 배치 | grace period 안에 다 끝낼 수 없으니, chunk 단위로 커밋하고 다음 chunk 전에 멈춰도 재시작할 수 있게 만든다 | 실행 상태가 "처리 중"으로 남아 다음 실행이 막힌다 |

메시지 소비와 배치는 아무리 잘 내려도 "처리는 했는데 ack나 상태 기록 전에 죽는" 틈이 남는다. 그래서 종료를 다듬는 것과 별개로, 같은 메시지가 두 번 와도 한 번만 반영되게 소비자를 멱등하게 만든다([[message-consumer-idempotency]]). 배치는 비정상 종료 뒤 남은 상태를 되살리는 기준을 둔다([[duplicate-execution-prevention]], [[retryable-batch-design]]).

## 자주 깨지는 곳

- `preStop` 지연 없이 배포하면, 라우팅 목록이 갱신되기 전에 앱이 포트를 닫아 배포 때마다 502가 몇 건씩 난다.
- `preStop` 시간과 `timeout-per-shutdown-phase`를 늘리고 `terminationGracePeriodSeconds`를 그대로 두면, 앱이 요청을 마치기 전에 SIGKILL을 맞는다.
- 셸 스크립트로 앱을 띄우면서 `exec`를 빼면, SIGTERM이 자바 프로세스에 닿지 않아 graceful shutdown이 한 번도 돌지 않는다.
- Spring Boot 3.3 이하에서 `server.shutdown`을 켜지 않으면, SIGTERM을 받는 즉시 처리 중인 요청이 끊긴다.
- 스레드 풀의 `await-termination`을 켜지 않으면, `@Async`로 넘긴 알림이나 후처리가 종료 때 조용히 사라진다.
- 처리 중인 요청이 grace period보다 오래 걸리는 API가 있으면, 설정을 아무리 맞춰도 그 요청은 끊긴다. 긴 작업은 비동기 작업으로 빼고 요청은 접수만 받는다.
- `exec` 방식 `preStop`을 셸 없는 이미지에 걸면, hook이 실패하고 kubelet이 컨테이너를 기다림 없이 종료한다. 이벤트에 `FailedPreStopHook`이 남는다.

## 운영에서 볼 것

- 배포하는 동안 Ingress나 로드밸런서의 502, 503 수를 본다. 배포 시각에만 튀면 종료 순서를 의심한다.
- `kubectl get endpointslices -l kubernetes.io/service-name=example-service -w`로 종료 중인 Pod가 언제 빠지는지 지켜본다.
- 앱 로그에서 `Graceful shutdown complete`와 `aborted`의 비율을 본다. `aborted`가 나오면 timeout보다 오래 걸리는 요청이 있다.
- `kubectl describe pod`의 이벤트에서 `FailedPreStopHook`이나 강제 종료가 있는지 본다.

## 한 번에 설명하기

> Graceful shutdown은 Pod가 내려갈 때 새 요청은 그만 받고 처리 중인 요청을 마친 뒤 종료하게 하는 것입니다. Kubernetes는 Pod를 지울 때 `preStop` 실행 뒤 SIGTERM을 보내는 일과 Service 엔드포인트에서 빼는 일을 동시에 하기 때문에, 앱이 먼저 포트를 닫으면 아직 들어오던 요청이 502로 실패합니다.
>
> 그래서 저는 `preStop`에서 몇 초 잠들어 라우팅에서 빠질 시간을 벌고, Spring Boot는 `server.shutdown=graceful`과 `timeout-per-shutdown-phase`로 처리 중인 요청을 기다리게 합니다. `terminationGracePeriodSeconds`는 이 둘을 합친 것보다 길게 잡습니다.
>
> 메시지 소비와 배치는 종료 중에 끊길 틈이 남으니, 다시 처리돼도 결과가 같게 멱등하게 만들고 재시작할 수 있게 설계합니다.

## 꼬리 질문

> [!question]- 배포 중에 502가 몇 건씩 나는 이유는?
> Pod를 지울 때 SIGTERM 전달과 엔드포인트 제외가 동시에 일어나서입니다. 라우팅 목록이 갱신되기 전에 앱이 포트를 닫으면, 아직 이 Pod로 요청을 보내는 Ingress나 kube-proxy가 연결 거부를 받습니다. `preStop`에서 잠깐 기다려 라우팅에서 먼저 빠지게 하면 줄어듭니다.

> [!question]- terminationGracePeriodSeconds는 어떻게 정하나?
> `preStop` 지연과 앱이 처리 중인 요청을 마치는 시간을 더한 것보다 길게 잡습니다. grace period는 `preStop`이 시작되기 전부터 세기 때문에, 짧으면 앱이 요청을 마치기 전에 SIGKILL을 맞습니다. 기본값은 30초입니다.

> [!question]- server.shutdown=graceful만 켜면 충분한가?
> 아닙니다. 그 설정은 SIGTERM을 받은 뒤의 일만 다룹니다. 엔드포인트에서 빠지기 전에 SIGTERM이 오면 앱은 새 요청을 거절하는데 트래픽은 아직 들어오니, `preStop` 지연이 같이 있어야 합니다. 스레드 풀 작업과 메시지 소비도 따로 기다리게 해야 합니다.

> [!question]- Kafka 같은 메시지를 소비하던 중에 Pod가 내려가면 어떻게 되나?
> 리스너가 새 메시지를 가져오지 않게 멈추고 처리 중인 메시지를 마친 뒤 offset을 커밋하는 게 정상 흐름입니다. 그래도 처리는 끝났는데 커밋 전에 죽으면 같은 메시지가 다른 Pod로 다시 갑니다. 그래서 소비자는 같은 메시지를 두 번 받아도 한 번만 반영되게 멱등하게 만듭니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Pod Lifecycle (Termination of Pods)](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Spring Boot: Graceful Shutdown](https://docs.spring.io/spring-boot/3.5/reference/web/graceful-shutdown.html)
- [Spring Boot: Deploying to the Cloud (Kubernetes Container Lifecycle)](https://docs.spring.io/spring-boot/3.5/how-to/deployment/cloud.html)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[rolling-update-and-rollback]]
- [[readiness-and-liveness-probe]]
- [[pod-and-container]]
- [[message-consumer-idempotency]]
