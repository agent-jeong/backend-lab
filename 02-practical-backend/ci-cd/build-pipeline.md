---
title: Build Pipeline
description: 소스 변경을 검증 가능한 artifact로 만드는 단계
---

# Build Pipeline

## 한 줄 정의

Build Pipeline은 소스 코드를 가져와 정적 검증, 테스트, 빌드, 이미지 생성, artifact 저장까지 반복 가능한 단계로 구성한 흐름이다.

## 실무에서 왜 문제 되는가

- 로컬에서만 빌드되는 코드는 팀과 CI 환경에서 재현성이 낮다.
- 테스트와 정적 검증이 없으면 배포 전 결함을 놓친다.
- artifact를 매번 새로 만들지 않거나 추적하지 않으면 어떤 코드가 배포됐는지 알기 어렵다.
- secret을 build log나 image layer에 남길 수 있다.

## 실무 판단 기준

| 단계 | 확인할 것 |
|---|---|
| Checkout | 정확한 commit 기준인지 |
| Dependency | lockfile 또는 버전 고정 여부 |
| Test | 단위/통합 테스트 범위 |
| Build | 재현 가능한 artifact 생성 |
| Image | tag, digest, 취약점 스캔 |
| Publish | artifact 저장소와 권한 |

## 자주 나는 실수

- latest tag만 사용해 배포 버전을 추적하지 못한다.
- 테스트 실패를 임시로 skip하고 배포한다.
- 빌드 시점 secret을 이미지에 남긴다.
- CI cache 문제로 깨끗한 환경에서 빌드되지 않는다.

## 확인 방법

- 같은 commit에서 같은 artifact가 생성되는지 확인한다.
- artifact tag와 commit SHA가 연결되는지 확인한다.
- build log에 secret이나 민감 값이 노출되지 않는지 확인한다.

## 핵심 요약

Build Pipeline은 변경을 검증 가능한 artifact로 만드는 과정이다.

빌드 결과는 commit과 추적 가능해야 한다.

테스트, 정적 분석, 이미지 생성, artifact 저장이 명확히 분리되어야 한다.

secret은 build log와 image layer에 남지 않게 해야 한다.

배포는 소스가 아니라 검증된 artifact를 대상으로 해야 한다.

## 꼬리 질문

- Build Pipeline의 필수 단계는 무엇인가?
- latest tag만 쓰면 어떤 문제가 생기는가?
- 빌드 과정에서 secret 노출을 어떻게 막을 것인가?

## 관련 문서

- [[ci-cd]]
- [[ci-vs-cd]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
