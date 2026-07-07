---
title: Deployment Strategy
description: 서비스 중단과 변경 위험을 줄이는 배포 전략 선택 기준
---

# Deployment Strategy

## 한 줄 정의

Deployment Strategy는 새 버전을 사용자에게 어떤 순서와 범위로 노출할지 정하는 배포 방식이다.

## 실무에서 왜 문제 되는가

- 한 번에 전체 트래픽을 새 버전으로 보내면 결함 영향이 커진다.
- 무중단 배포를 기대해도 readiness나 하위 호환성이 없으면 장애가 난다.
- DB schema 변경이 포함되면 애플리케이션 버전만 되돌려도 복구되지 않을 수 있다.
- 배포 전략과 모니터링이 연결되지 않으면 잘못된 버전이 오래 유지된다.

## 실무 판단 기준

| 전략 | 적합한 상황 | 한계 |
|---|---|---|
| Rolling | 일반적인 무중단 배포 | 오류가 일부 트래픽에 노출될 수 있다 |
| Blue-Green | 빠른 전환/복구 필요 | 인프라 비용이 더 든다 |
| Canary | 영향 범위를 작게 시작 | 지표와 라우팅 제어가 필요하다 |
| Recreate | 중단 허용 가능 | 서비스 공백이 생긴다 |

## 자주 나는 실수

- 전략 이름만 정하고 검증 지표를 정하지 않는다.
- readiness 없이 rolling update를 안전하다고 생각한다.
- DB migration과 애플리케이션 배포 순서를 고려하지 않는다.
- canary 비율만 낮추고 사용자 영향 지표를 보지 않는다.

## 확인 방법

- 배포 중 error rate, latency, saturation을 확인한다.
- 새 버전과 이전 버전이 동시에 떠도 DB schema가 호환되는지 확인한다.
- rollback 또는 traffic shift 절차를 사전에 검증한다.

## 핵심 요약

배포 전략은 새 버전 노출 범위와 복구 방식을 정하는 것이다.

Rolling은 일반적이지만 readiness와 replica가 뒷받침되어야 한다.

Canary는 영향 범위를 줄이지만 지표 기반 판단이 필요하다.

Blue-Green은 빠른 전환이 가능하지만 비용이 커질 수 있다.

DB 변경은 어떤 전략에서도 별도의 하위 호환 설계가 필요하다.

## 꼬리 질문

- Rolling과 Blue-Green은 무엇이 다른가?
- Canary 배포에서 어떤 지표를 볼 것인가?
- DB 변경이 있는 배포는 왜 더 조심해야 하는가?

## 관련 문서

- [[ci-cd]]
- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
- [[rollback-strategy]]
