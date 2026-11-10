---
title: CI/CD
description: 반복 가능하고 되돌릴 수 있는 배포 학습 인덱스
comments: false
---

# CI/CD

> 학습 인덱스다. 상세 내용은 `02-practical-backend/ci-cd/` 아래 개념 문서에 둔다.
> 개념 문서는 빌드, 테스트, 배포, 롤백을 다루고, 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓴다. 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[ci-vs-cd|CI와 CD의 차이]]
2. [[build-pipeline|Build Pipeline]]
3. Test Automation
4. [[deployment-strategy|Deployment Strategy]]
5. [[rollback-strategy|Rollback]]
6. [[config-and-secret-management|환경 변수와 Secret 관리]]
7. [[gitops|GitOps]]

## 핵심 질문

- CI와 CD는 각각 무엇을 자동화하고, 어디까지 사람이 승인해야 하는가?
- 같은 커밋을 다시 빌드했을 때 다른 결과물이 나오면 무엇이 문제인가?
- rolling, blue-green, canary 배포는 롤백 속도와 비용에서 어떻게 다른가?
- DB 스키마 변경이 포함된 배포는 왜 애플리케이션 롤백만으로 되돌릴 수 없는가?
- 환경 변수와 secret은 어디에 두고, 누가 바꿀 수 있어야 하는가?

## 실무에서 보는 것

- 빨리 배포하는 것보다 같은 결과를 반복할 수 있고 되돌릴 수 있는 배포가 먼저다.
- 배포 자동화는 테스트, 설정, 권한, 롤백 전략까지 같이 설계해야 끝난다.
- 면접에서는 파이프라인 단계와 각 단계가 실패했을 때의 대응을 말한다.

## 관련 문서

- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
- [[02-practical-backend/kubernetes/configmap-and-secret|configmap-and-secret]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-interview-cases/interview-questions|technical-questions]]
