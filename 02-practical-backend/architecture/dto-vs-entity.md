---
title: DTO와 Entity 분리
description: API 입출력 모델과 영속성 모델을 분리하는 기준
---

# DTO와 Entity 분리

## 한 줄 정의

DTO는 계층 간 데이터 전달과 API 입출력을 위한 모델이고, Entity는 영속성과 도메인 상태를 표현하는 모델이다.

## 실무에서 왜 문제 되는가

- Entity를 응답으로 그대로 노출하면 내부 필드와 연관관계가 API 계약이 된다.
- 요청 DTO를 Entity로 직접 바인딩하면 클라이언트가 바꾸면 안 되는 필드까지 변경할 수 있다.
- API 요구사항에 맞춰 Entity를 바꾸면 영속성 모델이 화면 요구에 끌려간다.
- DTO가 너무 많으면 변환 비용과 중복이 늘어난다.

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 외부 API 응답 | Response DTO | 노출 필드를 통제한다 |
| 생성/수정 요청 | Request DTO | 입력 가능한 필드를 제한한다 |
| 단순 내부 전달 | Command/Query DTO | 유스케이스 의도를 드러낸다 |
| 핵심 도메인 상태 | Entity | 영속성과 규칙을 함께 표현한다 |

## 자주 나는 실수

- Entity를 JSON 응답으로 그대로 반환한다.
- 양방향 연관관계 Entity를 직렬화해 순환 참조를 만든다.
- DTO를 만들기 싫어서 Entity setter를 열어둔다.
- 모든 내부 메서드까지 DTO로 감싸 복잡도를 늘린다.

## 확인 방법

- API 응답에서 내부 id, 상태, 연관 객체가 과도하게 노출되는지 확인한다.
- 요청 payload로 수정되면 안 되는 필드를 바꿀 수 있는지 테스트한다.
- Entity 변경이 API breaking change로 이어지는지 확인한다.

## 핵심 요약

DTO와 Entity 분리는 API 계약과 영속성 모델의 변경 이유를 분리하기 위한 것이다.

Entity를 그대로 노출하면 내부 구조가 외부 계약이 된다.

요청 DTO는 클라이언트가 변경 가능한 필드를 제한한다.

응답 DTO는 필요한 데이터만 안정적인 형태로 제공한다.

단순한 내부 흐름까지 무조건 DTO를 늘리는 것은 피하고 경계가 있는 곳에서 분리한다.

## 꼬리 질문

- Entity를 API 응답으로 바로 반환하면 어떤 문제가 생기는가?
- Request DTO와 Response DTO를 나누는 이유는 무엇인가?
- DTO가 너무 많아지는 문제는 어떻게 관리할 것인가?

## 관련 문서

- [[architecture]]
- [[entity-table-mapping]]
- [[serialization-and-jackson]]
