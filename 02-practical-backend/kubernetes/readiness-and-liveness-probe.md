---
title: Readiness Probe와 Liveness Probe
description: Kubernetes에서 트래픽 수신 가능 상태와 재시작 필요 상태를 구분하는 기준
---

# Readiness Probe와 Liveness Probe

## 한 줄 정의

Readiness probe는 Pod가 트래픽을 받을 준비가 되었는지 판단하고, Liveness probe는 container를 재시작해야 할 정도로 비정상인지 판단한다.

## 실무에서 왜 문제 되는가

- readiness가 없으면 초기화가 끝나기 전 Pod로 요청이 들어갈 수 있다.
- liveness를 너무 엄격하게 잡으면 일시 지연에도 container가 계속 재시작된다.
- 두 probe를 같은 endpoint로 대충 구성하면 트래픽 차단과 재시작 기준이 섞인다.
- DB나 외부 API 장애를 liveness 실패로 연결하면 전체 Pod가 재시작 폭풍을 만들 수 있다.

## 동작 원리

1. kubelet이 주기적으로 probe를 실행한다.
2. readiness가 실패하면 Service endpoint에서 Pod를 제외한다.
3. readiness가 다시 성공하면 트래픽 대상에 포함한다.
4. liveness가 반복 실패하면 kubelet이 container를 재시작한다.
5. startup probe가 있으면 초기 구동 시간이 긴 애플리케이션의 liveness 판단을 늦출 수 있다.

## 실무 판단 기준

| 상태 | Probe | 기준 |
|---|---|---|
| 요청 받을 준비 안 됨 | Readiness 실패 | endpoint에서 제외한다 |
| 복구 불가능한 hang | Liveness 실패 | container 재시작을 유도한다 |
| 구동 시간이 긴 앱 | Startup probe | 초기화 중 liveness 실패를 막는다 |
| 외부 API 장애 | Readiness에 신중히 반영 | 전체 트래픽 차단 위험을 본다 |
| DB 연결 일시 지연 | 서비스 특성별 판단 | 재시작이 해결책인지 확인한다 |

## 자주 나는 실수

- readiness와 liveness를 같은 의미로 사용한다.
- liveness에서 DB, Redis, 외부 API까지 모두 확인한다.
- timeout과 failureThreshold를 너무 낮게 설정한다.
- 배포 중 readiness 실패 원인을 애플리케이션 로그만 보고 찾는다.
- startup probe 없이 구동이 긴 앱에 liveness를 바로 적용한다.

## 확인 방법

- 명령: `kubectl describe pod`로 probe 실패 event를 확인한다.
- 명령: `kubectl get endpoints`로 readiness 실패 Pod가 Service에서 제외되는지 본다.
- 테스트: 배포 중 초기화가 끝나기 전 요청이 들어가지 않는지 확인한다.
- 메트릭: restart count, readiness failure, liveness failure를 본다.

## 장점과 한계

| Probe | 장점 | 한계 |
|---|---|---|
| Readiness | 준비되지 않은 Pod로 트래픽이 가지 않게 한다 | 기준이 과도하면 정상 Pod도 트래픽에서 제외된다 |
| Liveness | 멈춘 container를 자동 재시작할 수 있다 | 잘못 설정하면 재시작 폭풍을 만든다 |
| Startup | 긴 초기화 시간을 안전하게 처리한다 | 실제 readiness 기준은 별도로 필요하다 |

## 짧은 예제

```yaml
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

트래픽 수신 가능 상태와 재시작 필요 상태는 다른 질문이므로 endpoint도 분리하는 것이 안전하다.

## 핵심 요약

Readiness는 트래픽을 받을 수 있는지 판단한다.

Liveness는 container 재시작이 필요한지 판단한다.

readiness 실패는 Service endpoint 제외로 이어지고, liveness 실패는 재시작으로 이어진다.

외부 의존성 장애를 liveness에 넣으면 재시작 폭풍을 만들 수 있다.

구동 시간이 긴 애플리케이션은 startup probe를 함께 검토한다.

probe 설정은 배포 안정성과 장애 복구 방식에 직접 영향을 준다.

## 꼬리 질문

- Readiness와 Liveness의 차이는 무엇인가?
- DB 장애를 liveness 실패로 처리하면 어떤 문제가 생길 수 있는가?
- 배포 중 503이 발생하면 probe와 Service에서 무엇을 확인할 것인가?

## 관련 문서

- [[kubernetes]]
- [[deployment-service-ingress]]
- [[02-practical-backend/observability/metrics|metrics]]
