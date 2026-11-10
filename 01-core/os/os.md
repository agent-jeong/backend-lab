---
title: 운영체제
description: 운영체제 기본기와 서버 리소스 분석 학습 인덱스
comments: false
---

# 운영체제

> 학습 인덱스다. 상세 내용은 `01-core/os/` 아래 개념 문서에 둔다.
> 초점: 프로세스·스레드, 메모리, I/O, 장애 분석. 증상·원인·확인 방법 → 해결책의 장점과 한계 → 꼬리 질문 순으로 쓰고, 아직 학습하지 않은 내용은 미리 채우지 않는다.

## 학습 순서

1. [[process-and-thread|Process와 Thread]]
2. [[context-switching|Context Switching]]
3. [[memory|Memory]]
4. [[cpu-scheduling|CPU Scheduling]]
5. [[file-io|File I/O]]
6. [[socket-io|Socket I/O]]
7. [[blocking-and-non-blocking|Blocking과 Non-blocking]]
8. [[system-resource-monitoring|System Resource Monitoring]]

## 핵심 질문

- 백엔드 개발자가 OS를 왜 알아야 하나?
- I/O 대기는 서버 성능에 어떤 영향을 주는가?
- CPU, Memory, Disk, Network 병목은 어떻게 구분하는가?
- Process와 Thread의 메모리 공유 차이는 Java 서버 동작과 어떻게 연결되는가?
- 스레드 수가 많아지면 context switching 비용이 왜 증가하는가?
- Blocking I/O와 Non-blocking I/O는 서버 스레드 사용 방식이 어떻게 다른가?
- heap memory, native memory, swap, container limit은 OOM 분석에서 어떻게 구분하는가?
- CPU 사용률, run queue, load average는 병목 판단에 어떤 의미가 있는가?
- disk wait, network wait, connection backlog는 API 지연과 어떻게 연결되는가?
- 스레드 덤프, GC 로그, OS 지표를 함께 봐야 하는 상황은 언제인가?

## 실무에서 보는 것

- 서버 성능 문제, 리소스 고갈, 스레드 덤프, 메모리 분석은 전부 OS 지식 위에서 읽힌다.
- 애플리케이션 문제처럼 보여도 실제 원인이 CPU, Memory, Disk, Network 병목인 경우가 많다.
- Java 서버는 JVM만 봐서는 안 보이고, OS의 프로세스, 스레드, I/O 모델을 같이 봐야 이해된다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview-cases/interview-questions|technical-questions]]
