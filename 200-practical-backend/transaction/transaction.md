# Transaction

## 운영 방식

- 이 문서는 Transaction 학습 인덱스로만 사용한다.
- 상세 내용은 `200-practical-backend/transaction/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 문서는 정합성, 격리 수준, 락, 실패 복구, 면접 답변을 중심으로 작성한다.

## 학습 순서

1. Transaction이 필요한 이유
2. ACID
3. Isolation Level
4. Lock
5. Deadlock
6. Spring Transaction
7. 외부 API와 Transaction 경계
8. 보상 트랜잭션

## 핵심 질문

- Transaction 영역에서 실무적으로 중요한 문제는 무엇인가?
- 문제를 발견하면 어떤 순서로 원인을 좁히는가?
- 어떤 해결책이 있고 각각의 한계는 무엇인가?
- 프로젝트 경험과 어떻게 연결할 수 있는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- 트랜잭션은 데이터 정합성을 지키지만 범위가 커지면 락 경합과 장애 전파를 만든다.
- DB 작업과 외부 API 호출을 같은 사고방식으로 묶지 않는다.
- 면접에서는 ACID 암기보다 정합성 요구사항에 맞는 경계 설정을 설명한다.

## 관련 문서

- [[case-studies]]
- [[interview-questions]]
