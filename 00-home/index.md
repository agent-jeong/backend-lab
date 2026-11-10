---
title: Backend Lab
description: 백엔드 개념을 실무 판단 기준으로 정리하고, 직접 겪은 문제를 사례로 남기는 블로그
comments: false
---

# Backend Lab

백엔드 개념을 "실무에서 어떻게 판단하는가"로 정리하고, 직접 겪은 문제를 사례로 남기는 블로그다. 개념 노트와 실무 사례가 서로 이어져 있어서, 개념을 읽다가 그 개념이 실제로 쓰인 사례로 넘어갈 수 있다.

처음이라면 아래 실무 사례 하나를 먼저 읽어 보길 권한다. 어떤 기준으로 쓰는지는 [[00-home/about|이 블로그에 대해]]에 있다.

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

**운영**: [[02-practical-backend/performance/performance|성능]] · [[02-practical-backend/observability/observability|관측성]] · [[02-practical-backend/batch/batch-processing|배치]] · [[02-practical-backend/kubernetes/kubernetes|Kubernetes]] · [[02-practical-backend/ci-cd/ci-cd|CI·CD]]

**설계와 품질**: [[02-practical-backend/architecture/architecture|아키텍처]] · [[02-practical-backend/security/security|보안]] · [[02-practical-backend/testing/testing|테스트]]

**설계 사례**: [[04-design-cases/design-cases|설계 사례]] ([[first-come-limited-stock|선착순 한정 수량]], [[like-count|좋아요 수]]) · [[04-design-cases/interview-questions|기술 질문 모음]]

**AI**: [[05-ai-workflows/ai-workflows|AI 활용]]

주제마다 안내 글이 있다. 읽는 순서, 핵심 질문, 그 주제가 쓰인 내 사례가 정리돼 있다.

## 더 보기

- [[00-home/glossary|용어집]]: 자주 나오는 용어와 그 용어를 다룬 글
- [[00-home/about|이 블로그에 대해]]: 쓰는 기준, 날짜의 의미, 틀린 곳 알리기
- [RSS](https://agent-jeong.github.io/backend-lab/index.xml): 새 글 받아 보기
