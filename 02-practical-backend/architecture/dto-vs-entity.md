---
title: DTO와 Entity 분리
description: API로 주고받는 모델과 DB에 저장하는 모델을 왜, 어디서 나누는지
tags: [concept, architecture]
---

# DTO와 Entity 분리

DTO는 API로 주고받거나 계층 사이에 데이터를 넘길 때 쓰는 모델이고, Entity는 DB에 저장되는 도메인 상태를 담는 모델이다. 둘을 나누는 이유는 API 형식과 저장 모델이 서로 다른 이유로 바뀌기 때문이다.

주문 Entity를 그대로 응답으로 내보내면 내부 필드와 연관관계가 그대로 API 형식이 된다. 그 뒤로는 컬럼 하나를 바꿔도 클라이언트가 깨진다. 반대로 화면에 필드 하나를 더 보여 주려고 Entity를 고치면 저장 모델이 화면 사정에 끌려다닌다.

## 어디에 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 외부 API 응답 | Response DTO | 노출 필드를 통제한다 |
| 생성/수정 요청 | Request DTO | 입력 가능한 필드를 제한한다 |
| 단순 내부 전달 | Command/Query DTO | 유스케이스 의도를 드러낸다 |
| 핵심 도메인 상태 | Entity | 영속성과 규칙을 함께 표현한다 |

요청 DTO에는 클라이언트가 바꿔도 되는 필드만 두고, 응답 DTO에는 필요한 데이터만 잘 바뀌지 않는 형태로 담는다.

## 자주 깨지는 곳

- Entity를 JSON 응답으로 그대로 반환하면, 내부 id, 상태, 연관 객체가 밖으로 나가고 Entity를 고칠 때마다 API breaking change가 된다.
- 양방향 연관관계가 있는 Entity를 직렬화하면, 순환 참조가 생긴다.
- 요청을 Entity에 바로 바인딩하면, 클라이언트가 바꾸면 안 되는 필드까지 바꿀 수 있다.
- DTO를 만들기 싫어서 Entity setter를 열어 두면, 아무 데서나 상태를 바꿀 수 있게 된다.
- 내부 메서드까지 전부 DTO로 감싸면, 변환 코드와 중복만 늘어난다. 경계가 있는 곳에서만 나눈다.

## 확인하는 법

- API 응답에 내부 id, 상태, 연관 객체가 지나치게 많이 나가는지 본다.
- 요청 payload로 수정되면 안 되는 필드를 바꿀 수 있는지 테스트한다.
- Entity를 바꿨을 때 API breaking change로 이어지는지 확인한다.

## 한 번에 설명하기

> DTO와 Entity를 나누는 건, API 형식과 저장 모델이 서로 다른 이유로 바뀌기 때문입니다.
>
> Entity를 그대로 내보내면 내부 구조가 외부와의 약속이 되고, 요청을 Entity에 바로 받으면 바꾸면 안 되는 필드까지 열립니다. 그래서 요청 DTO로 입력 필드를 제한하고, 응답 DTO로 필요한 것만 내보냅니다.
>
> 다만 단순한 내부 흐름까지 DTO를 늘리지는 않고, 경계가 있는 곳에서만 나눕니다.

## 꼬리 질문

- Entity를 API 응답으로 바로 반환하면 어떤 문제가 생기나?
- Request DTO와 Response DTO를 나누는 이유는?
- DTO가 너무 많아지는 문제는 어떻게 관리하나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Martin Fowler: Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html)

## 관련 문서

- [[02-practical-backend/architecture/architecture|architecture]]
- [[entity-table-mapping]]
- [[serialization-and-jackson]]
