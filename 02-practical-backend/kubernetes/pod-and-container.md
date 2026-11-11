---
title: Pod와 Container
description: Kubernetes에서 애플리케이션이 도는 가장 작은 단위와 그 안의 컨테이너
tags: [concept, kubernetes]
---

# Pod와 Container

Pod는 Kubernetes가 배포하고 노드에 배치하는 가장 작은 실행 단위다. 안에는 container가 하나 이상 들어 있고, 이들은 네트워크와 일부 저장소를 함께 쓴다.

Pod는 언제든 사라지고 다시 만들어진다. 그래서 Pod IP를 다른 시스템에 등록해 두거나, 업로드 파일을 Pod 로컬 디스크에 저장하는 설계는 재배포 한 번에 깨진다. 장애를 볼 때도 문제가 container 하나에서 난 건지 Pod 전체에서 난 건지부터 나눠 본다.

## 동작

1. Deployment 같은 controller가 Pod template으로 Pod를 만든다.
2. Scheduler가 Pod를 실행할 Node를 고른다.
3. kubelet이 container runtime으로 container를 띄운다.
4. 같은 Pod 안의 container들은 network namespace를 공유해서 localhost로 통신한다.
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

운영에서는 Pod를 직접 만들지 않고 Deployment 같은 controller에 맡긴다. controller는 Pod 수를 원하는 대로 맞춰 주지만, 잘못 넣은 설정까지 고쳐 주지는 않는다.

## 상황별 판단

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| Pod 재시작 반복 | restart count, last state | OOM, 예외 종료, probe 실패를 구분한다 |
| 로그가 없음 | container 이름 | multi-container Pod일 수 있다 |
| Pod IP 직접 사용 | 피함 | Pod가 다시 만들어지면 IP가 바뀐다 |
| sidecar 필요 | 같은 Pod 배치 검토 | 로그 수집, 프록시처럼 생명주기를 공유한다 |
| 임시 파일 저장 | emptyDir 또는 외부 저장소 | container 파일시스템은 영속적이지 않다 |

한 Pod에 container를 여러 개 넣으면 생명주기와 자원 사용이 함께 묶인다. sidecar처럼 같이 뜨고 같이 죽어야 하는 것만 넣는다.

## 자주 깨지는 곳

- Pod와 container를 같은 것으로 보면, 원인 추적이 엇나간다. 재시작은 container 단위로, 재생성은 Pod 단위로 일어난다.
- Pod가 다시 만들어져도 로컬 파일이 남는다고 생각하면, 재배포 뒤에 파일이 사라진 걸 보고 놀란다. 남지 않는다.
- multi-container Pod에서 어느 container의 로그인지 확인하지 않으면, 엉뚱한 로그를 보고 "로그가 없다"고 판단한다.
- Pod IP를 설정 파일이나 외부 시스템에 직접 등록하면, Pod가 다시 만들어질 때 IP가 바뀌어 연결이 끊긴다.
- CrashLoopBackOff를 애플리케이션 로그만 보고 판단하면, 원인을 잘못 짚는다. 애플리케이션 버그인지, OOM인지, probe 실패인지, 노드 문제인지는 event와 last state를 봐야 갈린다.

## 운영에서 볼 것

- `kubectl get pods`로 상태와 재시작 횟수를 본다.
- `kubectl describe pod`로 이벤트, 종료 사유, probe 실패를 본다.
- `kubectl logs pod-name -c container-name`으로 container별 로그를 본다.
- Pod 안에 꼭 남아야 하는 데이터를 저장하는 설계가 아닌지 점검한다.

## 한 번에 설명하기

> Pod는 Kubernetes가 노드에 배치하는 가장 작은 단위이고, 그 안의 container들은 네트워크를 공유합니다. Pod는 언제든 다시 만들어지기 때문에, 저는 Pod IP나 로컬 파일에 기대지 않게 설계합니다.
>
> 재시작이 반복되면 로그만 보지 않고 event, last state, probe 결과를 같이 봅니다. multi-container Pod라면 지금 어느 container를 보고 있는지부터 확인합니다.

## 꼬리 질문

- Pod와 container는 어떤 관계인가?
- Pod가 계속 재시작되면 무엇부터 확인하나?
- Pod IP에 직접 의존하면 왜 위험한가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes: Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)

## 관련 문서

- [[kubernetes]]
- [[deployment-service-ingress]]
- [[readiness-and-liveness-probe]]
