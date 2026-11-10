---
title: 동시성 테스트와 재현
description: 단일 요청 테스트로 드러나지 않는 경쟁 조건을 재현하는 방법
tags: [concept, concurrency]
---

# 동시성 테스트와 재현

동시성 테스트는 같은 공유 자원에 여러 요청을 동시에 보내, 최종 상태와 실패 처리가 의도대로인지 검증하는 테스트다.

동시성 문제는 실행 타이밍에 따라 생겨서 일반 단위 테스트로는 잘 드러나지 않는다. 운영에서 간헐적으로 터지면 원인 추적과 재현에 비용이 크게 든다. 락이나 제약 조건을 넣었다면 실제로 막히는지 테스트로 확인하기 전까지는 안전하다고 볼 수 없다.

## 동작

1. 같은 자원 id를 대상으로 여러 작업을 준비한다.
2. `CountDownLatch` 같은 장치로 시작 시점을 최대한 맞춘다.
3. 여러 스레드나 요청을 동시에 실행한다.
4. 모든 작업이 끝날 때까지 기다린다.
5. 성공/실패 개수와 최종 DB 상태를 검증한다.

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

시작 시점을 맞춰 같은 자원에 동시에 접근하게 만든 테스트다. 초기 재고는 `initialStock`이라고 가정한다. 예외가 났는지만 보지 말고 성공 개수, 실패 개수, 최종 재고가 같은 불변식을 만족하는지 함께 검증한다.

## 무엇을 검증하나

| 검증 대상 | 확인할 결과 | 이유 |
|---|---|---|
| 재고 차감 | 최종 재고, 성공 주문 수 | 음수 재고와 초과 판매를 막아야 한다 |
| 중복 발급 | 발급 row 수 | unique 제약과 예외 처리를 확인한다 |
| 낙관적 락 | 충돌 실패 수와 재시도 결과 | 충돌 처리가 의도대로 되는지 본다 |
| 비관적 락 | 대기 시간과 timeout | 락 경합 비용을 확인한다 |
| 분산 락 | 동시 실행 수 | 여러 인스턴스에서 한 번만 실행되는지 본다 |

## 자주 깨지는 곳

- **시작 시점을 맞추지 않는다.** 스레드는 여러 개인데 실제로는 거의 순차 실행이 되어 거짓 안정감을 준다.
- **예외만 보고 최종 DB 상태를 안 본다.** 성공·실패 요청 수도 검증하지 않으면 불변식이 깨져도 테스트가 통과한다.
- **테스트 트랜잭션이 전체 테스트를 감싼다.** 실제 commit과 lock 동작이 가려진다.
- **in-memory DB로만 테스트한다.** 실제 DB의 락 동작과 차이를 놓친다. 실제 DB나 Testcontainers 기반 DB로 돌린다.
- **한 번 통과로 끝낸다.** 모든 타이밍을 재현할 수는 없으니 여러 번 반복 실행해 간헐적 실패를 잡는다. 테스트는 그만큼 느려진다.
- **실제 조건과 동떨어진다.** 트래픽 패턴과 DB 설정이 운영과 다르면 결과도 다르다.

## 운영에서 볼 것

- 요청별 시작/종료 시각, 대상 자원 id, 결과를 로그로 남긴다.
- p95/p99 latency, lock wait, retry count를 함께 본다.

## 한 번에 설명하기

> 동시성 테스트는 같은 자원에 여러 요청을 동시에 보내고 최종 상태를 검증하는 테스트입니다. 저는 `CountDownLatch`로 시작 시점을 맞추고, 예외가 났는지보다 성공 수·실패 수·최종 재고가 불변식을 지키는지를 봅니다. 테스트 트랜잭션이나 in-memory DB는 실제 락 동작을 가리기 때문에 실제 DB나 Testcontainers로 돌리고, 여러 번 반복해서 간헐적 실패를 잡습니다.

## 꼬리 질문

- 동시성 테스트에서 최종 상태 검증이 중요한 이유는 무엇인가?
- 테스트 트랜잭션이 동시성 테스트를 방해할 수 있는 이유는 무엇인가?
- in-memory DB 동시성 테스트의 한계는 무엇인가?

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Java SE 21 API: CountDownLatch](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CountDownLatch.html)
- [Testcontainers for Java](https://java.testcontainers.org/)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[race-condition-and-critical-section]]
- [[02-practical-backend/transaction/transaction|transaction]]
