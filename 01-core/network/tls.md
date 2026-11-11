---
title: "TLS/SSL 동작 원리"
description: TLS가 통신을 암호화하고 서버를 확인하는 방식과, 인증서를 운영할 때 생기는 문제
tags: [concept, network]
---

# TLS/SSL 동작 원리

TLS(Transport Layer Security)는 주고받는 내용을 암호화하고, 인증서로 상대 서버가 진짜인지 확인하는 프로토콜이다. HTTPS는 HTTP를 TLS 위에서 보내는 것이다.

실제로 TLS 때문에 나는 장애는 대부분 암호 알고리즘이 아니라 인증서 관리에서 생긴다. 인증서가 만료되면 서비스 전체에 접속이 안 되고, 중간 CA를 빠뜨리면 일부 클라이언트만 실패한다. 내부 통신을 평문 HTTP로 두면 보안 감사에서 걸린다. 반면 암호화 때문에 느려지는 정도는 생각보다 작다.

## Handshake (TLS 1.3)

```
Client                              Server
  │                                    │
  │── ClientHello ──────────────────▶  │  1. 지원하는 암호화 방식 전달
  │   (지원 cipher, 키 공유 데이터)      │
  │                                    │
  │◀── ServerHello + 인증서 + Finished  │  2. 선택된 cipher, 인증서, 키 교환
  │                                    │
  │── Finished ─────────────────────▶  │  3. 핸드셰이크 완료
  │                                    │
  │◀═══ 암호화된 통신 시작 ═══════════▶│
```

TLS 1.3은 1-RTT로 핸드셰이크가 끝난다(TLS 1.2는 2-RTT). 이전 세션을 이어 쓰면 0-RTT로 첫 요청을 바로 보낼 수도 있다. 다만 0-RTT 데이터는 공격자가 가로채 그대로 다시 보낼(replay) 수 있어서, 서버는 GET 같은 멱등 요청에만 허용해야 한다.

## 인증서

인증서는 세 가지 일을 한다.

1. 이 서버가 정말 example.com인지 확인해 준다.
2. 서버의 공개 키를 담고 있다. 서버는 핸드셰이크 내용에 자기 개인 키로 서명하고(CertificateVerify), 클라이언트는 이 공개 키로 서명을 확인한다. 실제 암호화에 쓸 키는 (EC)DHE로 따로 합의한다. TLS 1.3에서는 공개 키로 키를 실어 보내는 정적 RSA 방식이 빠졌다.
3. CA(Certificate Authority)의 서명이 붙어 있어서, 클라이언트가 이미 믿는 CA까지 서명을 따라 올라가며 확인할 수 있다.

```
Root CA (브라우저/OS에 내장)
  └── Intermediate CA (Root CA가 서명)
        └── Server Certificate (Intermediate CA가 서명)
```

클라이언트는 서버 인증서 → 중간 CA → 루트 CA 순서로 서명을 검증한다.

### 발급과 관리

| 방식 | 비용 | 맞는 상황 |
|---|---|---|
| Let's Encrypt | 무료 | 소규모 서비스, 자동 갱신 가능 |
| 상용 CA (DigiCert 등) | 유료 | 기업 서비스, EV 인증서 |
| 자체 서명 (Self-signed) | 무료 | 개발/테스트 환경 |

```bash
# Let's Encrypt 인증서 발급 (certbot)
certbot certonly --nginx -d example.com -d www.example.com

# 인증서 만료일 확인
openssl x509 -enddate -noout -in /etc/letsencrypt/live/example.com/cert.pem
```

인증서 만료는 실무에서 가장 흔한 장애 원인 중 하나다. 자동 갱신을 걸고, 갱신이 실패할 때를 대비해 만료일도 모니터링한다.

## HTTPS를 어디서 끝내나

### LB에서 SSL 종료 (가장 흔함)

```
Client ──HTTPS──▶ LB (SSL 종료) ──HTTP──▶ Backend
```

인증서는 LB에서만 관리하고 내부 통신은 HTTP로 한다. 관리하기 편하고 백엔드 서버는 암복호화를 하지 않아도 된다.

### End-to-End 암호화

```
Client ──HTTPS──▶ LB ──HTTPS──▶ Backend
```

금융이나 의료처럼 규제 때문에 내부 통신까지 암호화해야 할 때 쓴다. 구간마다 암복호화를 하니 조금 느려지지만, 내부망에서 패킷을 엿봐도 내용이 보이지 않는다.

## 자주 만나는 TLS 에러

| 에러 | 원인 | 해결 |
|---|---|---|
| `SSL certificate has expired` | 인증서 만료 | 갱신 후 재적용 |
| `SSL certificate problem: unable to get local issuer certificate` | 중간 CA 인증서 누락 | 인증서 체인에 중간 CA 포함 |
| `SSL: CERTIFICATE_VERIFY_FAILED` | 자체 서명 인증서 또는 신뢰 불가 | CA 인증서 신뢰 저장소에 추가 |
| `handshake failure` | 클라이언트/서버의 cipher suite 불일치 | TLS 버전 및 cipher 설정 확인 |

```bash
# 서버 인증서 정보 확인
openssl s_client -connect api.example.com:443 -showcerts

# 인증서 체인 검증
openssl verify -CAfile ca-bundle.crt server.crt
```

## Java에서의 TLS

```bash
# 자체 서명 인증서를 사용하는 외부 API 호출 시
# JVM의 truststore에 CA 인증서 추가
keytool -import -alias myca -file ca.crt \
    -keystore $JAVA_HOME/lib/security/cacerts \
    -storepass changeit

# 또는 시스템 속성으로 지정
-Djavax.net.ssl.trustStore=/path/to/truststore.jks
-Djavax.net.ssl.trustStorePassword=changeit
```

JVM은 OS가 아니라 자기 truststore(`cacerts`)를 보고 인증서를 검증한다. 사내 CA로 발급한 인증서를 쓰는 서버를 부르려면 그 CA를 truststore에 넣어야 한다.

## 성능 영향

| 항목 | 영향 |
|---|---|
| 핸드셰이크 | 첫 연결 시 1-RTT 추가 (TLS 1.3) |
| 암복호화 | CPU 사용량 증가 (AES-NI 하드웨어 가속으로 경감) |
| 인증서 검증 | OCSP 조회 시 추가 지연 가능 |

요즘 하드웨어에서는 TLS로 느려지는 정도가 아주 작다. 성능 때문에 HTTPS를 안 쓸 이유는 거의 없다.

## 자주 깨지는 곳

- 인증서 자동 갱신을 걸어 두지 않으면, 만료일에 서비스가 통째로 멈춘다.
- 중간 CA 인증서를 빠뜨리면, 중간 CA를 따로 갖고 있지 않은 클라이언트에서만 검증이 실패한다.
- 개발할 때 인증서 검증을 꺼 둔 코드가 운영에 나가면, 가짜 서버에 연결돼도 알아채지 못한다.
- TLS 1.0이나 1.1처럼 취약점이 알려진 버전을 열어 두면 그 버전으로 공격받을 수 있다.
- 규제 때문에 내부 통신도 암호화해야 하는 곳에서 HTTP를 쓰면 감사에서 걸린다.

## 한 번에 설명하기

> TLS는 통신을 암호화하고, 인증서로 서버가 진짜인지 확인하는 프로토콜입니다. HTTPS는 HTTP를 TLS 위에서 보내는 것이고, TLS 1.3은 1-RTT로 핸드셰이크가 끝나서 이전 버전보다 빠릅니다.
>
> 실무에서 가장 흔한 장애는 인증서 만료라서, 자동 갱신과 만료일 모니터링을 같이 둡니다.
>
> 보통은 LB에서 TLS를 풀고, 규제가 있는 환경이면 내부 구간까지 암호화합니다.

## 꼬리 질문

> [!question]- SSL과 TLS의 차이는?
> SSL은 TLS의 옛 버전입니다. SSL 3.0 다음 버전부터 TLS 1.0으로 이름이 바뀌었고, SSL은 보안 취약점 때문에 지금은 쓰면 안 됩니다. "SSL 인증서"라는 말은 습관처럼 남아 있을 뿐, 실제로 쓰는 건 TLS입니다.

> [!question]- 인증서를 자동 갱신하려면 어떻게 하는가?
> Let's Encrypt를 certbot으로 쓰면 `certbot renew`로 갱신합니다. 이걸 cron이나 systemd timer로 주기적으로 돌리고, 갱신한 뒤에는 웹서버를 reload합니다. AWS ACM 같은 관리형 서비스는 알아서 갱신해 줍니다.

> [!question]- mTLS(상호 TLS)란?
> 보통 TLS에서는 서버만 인증서를 내밀지만, mTLS에서는 클라이언트도 인증서를 내밉니다. 서버가 상대 클라이언트가 누군지도 확인할 수 있어서, 마이크로서비스끼리 통신하거나 API를 인증할 때 씁니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [RFC 8446: TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]