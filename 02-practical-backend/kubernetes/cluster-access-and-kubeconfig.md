---
title: 클러스터 접속과 kubeconfig
description: kubectl이 어느 클러스터에 누구로 접속할지 정하는 kubeconfig 구조와, 외부 인증 도우미로 토큰을 받는 흐름
tags: [concept, kubernetes]
---

# 클러스터 접속과 kubeconfig

`kubectl`은 명령을 HTTPS 요청으로 바꿔 클러스터의 API 서버에 보낸다. 어느 API 서버로 보낼지, 누구라고 밝힐지는 kubeconfig 파일에서 읽는다.

`kubectl`이 갑자기 접속을 못 하면 클러스터보다 내 kubeconfig를 먼저 의심한다. 클러스터 주소가 틀렸는지, 인증 정보가 낡았는지를 나눠 보면 원인이 빨리 좁혀진다.

## 밖에서 클러스터에 닿는 길은 API 서버 하나다

클러스터는 컨트롤 플레인과 노드로 나뉜다. 컨트롤 플레인은 무엇을 어디에 띄울지 정하고, 노드는 실제로 Pod를 돌리는 서버다. 밖에서 클러스터를 조회하거나 바꾸는 요청은 모두 컨트롤 플레인의 API 서버로 들어간다.

```text
내 PC: kubectl ── HTTPS + 인증 정보 ──→ API 서버 (컨트롤 플레인)
                                            │
                                ┌───────────┼───────────┐
                              노드 1       노드 2       노드 3
                              Pod Pod     Pod Pod     Pod Pod
```

그래서 `kubectl get pods`가 실패하면 Pod보다 API 서버까지의 경로와 인증을 먼저 본다.

## kubeconfig는 세 목록으로 되어 있다

`kubectl`은 기본으로 `$HOME/.kube/config` 파일을 읽는다. `KUBECONFIG` 환경 변수나 `--kubeconfig` 플래그로 다른 파일을 지정할 수 있다.

| 목록 | 담는 것 | 비유 |
|---|---|---|
| `clusters` | API 서버 주소, 서버 인증서를 검증할 CA | 어디로 걸지 |
| `users` | 인증 정보(토큰, 클라이언트 인증서, 인증 도우미 실행 설정) | 누구라고 밝힐지 |
| `contexts` | cluster 하나 + user 하나 + 기본 namespace를 묶은 이름 | 단축번호 |

```yaml
clusters:
- name: example-cluster
  cluster:
    server: https://api.example.com
contexts:
- name: example-admin@example-cluster
  context:
    cluster: example-cluster
    user: example-admin
users:
- name: example-admin
  user:
    exec: ...            # 아래 "토큰을 그때그때 받는 방식"
current-context: example-admin@example-cluster
```

`--context`를 주면 그 context가 가리키는 cluster와 user가 한 번에 정해진다. 주지 않으면 `current-context`를 쓴다.

## 토큰을 그때그때 받는 방식 (exec 인증 플러그인)

관리형 클라우드 클러스터에서는 user 항목에 토큰을 직접 적지 않는 경우가 많다. 대신 "이 프로그램을 실행해서 인증 정보를 받아 와라"는 `exec` 설정을 둔다. 이 프로그램을 client-go credential plugin이라 부른다.

```yaml
users:
- name: example-admin
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1
      command: example-cloud-auth        # 클라우드가 배포하는 인증 도우미
      env:
      - name: AUTH_URL                   # 클라우드 IAM 주소
        value: https://iam.example.com
      - name: ACCESS_KEY_ID              # 액세스 키. 만료되면 이 값을 바꾼다
        value: ...
      - name: ACCESS_KEY_SECRET
        value: ...
```

1. `kubectl`이 `command`를 실행하고, `env`의 값을 그 프로그램의 환경 변수로 넘긴다.
2. 인증 도우미가 액세스 키로 클라우드 IAM에 토큰을 요청한다.
3. 인증 도우미가 받은 토큰을 `ExecCredential` 형식으로 표준 출력에 찍는다.
4. `kubectl`이 그 토큰을 들고 API 서버에 요청한다.
5. API 서버는 webhook token authenticator 같은 서버 쪽 장치로 토큰이 진짜인지 확인한 뒤 요청을 처리한다.

받은 토큰은 만료 시각이 될 때까지, 서버가 401을 돌려줄 때까지, 또는 프로세스가 끝날 때까지 메모리에 캐시된다. `kubectl`은 명령마다 새 프로세스로 뜨므로, 인증 도우미가 따로 캐시하지 않는다면 명령을 칠 때마다 1~5가 다시 돈다.

## 접속이 안 될 때 어디를 보나

| 증상 | 의심할 곳 | 고칠 곳 |
|---|---|---|
| 주소를 못 찾음, 연결 시간 초과 | 네트워크, API 서버 주소 | `clusters[].cluster.server`, VPN·방화벽 |
| 인증서 검증 실패 | 클러스터 CA가 바뀜 | `clusters[].cluster.certificate-authority-data` |
| 인증 도우미가 오류를 내고 토큰을 못 받음 | 액세스 키 만료·삭제, 인증 도우미 미설치 | `users[].user.exec.env`, 도우미 설치 |
| 401 Unauthorized | 토큰이 거절됨 | user 인증 정보 |
| 403 Forbidden | 인증은 됐지만 권한이 없음 | 클러스터의 RBAC (kubeconfig 문제가 아니다) |

2번 단계에서 막히면 `kubectl`은 API 서버에 요청도 보내지 못한다. 이때 오류 문구는 인증 도우미가 낸 것이라 클러스터마다 다르다. 오류가 `kubectl`이 아니라 인증 도우미에서 나왔다는 것부터 알아보면 원인을 덜 헤맨다.

## 액세스 키를 바꾸는 순서

액세스 키가 만료되면 `clusters`와 `contexts`는 그대로 두고 user의 `env` 값만 바꾼다.

```bash
# 1. 원본 백업
cp ~/.kube/config ~/.kube/config.bak.$(date +%Y%m%d%H%M%S)

# 2. 키를 화면과 셸 히스토리에 남기지 않고 입력받기 (zsh 문법)
read -s "ID?Access Key ID: "; echo
read -s "SECRET?Access Key Secret: "; echo

# 3. 같은 이름의 env 값만 덮어쓰기
kubectl config set-credentials example-admin \
  --exec-env=ACCESS_KEY_ID="$ID" \
  --exec-env=ACCESS_KEY_SECRET="$SECRET"
unset ID SECRET

# 4. 접속 확인
kubectl --context example-admin@example-cluster get ns
```

`set-credentials`는 이미 있는 user 이름을 주면 새 값을 기존 값 위에 합친다. 그래서 `AUTH_URL`처럼 넘기지 않은 env는 남는다. 바꾼 뒤에는 `kubectl config view`로 나머지 값이 그대로인지 확인한다. exec env 값은 출력에 원문 그대로 보일 수 있으므로 화면 공유나 로그에 남기지 않는다.

## 자주 깨지는 곳

- kubeconfig를 설정 파일로만 보면, 남에게 쉽게 넘기게 된다. 액세스 키가 평문으로 들어 있어서, 파일을 메신저나 Git에 올리면 클러스터 권한이 같이 넘어간다.
- 출처를 모르는 kubeconfig를 그대로 쓰면, `exec`에 적힌 아무 프로그램이나 내 PC에서 실행된다. 공식 문서도 셸 스크립트처럼 먼저 열어 보라고 경고한다.
- 키를 명령줄 인자로 바로 넣으면, 셸 히스토리에 남는다. `read -s`로 받거나 앞에 공백을 두고 히스토리 제외 설정을 쓴다.
- 여러 클러스터가 같은 키를 공유하면, 키 하나가 만료될 때 클러스터 여러 곳이 동시에 접속 불가가 된다. 어떤 user가 어떤 키를 쓰는지 기록해 둔다.
- 401과 403을 같은 문제로 보면, kubeconfig를 아무리 고쳐도 403은 안 풀린다. 403은 클러스터 쪽 권한 문제다.
- `KUBECONFIG`에 파일 여러 개를 이어 두면, 같은 이름이 있을 때 먼저 나온 파일의 값이 이긴다. 고친 값이 반영되지 않으면 이 순서를 본다.

## 운영에서 볼 것

- `kubectl config get-contexts`로 어떤 context가 있고 무엇을 쓰고 있는지 본다.
- `kubectl config view --minify`로 지금 context가 실제로 쓰는 cluster와 user만 본다.
- `kubectl --context <이름> get ns`처럼 context를 명시해서 운영 클러스터에 실수로 명령을 보내지 않게 한다.
- 액세스 키의 만료일을 달력에 적어 두고, 만료 전에 교체한다.

## 한 번에 설명하기

> kubectl은 kubeconfig에서 어느 API 서버로, 어떤 인증 정보를 들고 갈지를 읽습니다. kubeconfig는 clusters, users, 그리고 둘을 묶은 contexts로 되어 있습니다.
>
> 클라우드 클러스터는 보통 user에 토큰 대신 인증 도우미를 실행하라는 exec 설정을 둡니다. 접속이 안 되면 저는 주소 문제인지, 토큰 발급 문제인지, 권한 문제인지부터 나눕니다. 키가 만료됐으면 백업한 뒤 user의 env만 바꿉니다.

## 꼬리 질문

- context를 바꾸면 무엇이 함께 바뀌나?
- 401과 403은 각각 어디를 고쳐야 하나?
- exec 인증 플러그인이 받은 토큰은 언제까지 재사용되나?
- 남이 준 kubeconfig를 그냥 쓰면 왜 위험한가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Kubernetes: Organizing Cluster Access Using kubeconfig Files](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [Kubernetes: Authenticating - client-go credential plugins](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#client-go-credential-plugins)
- [kubectl config set-credentials](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_config/kubectl_config_set-credentials/)

## 관련 문서

- [[02-practical-backend/kubernetes/kubernetes|kubernetes]]
- [[deployment-service-ingress]]
- [[configmap-and-secret]]
