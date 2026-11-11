---
title: 의존성 방향
description: 자주 바뀌는 웹, DB, 외부 API 코드가 업무 규칙을 흔들지 않게 참조 방향을 정하는 법
tags: [concept, architecture]
---

# 의존성 방향

의존성 방향은 "어떤 코드가 어떤 코드를 알아도 되는가"를 정한 규칙이다. 이미 나눠 둔 계층과 모듈 경계를 실제 import 관계로 지키는 수단이다.

이 규칙이 없으면 패키지 폴더는 그대로 있어도 경계는 무너진다. 할인 정책 클래스가 HTTP request 객체를 import하는 순간, 화면이 바뀔 때마다 할인 정책 코드도 같이 고쳐야 한다.

## 누가 누구를 아는가

| 관계 | 방향 |
|---|---|
| Controller와 Service | Controller가 Service에 의존한다 |
| Service와 Repository | Service가 Repository interface에 의존한다 |
| Domain과 Infrastructure | Domain은 infrastructure 세부사항을 모른다 |
| 공통 모듈과 업무 모듈 | 업무 모듈이 공통 모듈에 의존한다 |

중요한 업무 규칙은 웹, DB, 외부 API의 세부사항에 직접 기대지 않게 둔다. 도메인이 이런 타입을 직접 참조하면 테스트하기도 고치기도 어려워진다.

## 자주 깨지는 곳

- 도메인 객체가 HTTP request나 JPA repository를 직접 참조하면, 도메인을 테스트할 때 웹과 DB가 따라 들어온다.
- util이나 common 모듈에 업무 로직을 넣으면, 공통 모듈이 업무 모듈을 참조하게 되고 순환 의존이 생긴다.
- 순환 의존을 빌드 설정으로 우회하면, 빌드는 되지만 작은 변경도 여러 모듈로 번지는 구조는 그대로 남는다.
- 편하다고 양방향 참조를 허용하면, 한 곳을 고칠 때 영향이 미치는 범위가 커진다.
- 인터페이스를 만들었는데 이름과 시그니처가 구현 세부사항에 묶여 있으면, 나눠 놓은 효과가 없다.

## 확인하는 법

- 패키지 의존성 그래프에서 순환 의존을 찾는다.
- 핵심 도메인 테스트가 Spring context 없이 돌아가는지 본다.
- 하위 정책 코드가 상위 입출력 타입을 import하는지 검색한다. 규칙을 지키는지는 패키지 이름이 아니라 실제 import 관계로 확인한다.

## 한 번에 설명하기

> 의존성 방향은 계층과 모듈 경계를 실제 코드에서 지키게 하는 규칙입니다.
>
> 중요한 업무 규칙은 웹, DB, 외부 API 세부사항을 모르게 두고, 공통 모듈이 업무 모듈을 참조하지 않게 합니다.
>
> 순환 의존이 생기면 작은 변경도 여러 모듈로 번지기 때문에, 패키지 이름이 아니라 실제 import 관계를 보고 확인합니다.

## 꼬리 질문

- 도메인이 Repository를 직접 알아도 되나?
- 순환 의존이 생기면 어떤 문제가 생기나?
- 인터페이스 분리는 언제 의미가 있나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Robert C. Martin: The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## 관련 문서

- [[02-practical-backend/architecture/architecture|architecture]]
- [[layered-architecture]]
- [[module-boundary]]
- [[oop-design-principles]]
