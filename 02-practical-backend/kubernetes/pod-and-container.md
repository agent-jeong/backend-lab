---
title: Pod와 Container
description: Kubernetes에서 애플리케이션이 실행되는 최소 단위와 컨테이너 경계
tags: [concept, kubernetes]
---

# Pod와 Container

Pod는 Kubernetes가 배포하고 스케줄링하는 최소 실행 단위다. 안에는 하나 이상의 container가 있고, 이들은 네트워크와 일부 저장소를 공유한다.

Pod는 언제든 사라지고 다시 만들어진다. 그래서 Pod IP나 로컬 파일에 기대는 설계는 재배포 한 번에 깨진다. 장애를 볼 때도 문제 단위가 container인지 Pod인지부터 구분한다.

## 동작

1. Deployment 같은 controller가 Pod template으로 Pod를 만든다.
2. Scheduler가 Pod를 실행할 Node를 고른다.
3. kubelet이 container runtime으로 container를 실행한다.
4. 같은 Pod 안의 container는 같은 network namespace를 공유해 localhost로 통신한다.
5. container가 종료되면 restart policy와 controller 상태에 따라 재시작되거나 새 Pod가 만들어진다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: example-pod
spec:
  containers:
    - name: app
      image: example-service:1.0.0
      ports:
        - containerPort: 8080
```

운영에서는 Pod를 직접 만들기보다 Deployment 같은 controller로 관리한다. controller는 원하는 상태를 유지해 주지만, 잘못된 설정까지 고쳐 주지는 않는다.

## 상황별 판단

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| Pod 재시작 반복 | restart count, last state | OOM, 예외 종료, probe 실패를 구분한다 |
| 로그가 없음 | container 이름 | multi-container Pod일 수 있다 |
| Pod IP 직접 사용 | 피함 | Pod가 다시 만들어지면 IP가 바뀐다 |
| sidecar 필요 | 같은 Pod 배치 검토 | 로그 수집, 프록시처럼 생명주기를 공유한다 |
| 임시 파일 저장 | emptyDir 또는 외부 저장소 | container 파일시스템은 영속적이지 않다 |

한 Pod에 container를 여러 개 넣으면 생명주기와 리소스 사용이 함께 묶인다. sidecar처럼 같이 살고 같이 죽어야 하는 것만 넣는다.

## 자주 깨지는 곳

- **Pod와 container를 같은 것으로 본다.** 재시작은 container 단위, 재생성은 Pod 단위라 원인 추적이 엇나간다.
- **Pod가 다시 만들어져도 로컬 파일이 남는다고 생각한다.** 남지 않는다.
- **multi-container Pod에서 어느 container 로그인지 확인하지 않는다.** 엉뚱한 로그를 보고 "로그가 없다"고 판단한다.
- **Pod IP를 설정 파일이나 외부 시스템에 직접 등록한다.** 재생성되면 IP가 바뀌어 연결이 끊긴다.
- **CrashLoopBackOff를 애플리케이션 로그만 보고 판단한다.** 애플리케이션 버그, OOM, probe 실패, 노드 문제는 event와 last state를 봐야 갈린다.

## 운영에서 볼 것

- `kubectl get pods`로 상태와 재시작 횟수를 본다.
- `kubectl describe pod`로 이벤트, 종료 사유, probe 실패를 본다.
- `kubectl logs pod-name -c container-name`으로 container별 로그를 본다.
- Pod 내부 저장소에 영속 데이터가 남는 설계는 아닌지 점검한다.

## 면접에서 말하기

> Pod는 Kubernetes가 스케줄링하는 최소 단위이고, 그 안의 container들은 네트워크를 공유합니다. Pod는 언제든 다시 만들어지니 저는 Pod IP나 로컬 파일에 기대지 않게 설계합니다. 재시작이 반복되면 로그만 보지 않고 event, last state, probe 결과를 같이 보고, multi-container Pod라면 어떤 container를 보고 있는지부터 확인합니다.

## 꼬리 질문

- Pod와 container는 어떤 관계인가?
- Pod가 계속 재시작되면 무엇부터 확인하나?
- Pod IP에 직접 의존하면 왜 위험한가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Kubernetes: Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes: Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)

## 관련 문서

- [[kubernetes]]
- [[deployment-service-ingress]]
- [[readiness-and-liveness-probe]]
