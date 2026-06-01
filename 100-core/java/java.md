# Java

## 운영 방식

- 이 문서는 Java Core 학습 인덱스로만 사용한다.
- 상세 내용은 `100-core/java/` 아래 개념별 문서로 나눈다.
- 하루에 학습한 내용만 하나의 작은 문서에 정리한다.
- 아직 학습하지 않은 내용을 미리 길게 채우지 않는다.
- 각 개념 문서는 한 줄 정의, 동작 원리, 실무 주의점, 면접 답변을 중심으로 작성한다.

## 학습 순서

1. Java 언어 기본기
   - primitive type과 reference type
   - class, interface, enum, record
   - equals / hashCode / toString
   - exception 처리
2. Java 컬렉션
   - List, Set, Map의 차이
   - HashMap 동작 원리
   - 정렬, 중복 제거, 탐색 비용
3. Java 버전별 핵심 변화
   - Java 8: lambda, Stream, Optional
   - Java 11: LTS 기준 변화와 실무 사용성
   - Java 17: record, sealed class, pattern matching 기반
   - Java 21: virtual thread와 동시성 모델 변화
4. JVM 기본 구조
   - class loading
   - runtime data area
   - stack과 heap
   - JIT compiler
5. GC
   - GC가 필요한 이유
   - young / old generation
   - stop-the-world
   - G1 GC와 실무 튜닝 관점
6. 실무 연결
   - 메모리 누수
   - OOM
   - 과도한 객체 생성
   - Stream 남용
   - 동시성 문제

## 핵심 질문

- Java를 실무에서 왜 사용하는가?
- Java 언어 기능은 어떤 문제를 줄이기 위해 발전해 왔는가?
- JVM은 Java 코드를 어떻게 실행하는가?
- GC는 언제 성능 문제가 되는가?
- 이 주제의 핵심 동작 원리는 무엇인가?
- 실무에서 자주 발생하는 문제는 무엇인가?
- 어떤 상황에서 주의해야 하는가?
- 면접에서는 어떻게 설명할 수 있는가?

## 실무 관점

- Java는 문법보다 JVM, 메모리, 컬렉션, 동시성 이해가 실무 품질에 더 큰 영향을 준다.
- 버전별 기능은 단순 암기보다 "어떤 코드를 더 안전하고 읽기 쉽게 만드는가"로 정리한다.
- GC는 대부분 기본 설정으로 충분하지만, 지연 시간, 처리량, 메모리 사용량 문제가 생기면 원리를 알아야 분석할 수 있다.
- Spring, JPA, 동시성, 성능 문제는 Java Core 이해 부족에서 시작되는 경우가 많다.

## 관련 문서

- [[primitive-and-reference-types]]
- [[performance]]
- [[concurrency]]
- [[interview-questions]]
