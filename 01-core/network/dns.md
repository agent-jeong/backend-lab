---
title: DNS
description: DNS 동작 원리와 TTL, 장애 시 영향 분석
tags: [concept, network]
---

# DNS

DNS(Domain Name System)는 도메인 이름을 IP 주소로 바꿔 주는 분산 네임 시스템이다.

DNS 결과는 여러 층에서 TTL만큼 캐시된다. 그래서 도메인이나 IP를 바꿔도 한동안 이전 서버로 요청이 가고, 일부 클라이언트만 접속이 안 되는 일이 생긴다. 반대로 DNS가 죽으면 도메인으로 부르는 모든 외부 API 호출이 한꺼번에 실패한다.

## 조회 흐름

```
1. 브라우저/앱 → 로컬 DNS 캐시 확인
2. 캐시 없음 → OS의 DNS Resolver에 질의
3. Resolver → Root DNS (.com, .net 등의 위치 응답)
4. Resolver → TLD DNS (.com → example.com의 네임서버 응답)
5. Resolver → Authoritative DNS (example.com → 93.184.216.34 응답)
6. Resolver → 결과를 캐시하고 클라이언트에 반환
```

단계마다 결과가 TTL 동안 캐시되므로, 대부분의 요청은 캐시에서 끝난다.

## 레코드 타입

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

CNAME은 로드밸런서, CDN처럼 IP가 바뀔 수 있는 서비스에 쓴다. 대신 DNS 조회가 한 번 더 필요해서 약간 느려진다.

## TTL (Time To Live)

TTL은 DNS 캐시의 유효 시간(초)이다.

| TTL | 의미 | 맞는 상황 |
|---|---|---|
| 300 (5분) | 짧은 TTL | IP 변경이 잦은 환경, 마이그레이션 직전 |
| 3600 (1시간) | 일반적 | 변경이 드문 서비스 |
| 86400 (24시간) | 긴 TTL | 거의 변경 없는 도메인 |

IP를 옮길 때는 TTL을 미리 낮춰 둔다.

```
1. 마이그레이션 며칠 전: TTL을 300초로 낮춤
2. IP 변경: DNS 레코드를 새 IP로 교체
3. TTL 만료 대기: 이전 TTL 동안 일부 클라이언트가 구 IP로 접속 가능
4. 안정화 후: TTL을 원래 값으로 복구
```

미리 낮추지 않으면 이전의 긴 TTL이 만료될 때까지 구 IP로 요청이 간다.

## DNS가 장애를 만드는 방식

### DNS 서버 장애

DNS 서버가 응답하지 않으면 도메인으로 보내는 모든 요청이 실패한다.

```
# DNS 조회 실패 시 에러 예시
java.net.UnknownHostException: api.external-service.com
curl: (6) Could not resolve host: api.external-service.com
```

### JVM DNS 캐시

```
# 리눅스에서 DNS 캐시 확인
dig api.example.com

# Java에서 DNS 캐시 TTL 설정
# JVM은 기본적으로 성공한 DNS를 30초, 실패한 DNS를 10초 캐시
-Dsun.net.inetaddr.ttl=30
-Dsun.net.inetaddr.negative.ttl=10
```

JVM은 OS와 별도로 `InetAddress` 안에 DNS 결과를 캐시한다. 이 TTL이 길게 잡혀 있으면 DNS를 바꿔도 애플리케이션은 옛 IP를 계속 쓴다.

### 장애를 좁히는 순서

1. `dig` 또는 `nslookup`으로 DNS 응답을 확인한다.
2. 응답이 없으면 DNS 서버 문제다.
3. 응답이 엉뚱한 IP면 DNS 레코드나 캐시 문제다.
4. 응답이 정상이면 DNS 다음 단계(TCP 연결, 서버 응답 등)를 본다.

## 내부 DNS (Service Discovery)

마이크로서비스 환경에서는 내부 DNS로 서비스를 찾는다.

```
# Kubernetes 내부 DNS
order-service.default.svc.cluster.local → 10.96.0.15

# Spring Cloud + Eureka
order-service → 192.168.1.10:8080, 192.168.1.11:8080
```

인스턴스가 늘거나 줄면 내부 DNS가 알아서 반영한다.

## 자주 깨지는 곳

- **TTL을 낮추지 않고 IP를 바꾼다.** 일부 클라이언트가 한동안 구 IP로 접속한다.
- **DNS 장애를 가정하지 않고 외부 API를 부른다.** DNS가 죽으면 연동 전체가 같이 죽는다.
- **JVM DNS 캐시를 모른다.** IP를 바꾼 뒤에도 애플리케이션을 재시작하기 전까지 옛 IP로 간다.
- **루트 도메인에 CNAME을 걸려고 한다.** 루트 도메인에는 CNAME을 쓸 수 없다.
- **내부 서비스 호출에 외부 DNS를 쓴다.** 필요 없는 지연이 붙는다.

## 한 번에 설명하기

> DNS는 도메인을 IP로 바꾸는 분산 시스템이고, 결과는 TTL 동안 여러 층에서 캐시됩니다. 그래서 저는 IP를 옮기기 며칠 전에 TTL을 낮추고, 바꾼 뒤에는 이전 TTL이 끝날 때까지 기다립니다. 장애가 나면 먼저 `dig`나 `nslookup`으로 DNS 문제인지부터 가립니다. JVM은 OS와 따로 DNS를 캐시하기 때문에 그 TTL 설정도 같이 확인합니다.

## 꼬리 질문

> [!question]- DNS 조회가 느리면 어떤 영향이 있는가?
> 모든 HTTP 요청 전에 DNS 조회가 선행되므로, DNS 지연은 요청 전체의 지연으로 이어집니다. TTL 내 캐시를 활용하거나, 연결 풀(Connection Pool)로 이미 연결된 커넥션을 재사용하면 DNS 조회 횟수를 줄일 수 있습니다.

> [!question]- CNAME을 루트 도메인에 쓸 수 없는 이유는?
> DNS 표준(RFC 1034)에서 루트 도메인에는 SOA, NS 레코드가 반드시 존재해야 하고, CNAME은 다른 레코드와 공존할 수 없기 때문입니다. AWS의 ALIAS나 Cloudflare의 CNAME Flattening으로 우회할 수 있습니다.

> [!question]- JVM DNS 캐시는 어떻게 동작하는가?
> `InetAddress`가 내부적으로 DNS 결과를 캐시합니다. 보안 매니저가 설정된 경우 기본 TTL이 무한대(-1)가 될 수 있어 IP 변경이 영원히 반영되지 않습니다. `networkaddress.cache.ttl` 속성으로 제어할 수 있습니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [RFC 1035: Domain Names](https://www.rfc-editor.org/rfc/rfc1035)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]
