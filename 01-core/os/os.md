---
title: OS
description: 운영체제 기본기와 서버 리소스 분석 학습 인덱스
comments: false
---

# OS

## 운영 방식

- 이 문서는 OS 학습 인덱스로만 사용한다.
- 상세 내용은 `01-core/os/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 프로세스, 스레드, 메모리, I/O, 장애 분석, 면접 답변을 중심으로 작성한다.

## 오늘 남길 것

- 오늘 다룰 개념 또는 문제 상황 하나를 고른다.
- 실제 개발자가 마주치는 증상, 원인, 확인 방법을 먼저 쓴다.
- 해결책은 장점과 한계를 같이 적는다.
- 마지막에 핵심 요약과 꼬리 질문을 남긴다.

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

- OS를 실무에서 왜 사용하는가?
- Process와 Thread는 어떤 차이가 있는가?
- I/O 대기는 서버 성능에 어떤 영향을 주는가?
- CPU, Memory, Disk, Network 병목은 어떻게 구분하는가?
- 이 주제의 핵심 동작 원리는 무엇인가?
- 실무에서 자주 발생하는 문제는 무엇인가?
- 어떤 상황에서 주의해야 하는가?
- 면접에서는 어떻게 설명할 수 있는가?
- Process와 Thread의 메모리 공유 차이는 Java 서버 동작과 어떻게 연결되는가?
- 스레드 수가 많아지면 context switching 비용이 왜 증가하는가?
- Blocking I/O와 Non-blocking I/O는 서버 스레드 사용 방식이 어떻게 다른가?
- heap memory, native memory, swap, container limit은 OOM 분석에서 어떻게 구분하는가?
- CPU 사용률, run queue, load average는 병목 판단에 어떤 의미가 있는가?
- disk wait, network wait, connection backlog는 API 지연과 어떻게 연결되는가?
- 스레드 덤프, GC 로그, OS 지표를 함께 봐야 하는 상황은 언제인가?

## 실무 관점

- OS 지식은 서버 성능 문제, 리소스 고갈, 스레드 덤프, 메모리 분석의 기반이다.
- 애플리케이션 문제처럼 보여도 실제 원인은 CPU, Memory, Disk, Network 병목일 수 있다.
- Java 서버를 이해하려면 JVM뿐 아니라 OS의 프로세스, 스레드, I/O 모델을 함께 봐야 한다.

## 관련 문서

- [[02-practical-backend/performance/performance|performance]]
- [[04-interview/interview-questions|interview-questions]]
