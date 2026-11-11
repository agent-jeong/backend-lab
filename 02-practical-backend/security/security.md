---
title: 보안
description: 인증, 인가, 민감 정보 보호 학습 인덱스
tags: [security]
comments: false
---

# 보안

인증과 인가, 세션·토큰과 OAuth·OIDC, 비밀번호 저장, CORS·CSRF·XSS, SQL 인젝션, 로그 속 민감 정보, 권한 검증 위치, Spring Security 흐름을 다룬다. 권한 검사가 빠지는 곳과 정보가 새는 곳을 어디서 막는지가 중심이다.

## 읽는 순서

1. [[authentication-and-authorization|인증과 인가]]
2. [[session-and-token|Session과 Token]]
3. [[oauth2-and-oidc|OAuth 2.0과 OpenID Connect]]
4. [[password-storage|Password 저장]]
5. [[cors|CORS]]
6. [[csrf|CSRF]]
7. [[xss|XSS]]
8. [[sql-injection|SQL Injection]]
9. [[sensitive-data-logging|민감 정보 로깅 방지]]
10. [[authorization-check-location|권한 검증 위치]]
11. [[spring-security-flow|Spring Security 인증과 인가 흐름]]

## 먼저 답해 볼 질문

- 인증과 인가는 무엇이 다르고, 각각 실패하면 401과 403 중 무엇을 돌려주나?
- 세션과 JWT는 로그아웃, 탈취 대응, 수평 확장에서 어떻게 다른가?
- 비밀번호는 왜 암호화가 아니라 느린 단방향 해시(bcrypt, Argon2 등)로 저장하나?
- CORS를 설정하면 CSRF도 막히나?
- 권한 검증을 Controller, Service, 쿼리 조건 중 어디에 두어야 누락이 줄어드나?
- 로그와 에러 응답으로 민감 정보가 새는 경로는 어디인가?

## 실무에서 보는 것

- 보안은 다 만든 뒤에 붙이는 기능이 아니다. 처음 설계할 때와 운영하는 습관에서 챙긴다.
- 인증과 인가를 나눠서 본다. 실제 사고는 "로그인은 했는데 남의 데이터에 접근했다"는 인가 누락에서 자주 난다.
- 민감 정보는 저장, 로그, 응답, 외부 전송 경로를 하나씩 따라가며 확인한다.

## 관련 문서

- [[01-core/network/cors|cors]]
- [[02-practical-backend/observability/logging|logging]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
