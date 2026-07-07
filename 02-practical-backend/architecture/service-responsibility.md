---
title: Controller, Service, Repository 책임
description: 웹 요청 처리, 유스케이스 조합, 데이터 접근 책임을 나누는 기준
---

# Controller, Service, Repository 책임

## 한 줄 정의

Controller는 HTTP 경계, Service는 유스케이스와 트랜잭션 경계, Repository는 데이터 접근을 담당한다.

## 실무에서 왜 문제 되는가

- Controller가 비대해지면 API와 업무 정책 변경이 강하게 결합된다.
- Service가 단순 전달만 하면 계층이 형식만 남고 설계 이점이 없다.
- Repository에 권한, 상태 전이 같은 정책이 들어가면 재사용과 테스트가 어려워진다.
- 책임 기준이 없으면 같은 로직이 여러 계층에 중복된다.

## 실무 판단 기준

| 책임 | 위치 | 이유 |
|---|---|---|
| request validation, path/body binding | Controller | HTTP 경계 처리다 |
| 인증 사용자 context 전달 | Controller | 요청 context를 애플리케이션으로 넘긴다 |
| 트랜잭션 경계 | Service | 하나의 유스케이스 단위다 |
| 상태 전이 판단 | Domain 또는 Service | 업무 규칙이다 |
| query 최적화 | Repository/Query layer | 저장소 접근 책임이다 |

## 자주 나는 실수

- Controller에서 여러 Repository를 직접 호출한다.
- Service가 DTO 변환과 DB 호출만 하고 정책이 없다.
- Repository에서 예외 메시지나 API 응답 형식을 만든다.
- 권한 검증 위치를 정하지 않아 API마다 달라진다.

## 확인 방법

- API 형식이 바뀔 때 Service 변경이 필요한지 본다.
- DB 접근 방식이 바뀔 때 Controller 변경이 필요한지 본다.
- 같은 업무 규칙이 Controller와 Service에 중복되는지 확인한다.

## 핵심 요약

Controller는 HTTP 요청을 애플리케이션 명령으로 바꾸는 경계다.

Service는 여러 도메인 객체와 Repository를 조합해 하나의 유스케이스를 수행한다.

Repository는 데이터 접근 방법을 숨기고 저장소 세부사항을 담당한다.

책임 분리는 변경 이유를 기준으로 판단해야 한다.

권한 검증과 트랜잭션 경계는 유스케이스 성격에 맞게 일관되게 배치해야 한다.

## 꼬리 질문

- Controller에 두면 안 되는 로직은 무엇인가?
- Service와 Domain의 책임은 어떻게 나눌 것인가?
- Repository가 업무 규칙을 알면 어떤 문제가 생기는가?

## 관련 문서

- [[architecture]]
- [[transaction-boundary]]
- [[authorization-check-location]]
