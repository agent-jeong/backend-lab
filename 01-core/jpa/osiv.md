---
title: OSIV (Open Session In View)
description: OSIV의 동작 원리, Spring Boot 기본값, 실무에서 끄는 판단 기준
tags: [concept, jpa]
---

# OSIV (Open Session In View)

OSIV는 영속성 컨텍스트(EntityManager)의 생명주기를 트랜잭션이 아니라 HTTP 요청 전체로 늘려서, 컨트롤러나 뷰 렌더링에서도 지연 로딩이 되게 하는 설정이다.

Spring Boot에서는 **기본값이 `true`**라서 모르면 켜진 채로 운영한다. 컨트롤러에서 지연 로딩이 편하게 되는 대가로 DB 커넥션을 응답이 끝날 때까지 잡고 있고, 트래픽이 늘면 커넥션 풀이 고갈되어 갑자기 장애가 난다.

## 동작

### OSIV ON (기본값)

```
HTTP 요청 시작 ──────────────────────────────── HTTP 응답 완료
│                                                │
│  EntityManager 생성 ────────────────────────── EntityManager 종료
│  │                                          │  │
│  │  트랜잭션 시작 ── 트랜잭션 종료          │  │
│  │  │  Service 로직  │                      │  │
│  │  └────────────────┘                      │  │
│  │                                          │  │
│  │  Controller에서 지연 로딩 가능 ──────────│  │
│  │  (트랜잭션 밖, 읽기 전용)                │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  ⚠️ DB 커넥션을 요청 끝까지 점유               │
└────────────────────────────────────────────────┘
```

- 영속성 컨텍스트가 HTTP 요청 전체 동안 살아 있다. 트랜잭션이 끝나도 유지된다.
- 컨트롤러와 뷰에서 지연 로딩이 된다(읽기 전용 쿼리 실행).
- DB 커넥션을 응답이 끝날 때까지 반환하지 않는다.

### OSIV OFF

```
HTTP 요청 시작 ──────────────────────────────── HTTP 응답 완료
│                                                │
│  트랜잭션 시작 ── 트랜잭션 종료                │
│  │  EntityManager 생성 ── EntityManager 종료│  │
│  │  │  Service 로직  │                      │  │
│  │  └────────────────┘                      │  │
│  └──────────────────────────────────────────┘  │
│                                                │
│  Controller에서 지연 로딩 ❌                    │
│  (LazyInitializationException 발생)            │
└────────────────────────────────────────────────┘
```

- 영속성 컨텍스트가 트랜잭션과 함께 종료된다.
- DB 커넥션을 트랜잭션이 끝나는 즉시 반환한다.
- 컨트롤러에서 지연 로딩하면 `LazyInitializationException`이 난다.

## 설정

```yaml
# application.yml
spring:
  jpa:
    open-in-view: false  # OSIV 비활성화 (기본값: true)
```

OSIV가 켜진 채로 Spring Boot를 띄우면 경고 로그가 나온다.
```
WARN: spring.jpa.open-in-view is enabled by default. Therefore, database queries may be performed during view rendering.
```

## 끌지 말지

| 상황 | 선택 | 이유 |
|---|---|---|
| 트래픽이 적고 빠르게 개발해야 할 때 | OSIV ON | 편의성 우선 |
| 트래픽이 많고 커넥션 풀이 중요한 서비스 | OSIV OFF | 커넥션 점유 시간 최소화 |
| API 서버 (뷰 렌더링 없음) | OSIV OFF | 지연 로딩 편의가 필요 없음 |
| 외부 API 호출이 응답에 포함되는 경우 | OSIV OFF | 외부 대기 중에도 커넥션을 점유하면 위험 |

## 끈 뒤에 할 일

OSIV를 끄면 `LazyInitializationException`이 나는 곳이 생기므로 코드 구조를 바꿔야 한다. 원칙은 Service 계층의 트랜잭션 안에서 필요한 데이터를 다 로딩하는 것이다.

| 전략 | 방법 |
|---|---|
| Fetch Join | `@Query`에서 `JOIN FETCH`로 필요한 연관 엔티티를 한 번에 로딩 |
| DTO 조회 | Service에서 필요한 데이터만 DTO로 변환해서 반환 |
| @EntityGraph | 특정 조회에서 EAGER로 가져올 연관 관계 지정 |
| batch size | `default_batch_fetch_size` 설정으로 IN 쿼리로 일괄 로딩 |

```java
// OSIV OFF 환경에서의 Service 설계
@Service
@Transactional(readOnly = true)
public class OrderService {

    public OrderDetailResponse getOrderDetail(Long orderId) {
        // 트랜잭션 안에서 필요한 데이터를 모두 로딩
        Order order = orderRepository.findWithItemsAndUser(orderId);

        // DTO로 변환하여 반환 (트랜잭션 밖에서 엔티티 접근 불필요)
        return OrderDetailResponse.from(order);
    }
}
```

## 자주 깨지는 곳

- **OSIV가 기본으로 켜져 있는 걸 모른다.** 개발 환경에서는 커넥션이 남아돌다가 운영 트래픽에서 갑자기 장애가 난다.
- **예외가 난 곳을 전부 EAGER로 바꿔서 막는다.** N+1이 생긴다.
- **Service가 엔티티를 그대로 컨트롤러에 넘긴다.** 직렬화 시점에 지연 로딩이 일어난다.

## 한 번에 설명하기

> OSIV는 영속성 컨텍스트를 HTTP 요청 전체로 늘리는 설정이고 Spring Boot 기본값은 `true`입니다. 켜 두면 컨트롤러에서도 지연 로딩이 되지만 DB 커넥션을 응답이 끝날 때까지 잡고 있어서, 트래픽이 많은 서비스에서는 커넥션 풀 고갈을 막으려고 끕니다. 끈 뒤에는 Service 트랜잭션 안에서 fetch join이나 batch size로 필요한 데이터를 다 읽고 DTO로 바꿔서 반환합니다.

## 꼬리 질문

> [!question]- OSIV를 켜면 왜 커넥션 풀이 고갈되는가?
> 영속성 컨텍스트가 요청 끝까지 유지되면서 DB 커넥션도 함께 점유합니다. 외부 API 호출이나 뷰 렌더링이 느리면 그 시간 동안 커넥션이 묶여 있어서 다른 요청이 커넥션을 얻지 못합니다.

> [!question]- OSIV를 끄면 LazyInitializationException이 나는 이유는?
> 트랜잭션이 끝나면 영속성 컨텍스트도 종료됩니다. 이후 엔티티의 지연 로딩 프록시에 접근하면 세션이 없어서 예외가 발생합니다.

> [!question]- OSIV OFF에서 지연 로딩 문제를 해결하는 방법은?
> Fetch Join, DTO 조회, @EntityGraph, batch_fetch_size 설정 등으로 Service 계층에서 필요한 데이터를 미리 로딩합니다. 엔티티 대신 DTO를 컨트롤러에 반환하는 것이 근본적인 해결입니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>OSIV를 켰을 때 커넥션 풀이 고갈될 수 있는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="요청 처리 후 view/response 단계까지 영속성 컨텍스트와 DB 커넥션 점유 시간이 길어질 수 있기 때문이다." aria-pressed="false">A. 요청 끝부분까지 커넥션 점유 시간이 길어질 수 있기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="OSIV가 커넥션 풀 크기를 자동으로 늘리지 않는다." aria-pressed="false">B. OSIV가 커넥션을 무한히 생성하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="OSIV는 브라우저 캐시 기능이 아니다." aria-pressed="false">C. 브라우저가 DB 커넥션을 직접 열기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>OSIV를 끄면 Controller/Serializer 계층에서 lazy 연관을 접근할 때 LazyInitializationException이 발생할 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="서비스 트랜잭션 안에서 필요한 데이터를 fetch join, DTO projection 등으로 미리 조회해야 한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="OSIV OFF에서는 영속성 컨텍스트 범위가 짧아져 지연 로딩 접근 위치를 명확히 해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>OSIV를 끈 상태에서 지연 로딩 문제를 푸는 방법은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="서비스 계층에서 필요한 조회 범위를 명확히 하고 fetch join, batch size, DTO projection 등을 사용한다." aria-pressed="false">A. 트랜잭션 안에서 필요한 데이터를 명시적으로 조회한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="모든 연관관계를 EAGER로 바꾸면 성능 문제가 더 커질 수 있다." aria-pressed="false">B. 모든 연관관계를 EAGER로 바꾼다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="예외를 삼키면 응답 데이터가 불완전해지고 원인 파악이 어렵다." aria-pressed="false">C. LazyInitializationException을 빈 catch로 무시한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Spring Boot: Open EntityManager in View](https://docs.spring.io/spring-boot/reference/data/sql.html)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[lazy-and-eager-loading]]
- [[n-plus-one-and-fetch-join]]
- [[transaction-and-flush]]