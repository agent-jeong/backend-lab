---
title: 계층형 아키텍처
description: 계층별 책임을 나누어 변경 비용과 의존성 혼란을 줄이는 설계
tags: [concept, architecture]
---

# 계층형 아키텍처

Layered Architecture는 애플리케이션을 표현, 비즈니스, 데이터 접근 같은 계층으로 나누고, 계층마다 책임과 의존 방향을 제한하는 구조다. 목적은 계층 자체가 아니라 변경 이유를 나누는 데 있다.

## 계층별 책임

1. Controller는 요청/응답 변환과 인증된 사용자 context 전달을 맡는다.
2. Service는 유스케이스 흐름, 트랜잭션 경계, 도메인 규칙 조합을 맡는다.
3. Domain은 상태와 규칙을 표현한다.
4. Repository는 저장소 접근을 추상화한다.
5. 의존성은 보통 바깥 계층에서 안쪽 계층으로만 흐르게 제한한다.

업무 규칙은 되도록 웹과 DB 세부사항에서 떨어뜨려 둔다.

## 변경이 어디에 머물러야 하나

| 변경 | 영향이 머물러야 할 곳 |
|---|---|
| API 형식 변경 | Controller/DTO |
| 업무 규칙 변경 | Service/Domain |
| 저장소 변경 | Repository 구현 |
| 어느 계층에 둘지 고민될 때 | 변경 이유가 같은 코드를 같은 계층에 둔다 |

## 자주 깨지는 곳

- **Controller에 비즈니스 로직이 쌓인다.** API 변경과 정책 변경이 함께 흔들린다.
- **계층은 나눴지만 모든 로직을 Service에 몰아넣는다.** Service 하나가 모든 변경 이유를 떠안는다.
- **Repository에 업무 규칙이 들어간다.** 메서드명에 정책이 담기고 데이터 접근과 도메인 판단이 섞인다.
- **의존 방향이 뒤섞인다.** 테스트와 변경 영향 분석이 어려워진다.
- **Entity를 응답으로 그대로 노출한다.** 영속성 모델이 API 계약이 된다.
- **계층이 많을수록 좋다고 생각한다.** 단순 CRUD에 계층을 과하게 두면 이해 비용만 커지고 생산성이 떨어진다.

## 확인하는 법

- 코드 리뷰: 각 계층 코드가 어떤 변경 이유로 바뀌는지 본다.
- 테스트: 핵심 업무 규칙을 웹/DB 없이 검증할 수 있는지 본다.
- 의존성: 하위 계층이 상위 계층 타입을 참조하지 않는지 확인한다.

## 면접에서 말하기

> Layered Architecture의 목적은 계층을 나누는 것 자체가 아니라 변경 이유를 나누는 것입니다. Controller는 입출력 변환, Service는 유스케이스 흐름, Repository는 저장소 접근을 맡고, 업무 규칙은 웹과 DB에서 떨어뜨려 둡니다. 저는 설계가 맞는지를 변경 영향과 테스트 가능성으로 확인하고, 단순한 기능에는 계층을 과하게 두지 않습니다.

## 꼬리 질문

- 계층을 나누는 기준은?
- Service가 너무 커지는 이유는?
- 단순 CRUD에서도 항상 같은 계층 구조가 필요한가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Martin Fowler: Presentation Domain Data Layering](https://martinfowler.com/bliki/PresentationDomainDataLayering.html)

## 관련 문서

- [[architecture]]
- [[service-responsibility]]
- [[dependency-direction]]
