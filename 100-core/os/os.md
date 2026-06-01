# OS

## 운영 방식

- 이 문서는 OS 학습 인덱스로만 사용한다.
- 상세 내용은 `100-core/os/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 프로세스, 스레드, 메모리, I/O, 장애 분석, 면접 답변을 중심으로 작성한다.

## 학습 순서

1. Process와 Thread
2. CPU Scheduling
3. Memory
4. Context Switching
5. File I/O
6. Socket I/O
7. Blocking과 Non-blocking
8. System Resource Monitoring

## 핵심 질문

- OS를 실무에서 왜 사용하는가?
- Process와 Thread는 어떤 차이가 있는가?
- I/O 대기는 서버 성능에 어떤 영향을 주는가?
- CPU, Memory, Disk, Network 병목은 어떻게 구분하는가?
- 이 주제의 핵심 동작 원리는 무엇인가?
- 실무에서 자주 발생하는 문제는 무엇인가?
- 어떤 상황에서 주의해야 하는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- OS 지식은 서버 성능 문제, 리소스 고갈, 스레드 덤프, 메모리 분석의 기반이다.
- 애플리케이션 문제처럼 보여도 실제 원인은 CPU, Memory, Disk, Network 병목일 수 있다.
- Java 서버를 이해하려면 JVM뿐 아니라 OS의 프로세스, 스레드, I/O 모델을 함께 봐야 한다.

## 관련 문서

- [[performance]]
- [[interview-questions]]
