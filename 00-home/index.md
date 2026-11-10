---
title: Backend Lab
description: 실무 중심 백엔드 CS 학습과 기술 질문 대응을 위한 학습 노트
comments: false
---

# Backend Lab

백엔드 개념을 실무에서 어떻게 판단하는지, 그리고 면접에서 어떻게 말할지로 정리하는 위키다. 개념 노트와 직접 겪은 사례가 서로 이어져 있다.

## 내 실무 사례

직접 겪은 문제를 회사·시스템 이름 없이 일반화했다. 각 문서 맨 위 요약 표와 "면접에서 말하기"만 읽어도 흐름이 잡힌다.

| 사례 | 한 줄 요약 | 핵심 숫자 |
|---|---|---|
| [[irreversible-approval-once\|되돌릴 수 없는 승인을 한 번만 보내기]] | 멱등키 없는 외부 송금 승인을 중복 없이 | 응답 대기 최대 120초 |
| [[webhook-once-without-loss\|웹훅을 잃지 않고 한 번만 처리하기]] | 저장 후 바로 응답, 커밋 후 비동기 처리 | 응답 제한 60초 |
| [[slow-admin-query-tuning\|5초 걸리던 조회를 실행계획으로 고치기]] | 서브쿼리와 함수 때문에 못 탄 인덱스 | 부하 시 p95 90ms |
| [[point-balance-and-idempotent-batch\|포인트 잔액 계산과 멱등 지급 배치]] | 잔액은 계산하고, 지급은 한 번만 | |
| [[file-storage-migration\|첨부파일 18만 건 이관]] | 추정 바로잡기, 누락 검사, 안전장치 | 26분, 누락 0건 |
| [[inherited-access-system-incidents\|이어받은 출입 시스템의 장애 추적]] | 성공한 날과 실패한 날 대조 | 9일 중 7일 실패, 실패율 18% |
| [[rag-search-over-past-inquiries\|과거 문의 RAG 검색]] | 하이브리드 검색과 평가 세트 | top3 95.6% |

전체 목록과 문서 구성: [[03-work-cases/work-cases|내 실무 사례]]

## 주제 지도

**기본기**: [[01-core/java/java|Java]] · [[01-core/kotlin/kotlin|Kotlin]] · [[01-core/spring/spring|Spring]] · [[01-core/jpa/jpa|JPA]] · [[01-core/database/database|Database]] · [[01-core/redis/redis|Redis]] · [[01-core/network/network|Network]] · [[01-core/os/os|OS]]

**정합성**: [[02-practical-backend/transaction/transaction|트랜잭션]] · [[02-practical-backend/concurrency/concurrency|동시성]] · [[02-practical-backend/idempotency/idempotency|멱등성]]

**운영**: [[02-practical-backend/performance/performance|성능]] · [[02-practical-backend/observability/observability|관측성]] · [[02-practical-backend/batch/batch-processing|배치]] · [[02-practical-backend/kubernetes/kubernetes|Kubernetes]] · [[02-practical-backend/ci-cd/ci-cd|CI/CD]]

**설계와 품질**: [[02-practical-backend/architecture/architecture|아키텍처]] · [[02-practical-backend/security/security|보안]] · [[02-practical-backend/testing/testing|테스트]]

**면접**: [[04-interview-cases/interview-questions|기술 질문]] · [[04-interview-cases/design-cases|면접 설계 문제]]

**AI**: [[05-ai-workflows/ai-workflows|AI 활용]]

주제마다 인덱스 문서가 있고, 인덱스는 학습 순서 → 핵심 질문 → 실무에서 보는 것 → 내 사례 → 관련 문서 순서로 되어 있다.

## 공부하는 법

1. [[00-home/daily-study-board|학습 보드]]에서 주제 하나를 고른다.
2. 그 주제 인덱스에서 질문 하나를 골라 개념 노트를 보강한다.
3. 노트 끝의 "면접에서 말하기"를 소리 내어 말해 본다.
4. 이어진 내 사례가 있으면 같이 읽고, 개념과 경험을 한 답변으로 묶는다.

노트 하나가 끝났다고 보는 기준은 네 가지다.

- 무엇을 해결하는 개념인지 첫 문단에 보인다.
- 실무에서 깨지는 상황과 판단 기준이 있다.
- 장점만이 아니라 한계와 대가가 있다.
- 1분 안에 말할 답변과 꼬리 질문이 있다.

## 참고

- [[00-home/mastery-map|숙련도 지도]]: 주제별 목표 수준
- [[00-home/learning-principles|학습 원칙]]: 문서 작성 기준과 완료 조건
- [[00-home/glossary|용어집]]: 실무 핵심 용어
