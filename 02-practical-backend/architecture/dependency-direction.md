---
title: 의존성 방향
description: 변경이 잦은 세부사항이 핵심 정책을 흔들지 않게 하는 의존성 기준
tags: [concept, architecture]
---

# 의존성 방향

의존성 방향은 이미 정한 계층과 모듈 경계를 코드의 참조 관계로 지키는 규칙이다. 규칙이 없으면 패키지 구조는 남아 있어도 설계 경계는 무너진다.

## 누가 누구를 아는가

| 관계 | 방향 |
|---|---|
| Controller와 Service | Controller가 Service에 의존한다 |
| Service와 Repository | Service가 Repository interface에 의존한다 |
| Domain과 Infrastructure | Domain은 infrastructure 세부사항을 모른다 |
| 공통 모듈과 업무 모듈 | 업무 모듈이 공통 모듈에 의존한다 |

핵심 업무 규칙은 웹, DB, 외부 API 세부사항에 직접 기대지 않게 둔다. 도메인이 이런 타입을 직접 참조하면 테스트도 변경도 어려워진다.

## 자주 깨지는 곳

- **도메인 객체가 HTTP request나 JPA repository를 직접 참조한다.** 도메인 테스트에 웹과 DB가 따라 들어온다.
- **util/common 모듈에 업무 로직을 넣는다.** 공통 모듈이 업무 모듈을 참조하게 되고 순환 의존이 생긴다.
- **순환 의존을 빌드 설정으로 우회한다.** 작은 변경도 여러 모듈로 번지는 구조는 그대로 남는다.
- **편의상 양방향 참조를 허용한다.** 한 곳을 고칠 때 영향 범위가 커진다.
- **인터페이스를 만들었지만 이름과 시그니처가 구현 세부사항에 묶여 있다.** 분리한 효과가 없다.

## 확인하는 법

- 패키지 의존성 그래프에서 순환 의존을 찾는다.
- 핵심 도메인 테스트가 Spring context 없이 돌아가는지 본다.
- 하위 정책 코드가 상위 입출력 타입을 import하는지 검색한다. 규칙은 패키지 이름이 아니라 실제 import 관계로 검증한다.

## 한 번에 설명하기

> 의존성 방향은 계층과 모듈 경계를 실제 코드에서 지키는 규칙입니다. 저는 핵심 업무 규칙이 웹, DB, 외부 API 세부사항을 모르게 두고, 공통 모듈이 업무 모듈을 참조하지 않게 합니다. 순환 의존은 작은 변경을 여러 모듈로 번지게 하기 때문에, 패키지 이름이 아니라 실제 import 관계로 확인합니다.

## 꼬리 질문

- 도메인이 Repository를 직접 알아도 되나?
- 순환 의존이 생기면 어떤 문제가 생기나?
- 인터페이스 분리는 언제 의미가 있나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Robert C. Martin: The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## 관련 문서

- [[architecture]]
- [[layered-architecture]]
- [[module-boundary]]
