---
title: URL을 입력하면 일어나는 일
description: 브라우저에 URL을 넣고 응답을 받기까지 거치는 단계와, 장애 때 단계마다 백엔드 개발자가 보는 곳
tags: [concept, network]
---

# URL을 입력하면 일어나는 일

브라우저 주소창에 `https://shop.example.com/orders/42`를 넣으면 요청은 DNS 조회, TCP 연결, TLS 핸드셰이크, HTTP 요청, 로드밸런서, 애플리케이션 서버를 차례로 지나고, 응답은 같은 길을 거꾸로 돌아와 화면에 그려진다.

"주문 페이지가 안 열린다"는 신고 하나에도 원인은 이 단계 중 어디에든 있다. 도메인이 엉뚱한 IP를 가리킬 수도, 인증서가 만료됐을 수도, 로드밸런서가 서버를 모두 빼 버렸을 수도, 애플리케이션 스레드가 외부 결제 API를 기다리며 다 묶였을 수도 있다. 단계를 순서대로 알고 있으면 어느 구간에서 멈췄는지부터 나누고, 그 구간의 로그와 지표만 본다.

## 전체 흐름

```
브라우저
  1. URL 해석, 캐시 확인
  2. DNS 조회           shop.example.com → 203.0.113.10
  3. TCP 연결           SYN / SYN-ACK / ACK
  4. TLS 핸드셰이크     인증서 확인, 키 합의
  5. HTTP 요청          GET /orders/42
로드밸런서 / 리버스 프록시
  6. TLS 종료, 라우팅, 헬스체크 통과한 서버 고르기
애플리케이션 서버
  7. Tomcat 스레드 → Filter → DispatcherServlet → Controller → Service → DB
  8. 응답 생성          200 OK, JSON 또는 HTML
브라우저
  9. 응답 받기, 파싱, 렌더링
```

## 1. URL 해석과 브라우저 캐시

브라우저는 URL에서 스킴(`https`), 호스트(`shop.example.com`), 경로(`/orders/42`)를 나눈다. 같은 자원이 캐시에 있고 `Cache-Control` 기한 안이면 네트워크로 나가지 않고 캐시에서 바로 쓴다.

장애 때 보는 곳: 사용자만 옛 화면을 본다면 응답의 `Cache-Control`과 CDN 캐시를 본다. 브라우저 개발자 도구 Network 탭에서 `(disk cache)`로 찍혔는지 확인한다.

## 2. DNS 조회

호스트 이름을 IP로 바꾼다. 브라우저, OS, 리졸버 캐시를 차례로 보고, 없으면 권한 있는 네임서버까지 묻는다. 자세한 흐름과 TTL은 [[dns]]에 있다.

장애 때 보는 곳: `dig shop.example.com`으로 지금 어떤 IP가 나오는지 본다. 일부 사용자만 실패하면 TTL이 남은 옛 레코드를 의심한다. 서버끼리 호출하는 경우에는 JVM의 DNS 캐시가 OS와 따로 있다는 것도 같이 본다.

## 3. TCP 연결

받은 IP의 443 포트로 3-way handshake를 한다. 왕복(RTT) 한 번이 지나야 요청을 보낼 수 있다. keep-alive로 연결을 다시 쓰면 다음 요청부터 이 단계가 빠진다. 자세한 내용은 [[tcp-connection]]에 있다.

장애 때 보는 곳: 연결 자체가 안 되면 connect timeout이 난다. 서버가 꺼졌거나, 방화벽이나 보안 그룹이 막았거나, 포트가 열려 있지 않은 경우다. `nc -vz shop.example.com 443`으로 포트가 열리는지 본다.

## 4. TLS 핸드셰이크

브라우저는 서버 인증서가 이 도메인용인지, 믿을 수 있는 CA가 서명했는지, 기한이 남았는지 확인하고 암호화 키를 합의한다. TLS 1.3은 왕복 한 번에 끝나고, TLS 1.2는 두 번 걸린다. 이 단계에서 ALPN으로 HTTP/2를 쓸지도 정한다. 자세한 내용은 [[tls]]에 있다.

장애 때 보는 곳: 모든 사용자가 갑자기 접속을 못 하면 인증서 만료부터 본다. 일부 클라이언트만 실패하면 중간 인증서가 빠졌는지 본다. `openssl s_client -connect shop.example.com:443 -servername shop.example.com`으로 인증서 체인과 만료일을 확인한다.

## 5. HTTP 요청

암호화된 연결 위로 요청 줄, 헤더, 본문을 보낸다. `Host` 헤더가 같은 IP에 붙은 여러 도메인 중 어디로 가는 요청인지 알려 주고, 쿠키나 `Authorization` 헤더가 사용자를 알려 준다. 요청 형식은 [[http-basics]]에 있다.

장애 때 보는 곳: `curl -w`로 구간별 시간을 나눠 잰다. 어느 숫자가 튀는지 보면 DNS, 연결, TLS, 서버 처리 중 어디가 느린지 바로 갈린다.

```bash
curl -s -o /dev/null https://shop.example.com/orders/42 -w '
dns      %{time_namelookup}
connect  %{time_connect}
tls      %{time_appconnect}
ttfb     %{time_starttransfer}
total    %{time_total}
'
```

값은 요청 시작부터 그 단계가 끝날 때까지 쌓인 시간이다. `ttfb - tls`가 크면 서버가 첫 바이트를 만드는 데 오래 걸린 것이다.

## 6. 로드밸런서와 리버스 프록시

요청은 보통 애플리케이션 서버에 바로 가지 않고 로드밸런서(L7이면 리버스 프록시 역할도 한다)를 먼저 지난다. 여기서 TLS를 풀고, 경로나 호스트로 대상 그룹을 고르고, 헬스체크를 통과한 서버 중 하나로 넘긴다. 원래 클라이언트 IP와 스킴은 `X-Forwarded-For`, `X-Forwarded-Proto` 헤더에 담아 보낸다. 자세한 내용은 [[load-balancer]]에 있다.

장애 때 보는 곳: 응답 코드가 어디서 만들어졌는지부터 가른다. 애플리케이션 로그에 그 요청이 없는데 사용자는 502, 503, 504를 받았다면 로드밸런서가 만든 응답이다. 503은 보낼 서버가 없을 때(헬스체크 전부 실패), 504는 서버 응답을 기다리다 끊었을 때, 502는 서버가 연결을 끊거나 잘못된 응답을 줬을 때 흔히 나온다. 로드밸런서 접근 로그의 대상 서버 처리 시간과 헬스체크 상태를 같이 본다.

Spring Boot 뒤에 프록시가 있으면 `server.forward-headers-strategy`를 설정해야 애플리케이션이 원래 클라이언트 IP와 `https`를 본다. 설정하지 않으면 리다이렉트 URL이 `http`로 나가거나 접근 로그에 로드밸런서 IP만 찍힌다.

## 7. 애플리케이션 서버

Spring Boot 3.x 기본 구성에서는 내장 Tomcat이 연결을 받아 요청 처리 스레드 하나에 맡긴다. 그 스레드가 Filter 체인, DispatcherServlet, HandlerMapping, Controller, Service, Repository를 차례로 지나고, 반환값을 HttpMessageConverter가 JSON으로 바꾼다. 단계별 컴포넌트는 [[spring-mvc-request-flow]]에 있다.

요청 처리 스레드는 응답을 다 쓸 때까지 그 요청에 묶인다. 중간에 DB 커넥션을 빌리거나 외부 API를 부르면, 기다리는 시간만큼 스레드와 커넥션을 같이 쥐고 있다. 그래서 의존성 하나가 느려지면 스레드 풀이 바닥나고, 그 의존성과 상관없는 요청까지 대기열에서 멈춘다. 이 흐름은 [[connection-pool-and-timeout]]과 [[circuit-breaker]]에서 이어진다.

장애 때 보는 곳: 애플리케이션 접근 로그에서 요청이 들어왔는지, 처리 시간이 얼마인지 본다. 느리면 Tomcat busy 스레드 수, HikariCP 대기 시간, 외부 호출 지연을 본다. 스레드가 다 차 있으면 thread dump로 스레드들이 무엇을 기다리는지 확인한다.

## 8. 응답과 렌더링

응답은 같은 연결을 거슬러 브라우저에 온다. HTML이면 브라우저는 HTML로 DOM을, CSS로 CSSOM을 만들고, 둘을 합쳐 레이아웃을 계산한 뒤 화면에 그린다. HTML을 읽다 만난 CSS, JavaScript, 이미지는 각각 따로 요청하고, 다른 도메인이면 DNS 조회부터 다시 한다. JSON API라면 JavaScript가 응답을 받아 화면 일부를 다시 그린다.

장애 때 보는 곳: 서버 응답은 빠른데 화면이 늦게 뜬다면 백엔드보다 프런트 자원 로딩을 본다. 개발자 도구 Network 탭의 waterfall에서 어떤 자원이 오래 걸렸는지 확인한다.

## 구간별로 나눠 보기

| 증상 | 의심할 구간 | 먼저 볼 것 |
|---|---|---|
| 일부 사용자만 접속 실패 | DNS, TLS | `dig` 결과, 인증서 체인 |
| 전체 접속 불가, 인증서 경고 | TLS | 인증서 만료일 |
| 연결이 안 맺어짐 | TCP, 방화벽 | `nc -vz`, 보안 그룹 |
| 503이 쏟아지고 앱 로그는 조용함 | 로드밸런서 | 헬스체크 상태, 등록된 서버 수 |
| 504가 나고 앱 로그엔 긴 처리 시간 | 애플리케이션, 외부 의존성 | 처리 시간, 스레드 풀, DB 풀 |
| 첫 바이트는 빠른데 화면이 늦음 | 브라우저 렌더링 | Network waterfall |

## 자주 깨지는 곳

- 애플리케이션 로그만 보면, 로드밸런서가 만든 502, 503, 504를 놓치고 "요청이 안 왔다"고 결론 낸다.
- 서버 IP를 옮기면서 DNS TTL을 미리 낮추지 않으면, TTL 동안 일부 사용자가 옛 서버로 간다.
- 인증서 만료 알림이 없으면, 만료 순간 HTTPS로 오는 모든 요청이 TLS 단계에서 끊긴다.
- 프록시 뒤에서 forward 헤더 설정을 빠뜨리면, 애플리케이션이 모든 요청을 로드밸런서 IP에서 온 `http` 요청으로 본다. IP로 거르는 접근 제한이나 리다이렉트가 틀어진다.
- 로드밸런서 idle timeout과 애플리케이션 keep-alive timeout을 맞추지 않으면, 한쪽이 먼저 닫은 연결로 요청이 가서 간헐적인 502가 난다.
- 요청 처리 스레드에서 느린 외부 API를 timeout 없이 부르면, 그 API와 무관한 페이지까지 스레드가 없어 멈춘다.

## 한 번에 설명하기

> URL을 입력하면 브라우저는 DNS로 IP를 찾고, TCP 연결과 TLS 핸드셰이크를 마친 뒤 HTTP 요청을 보냅니다. 요청은 로드밸런서에서 TLS가 풀리고 헬스체크를 통과한 서버로 가며, Spring 애플리케이션에서는 Tomcat 스레드 하나가 Filter, DispatcherServlet, Controller를 거쳐 응답을 만듭니다.
>
> 장애가 나면 이 순서대로 어느 구간에서 멈췄는지부터 나눕니다. `curl -w`로 DNS, 연결, TLS, 첫 바이트까지 시간을 따로 재고, 애플리케이션 로그에 요청이 없으면 로드밸런서를 봅니다.
>
> 애플리케이션 안에서는 스레드와 커넥션이 무엇을 기다리는지를 봅니다. 외부 의존성 하나가 느려도 스레드가 묶여서 전체가 멈추기 때문입니다.

## 꼬리 질문

> [!question]- HTTPS 요청 하나를 보내기 전까지 왕복이 몇 번 필요한가요?
> DNS가 캐시에 있다고 하면, TCP 연결에 한 번, TLS 1.3 핸드셰이크에 한 번이 필요하고 그다음에 HTTP 요청을 보냅니다. TLS 1.2면 핸드셰이크가 두 번이라 하나 더 늘어납니다. keep-alive로 연결을 다시 쓰면 이 비용은 첫 요청에서만 냅니다.

> [!question]- 사용자는 504를 받았는데 애플리케이션 로그에는 200이 찍혀 있습니다. 무슨 일인가요?
> 로드밸런서가 정해 둔 시간 안에 응답을 못 받아 먼저 504를 돌려준 것입니다. 애플리케이션은 그 뒤에도 끝까지 처리해서 200을 남겼습니다. 결제 같은 요청이면 사용자는 실패로 알고 다시 시도할 수 있어서, 멱등키로 중복을 막고 애플리케이션 timeout을 로드밸런서 timeout보다 짧게 맞춥니다.

> [!question]- 로드밸런서 뒤에서 클라이언트 IP는 어떻게 아나요?
> 로드밸런서가 `X-Forwarded-For` 헤더에 원래 IP를 담아 보냅니다. Spring Boot에서는 `server.forward-headers-strategy`를 설정해야 `request.getRemoteAddr()`가 그 값을 씁니다. 이 헤더는 클라이언트가 직접 넣을 수도 있으니, 믿을 수 있는 프록시가 붙인 값만 씁니다.

> [!question]- 페이지가 느리다는 신고를 받으면 어디부터 보나요?
> `curl -w`로 구간을 나눠 잽니다. DNS나 연결이 느리면 네트워크와 인프라를, 첫 바이트까지가 느리면 애플리케이션과 DB를, 첫 바이트는 빠른데 화면이 늦으면 프런트 자원 로딩을 봅니다.

## 내 사례

- [[irreversible-approval-once|되돌릴 수 없는 승인을 한 번만 보내기]]: DNS, 연결, TLS 단계의 실패는 "안 감"으로, 요청을 보낸 뒤의 실패는 "모름"으로 나누기

## 참고

2026년 11월에 확인한 공식 문서다.

- [MDN: Populating the page: how browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)
- [RFC 8446: The Transport Layer Security (TLS) Protocol Version 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- [curl man page (`--write-out`)](https://curl.se/docs/manpage.html)

## 관련 문서

- [[01-core/network/network|network]]
- [[dns]]
- [[tcp-connection]]
- [[tls]]
- [[http-basics]]
- [[load-balancer]]
- [[spring-mvc-request-flow]]
- [[connection-pool-and-timeout]]
- [[circuit-breaker]]
