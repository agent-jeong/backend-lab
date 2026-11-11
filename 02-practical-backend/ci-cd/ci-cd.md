---
title: CI/CD
description: 같은 결과를 반복해서 배포하고, 잘못되면 되돌리는 법을 모은 노트
tags: [ci-cd]
comments: false
---

# CI/CD

빌드 파이프라인, 배포 전략, 롤백, 설정과 비밀값, GitOps를 다룬다. 잘못된 배포를 빨리 알아채고 되돌리는 법을 주로 이야기한다.

## 읽는 순서

1. [[ci-vs-cd|CI와 CD의 차이]]
2. [[build-pipeline|Build Pipeline]]
3. Test Automation
4. [[deployment-strategy|Deployment Strategy]]
5. [[rollback-strategy|Rollback]]
6. [[config-and-secret-management|환경 변수와 Secret 관리]]
7. [[gitops|GitOps]]

## 먼저 답해 볼 질문

- CI와 CD는 각각 무엇을 자동화하고, 어디까지 사람이 승인해야 하는가?
- 같은 커밋을 다시 빌드했는데 다른 결과물이 나오면 무엇이 잘못된 것인가?
- rolling, blue-green, canary 배포는 되돌리는 속도와 비용이 어떻게 다른가?
- DB 스키마 변경이 들어간 배포는 왜 애플리케이션 롤백만으로 되돌릴 수 없는가?
- 환경 변수와 secret은 어디에 두고, 누가 바꿀 수 있어야 하는가?

## 실무에서 보는 것

- 빨리 배포하는 것보다, 같은 결과를 반복해서 낼 수 있고 되돌릴 수 있는 배포가 먼저다.
- 배포 자동화는 테스트, 설정, 권한, 롤백 방법까지 같이 갖춰야 끝난다.
- 면접에서는 파이프라인 단계와, 각 단계가 실패했을 때 어떻게 대응하는지를 말한다.

## 관련 문서

- [[02-practical-backend/kubernetes/rolling-update-and-rollback|rolling-update-and-rollback]]
- [[02-practical-backend/kubernetes/configmap-and-secret|configmap-and-secret]]
- [[03-work-cases/work-cases|work-cases]]
- [[04-design-cases/interview-questions|technical-questions]]
