---
title: "로드 밸런서 동작과 분산 전략"
description: 로드밸런서 동작 원리와 알고리즘, 헬스체크
---

# 로드 밸런서 동작과 분산 전략

로드밸런서(LB)는 들어오는 요청을 여러 서버에 나눠 보내 가용성과 성능을 높이는 장치나 소프트웨어다.

서버를 늘렸는데 한 서버에만 요청이 몰리거나, 배포 중에 요청이 실패하거나, 죽은 서버로 요청이 계속 간다면 LB의 분산 알고리즘, 헬스체크, connection draining 중 하나가 잘못 잡힌 것이다.

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

대부분의 웹 서비스는 L7을 쓴다. URL 기반 라우팅, SSL 종료, 헤더 기반 분기가 필요해서다.

## 분산 알고리즘

| 알고리즘 | 동작 | 맞는 상황 |
|---|---|---|
| Round Robin | 순서대로 돌아가며 분배 | 서버 스펙이 동일할 때 |
| Weighted Round Robin | 가중치에 따라 분배 | 서버 스펙이 다를 때 |
| Least Connections | 연결 수가 가장 적은 서버로 | 요청 처리 시간이 불균일할 때 |
| IP Hash | 클라이언트 IP 기반 고정 분배 | 세션 고정이 필요할 때 |

Round Robin은 서버 상태를 보지 않는다.

```
Server A: CPU 90% (느린 요청 처리 중)
Server B: CPU 20% (유휴 상태)

Round Robin → 여전히 A에 절반의 요청 분배 → A 과부하 악화
Least Connections → B에 더 많은 요청 분배 → 자연스러운 부하 균형
```

## 헬스체크

LB는 주기적으로 서버 상태를 확인하고, 비정상인 서버에는 요청을 보내지 않는다.

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

LB가 SSL을 처리하면 백엔드 서버는 HTTP로 통신하므로 암복호화 부담이 없다. 인증서도 LB에서만 관리하면 된다.

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

서버를 LB에서 뺄 때, 처리 중인 요청이 끝날 때까지 기다리는 설정이다.

```
LB에서 Server A 제외 시:
- 새 요청: Server A로 보내지 않음
- 기존 요청: 완료될 때까지 대기 (보통 30~300초)
- 대기 시간 초과: 강제 종료
```

이 설정 없이 서버를 바로 빼면 처리 중이던 요청이 실패한다.

## 자주 깨지는 곳

- **헬스체크가 없다.** 죽은 서버로 요청이 계속 간다.
- **헬스체크가 DB까지 확인한다.** DB가 잠깐 끊기면 모든 서버가 동시에 비정상으로 빠진다.
- **Connection Draining 없이 배포한다.** 처리 중인 요청이 끊긴다.
- **세션을 서버 메모리에 두고 Round Robin을 쓴다.** 다음 요청이 다른 서버로 가서 세션이 사라진다.
- **URL 기반 라우팅을 L4에서 하려고 한다.** L4는 URL을 보지 않는다.

## 면접에서 말하기

> 로드밸런서는 L4에서는 IP와 Port로, L7에서는 URL이나 헤더로 요청을 나눕니다. 서버 스펙이 같으면 Round Robin, 처리 시간이 들쭉날쭉하면 Least Connections를 고릅니다. 저는 헬스체크로 비정상 서버를 자동으로 빼고, 배포할 때는 Connection Draining으로 처리 중인 요청이 끊기지 않게 합니다. 헬스체크에 DB를 넣으면 DB 순단 때 전체 서버가 빠질 수 있어서 범위를 신중하게 정합니다.

## 꼬리 질문

> [!question]- 세션을 사용하면서 LB를 쓰려면 어떻게 해야 하는가?
> Sticky Session(IP Hash)으로 같은 클라이언트를 같은 서버로 보내거나, 세션을 Redis 같은 외부 저장소에 저장해서 어떤 서버로 가든 세션을 공유합니다. 외부 저장소 방식이 서버 장애에 더 안전합니다.

> [!question]- 헬스체크 엔드포인트에서 무엇을 체크해야 하는가?
> 최소한 애플리케이션이 요청을 처리할 수 있는 상태인지 확인합니다. DB, 캐시 같은 핵심 의존성의 상태를 체크하되, 외부 API처럼 일시적으로 불안정한 의존성은 포함하지 않는 것이 좋습니다.

> [!question]- 502 Bad Gateway는 언제 발생하는가?
> LB가 백엔드 서버에 요청을 전달했는데 서버가 잘못된 응답을 반환하거나, 서버 프로세스가 죽어있는 경우입니다. 배포 중에 서버가 아직 준비되지 않았을 때도 발생합니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[dns]]
- [[tls]]
