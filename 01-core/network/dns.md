---
title: DNS
description: 도메인이 IP로 바뀌는 과정과 TTL, DNS가 장애를 일으키는 방식
tags: [concept, network]
---

# DNS

DNS(Domain Name System)는 `api.example.com` 같은 도메인 이름을 IP 주소로 바꿔 주는 시스템이다. 이름과 주소를 한 서버가 다 들고 있지 않고, 여러 서버가 나눠 맡는다.

DNS 조회 결과는 여러 곳에서 TTL만큼 캐시된다. 그래서 서버 IP를 바꿔도 한동안은 옛 서버로 요청이 가고, 일부 클라이언트만 접속이 안 되는 일이 생긴다. 반대로 DNS가 죽으면 결제 API처럼 도메인으로 부르는 외부 호출이 한꺼번에 실패한다.

## 조회 흐름

```
1. 브라우저/앱 → 로컬 DNS 캐시 확인
2. 캐시 없음 → OS의 DNS Resolver에 질의
3. Resolver → Root DNS (.com, .net 등의 위치 응답)
4. Resolver → TLD DNS (.com → example.com의 네임서버 응답)
5. Resolver → Authoritative DNS (example.com → 93.184.216.34 응답)
6. Resolver → 결과를 캐시하고 클라이언트에 반환
```

단계마다 결과가 TTL 동안 캐시되니, 대부분의 조회는 캐시에서 끝난다.

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

CNAME은 로드밸런서나 CDN처럼 IP가 바뀔 수 있는 곳을 가리킬 때 쓴다. 대신 DNS 조회를 한 번 더 해야 해서 조금 느려진다.

## TTL (Time To Live)

TTL은 DNS 조회 결과를 캐시에 둘 수 있는 시간(초)이다.

| TTL | 의미 | 맞는 상황 |
|---|---|---|
| 300 (5분) | 짧은 TTL | IP 변경이 잦은 환경, 마이그레이션 직전 |
| 3600 (1시간) | 일반적 | 변경이 드문 서비스 |
| 86400 (24시간) | 긴 TTL | 거의 변경 없는 도메인 |

IP를 옮길 때는 TTL을 며칠 전에 미리 낮춰 둔다.

```
1. 마이그레이션 며칠 전: TTL을 300초로 낮춤
2. IP 변경: DNS 레코드를 새 IP로 교체
3. TTL 만료 대기: 이전 TTL 동안 일부 클라이언트가 구 IP로 접속 가능
4. 안정화 후: TTL을 원래 값으로 복구
```

미리 낮추지 않으면, 바꾸기 전에 걸려 있던 긴 TTL이 끝날 때까지 옛 IP로 요청이 간다.

## DNS가 장애를 만드는 방식

### DNS 서버 장애

DNS 서버가 응답하지 않으면 도메인으로 보내는 요청이 전부 실패한다.

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

JVM은 OS와 따로 `InetAddress` 안에 DNS 결과를 캐시한다. 이 TTL이 길게 잡혀 있으면 DNS 레코드를 바꿔도 애플리케이션은 옛 IP를 계속 쓴다.

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

인스턴스가 늘거나 줄면 내부 DNS가 알아서 목록을 고친다.

## 자주 깨지는 곳

- TTL을 낮추지 않고 IP를 바꾸면, 일부 클라이언트가 한동안 옛 IP로 접속한다.
- DNS가 죽는 경우를 생각하지 않고 외부 API를 부르면, DNS 장애 하나로 연동 전체가 같이 멈춘다.
- JVM DNS 캐시를 모르면, IP를 바꾼 뒤에도 애플리케이션을 재시작할 때까지 옛 IP로 요청이 가는 이유를 찾지 못한다.
- 루트 도메인에는 CNAME을 쓸 수 없다. 걸려고 하면 설정이 거부된다.
- 내부 서비스를 부를 때 외부 DNS를 거치면 쓸데없는 지연이 붙는다.

## 한 번에 설명하기

> DNS는 도메인을 IP로 바꿔 주고, 그 결과는 TTL 동안 여러 곳에 캐시됩니다. 그래서 IP를 옮길 때는 며칠 전에 TTL을 낮추고, 바꾼 뒤에는 이전 TTL이 끝날 때까지 기다립니다.
>
> 장애가 나면 먼저 `dig`나 `nslookup`으로 DNS 문제인지부터 가립니다.
>
> JVM은 OS와 따로 DNS를 캐시해서, 애플리케이션 쪽 TTL 설정도 같이 확인합니다.

## 꼬리 질문

> [!question]- DNS 조회가 느리면 어떤 영향이 있는가?
> HTTP 요청을 보내기 전에 DNS 조회부터 하니까, DNS가 느리면 요청 전체가 느려집니다. TTL 동안은 캐시된 결과를 쓰고, 커넥션 풀로 이미 맺어 둔 연결을 다시 쓰면 DNS 조회 횟수가 줄어듭니다.

> [!question]- CNAME을 루트 도메인에 쓸 수 없는 이유는?
> DNS 표준(RFC 1034)상 루트 도메인에는 SOA와 NS 레코드가 꼭 있어야 하는데, CNAME은 다른 레코드와 같이 둘 수 없어서입니다. 필요하면 AWS의 ALIAS나 Cloudflare의 CNAME Flattening으로 돌아갑니다.

> [!question]- JVM DNS 캐시는 어떻게 동작하는가?
> `InetAddress`가 안에서 DNS 결과를 캐시합니다. 보안 매니저가 설정돼 있으면 기본 TTL이 무한대(-1)가 될 수 있고, 그러면 IP를 바꿔도 끝내 반영되지 않습니다. 이 시간은 `networkaddress.cache.ttl` 속성으로 바꿉니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 1035: Domain Names](https://www.rfc-editor.org/rfc/rfc1035)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]
