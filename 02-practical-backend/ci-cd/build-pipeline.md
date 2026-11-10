---
title: 빌드 파이프라인
description: 소스 변경을 검증 가능한 artifact로 만드는 단계
tags: [concept, ci-cd]
---

# 빌드 파이프라인

Build Pipeline은 소스 코드를 가져와 정적 검증, 테스트, 빌드, 이미지 생성, artifact 저장까지 매번 같은 단계로 돌리는 흐름이다.

배포 대상은 소스가 아니라 이 파이프라인을 통과한 artifact다. 로컬에서만 빌드되는 코드는 팀과 CI에서 재현되지 않고, artifact가 commit과 이어지지 않으면 무엇이 배포됐는지 알 수 없다.

## 단계별로 볼 것

| 단계 | 확인할 것 |
|---|---|
| Checkout | 정확한 commit 기준인지 |
| Dependency | lockfile 또는 버전 고정 여부 |
| Test | 단위/통합 테스트 범위 |
| Build | 재현 가능한 artifact 생성 |
| Image | tag, digest, 취약점 스캔 |
| Publish | artifact 저장소와 권한 |

테스트, 정적 분석, 이미지 생성, artifact 저장은 단계를 나눠 둔다. 그래야 어디서 실패했는지 바로 보인다.

## 자주 깨지는 곳

- **latest tag만 쓴다.** 어떤 버전이 배포됐는지 추적할 수 없다.
- **테스트 실패를 임시로 skip하고 배포한다.** 배포 전에 잡을 결함을 운영에서 만난다.
- **빌드 시점 secret을 이미지에 남긴다.** build log나 image layer에서 그대로 읽힌다.
- **CI cache에 기대 빌드한다.** 깨끗한 환경에서는 빌드가 안 되는 상태를 모르고 지나간다.

## 운영에서 볼 것

- 같은 commit에서 같은 artifact가 나오는지 확인한다.
- artifact tag와 commit SHA가 연결되는지 확인한다.
- build log에 secret이나 민감 값이 찍히지 않는지 확인한다.

## 면접에서 말하기

> Build Pipeline은 변경을 검증된 artifact로 만드는 과정입니다. 저는 테스트, 정적 분석, 이미지 생성, 저장 단계를 나누고, 결과물이 commit SHA와 이어지게 해서 무엇이 배포됐는지 추적합니다. secret은 build log와 image layer에 남지 않게 하고, 배포는 소스가 아니라 이렇게 검증된 artifact로 합니다.

## 꼬리 질문

- Build Pipeline에 꼭 있어야 하는 단계는?
- latest tag만 쓰면 어떤 문제가 생기나?
- 빌드 과정에서 secret 노출을 어떻게 막나?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 관련 문서

- [[ci-cd]]
- [[ci-vs-cd]]
- [[02-practical-backend/security/sensitive-data-logging|sensitive-data-logging]]
