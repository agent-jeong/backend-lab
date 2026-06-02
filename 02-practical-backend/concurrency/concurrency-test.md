---
title: 동시성 테스트와 재현
description: 단일 요청 테스트로 드러나지 않는 경쟁 조건을 재현하는 방법
---

# 동시성 테스트와 재현

## 한 줄 정의

동시성 테스트는 같은 공유 자원에 여러 요청을 동시에 보내 최종 상태와 실패 처리가 의도대로 동작하는지 검증하는 테스트다.

## 실무에서 왜 문제 되는가

- 동시성 문제는 실행 타이밍에 따라 발생하므로 일반 단위 테스트로는 잘 드러나지 않는다.
- 운영에서만 간헐적으로 발생하면 원인 추적과 재현 비용이 커진다.
- 락이나 제약 조건을 추가해도 실제로 보호되는지 검증하지 않으면 안전하다고 볼 수 없다.
- 테스트가 잘못 작성되면 동시에 실행되지 않아 거짓 안정감을 준다.

## 동작 원리

1. 같은 자원 id를 대상으로 여러 작업을 준비한다.
2. `CountDownLatch` 같은 장치로 시작 시점을 최대한 맞춘다.
3. 여러 스레드나 요청을 동시에 실행한다.
4. 모든 작업이 끝날 때까지 기다린다.
5. 성공/실패 개수와 최종 DB 상태를 검증한다.

## 실무 판단 기준

| 검증 대상 | 확인할 결과 | 이유 |
|---|---|---|
| 재고 차감 | 최종 재고, 성공 주문 수 | 음수 재고와 초과 판매를 막아야 한다 |
| 중복 발급 | 발급 row 수 | unique 제약과 예외 처리를 확인한다 |
| 낙관적 락 | 충돌 실패 수와 재시도 결과 | 충돌 처리가 의도대로 되는지 본다 |
| 비관적 락 | 대기 시간과 timeout | 락 경합 비용을 확인한다 |
| 분산 락 | 동시 실행 수 | 여러 인스턴스에서 한 번만 실행되는지 본다 |

## 자주 나는 실수

- 스레드를 여러 개 만들었지만 시작 시점이 달라 실제 동시성이 약하다.
- 테스트 후 예외만 확인하고 최종 DB 상태를 확인하지 않는다.
- 성공 요청 수와 실패 요청 수를 검증하지 않는다.
- 테스트 트랜잭션이 전체 테스트를 감싸 실제 commit/lock 동작을 가린다.
- in-memory DB로만 테스트해 실제 DB 락 동작과 차이를 놓친다.

## 확인 방법

- 테스트: 실제 DB 또는 Testcontainers 기반 DB로 동시 요청을 보낸다.
- 로그: 요청별 시작/종료 시각, 대상 자원 id, 결과를 남긴다.
- 메트릭: p95/p99 latency, lock wait, retry count를 함께 본다.
- 반복 실행: 테스트를 여러 번 반복해 간헐적 실패를 잡는다.

## 장점과 한계

| 장점 | 한계 |
|---|---|
| 운영 전에 경쟁 조건을 재현할 수 있다 | 모든 타이밍을 완전히 재현하기는 어렵다 |
| 락과 제약 조건의 효과를 검증한다 | 테스트가 느려질 수 있다 |
| 최종 상태 기반으로 안전성을 확인한다 | 실제 트래픽 패턴과 DB 설정을 반영해야 한다 |

## 짧은 예제

```java
@Test
void 동시에_재고를_차감해도_초과_판매되지_않는다() throws Exception {
    int initialStock = 10;
    int threadCount = 20;
    ExecutorService executor = Executors.newFixedThreadPool(threadCount);
    CountDownLatch ready = new CountDownLatch(threadCount);
    CountDownLatch start = new CountDownLatch(1);
    CountDownLatch done = new CountDownLatch(threadCount);
    AtomicInteger successCount = new AtomicInteger();
    AtomicInteger failureCount = new AtomicInteger();

    for (int i = 0; i < threadCount; i++) {
        executor.submit(() -> {
            ready.countDown();
            start.await();
            try {
                stockService.decrease(productId, 1);
                successCount.incrementAndGet();
            } catch (SoldOutException e) {
                failureCount.incrementAndGet();
            } finally {
                done.countDown();
            }
            return null;
        });
    }

    ready.await();
    start.countDown();
    done.await();
    executor.shutdown();

    Product product = productRepository.findById(productId).orElseThrow();
    assertThat(successCount.get()).isLessThanOrEqualTo(initialStock);
    assertThat(successCount.get() + failureCount.get()).isEqualTo(threadCount);
    assertThat(product.getStock()).isEqualTo(initialStock - successCount.get());
}
```

이 테스트는 시작 시점을 맞춰 같은 자원에 동시 접근하도록 만든다. 예제에서는 초기 재고가 `initialStock`이라고 가정한다. 실무에서는 예외 발생 여부만 보지 말고 성공 개수, 실패 개수, 최종 재고가 같은 불변식을 만족하는지 함께 검증해야 한다.

## 핵심 요약

동시성 테스트는 같은 공유 자원에 여러 요청을 동시에 보내 최종 상태를 검증한다.

핵심은 예외 발생 여부보다 업무 불변식이 깨지지 않았는지 확인하는 것이다.

`CountDownLatch`는 여러 스레드의 시작 시점을 맞추는 데 유용하다.

테스트 트랜잭션과 in-memory DB는 실제 락 동작을 가릴 수 있으므로 주의해야 한다.

중요한 동시성 기능은 성공/실패 수와 최종 DB 상태를 함께 검증한다.

## 꼬리 질문

- 동시성 테스트에서 최종 상태 검증이 중요한 이유는 무엇인가?
- 테스트 트랜잭션이 동시성 테스트를 방해할 수 있는 이유는 무엇인가?
- in-memory DB 동시성 테스트의 한계는 무엇인가?

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[race-condition-and-critical-section]]
- [[02-practical-backend/transaction/transaction|transaction]]
