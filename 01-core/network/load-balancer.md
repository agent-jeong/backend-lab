---
title: "로드 밸런서 동작과 분산 전략"
description: 로드밸런서가 요청을 나누는 방식과 헬스체크, 배포 때 요청을 끊지 않는 법
tags: [concept, network]
---

# 로드 밸런서 동작과 분산 전략

로드밸런서(LB)는 들어오는 요청을 여러 서버에 나눠 보내는 장치나 소프트웨어다. 서버 한 대가 죽어도 나머지가 요청을 받고, 서버를 늘린 만큼 더 많은 요청을 처리할 수 있다.

서버를 늘렸는데 한 서버에만 요청이 몰리거나, 배포 중에 주문 요청이 실패하거나, 죽은 서버로 요청이 계속 간다면 LB의 분산 알고리즘, 헬스체크, connection draining 중 하나가 잘못 잡혀 있다.

## L4와 L7

| 구분 | L4 (Transport Layer) | L7 (Application Layer) |
|---|---|---|
| 기준 | IP, Port | URL, Host, Header, Cookie |
| 속도 | 빠름 (패킷 수준) | 상대적으로 느림 (HTTP 파싱) |
| 기능 | 단순 분산 | URL 기반 라우팅, SSL 종료, 헤더 조작 |
| 예시 | AWS NLB, HAProxy (TCP) | AWS ALB, Nginx, HAProxy (HTTP) |

```
L4: 클라이언트 → LB(IP:Port 기반 분산) → Server A 또는 B

L7: 클라이언트 → LB(URL 기반 분산)
    /api/orders → Order Server
    /api/users  → User Server
    /static/*   → CDN
```

웹 서비스는 대부분 L7을 쓴다. URL에 따라 서버를 나누고, SSL을 LB에서 풀고, 헤더를 보고 분기해야 해서다.

## 분산 알고리즘

| 알고리즘 | 동작 | 맞는 상황 |
|---|---|---|
| Round Robin | 순서대로 돌아가며 분배 | 서버 스펙이 동일할 때 |
| Weighted Round Robin | 가중치에 따라 분배 | 서버 스펙이 다를 때 |
| Least Connections | 연결 수가 가장 적은 서버로 | 요청 처리 시간이 불균일할 때 |
| IP Hash | 클라이언트 IP 기반 고정 분배 | 세션 고정이 필요할 때 |

Round Robin은 서버가 바쁜지 한가한지 보지 않고 순서대로 보낸다.

```
Server A: CPU 90% (느린 요청 처리 중)
Server B: CPU 20% (유휴 상태)

Round Robin → 여전히 A에 절반의 요청 분배 → A 과부하 악화
Least Connections → B에 더 많은 요청 분배 → 자연스러운 부하 균형
```

## 헬스체크

LB는 주기적으로 서버에 상태를 묻고, 응답이 비정상인 서버에는 요청을 보내지 않는다.

```
LB → GET /health → Server A: 200 OK     → 정상, 요청 분배
LB → GET /health → Server B: 503 Error  → 비정상, 요청 제외
LB → GET /health → Server C: timeout    → 비정상, 요청 제외
```

```java
// Spring Boot Actuator 헬스체크 엔드포인트
// GET /actuator/health → {"status": "UP"}

@Component
public class CustomHealthIndicator implements HealthIndicator {
    
    @Override
    public Health health() {
        if (isDatabaseConnected() && isCacheAvailable()) {
            return Health.up().build();
        }
        return Health.down()
            .withDetail("reason", "dependency unavailable")
            .build();
    }
}
```

| 항목 | 설명 | 권장값 |
|---|---|---|
| Interval | 체크 주기 | 10~30초 |
| Timeout | 응답 대기 시간 | 5초 |
| Unhealthy Threshold | 비정상 판단 횟수 | 2~3회 연속 실패 |
| Healthy Threshold | 정상 복구 판단 횟수 | 2회 연속 성공 |

## SSL/TLS 종료 (SSL Termination)

```
Client ──HTTPS──▶ LB ──HTTP──▶ Backend Server
                  ↑
            SSL 인증서 관리
            암복호화 처리
```

LB가 SSL을 풀어 주면 백엔드 서버는 HTTP로 통신하니 암복호화를 하지 않아도 된다. 인증서도 LB에서만 관리하면 된다.

## 무중단 배포

### Rolling Update

```
1. Server B를 LB에서 제외 (헬스체크 실패 또는 수동 제외)
2. Server B에 새 버전 배포
3. Server B를 LB에 등록 (헬스체크 통과)
4. Server A를 LB에서 제외
5. Server A에 새 버전 배포
6. Server A를 LB에 등록
```

### Connection Draining (Deregistration Delay)

서버를 LB에서 뺄 때, 그 서버가 처리하고 있던 요청이 끝날 때까지 기다리는 설정이다.

```
LB에서 Server A 제외 시:
- 새 요청: Server A로 보내지 않음
- 기존 요청: 완료될 때까지 대기 (보통 30~300초)
- 대기 시간 초과: 강제 종료
```

이 설정 없이 서버를 바로 빼면, 처리 중이던 요청이 중간에 끊겨 실패한다.

## 자주 깨지는 곳

- 헬스체크가 없으면 죽은 서버로 요청이 계속 간다.
- 헬스체크에서 DB까지 확인하면, DB가 잠깐 끊겼을 때 모든 서버가 한꺼번에 비정상으로 빠진다.
- Connection Draining 없이 배포하면 처리 중이던 요청이 끊긴다.
- 세션을 서버 메모리에 두고 Round Robin을 쓰면, 다음 요청이 다른 서버로 가서 로그인이 풀린다.
- URL에 따라 서버를 나누는 일을 L4에서 하려고 하면 안 된다. L4는 URL을 보지 않는다.

## 한 번에 설명하기

> 로드밸런서는 L4에서는 IP와 Port로, L7에서는 URL이나 헤더를 보고 요청을 나눕니다. 서버 스펙이 같으면 Round Robin을, 요청마다 처리 시간이 들쭉날쭉하면 Least Connections를 고릅니다.
>
> 헬스체크로 비정상 서버를 자동으로 빼고, 배포할 때는 Connection Draining으로 처리 중인 요청이 끊기지 않게 합니다.
>
> 헬스체크에 DB를 넣으면 DB가 잠깐 끊길 때 서버가 전부 빠질 수 있어서, 무엇까지 확인할지는 신중하게 정합니다.

## 꼬리 질문

> [!question]- 세션을 사용하면서 LB를 쓰려면 어떻게 해야 하는가?
> Sticky Session(IP Hash)으로 같은 클라이언트를 늘 같은 서버로 보내거나, 세션을 Redis 같은 외부 저장소에 두고 어느 서버로 가든 같은 세션을 읽게 합니다. 서버 한 대가 죽어도 세션이 남으니 외부 저장소 쪽이 더 안전합니다.

> [!question]- 헬스체크 엔드포인트에서 무엇을 체크해야 하는가?
> 적어도 애플리케이션이 요청을 받을 수 있는 상태인지는 확인합니다. DB나 캐시처럼 없으면 일을 못 하는 의존성은 볼 수 있지만, 외부 API처럼 잠깐씩 흔들리는 의존성은 넣지 않는 게 좋습니다.

> [!question]- 502 Bad Gateway는 언제 발생하는가?
> LB가 백엔드 서버에 요청을 넘겼는데 서버가 이상한 응답을 돌려주거나, 서버 프로세스가 죽어 있을 때 납니다. 배포 중에 서버가 아직 뜨지 않았을 때도 납니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [NGINX: HTTP Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[dns]]
- [[tls]]
- [[request-journey]]
