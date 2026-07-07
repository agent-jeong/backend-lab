---
title: Pod와 Container
description: Kubernetes에서 애플리케이션이 실행되는 최소 단위와 컨테이너 경계
---

# Pod와 Container

## 한 줄 정의

Pod는 Kubernetes에서 배포되고 스케줄링되는 최소 실행 단위이며, 하나 이상의 container가 네트워크와 일부 저장소를 공유하는 묶음이다.

## 실무에서 왜 문제 되는가

- 애플리케이션 로그나 이벤트를 볼 때 문제의 단위가 container인지 Pod인지 구분해야 한다.
- Pod는 사라지고 다시 생성될 수 있으므로 로컬 파일이나 Pod IP에 의존하면 장애에 취약하다.
- 하나의 Pod에 여러 container를 넣으면 생명주기와 리소스 사용이 묶인다.
- 재시작 원인을 모르면 애플리케이션 버그, OOM, probe 실패, 노드 문제를 구분하기 어렵다.

## 동작 원리

1. Deployment 같은 controller가 Pod template을 기준으로 Pod를 만든다.
2. Scheduler가 Pod를 실행할 Node를 선택한다.
3. kubelet이 container runtime을 통해 container를 실행한다.
4. 같은 Pod 안의 container는 같은 network namespace를 공유한다.
5. container가 종료되면 restart policy와 controller 상태에 따라 재시작되거나 새 Pod가 만들어진다.

## 실무 판단 기준

| 상황 | 확인 대상 | 이유 |
|---|---|---|
| Pod 재시작 반복 | restart count, last state | OOM, 예외 종료, probe 실패를 구분한다 |
| 로그가 없음 | container 이름 | multi-container Pod일 수 있다 |
| Pod IP 직접 사용 | 피함 | Pod 재생성 시 IP가 바뀐다 |
| sidecar 필요 | 같은 Pod 배치 검토 | 로그 수집, 프록시처럼 생명주기를 공유한다 |
| 임시 파일 저장 | emptyDir 또는 외부 저장소 | container 파일시스템은 영속적이지 않다 |

## 자주 나는 실수

- Pod와 container를 같은 개념으로 생각한다.
- Pod가 재생성되어도 로컬 파일이 유지된다고 생각한다.
- multi-container Pod에서 어떤 container 로그를 보는지 확인하지 않는다.
- Pod IP를 설정 파일이나 외부 시스템에 직접 등록한다.
- CrashLoopBackOff를 애플리케이션 로그만 보고 판단한다.

## 확인 방법

- 명령: `kubectl get pods`로 상태와 재시작 횟수를 확인한다.
- 명령: `kubectl describe pod`로 이벤트, 종료 사유, probe 실패를 확인한다.
- 명령: `kubectl logs pod-name -c container-name`으로 container별 로그를 본다.
- 점검: Pod 내부 저장소에 영속 데이터가 남는 설계인지 확인한다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| container 묶음을 하나의 배포 단위로 관리한다 | Pod 자체는 언제든 사라질 수 있다 |
| 같은 Pod 안에서 localhost 통신이 가능하다 | container 생명주기가 강하게 묶인다 |
| controller가 원하는 상태를 유지한다 | 잘못된 설정까지 자동으로 고치지는 않는다 |

## 짧은 예제

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

운영에서는 보통 Pod를 직접 만들기보다 Deployment 같은 controller를 통해 관리한다.

## 핵심 요약

Pod는 Kubernetes에서 스케줄링되는 최소 실행 단위다.

container는 Pod 안에서 실행되며 같은 Pod 안에서는 네트워크를 공유한다.

Pod는 사라지고 다시 만들어질 수 있으므로 IP와 로컬 파일에 의존하면 안 된다.

재시작 원인은 로그뿐 아니라 event, last state, probe 결과를 함께 봐야 한다.

multi-container Pod에서는 어떤 container의 로그와 상태를 보는지 명확히 해야 한다.

## 꼬리 질문

- Pod와 container는 어떤 관계인가?
- Pod가 계속 재시작되면 무엇부터 확인할 것인가?
- Pod IP에 직접 의존하면 왜 위험한가?

## 관련 문서

- [[kubernetes]]
- [[deployment-service-ingress]]
- [[readiness-and-liveness-probe]]
