---
title: Controller, Service, Repository 책임
description: 웹 요청 처리, 유스케이스 조립, 데이터 접근을 어느 계층에 맡기는지
tags: [concept, architecture]
---

# Controller, Service, Repository 책임

Controller는 HTTP 요청을 받는 입구이고, Service는 유스케이스 하나를 처리하면서 트랜잭션 경계를 정하고, Repository는 데이터를 읽고 쓴다.

어디에 무엇을 둘지 정해 두지 않으면 같은 로직이 여러 계층에 흩어진다. 주문 취소 규칙 하나를 바꾸려는데 Controller와 Service 양쪽에 같은 조건문이 있으면, 한쪽만 고쳐서 버그가 난다.

- Controller는 HTTP 요청을 애플리케이션이 이해하는 명령으로 바꾼다.
- Service는 여러 도메인 객체와 Repository를 엮어 유스케이스 하나를 처리한다.
- Repository는 데이터에 어떻게 접근하는지를 감추고 저장소 세부사항을 맡는다.

## 무엇을 어디에 두나

| 책임 | 위치 | 이유 |
|---|---|---|
| request validation, path/body binding | Controller | HTTP 경계 처리다 |
| 인증 사용자 context 전달 | Controller | 요청 context를 애플리케이션으로 넘긴다 |
| 트랜잭션 경계 | Service | 하나의 유스케이스 단위다 |
| 상태 전이 판단 | Domain 또는 Service | 업무 규칙이다 |
| query 최적화 | Repository/Query layer | 저장소 접근 책임이다 |

어디에 둘지 헷갈리면 그 코드가 무엇 때문에 바뀌는지를 본다. 권한 검사와 트랜잭션 경계는 유스케이스 성격에 맞춰 정하고, 한번 정한 방식을 모든 API에 똑같이 적용한다.

## 자주 깨지는 곳

- Controller에서 여러 Repository를 직접 부르면, Controller가 비대해지고 API 변경과 업무 정책 변경이 한데 묶인다.
- Service가 DTO 변환과 DB 호출만 하면, 계층은 껍데기만 남고 나눈 이점이 없다.
- Repository에 권한이나 상태 전이 같은 정책이 들어가면, 다른 곳에서 다시 쓰기도 테스트하기도 어려워진다.
- Repository에서 예외 메시지나 API 응답 형식을 만들면, 저장소 계층이 HTTP 사정을 알게 된다.
- 권한 검사를 어디서 할지 정하지 않으면, API마다 검사 위치가 달라서 빠진 곳을 찾기 어렵다.

## 확인하는 법

- API 형식이 바뀔 때 Service까지 고쳐야 하는지 본다.
- DB 접근 방식이 바뀔 때 Controller까지 고쳐야 하는지 본다.
- 같은 업무 규칙이 Controller와 Service에 중복돼 있는지 확인한다.

## 한 번에 설명하기

> Controller는 HTTP 요청을 애플리케이션 명령으로 바꾸는 입구이고, Service는 도메인 객체와 Repository를 엮어 유스케이스 하나를 처리하며, Repository는 저장소 세부사항을 감춥니다.
>
> 어떤 코드를 어디에 둘지는 그 코드가 무엇 때문에 바뀌는지를 보고 정합니다.
>
> 권한 검사와 트랜잭션 경계는 유스케이스 성격에 맞춰 한 곳에 두고, 모든 API에 같은 방식으로 적용합니다.

## 꼬리 질문

- Controller에 두면 안 되는 로직은?
- Service와 Domain의 책임은 어떻게 나누나?
- Repository가 업무 규칙을 알면 어떤 문제가 생기나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Martin Fowler: Service Layer](https://martinfowler.com/eaaCatalog/serviceLayer.html)

## 관련 문서

- [[02-practical-backend/architecture/architecture|architecture]]
- [[transaction-boundary]]
- [[authorization-check-location]]
