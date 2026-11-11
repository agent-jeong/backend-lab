---
title: 동시성 테스트와 재현
description: 요청을 하나씩 보내는 테스트로는 안 보이는 경쟁 조건을 일부러 재현하는 방법
tags: [concept, concurrency]
---

# 동시성 테스트와 재현

동시성 테스트는 같은 자원에 여러 요청을 한꺼번에 보내고, 끝난 뒤의 상태와 실패 처리가 의도대로인지 확인하는 테스트다.

동시성 문제는 요청이 어떤 타이밍에 겹치느냐에 따라 생겨서 평범한 단위 테스트로는 잘 잡히지 않는다. 운영에서 가끔씩 재고가 음수가 되는 식으로 터지면, 원인을 찾고 재현하는 데 시간이 많이 든다. 락이나 제약 조건을 넣었더라도 테스트로 실제로 막히는 걸 보기 전까지는 안전하다고 말할 수 없다.

## 동작

1. 같은 자원 id를 대상으로 여러 작업을 준비한다.
2. `CountDownLatch` 같은 도구로 시작 시점을 최대한 맞춘다.
3. 여러 스레드나 요청을 동시에 실행한다.
4. 모든 작업이 끝날 때까지 기다린다.
5. 성공 개수, 실패 개수, 최종 DB 상태를 확인한다.

```java
@Test
void 동시에_재고를_차감해도_초과_판매되지_않는다() throws Exception {
    int initialStock = 10;
    int threadCount = 20;
    Long productId = productRepository.save(Product.withStock(initialStock)).getId();
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

시작 시점을 맞춰서 모든 스레드가 같은 재고에 동시에 달려들게 만든 테스트다. 재고가 `initialStock`인 상품을 먼저 저장해 두고 시작한다. 예외가 났는지만 보지 말고, 성공 개수와 실패 개수와 최종 재고가 서로 맞는지 같이 확인한다.

## 무엇을 검증하나

| 검증 대상 | 확인할 결과 | 이유 |
|---|---|---|
| 재고 차감 | 최종 재고, 성공 주문 수 | 음수 재고와 초과 판매를 막아야 한다 |
| 중복 발급 | 발급 row 수 | unique 제약과 예외 처리를 확인한다 |
| 낙관적 락 | 충돌 실패 수와 재시도 결과 | 충돌 처리가 의도대로 되는지 본다 |
| 비관적 락 | 대기 시간과 timeout | 락 경합 비용을 확인한다 |
| 분산 락 | 동시 실행 수 | 여러 인스턴스에서 한 번만 실행되는지 본다 |

## 자주 깨지는 곳

- 시작 시점을 맞추지 않으면, 스레드는 여러 개여도 실제로는 거의 하나씩 돌아서 문제가 없는 것처럼 보인다.
- 예외만 보고 최종 DB 상태를 안 보면, 그리고 성공과 실패 요청 수도 확인하지 않으면, 재고가 틀어져도 테스트가 통과한다.
- 테스트 트랜잭션이 테스트 전체를 감싸면, 실제 commit과 락이 어떻게 걸리는지 가려진다.
- in-memory DB로만 테스트하면, 실제 DB와 락 동작이 달라서 놓치는 게 생긴다. 실제 DB나 Testcontainers로 띄운 DB로 돌린다.
- 한 번 통과했다고 끝내면 가끔씩만 나는 실패를 놓친다. 모든 타이밍을 재현할 수는 없으니 여러 번 반복해 돌린다. 그만큼 테스트는 느려진다.
- 트래픽 모양이나 DB 설정이 운영과 많이 다르면, 테스트 결과도 운영과 다르게 나온다.

## 운영에서 볼 것

- 요청마다 시작과 끝 시각, 대상 자원 id, 결과를 로그로 남긴다.
- p95/p99 latency, lock wait, 재시도 횟수를 함께 본다.

## 한 번에 설명하기

> 동시성 테스트는 같은 자원에 여러 요청을 한꺼번에 보내고, 끝난 뒤 데이터가 맞는지 확인하는 테스트입니다.
>
> 저는 `CountDownLatch`로 시작 시점을 맞추고, 예외가 났는지보다 성공 수, 실패 수, 최종 재고가 서로 맞는지를 봅니다.
>
> 테스트 트랜잭션이나 in-memory DB는 실제 락 동작을 가리기 때문에 실제 DB나 Testcontainers로 돌립니다. 그리고 여러 번 반복해서 가끔씩만 나는 실패까지 잡습니다.

## 꼬리 질문

- 동시성 테스트에서 최종 상태를 꼭 확인해야 하는 이유는?
- 테스트 트랜잭션이 동시성 테스트를 방해하는 이유는?
- in-memory DB로 동시성을 테스트하면 무엇을 놓치나?

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: CountDownLatch](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CountDownLatch.html)
- [Testcontainers for Java](https://java.testcontainers.org/)

## 관련 문서

- [[02-practical-backend/concurrency/concurrency|concurrency]]
- [[race-condition-and-critical-section]]
- [[02-practical-backend/transaction/transaction|transaction]]
