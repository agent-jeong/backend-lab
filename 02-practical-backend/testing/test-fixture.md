---
title: 테스트 픽스처
description: 테스트에 필요한 데이터를 읽기 쉽고 고치기 쉽게 준비하는 방법
tags: [concept, testing]
---

# 테스트 픽스처

Test Fixture는 테스트를 돌리기 전에 준비해 두는 객체, DB 데이터, 외부 응답 같은 것들이다.

fixture는 "이런 상황에서"에 해당하는 부분이다. 예를 들어 "결제 완료된 주문은 취소할 수 없다"를 테스트한다면, 결제 완료 상태의 주문이 fixture다. 좋은 fixture는 짧고 그 조건만 드러낸다. fixture가 복잡해지면 테스트가 무엇을 확인하는지 읽히지 않는다.

## 상황별 선택

| 상황 | 선택 |
|---|---|
| 단순 값 객체 | 테스트 안에서 직접 생성 |
| 반복되는 도메인 객체 | Test Data Builder |
| DB 상태 필요 | 테스트별 명시적 setup |
| 복잡한 시나리오 | 의미 있는 factory 메서드 |

공유 fixture와 builder를 쓰면 같은 준비 코드를 여러 번 쓰지 않아도 된다. 그 대신 공유 fixture는 테스트끼리 서로 엮이게 만들고, builder를 너무 범용으로 만들면 어떤 기본값이 들어가는지 안 보인다.

## 자주 깨지는 곳

- 커다란 fixture 하나를 여러 테스트가 같이 쓰면, 실행 순서에 따라 테스트가 깨진다.
- 테스트에 필요 없는 필드까지 다 적어 두면, 어떤 값이 중요한지 안 보인다.
- fixture 기본값이 도메인 규칙을 어기면, 실제로는 나올 수 없는 상태를 테스트하게 되어 결과를 믿을 수 없다.
- 랜덤 데이터를 쓰면, 실패했을 때 어떤 값 때문인지 알기 어렵다.

## 점검할 것

- 테스트 이름과 fixture만 보고 조건을 알 수 있는지 본다.
- 테스트 실행 순서를 바꿔도 통과하는지 본다.
- fixture가 실제 도메인 invariant를 지키는지 확인한다.

## 한 번에 설명하기

> Fixture는 테스트의 전제 조건이라서, 확인하려는 조건만 보이게 짧게 씁니다.
>
> 자주 쓰는 도메인 객체는 Test Data Builder로 만들되, 숨어 있는 기본값이 도메인 규칙을 어기지 않는지 확인합니다.
>
> 테스트끼리 데이터를 같이 쓰면 순서에 따라 깨지기 때문에, DB 상태는 테스트마다 따로 준비합니다.

## 꼬리 질문

- 테스트 fixture가 복잡하면 어떤 문제가 생기나?
- Test Data Builder는 언제 유용한가?
- 테스트 데이터 공유는 왜 위험한가?

## 참고

2026년 11월에 확인한 공식 문서다.

- [JUnit User Guide](https://docs.junit.org/current/user-guide/)
- [Martin Fowler: Object Mother](https://martinfowler.com/bliki/ObjectMother.html)

## 관련 문서

- [[02-practical-backend/testing/testing|testing]]
- [[unit-vs-integration-test]]
