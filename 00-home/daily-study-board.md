---
title: Daily Study Board
description: 매일 실무와 기술 면접을 함께 준비하기 위한 백엔드 학습 보드
---

# Daily Study Board

## 사용 방법

- 하루에 한 줄만 진행한다.
- 이미 아는 주제라도 면접 답변과 실무 체크리스트가 없으면 다시 정리한다.
- 완료한 날에는 연결 문서에 작은 개선을 남긴다.
- 실제 회사 정보는 쓰지 않고 공개 가능한 예시만 사용한다.

## 20일 기본 루트

| Day | 주제 | 오늘 남길 산출물 | 면접 질문 |
|---:|---|---|---|
| 1 | [[primitive-and-reference-types]] | `==`, `equals()`, wrapper null 실수 정리 | primitive type과 reference type의 차이는? |
| 2 | [[java]] Collection | List, Set, Map 선택 기준 | HashMap은 언제 성능이 나빠질 수 있나? |
| 3 | [[java]] JVM / GC | OOM, GC pause 확인 방법 | GC가 지연 시간에 영향을 주는 경우는? |
| 4 | [[spring]] DI / Bean | Bean 생성, 주입, scope 흐름 | DI는 왜 필요한가? |
| 5 | [[spring]] AOP / Proxy | 프록시가 적용되지 않는 경우 | `@Transactional`이 안 먹는 경우는? |
| 6 | [[jpa]] 영속성 컨텍스트 | 1차 캐시, dirty checking, flush | 영속성 컨텍스트의 장점과 주의점은? |
| 7 | [[jpa]] N+1 | 쿼리 수 확인과 fetch 전략 | N+1은 왜 발생하고 어떻게 줄이나? |
| 8 | [[database]] Index | 선택도, 복합 인덱스 순서 | 복합 인덱스 컬럼 순서는 어떻게 정하나? |
| 9 | [[database]] 실행 계획 | full scan, range scan, join 확인 | 실행 계획에서 무엇을 보나? |
| 10 | [[transaction]] Isolation / Lock | 정합성 문제와 락 경합 정리 | 격리 수준은 어떤 문제를 막나? |
| 11 | [[concurrency]] Race Condition | 동시에 들어온 요청 재현 방법 | 동시성 문제를 어떻게 재현하나? |
| 12 | [[idempotency]] Retry / Key | 중복 요청 방지 흐름 | 멱등성은 어떻게 보장하나? |
| 13 | [[performance]] Latency / Throughput | 병목 측정 순서 | 성능 문제를 어떤 순서로 분석하나? |
| 14 | [[redis]] Cache Aside / TTL | 캐시 정합성 체크리스트 | 캐시는 어떤 문제를 만들 수 있나? |
| 15 | [[network]] Timeout / Retry | timeout, retry, circuit breaker 판단 | retry는 왜 위험할 수 있나? |
| 16 | [[os]] Resource | CPU, memory, disk, network 병목 구분 | 서버 리소스 병목을 어떻게 확인하나? |
| 17 | [[testing]] Unit / Integration | 테스트 범위 선택 기준 | 단위 테스트와 통합 테스트를 어떻게 나누나? |
| 18 | [[observability]] Log / Metric / Trace | 장애 분석 순서 | 로그, 메트릭, 트레이스는 각각 무엇을 보나? |
| 19 | [[ci-cd]] Rollback | 배포 실패 대응 절차 | 배포 실패 시 어떻게 되돌리나? |
| 20 | [[case-studies]] | 하나의 사례를 문제-원인-해결로 정리 | 프로젝트 경험을 어떻게 기술적으로 설명하나? |

## 매일 체크리스트

- 문제 상황을 먼저 썼는가?
- 원인을 확인하는 방법을 썼는가?
- 해결책의 한계나 부작용을 썼는가?
- 면접 답변 1분 버전으로 줄였는가?
- 관련 문서 링크를 1개 이상 연결했는가?
