---
title: Password 저장
description: 비밀번호를 해시, salt, 비용 계수로 저장하는 방법과 각각이 막는 것
tags: [concept, security]
---

# Password 저장

비밀번호는 원문으로 저장하지 않는다. 사용자마다 다른 salt를 섞어 느린 단방향 해시로 저장해서, DB가 통째로 유출돼도 원래 비밀번호를 알아내기 어렵게 만든다.

원문이나 빠른 해시로 저장해 두면 DB가 한 번 새는 것만으로 수많은 계정이 한꺼번에 넘어간다.

## 저장과 검증 흐름

1. 사용자가 비밀번호를 입력한다.
2. 서버는 사용자별 salt를 넣어 bcrypt, scrypt, Argon2 같은 password hashing 알고리즘으로 해시한다.
3. DB에는 원문이 아니라 알고리즘 정보, 비용 계수, salt가 담긴 해시 결과만 저장한다.
4. 로그인 때는 입력값을 같은 방식으로 검증하고 결과만 비교한다.
5. 비용 계수나 알고리즘을 바꿀 때는 사용자가 다시 로그인하거나 비밀번호를 바꿀 때 하나씩 갱신한다.

```java
public void changePassword(User user, String rawPassword) {
    String encoded = passwordEncoder.encode(rawPassword);
    user.changePassword(encoded);
}

public boolean matches(String rawPassword, User user) {
    return passwordEncoder.matches(rawPassword, user.passwordHash());
}
```

비밀번호 원문은 검증하거나 바꾸는 순간에만 메모리에 있고, 저장소와 로그에는 남지 않는다.

## 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반 비밀번호 저장 | Argon2id, 쓸 수 없으면 scrypt, 레거시 환경이면 bcrypt | brute force 비용을 높인다. OWASP가 권하는 순서다. bcrypt는 입력을 72바이트까지만 본다 |
| 단순 SHA 계열 해시 | 사용하지 않음 | 너무 빨라 대입 공격에 약하다 |
| 사용자별 salt | 필수 | 같은 비밀번호도 다른 해시가 되게 한다 |
| 비용 계수 | 운영 부하 기준으로 조정 | 보안과 로그인 성능 사이에서 정해야 한다 |
| 재설정 링크 | 짧은 TTL의 단회성 토큰 | 비밀번호와 같은 수준으로 탈취 위험을 본다 |

salt가 있으면 같은 비밀번호도 사용자마다 다른 해시가 된다. 그래서 rainbow table을 쓰거나 같은 해시끼리 묶어 보는 분석이 통하지 않는다. 비용 계수는 공격자가 한 번 대입해 보는 데 드는 시간을 늘리지만, 그만큼 우리 서버 CPU도 더 쓴다. 너무 낮으면 brute force에 약하고, 너무 높으면 로그인이 느려지고 CPU 부하가 커진다.

이 방식으로 막지 못하는 것도 있다. 사용자가 고른 약한 비밀번호 자체는 어쩔 수 없고, 다른 곳에서 샌 계정 목록을 대입하는 credential stuffing은 따로 막아야 한다.

## 자주 깨지는 곳

- SHA-256 같은 빠른 해시만 쓰면, 대입 공격 속도를 거의 늦추지 못한다.
- 모든 사용자에게 같은 salt를 쓰면, 같은 비밀번호를 쓴 사용자들이 같은 해시로 드러난다.
- 비밀번호를 로그, 이벤트, 예외 메시지에 남기면, 해시를 아무리 잘해도 원문이 다른 길로 샌다.
- 임시 비밀번호를 평문으로 저장하거나 여러 번 쓸 수 있게 두면, 그 경로가 구멍이 된다. 비밀번호 변경, 임시 비밀번호, 재설정 토큰도 비밀번호와 같은 기준으로 다룬다.
- 해시 비용 계수를 운영 CPU 부하와 함께 시험해 보지 않으면, 로그인이 몰리는 시간에 CPU가 먼저 바닥난다.

## 확인하는 법

- 코드 리뷰: 비밀번호 원문이 DB, 로그, 이벤트에 남지 않는지 본다.
- 테스트: 같은 비밀번호라도 사용자마다 저장된 해시가 다른지 본다.
- 부하 테스트: 로그인 peak 상황에서 해시 비용이 CPU를 지나치게 쓰지 않는지 본다.
- 보안 점검: 재설정 토큰의 TTL, 단회성 사용, 실패 횟수 제한을 확인한다.

## 한 번에 설명하기

> 비밀번호는 원문이나 SHA 같은 빠른 해시가 아니라, bcrypt, scrypt, Argon2 같은 느린 password hashing 알고리즘으로 저장합니다.
>
> 사용자별 salt를 넣어서 같은 비밀번호가 같은 해시로 보이지 않게 하고, 비용 계수는 공격자가 치를 비용과 로그인 때 우리 CPU 부하를 같이 보고 정합니다.
>
> 재설정 토큰도 TTL을 짧게 두고 한 번만 쓰게 하며, 로그나 예외 메시지에 원문이 남지 않는지 확인합니다.

## 꼬리 질문

- 비밀번호 저장에 SHA-256만 쓰면 왜 위험한가?
- salt와 비용 계수는 각각 어떤 문제를 줄이나?
- 비밀번호 재설정 기능에서 조심할 점은?

## 참고

2026년 11월에 확인한 공식 문서다.

- [OWASP: Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## 관련 문서

- [[02-practical-backend/security/security|security]]
- [[authentication-and-authorization]]
- [[sensitive-data-logging]]
