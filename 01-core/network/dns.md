---
title: DNS
description: DNS 동작 원리와 TTL, 장애 시 영향 분석
---

# DNS

## 한 줄 정의

DNS(Domain Name System)는 도메인 이름을 IP 주소로 변환하는 분산 네임 시스템이다.

## 실무에서 왜 중요한가

DNS를 이해하지 못하면 다음 문제가 생긴다.

- 도메인을 변경했는데 한동안 이전 서버로 요청이 간다.
- DNS 장애 시 모든 외부 API 호출이 실패하는 원인을 모른다.
- TTL을 모르고 DNS 캐시 관련 문제를 재현하지 못한다.
- 서버 IP를 교체했는데 일부 클라이언트만 접속이 안 되는 이유를 모른다.

## DNS 조회 흐름

```
1. 브라우저/앱 → 로컬 DNS 캐시 확인
2. 캐시 없음 → OS의 DNS Resolver에 질의
3. Resolver → Root DNS (.com, .net 등의 위치 응답)
4. Resolver → TLD DNS (.com → example.com의 네임서버 응답)
5. Resolver → Authoritative DNS (example.com → 93.184.216.34 응답)
6. Resolver → 결과를 캐시하고 클라이언트에 반환
```

각 단계의 결과는 TTL 동안 캐시된다. 대부분의 요청은 캐시에서 처리된다.

## DNS 레코드 타입

| 레코드 | 용도 | 예시 |
|---|---|---|
| A | 도메인 → IPv4 주소 | `api.example.com → 93.184.216.34` |
| AAAA | 도메인 → IPv6 주소 | `api.example.com → 2001:db8::1` |
| CNAME | 도메인 → 다른 도메인 | `www.example.com → example.com` |
| MX | 메일 서버 지정 | `example.com → mail.example.com` |
| TXT | 텍스트 정보 | SPF, DKIM 등 인증 정보 |
| NS | 네임서버 지정 | `example.com → ns1.dns.provider.com` |

### CNAME vs A 레코드

```
# A 레코드: 도메인을 직접 IP에 매핑
api.example.com → 93.184.216.34

# CNAME: 도메인을 다른 도메인에 매핑 (간접)
api.example.com → my-app.elb.amazonaws.com → 실제 IP
```

CNAME은 로드밸런서, CDN처럼 IP가 변할 수 있는 서비스에 유용하다. 다만 CNAME은 추가 DNS 조회가 필요하므로 약간의 지연이 발생한다.

## TTL (Time To Live)

TTL은 DNS 캐시의 유효 시간(초)이다.

| TTL | 의미 | 적합한 상황 |
|---|---|---|
| 300 (5분) | 짧은 TTL | IP 변경이 잦은 환경, 마이그레이션 직전 |
| 3600 (1시간) | 일반적 | 안정적인 서비스 |
| 86400 (24시간) | 긴 TTL | 거의 변경 없는 도메인 |

### 마이그레이션 시 TTL 전략

```
1. 마이그레이션 며칠 전: TTL을 300초로 낮춤
2. IP 변경: DNS 레코드를 새 IP로 교체
3. TTL 만료 대기: 이전 TTL 동안 일부 클라이언트가 구 IP로 접속 가능
4. 안정화 후: TTL을 원래 값으로 복구
```

TTL을 미리 낮추지 않으면, 이전 긴 TTL이 만료될 때까지 구 IP로 요청이 갈 수 있다.

## DNS와 장애

### DNS 서버 장애

DNS 서버가 응답하지 않으면 도메인 기반의 모든 요청이 실패한다.

```
# DNS 조회 실패 시 에러 예시
java.net.UnknownHostException: api.external-service.com
curl: (6) Could not resolve host: api.external-service.com
```

### DNS 캐시 문제

```
# 리눅스에서 DNS 캐시 확인
dig api.example.com

# Java에서 DNS 캐시 TTL 설정
# JVM은 기본적으로 성공한 DNS를 30초, 실패한 DNS를 10초 캐시
-Dsun.net.inetaddr.ttl=30
-Dsun.net.inetaddr.negative.ttl=10
```

JVM의 DNS 캐시는 OS와 별도로 동작한다. `InetAddress` 내부에 캐시되며, 긴 TTL로 설정되어 있으면 IP 변경이 반영되지 않을 수 있다.

### 장애 분석 순서

1. `dig` 또는 `nslookup`으로 DNS 응답 확인
2. 응답이 없으면 DNS 서버 문제
3. 응답이 잘못된 IP면 DNS 레코드 또는 캐시 문제
4. 응답이 정상이면 DNS 이후 단계 (TCP 연결, 서버 응답 등) 확인

## 내부 DNS (Service Discovery)

마이크로서비스 환경에서는 내부 DNS로 서비스를 찾는다.

```
# Kubernetes 내부 DNS
order-service.default.svc.cluster.local → 10.96.0.15

# Spring Cloud + Eureka
order-service → 192.168.1.10:8080, 192.168.1.11:8080
```

내부 DNS는 서비스 인스턴스의 추가/삭제를 자동으로 반영한다.

## 자주 나는 실수

- DNS TTL을 고려하지 않고 IP를 교체해서 일부 클라이언트가 구 IP로 접속한다.
- DNS 장애 가능성을 고려하지 않고 외부 API를 호출한다.
- JVM DNS 캐시를 모르고 IP 변경 후 애플리케이션을 재시작하지 않는다.
- CNAME을 루트 도메인에 설정하려다 실패한다 (루트 도메인에는 CNAME 불가).
- 내부 서비스 호출에 외부 DNS를 사용해서 불필요한 지연이 발생한다.

## 핵심 요약

DNS는 도메인을 IP로 변환하는 분산 시스템으로, TTL 동안 결과가 캐시됩니다.
IP 변경 시에는 사전에 TTL을 낮추고, 변경 후 이전 TTL 만료까지 대기해야 합니다.

DNS 장애는 모든 도메인 기반 통신에 영향을 주므로, `dig`/`nslookup`으로 원인을 먼저 확인합니다.
JVM은 OS와 별도로 DNS를 캐시하므로 IP 변경 반영에 주의해야 합니다.

## 꼬리 질문

> [!question]- DNS 조회가 느리면 어떤 영향이 있는가?
> 모든 HTTP 요청 전에 DNS 조회가 선행되므로, DNS 지연은 요청 전체의 지연으로 이어집니다. TTL 내 캐시를 활용하거나, 연결 풀(Connection Pool)로 이미 연결된 커넥션을 재사용하면 DNS 조회 횟수를 줄일 수 있습니다.

> [!question]- CNAME을 루트 도메인에 쓸 수 없는 이유는?
> DNS 표준(RFC 1034)에서 루트 도메인에는 SOA, NS 레코드가 반드시 존재해야 하고, CNAME은 다른 레코드와 공존할 수 없기 때문입니다. AWS의 ALIAS나 Cloudflare의 CNAME Flattening으로 우회할 수 있습니다.

> [!question]- JVM DNS 캐시는 어떻게 동작하는가?
> `InetAddress`가 내부적으로 DNS 결과를 캐시합니다. 보안 매니저가 설정된 경우 기본 TTL이 무한대(-1)가 될 수 있어 IP 변경이 영원히 반영되지 않습니다. `networkaddress.cache.ttl` 속성으로 제어할 수 있습니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]