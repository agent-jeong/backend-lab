---
title: Password 저장
description: 비밀번호를 안전하게 저장하기 위한 해시, salt, 비용 계수 기준
---

# Password 저장

비밀번호는 원문으로 저장하지 않는다. 사용자별 salt와 느린 단방향 해시로 저장해서, DB가 유출돼도 원문을 되살리기 어렵게 만든다. 원문이나 빠른 해시로 저장하면 DB 유출 한 번에 계정이 대량으로 탈취된다.

## 저장과 검증 흐름

1. 사용자가 비밀번호를 입력한다.
2. 서버는 사용자별 salt를 포함해 bcrypt, scrypt, Argon2 같은 password hashing 알고리즘으로 해시한다.
3. DB에는 원문이 아니라 알고리즘 정보, 비용 계수, salt가 포함된 해시 결과만 저장한다.
4. 로그인 때는 입력값을 같은 방식으로 검증하고 결과만 비교한다.
5. 비용 계수나 알고리즘을 바꿀 때는 재로그인이나 비밀번호 변경 시점에 하나씩 갱신한다.

```java
public void changePassword(User user, String rawPassword) {
    String encoded = passwordEncoder.encode(rawPassword);
    user.changePassword(encoded);
}

public boolean matches(String rawPassword, User user) {
    return passwordEncoder.matches(rawPassword, user.passwordHash());
}
```

비밀번호 원문은 검증이나 변경하는 순간에만 메모리에 있고, 저장소와 로그에는 남지 않는다.

## 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 일반 비밀번호 저장 | bcrypt, scrypt, Argon2 | brute force 비용을 높인다 |
| 단순 SHA 계열 해시 | 사용하지 않음 | 너무 빨라 대입 공격에 약하다 |
| 사용자별 salt | 필수 | 같은 비밀번호도 다른 해시가 되게 한다 |
| 비용 계수 | 운영 부하 기준으로 조정 | 보안과 로그인 성능 사이에서 정해야 한다 |
| 재설정 링크 | 짧은 TTL의 단회성 토큰 | 비밀번호와 같은 수준으로 탈취 위험을 본다 |

salt는 같은 비밀번호가 같은 해시로 보이는 문제를 없애 rainbow table과 패턴 분석을 막는다. 비용 계수는 공격 비용을 올리지만 서버 CPU 비용도 같이 올린다. 너무 낮으면 brute force에 약하고, 너무 높으면 로그인이 느려지고 CPU 부하가 커진다.

이 방식이 막지 못하는 것도 있다. 약한 비밀번호 자체는 막지 못하고, credential stuffing은 따로 대응해야 한다.

## 자주 깨지는 곳

- **SHA-256 같은 빠른 해시만 쓴다.** 대입 공격 속도를 늦추지 못한다.
- **모든 사용자에게 같은 salt를 쓴다.** 같은 비밀번호가 같은 해시로 드러난다.
- **비밀번호를 로그, 이벤트, 예외 메시지에 남긴다.** 해시를 아무리 잘해도 원문이 다른 경로로 샌다.
- **임시 비밀번호를 평문으로 저장하거나 재사용 가능하게 둔다.** 비밀번호 변경, 임시 비밀번호, 재설정 토큰도 같은 수준의 기준이 필요하다.
- **해시 비용 계수를 운영 CPU 부하와 함께 검증하지 않는다.** 로그인 peak 때 CPU가 먼저 바닥난다.

## 확인하는 법

- 코드 리뷰: 비밀번호 원문이 DB, 로그, 이벤트에 남지 않는지 본다.
- 테스트: 같은 비밀번호라도 사용자마다 저장된 해시가 다른지 본다.
- 부하 테스트: 로그인 peak 상황에서 해시 비용이 CPU를 지나치게 쓰지 않는지 본다.
- 보안 점검: 재설정 토큰의 TTL, 단회성 사용, 실패 횟수 제한을 확인한다.

## 면접에서 말하기

> 비밀번호는 원문이나 SHA 같은 빠른 해시가 아니라 bcrypt, scrypt, Argon2 같은 느린 password hashing 알고리즘으로 저장합니다. 사용자별 salt로 같은 비밀번호가 같은 해시로 보이지 않게 하고, 비용 계수는 공격 비용과 로그인 CPU 부하를 같이 보고 정합니다. 재설정 토큰도 짧은 TTL에 한 번만 쓰게 하고, 로그나 예외 메시지에 원문이 남지 않는지 확인합니다.

## 꼬리 질문

- 비밀번호 저장에 SHA-256만 쓰면 왜 위험한가?
- salt와 비용 계수는 각각 어떤 문제를 줄이나?
- 비밀번호 재설정 기능에서 조심할 점은?

## 관련 문서

- [[security]]
- [[authentication-and-authorization]]
- [[sensitive-data-logging]]
