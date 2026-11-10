---
title: Controller, Service, Repository 책임
description: 웹 요청 처리, 유스케이스 조합, 데이터 접근 책임을 나누는 기준
tags: [concept, architecture]
---

# Controller, Service, Repository 책임

Controller는 HTTP 경계, Service는 유스케이스와 트랜잭션 경계, Repository는 데이터 접근을 맡는다. 책임 기준이 없으면 같은 로직이 여러 계층에 중복되고, 무엇을 고칠 때 어디가 같이 바뀌는지 알 수 없게 된다.

- Controller는 HTTP 요청을 애플리케이션 명령으로 바꾸는 경계다.
- Service는 여러 도메인 객체와 Repository를 조합해 유스케이스 하나를 수행한다.
- Repository는 데이터 접근 방법을 숨기고 저장소 세부사항을 맡는다.

## 무엇을 어디에 두나

| 책임 | 위치 | 이유 |
|---|---|---|
| request validation, path/body binding | Controller | HTTP 경계 처리다 |
| 인증 사용자 context 전달 | Controller | 요청 context를 애플리케이션으로 넘긴다 |
| 트랜잭션 경계 | Service | 하나의 유스케이스 단위다 |
| 상태 전이 판단 | Domain 또는 Service | 업무 규칙이다 |
| query 최적화 | Repository/Query layer | 저장소 접근 책임이다 |

판단 기준은 변경 이유다. 권한 검증과 트랜잭션 경계는 유스케이스 성격에 맞춰 한 가지 방식으로 일관되게 둔다.

## 자주 깨지는 곳

- **Controller에서 여러 Repository를 직접 호출한다.** Controller가 비대해지고 API와 업무 정책 변경이 한데 묶인다.
- **Service가 DTO 변환과 DB 호출만 한다.** 계층은 형식만 남고 나눈 이점이 없다.
- **Repository에 권한, 상태 전이 같은 정책이 들어간다.** 재사용과 테스트가 어려워진다.
- **Repository에서 예외 메시지나 API 응답 형식을 만든다.** 저장소 계층이 HTTP 사정을 알게 된다.
- **권한 검증 위치를 정하지 않는다.** API마다 검증 위치가 달라진다.

## 확인하는 법

- API 형식이 바뀔 때 Service까지 고쳐야 하는지 본다.
- DB 접근 방식이 바뀔 때 Controller까지 고쳐야 하는지 본다.
- 같은 업무 규칙이 Controller와 Service에 중복돼 있는지 확인한다.

## 면접에서 말하기

> Controller는 HTTP 요청을 애플리케이션 명령으로 바꾸는 경계이고, Service는 도메인 객체와 Repository를 조합해 유스케이스 하나를 수행하며, Repository는 저장소 세부사항을 숨깁니다. 저는 어떤 코드를 어디에 둘지 변경 이유로 판단합니다. 권한 검증과 트랜잭션 경계는 유스케이스 성격에 맞춰 한 곳에 일관되게 둡니다.

## 꼬리 질문

- Controller에 두면 안 되는 로직은?
- Service와 Domain의 책임은 어떻게 나누나?
- Repository가 업무 규칙을 알면 어떤 문제가 생기나?

## 관련 문서

- [[architecture]]
- [[transaction-boundary]]
- [[authorization-check-location]]
