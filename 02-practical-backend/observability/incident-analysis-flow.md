---
title: 장애 분석 흐름
description: 장애 발생 시 영향 범위, 원인 후보, 복구 우선순위를 좁히는 절차
tags: [concept, observability]
---

# 장애 분석 흐름

장애 분석은 사용자 영향부터 확인하고, 메트릭 → 트레이스 → 로그 순서로 원인 후보를 좁혀 복구와 재발 방지까지 잇는 절차다.

원인부터 찾으려 들면 복구가 늦어진다. 먼저 영향을 줄이고, 근본 원인은 그다음에 끝까지 정리한다. 영향 범위를 모르면 우선순위와 커뮤니케이션도 흔들린다.

## 순서

1. 사용자 영향과 장애 범위를 확인한다.
2. 최근 배포, 설정 변경, 트래픽 급증, 외부 의존성 상태를 확인한다.
3. 메트릭으로 latency, error, traffic, saturation 변화를 본다.
4. 트레이스로 느리거나 실패한 구간을 찾는다.
5. 로그로 구체적인 예외와 상태를 확인한다.
6. 우회, 롤백, 차단, 스케일링 중 복구 조치를 고른다.
7. 회고에서 원인, 탐지, 대응, 예방책을 정리한다.

```text
장애 분석 순서:
1. checkout API 5xx 3% 확인
2. 특정 배포 이후 증가 확인
3. trace에서 Redis timeout span 증가 확인
4. 로그에서 cache fallback 실패 확인
5. 임시로 cache 사용 우회 후 복구
6. timeout, fallback, alert 보완
```

## 단계별 질문

| 단계 | 질문 | 확인 대상 |
|---|---|---|
| 영향 확인 | 누가 얼마나 영향받는가 | SLI, error rate, CS 문의 |
| 범위 축소 | 특정 API인가 전체인가 | endpoint, instance, region |
| 변경 확인 | 최근 무엇이 바뀌었나 | deploy, config, schema |
| 원인 후보 | 어디서 시간이 쓰이나 | trace, dependency metric |
| 복구 | 가장 빠른 완화책은 무엇인가 | rollback, feature flag, rate limit |

이 흐름은 계측이 충분할 때만 돌아간다. 복합 장애라면 가설 하나를 끝까지 파기보다 여러 가설을 나란히 본다. 조직의 대응 체계도 함께 갖춰져 있어야 한다.

## 자주 깨지는 곳

- **사용자 영향을 보기 전에 코드 원인부터 찾는다.** 분석하는 사이 장애가 길어진다.
- **최근 배포와 설정 변경을 안 본다.** 최근 변경, 의존성 장애, 자원 포화를 같이 보지 않으면 원인을 오판한다.
- **로그 한 줄로 원인을 단정한다.** 그 로그가 원인인지 결과인지 메트릭과 트레이스로 확인해야 한다.
- **복구 조치와 원인 분석을 섞는다.** 목적이 다르다. 복구는 빨리, 분석은 끝까지.
- **장애 후 계측, 알림, runbook을 보완하지 않는다.** 기록이 없으면 같은 문제가 반복된다.

## 운영에서 볼 것

- 장애 훈련에서 영향 확인부터 복구까지 흐름을 실제로 돌려 본다.
- error log와 trace id로 실패 조건을 확인한다.
- 메트릭에서 장애 시작 시점과 지표가 꺾인 지점을 찾는다.
- 트레이스에서 가장 긴 span, timeout, retry 구간을 본다.

## 면접에서 말하기

> 장애가 나면 저는 사용자 영향부터 확인합니다. 메트릭으로 범위와 시작 시점을 보고, 트레이스로 지연 구간을 좁히고, 로그로 구체적인 실패 조건을 확인합니다. 복구와 근본 원인 분석은 목적이 달라서 먼저 롤백이나 우회로 영향을 줄이고, 그 뒤 회고에서 계측, 알림, 대시보드, runbook을 보완합니다.

## 꼬리 질문

- 장애가 나면 어떤 순서로 확인하나?
- 복구와 원인 분석을 나눠야 하는 이유는?
- 장애 회고에 꼭 남겨야 할 내용은?

## 내 사례

- [[inherited-access-system-incidents|이어받은 출입 시스템의 장애 추적]]: 9일치 로그 대조로 원인 좁히기

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Google SRE Book: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/)
- [Google SRE Book: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)

## 관련 문서

- [[observability]]
- [[dashboard]]
- [[alert-and-slo]]
- [[02-practical-backend/performance/bottleneck-analysis|bottleneck-analysis]]
