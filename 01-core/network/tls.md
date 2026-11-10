---
title: "TLS/SSL 동작 원리"
description: TLS 동작 원리와 인증서, HTTPS 적용 실무
---

# TLS/SSL 동작 원리

TLS(Transport Layer Security)는 통신 내용을 암호화하고, 인증서로 서버 신원을 검증하는 보안 프로토콜이다. HTTPS는 HTTP에 TLS를 얹은 것이다.

실무에서 TLS 장애는 대개 암호 알고리즘이 아니라 인증서 운영에서 난다. 인증서가 만료되면 서비스 전체에 접속할 수 없고, 중간 CA를 빠뜨리면 일부 클라이언트만 실패한다. 내부 통신을 평문 HTTP로 두면 보안 감사에 걸린다. 성능 부담은 생각보다 작다.

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

TLS 1.3은 1-RTT로 핸드셰이크가 끝난다(TLS 1.2는 2-RTT). 이전 세션을 재개하면 0-RTT로 첫 요청을 바로 보낼 수도 있다. 단 0-RTT 데이터는 공격자가 그대로 재전송(replay)할 수 있어서, 서버는 GET 같은 멱등 요청에만 허용해야 한다.

## 인증서

인증서는 세 가지 일을 한다.

1. **서버 인증**: 이 서버가 실제로 example.com인지 검증한다.
2. **공개 키 전달**: 암호화에 쓸 서버의 공개 키를 담고 있다.
3. **신뢰 체인**: CA(Certificate Authority)의 서명으로 신뢰를 보장한다.

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

인증서 만료는 실무에서 가장 흔한 장애 원인 중 하나다. 자동 갱신을 걸고, 만료일을 모니터링한다.

## HTTPS를 어디서 끝내나

### LB에서 SSL 종료 (가장 흔함)

```
Client ──HTTPS──▶ LB (SSL 종료) ──HTTP──▶ Backend
```

인증서를 LB에서만 관리하고 내부 통신은 HTTP로 한다. 관리가 간편하고 백엔드 서버가 암복호화를 하지 않는다.

### End-to-End 암호화

```
Client ──HTTPS──▶ LB ──HTTPS──▶ Backend
```

금융, 의료 같은 규제 환경처럼 내부 통신까지 암호화해야 할 때 쓴다. 성능 오버헤드가 있지만 보안 수준이 높다.

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

```java
// 자체 서명 인증서를 사용하는 외부 API 호출 시
// JVM의 truststore에 CA 인증서 추가
keytool -import -alias myca -file ca.crt \
    -keystore $JAVA_HOME/lib/security/cacerts \
    -storepass changeit

// 또는 시스템 속성으로 지정
-Djavax.net.ssl.trustStore=/path/to/truststore.jks
-Djavax.net.ssl.trustStorePassword=changeit
```

JVM은 자체 truststore(`cacerts`)로 인증서를 검증한다. 사내 CA를 쓰면 그 CA를 truststore에 추가해야 한다.

## 성능 영향

| 항목 | 영향 |
|---|---|
| 핸드셰이크 | 첫 연결 시 1-RTT 추가 (TLS 1.3) |
| 암복호화 | CPU 사용량 증가 (AES-NI 하드웨어 가속으로 경감) |
| 인증서 검증 | OCSP 조회 시 추가 지연 가능 |

현대 하드웨어에서 TLS 오버헤드는 매우 작다. 성능을 이유로 HTTPS를 안 쓸 이유는 거의 없다.

## 자주 깨지는 곳

- **인증서 자동 갱신을 안 건다.** 만료일에 서비스가 통째로 멈춘다.
- **중간 CA 인증서를 빠뜨린다.** 일부 클라이언트에서만 검증이 실패한다.
- **개발용으로 인증서 검증을 끈 코드가 운영에 나간다.**
- **TLS 1.0/1.1 같은 취약한 버전을 열어 둔다.**
- **내부 통신 암호화가 필요한 규제 환경에서 HTTP를 쓴다.**

## 면접에서 말하기

> TLS는 통신을 암호화하고 서버 신원을 인증서로 검증하는 프로토콜이고, HTTPS는 HTTP에 TLS를 얹은 것입니다. TLS 1.3은 1-RTT로 핸드셰이크가 끝나서 이전 버전보다 빠릅니다. 실무에서 제일 흔한 장애는 인증서 만료라서, 저는 자동 갱신과 만료일 모니터링을 같이 둡니다. 보통은 LB에서 TLS를 종료하고, 규제 환경이면 내부 구간까지 암호화합니다.

## 꼬리 질문

> [!question]- SSL과 TLS의 차이는?
> SSL은 TLS의 이전 버전입니다. SSL 3.0 이후 TLS 1.0으로 이름이 바뀌었고, 현재 SSL은 보안 취약점으로 사용이 금지되어 있습니다. "SSL 인증서"라는 용어가 관행적으로 쓰이지만, 실제로는 TLS를 사용합니다.

> [!question]- 인증서를 자동 갱신하려면 어떻게 하는가?
> Let's Encrypt + certbot을 사용하면 `certbot renew` 명령으로 자동 갱신이 가능합니다. cron이나 systemd timer로 주기적으로 실행하고, 갱신 후 웹서버를 reload합니다. AWS ACM 같은 관리형 서비스는 자동 갱신을 지원합니다.

> [!question]- mTLS(상호 TLS)란?
> 일반 TLS는 서버만 인증서를 제시하지만, mTLS는 클라이언트도 인증서를 제시합니다. 서버가 클라이언트의 신원도 검증하므로, 마이크로서비스 간 통신이나 API 인증에 사용됩니다.

## 관련 문서

- [[01-core/network/network|network]]
- [[http-basics]]
- [[tcp-connection]]
- [[load-balancer]]