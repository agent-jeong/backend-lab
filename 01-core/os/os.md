---
title: 운영체제
description: 운영체제 기본기와 서버 리소스 분석 학습 인덱스
tags: [os]
comments: false
---

# 운영체제

프로세스와 스레드, 메모리, I/O, CPU 스케줄링을 다룬다. API가 느려졌을 때 코드 문제인지, CPU나 메모리, 디스크, 네트워크 같은 서버 자원이 모자란 건지 가려내는 데 초점을 둔다.

## 읽는 순서

1. [[process-and-thread|Process와 Thread]]
2. [[context-switching|Context Switching]]
3. [[memory|Memory]]
4. [[cpu-scheduling|CPU Scheduling]]
5. [[file-io|파일 입출력]]
6. [[socket-io|소켓 입출력]]
7. [[blocking-and-non-blocking|Blocking과 Non-blocking]]
8. [[system-resource-monitoring|System Resource Monitoring]]

## 먼저 답해 볼 질문

- 백엔드 개발자가 OS를 왜 알아야 하나?
- I/O 대기는 서버 성능에 어떤 영향을 주는가?
- CPU, Memory, Disk, Network 병목은 어떻게 구분하는가?
- Process와 Thread의 메모리 공유 차이는 Java 서버 동작과 어떻게 연결되는가?
- 스레드 수가 많아지면 context switching 비용이 왜 증가하는가?
- Blocking I/O와 Non-blocking I/O는 서버 스레드 사용 방식이 어떻게 다른가?
- heap memory, native memory, swap, container limit은 OOM 분석에서 어떻게 구분하는가?
- 병목을 판단할 때 CPU 사용률, run queue, load average는 각각 무엇을 알려 주는가?
- disk wait, network wait, connection backlog는 API 지연과 어떻게 연결되는가?
- 스레드 덤프, GC 로그, OS 지표를 함께 봐야 하는 상황은 언제인가?

## 실무에서 보는 것

- 서버 성능 문제, 자원 고갈, 스레드 덤프, 메모리 분석은 OS를 알아야 제대로 읽힌다.
- 애플리케이션 문제처럼 보여도 실제 원인이 CPU, Memory, Disk, Network 병목인 경우가 많다.
- Java 서버는 JVM만 봐서는 다 보이지 않는다. OS의 프로세스, 스레드, I/O 모델을 같이 봐야 왜 그렇게 도는지 이해된다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-design-cases/interview-questions|technical-questions]]
