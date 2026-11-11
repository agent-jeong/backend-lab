---
title: 처리율 제한(Rate Limiting)
description: 한 사용자나 클라이언트가 정해진 시간에 보낼 수 있는 요청 수를 세고 넘치면 429로 거절하는 방법과 알고리즘별 경계 문제
tags: [concept, performance]
---

# 처리율 제한(Rate Limiting)

처리율 제한은 한 주체(사용자, API 키, IP)가 정해진 시간 동안 보낼 수 있는 요청 수를 정해 두고, 넘치면 거절하는 장치다.

제한이 없으면 클라이언트 하나가 시스템 전체를 멈출 수 있다. 외부 파트너가 재시도 루프를 잘못 짜서 주문 조회 API를 초당 수천 번 부르면, DB 커넥션이 그 요청에 다 묶여 다른 사용자의 결제까지 실패한다. 로그인 API에 제한이 없으면 비밀번호를 무한히 대입해 볼 수 있다. 그래서 처리율 제한은 성능 장치이면서 보안 장치다.

## 어디에 거는가

| 대상 | 막으려는 것 | 세는 기준 |
|---|---|---|
| 외부 공개 API | 클라이언트 하나가 몫을 넘어 다른 클라이언트를 밀어내는 것 | API 키, 클라이언트 ID |
| 로그인, 인증번호 확인 | 비밀번호와 인증번호 대입 | 계정과 IP를 각각 |
| 검색, 엑셀 다운로드 같은 비싼 조회 | DB와 CPU를 오래 쥐는 요청이 몰리는 것 | 사용자 ID |
| 문자, 메일 발송 | 비용 폭증과 발송 남용 | 사용자 ID, 수신 번호 |

로그인은 계정 기준과 IP 기준을 둘 다 센다. 계정 기준만 있으면 공격자가 계정을 바꿔 가며 같은 비밀번호를 대입하고, IP 기준만 있으면 IP를 바꿔 가며 한 계정을 노린다.

## 알고리즘 네 가지와 경계 문제

### 고정 윈도우

시간을 1분 같은 칸으로 자르고 칸마다 카운터를 하나 둔다. 칸이 바뀌면 카운터는 0부터 다시 센다. 가장 단순하고 Redis `INCR` 하나로 만든다.

경계 문제가 있다. 한도가 분당 100개일 때 0분 59초에 100개, 1분 0초에 100개를 보내면 2초 사이에 200개가 통과한다. 칸 경계를 끼고 한도의 두 배까지 들어온다.

### 슬라이딩 윈도우

경계 문제를 줄이려고 "지금부터 거꾸로 60초"를 센다. 두 가지 방식이 있다.

- 로그 방식은 요청 시각을 전부 저장하고(Redis Sorted Set), 60초보다 오래된 기록을 지운 뒤 개수를 센다. 정확하지만 요청마다 기록이 하나씩 쌓여 메모리를 많이 쓴다.
- 카운터 방식은 직전 칸과 지금 칸의 카운터만 두고, `직전 칸 개수 × 아직 겹치는 비율 + 지금 칸 개수`로 어림한다. 메모리는 고정 윈도우와 같지만, 직전 칸 안에서 요청이 고르게 왔다고 가정한 근사치다.

### 토큰 버킷

버킷에 일정 속도로 토큰을 채우고, 요청 하나가 토큰 하나를 쓴다. 토큰이 없으면 거절한다. 토큰은 버킷 용량까지만 쌓인다.

평균 속도는 채우는 속도로 묶이고, 버킷 용량만큼 순간 몰림(burst)을 허용한다. 그 대신 한동안 조용하던 클라이언트는 버킷 용량만큼 한꺼번에 보낼 수 있다. 용량이 곧 순간 최대치라서, 뒤쪽 시스템이 그 순간 몰림을 버티는지 보고 용량을 정한다.

### 누출 버킷

요청을 큐에 담고, 큐에서 일정 속도로 꺼내 처리한다. 큐가 차면 새 요청을 거절한다. 뒤쪽으로 나가는 속도가 늘 일정해서 DB나 외부 API를 고른 속도로 부를 때 맞다.

몰릴 때 큐에 쌓인 요청은 그만큼 늦게 처리된다. 그래서 응답이 빨라야 하는 API에서는 큐를 짧게 둔다. Nginx의 `limit_req`가 이 방식이고, `burst`가 큐 길이, `nodelay`는 큐에 든 요청을 기다리게 하지 않고 바로 처리한다.

| 알고리즘 | 메모리 | 순간 몰림 | 경계 문제 |
|---|---|---|---|
| 고정 윈도우 | 키당 카운터 1개 | 칸 경계에서 한도의 두 배 | 있다 |
| 슬라이딩 윈도우 로그 | 요청 수만큼 | 윈도 안 한도까지는 한꺼번에 허용 | 없다 |
| 슬라이딩 윈도우 카운터 | 키당 카운터 2개 | 윈도 한도 근처까지 허용(근사) | 작다 |
| 토큰 버킷 | 키당 토큰 수와 마지막 충전 시각 | 버킷 용량만큼 허용 | 없지만 용량만큼 몰린다 |
| 누출 버킷 | 큐 길이만큼 | 큐로 흡수하고 지연시킨다 | 없다 |

## 여러 서버에서 Redis로 세기

서버마다 메모리에 카운터를 두면 서버 수만큼 한도가 늘어난다. 서버가 4대면 분당 100개 제한이 사실상 400개가 된다. 그래서 서버 여러 대가 같은 카운터를 보도록 Redis에 둔다.

고정 윈도우는 `INCR`로 카운터를 올리고, 처음 만든 key에 `EXPIRE`를 건다. 이 둘을 따로 보내면 `INCR` 뒤에 서버가 죽었을 때 TTL 없는 key가 남는다. Redis 문서는 이 경합을 짚고 Lua 스크립트로 묶는 방법을 보여 준다. Lua 스크립트는 Redis에서 원자적으로 실행된다.

```java
@Component
@RequiredArgsConstructor
public class OrderRateLimiter {

    private static final long LIMIT_PER_MINUTE = 100;
    private static final RedisScript<Long> INCR_WITH_TTL = RedisScript.of("""
            local current = redis.call('INCR', KEYS[1])
            if current == 1 then
              redis.call('EXPIRE', KEYS[1], ARGV[1])
            end
            return current
            """, Long.class);

    private final StringRedisTemplate redisTemplate;

    public boolean tryAcquire(long userId) {
        long minute = Instant.now().getEpochSecond() / 60;
        String key = "rate:order-create:" + userId + ":" + minute;
        Long count = redisTemplate.execute(INCR_WITH_TTL, List.of(key), "120");
        return count != null && count <= LIMIT_PER_MINUTE;
    }
}
```

key에 분 단위 시각을 넣어서 칸이 바뀌면 새 key를 쓴다. TTL은 칸 길이보다 넉넉하게 두어 지난 칸의 key가 알아서 지워지게 한다. 토큰 버킷도 같은 방식으로, 토큰 수와 마지막 충전 시각을 Hash에 두고 충전 계산과 차감을 Lua 하나에서 한다. 자료구조별 쓰임은 [[redis-data-structures]]에 있다.

Redis가 죽었을 때 어떻게 할지도 정한다. 막으면(fail-closed) 정상 사용자까지 거절되고, 통과시키면(fail-open) 그동안 제한이 없다. 로그인처럼 공격을 막는 제한은 막는 쪽, 비싼 조회를 줄이려는 제한은 통과시키는 쪽을 고르는 식으로 기능마다 정한다. 자세한 기준은 [[redis-failure-and-fallback]]에 있다.

## 429와 Retry-After

한도를 넘은 요청에는 429 Too Many Requests로 답한다. RFC 6585는 429를 "정해진 시간 안에 요청을 너무 많이 보냈다"는 뜻으로 정의하고, `Retry-After` 헤더로 언제 다시 보내면 되는지 알려 줄 수 있게 했다. 429 응답은 캐시에 저장하면 안 된다.

```java
if (!orderRateLimiter.tryAcquire(userId)) {
    long secondsToNextMinute = 60 - (Instant.now().getEpochSecond() % 60);
    return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
            .header(HttpHeaders.RETRY_AFTER, String.valueOf(secondsToNextMinute))
            .build();
}
```

`Retry-After`가 없으면 클라이언트는 언제 다시 보낼지 몰라 바로 재시도하고, 그게 다시 한도를 갉아먹는다. 클라이언트 쪽에서 429를 어떻게 다시 보내는지는 [[retry]]에 있다.

Nginx `limit_req`는 거절한 요청에 기본으로 503을 돌려준다. 클라이언트가 서버 장애와 한도 초과를 구분하게 하려면 `limit_req_status 429;`로 바꾼다.

## 어디서 막나

| 위치 | 잘하는 것 | 못하는 것 |
|---|---|---|
| API 게이트웨이, Nginx | 요청이 애플리케이션 스레드에 닿기 전에 버린다. IP와 경로 단위로 넓게 막는다 | 로그인한 사용자 ID, 요금제, 업무 규칙을 모른다 |
| 애플리케이션 | 사용자 ID, 요금제, "하루 쿠폰 발급 3회" 같은 업무 규칙으로 센다 | 거절할 요청도 이미 스레드와 커넥션을 잠깐 쓴다 |

보통 둘을 같이 쓴다. 바깥에서는 IP 기준으로 넓게 막아 대량 요청을 일찍 버리고, 안에서는 사용자와 업무 기준으로 세밀하게 센다.

## 자주 깨지는 곳

- 서버 메모리에 카운터를 두면, 서버를 늘릴 때마다 한도도 같이 늘어난다.
- `INCR`와 `EXPIRE`를 따로 보내면, 그 사이에 서버가 죽었을 때 TTL 없는 카운터가 남는다. key에 시각이 없으면 그 사용자가 계속 거절되고, 시각을 넣은 key라도 지워지지 않는 key가 쌓여 메모리가 샌다.
- 고정 윈도우의 경계 문제를 모르고 한도를 정하면, 칸 경계에서 한도의 두 배가 뒤쪽 시스템으로 들어간다.
- 프록시 뒤에서 IP로 세면서 실제 클라이언트 IP를 꺼내지 않으면, 모든 요청이 프록시 IP 하나로 묶여 전체가 함께 거절된다. 반대로 `X-Forwarded-For`를 그대로 믿으면 공격자가 헤더를 바꿔 제한을 피한다.
- 거절 응답에 `Retry-After`가 없으면, 클라이언트가 바로 재시도해서 거절 트래픽이 줄지 않는다.
- 처리율 제한 카운터를 캐시와 같은 Redis에 두면, 캐시 부하로 Redis가 느려질 때 모든 요청의 제한 확인이 같이 느려진다.

## 운영에서 볼 것

- 429 응답 수를 엔드포인트별, 거절 기준별로 본다. 한 클라이언트가 계속 거절되는지, 정상 사용자가 넓게 거절되는지가 갈린다.
- 거절당한 상위 키(API 키, 사용자 ID, IP) 목록을 본다.
- 제한 확인에 쓰는 Redis 호출의 latency와 timeout, fail-open으로 통과시킨 횟수를 로그와 메트릭으로 남긴다.

## 한 번에 설명하기

> 처리율 제한은 한 사용자나 클라이언트가 정해진 시간에 보낼 수 있는 요청 수를 세서 넘치면 거절하는 장치입니다. 공개 API의 남용, 로그인 대입 공격, 비싼 조회가 몰리는 것을 막습니다.
>
> 알고리즘은 고정 윈도우, 슬라이딩 윈도우, 토큰 버킷, 누출 버킷이 있고, 고정 윈도우는 칸 경계에서 한도의 두 배가 들어오는 문제가 있습니다. 순간 몰림을 어느 정도 허용하려면 토큰 버킷을, 뒤쪽으로 나가는 속도를 일정하게 하려면 누출 버킷을 씁니다.
>
> 서버가 여러 대면 카운터를 Redis에 두고 `INCR`과 `EXPIRE`를 Lua로 묶어 원자적으로 셉니다. 거절할 때는 429와 `Retry-After`를 함께 보내고, 게이트웨이에서 IP 기준으로 넓게, 애플리케이션에서 사용자 기준으로 좁게 막습니다.

## 꼬리 질문

> [!question]- 고정 윈도우의 경계 문제는 무엇이고 어떻게 줄이나?
> 칸이 바뀌는 순간 카운터가 0이 되기 때문에, 칸 끝과 다음 칸 처음에 몰아서 보내면 짧은 시간에 한도의 두 배가 통과합니다. 슬라이딩 윈도우로 "지금부터 거꾸로 N초"를 세거나, 토큰 버킷으로 순간 몰림의 최대치를 버킷 용량으로 묶어서 줄입니다.

> [!question]- 토큰 버킷과 누출 버킷은 어떻게 다른가?
> 토큰 버킷은 쌓인 토큰만큼 요청을 한꺼번에 바로 처리하니 순간 몰림을 허용합니다. 누출 버킷은 요청을 큐에 넣고 일정 속도로만 꺼내니 뒤쪽으로 나가는 속도가 일정하지만, 몰릴 때 큐에 든 요청은 늦게 처리됩니다.

> [!question]- Redis에서 INCR 뒤에 EXPIRE를 따로 호출하면 무엇이 문제인가?
> 두 명령 사이에 애플리케이션이 죽으면 TTL 없는 카운터가 남습니다. key에 시각이 없으면 그 사용자는 한도를 넘은 상태로 계속 거절되고, 시각을 넣은 key라도 지워지지 않는 key가 쌓여 메모리가 샙니다. Lua 스크립트로 두 명령을 묶어 원자적으로 실행합니다.

> [!question]- Redis가 죽으면 처리율 제한은 어떻게 동작해야 하나?
> 기능마다 정합니다. 로그인처럼 공격을 막는 제한은 Redis가 없을 때 막는 쪽을 고르고, 비싼 조회를 줄이려는 제한은 통과시키는 쪽을 고를 수 있습니다. 어느 쪽이든 Redis 호출에 짧은 timeout을 두고, 몇 번 통과시켰는지 메트릭으로 남깁니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Redis Docs: INCR (Pattern: Rate limiter)](https://redis.io/docs/latest/commands/incr/)
- [RFC 6585: Additional HTTP Status Codes (429 Too Many Requests)](https://www.rfc-editor.org/rfc/rfc6585)
- [NGINX: Module ngx_http_limit_req_module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[retry]]
- [[status-code]]
- [[redis-data-structures]]
- [[cache-aside-and-ttl]]
- [[redis-failure-and-fallback]]
