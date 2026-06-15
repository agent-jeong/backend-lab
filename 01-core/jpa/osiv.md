---
title: OSIV (Open Session In View)
description: OSIV의 동작 원리, Spring Boot 기본값, 실무에서 끄는 판단 기준
---

# OSIV (Open Session In View)

## 한 줄 정의

OSIV는 영속성 컨텍스트(EntityManager)의 생명주기를 트랜잭션이 아닌 HTTP 요청 전체로 확장하여, 뷰 렌더링이나 컨트롤러에서도 지연 로딩을 가능하게 하는 설정이다.

## 실무에서 왜 문제 되는가

- Spring Boot에서 **기본값이 `true`**이므로 모르면 의도치 않게 켜져 있다.
- DB 커넥션을 요청 끝까지 점유해서 커넥션 풀 고갈로 이어질 수 있다.
- 컨트롤러에서 지연 로딩이 "편하게" 동작하지만, 트래픽이 많아지면 갑자기 장애가 난다.
- OSIV를 끄면 `LazyInitializationException`이 발생해서 코드 구조 변경이 필요하다.

## 동작 원리

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

- 영속성 컨텍스트가 HTTP 요청 전체 동안 살아있다.
- 트랜잭션이 끝나도 영속성 컨텍스트는 유지된다.
- 컨트롤러, 뷰에서 지연 로딩이 가능하다 (읽기 전용 쿼리 실행).
- **DB 커넥션을 응답 완료까지 반환하지 않는다.**

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
- **DB 커넥션을 트랜잭션 종료 시 바로 반환**한다.
- 컨트롤러에서 지연 로딩하면 `LazyInitializationException` 발생.

## 설정 방법

```yaml
# application.yml
spring:
  jpa:
    open-in-view: false  # OSIV 비활성화 (기본값: true)
```

Spring Boot 시작 시 OSIV가 켜져 있으면 경고 로그가 출력된다:
```
WARN: spring.jpa.open-in-view is enabled by default. Therefore, database queries may be performed during view rendering.
```

## OSIV OFF 시 대응 전략

OSIV를 끄면 Service 계층에서 필요한 데이터를 모두 로딩해야 한다.

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

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 트래픽이 적고 빠르게 개발해야 할 때 | OSIV ON | 편의성 우선 |
| 트래픽이 많고 커넥션 풀이 중요한 서비스 | OSIV OFF | 커넥션 점유 시간 최소화 |
| API 서버 (뷰 렌더링 없음) | OSIV OFF | 지연 로딩 편의가 필요 없음 |
| 외부 API 호출이 응답에 포함되는 경우 | OSIV OFF | 외부 대기 중에도 커넥션을 점유하면 위험 |

## 자주 나는 실수

- OSIV가 기본으로 켜져 있는 것을 모르고 운영한다.
- 개발 환경에서는 커넥션 부족이 안 나지만 운영 트래픽에서 갑자기 장애가 발생한다.
- OSIV를 끄면서 `LazyInitializationException`을 모든 곳에서 EAGER로 바꿔서 해결한다 (N+1 유발).
- Service에서 엔티티를 그대로 컨트롤러에 반환하면서 직렬화 시점에 지연 로딩이 발생한다.

## 핵심 요약

OSIV는 영속성 컨텍스트를 HTTP 요청 전체로 확장하는 설정으로, Spring Boot 기본값이 `true`입니다.
켜져 있으면 컨트롤러에서도 지연 로딩이 가능하지만, DB 커넥션을 응답 완료까지 점유합니다.

트래픽이 많은 서비스에서는 커넥션 풀 고갈을 방지하기 위해 OSIV를 끄는 것이 권장됩니다.
OSIV를 끄면 Service 계층에서 필요한 데이터를 모두 로딩하고 DTO로 변환하여 반환해야 합니다.

## 꼬리 질문

> [!question]- OSIV를 켜면 왜 커넥션 풀이 고갈되는가?
> 영속성 컨텍스트가 요청 끝까지 유지되면서 DB 커넥션도 함께 점유합니다. 외부 API 호출이나 뷰 렌더링이 느리면 그 시간 동안 커넥션이 묶여 있어서 다른 요청이 커넥션을 얻지 못합니다.

> [!question]- OSIV를 끄면 LazyInitializationException이 나는 이유는?
> 트랜잭션이 끝나면 영속성 컨텍스트도 종료됩니다. 이후 엔티티의 지연 로딩 프록시에 접근하면 세션이 없어서 예외가 발생합니다.

> [!question]- OSIV OFF에서 지연 로딩 문제를 해결하는 방법은?
> Fetch Join, DTO 조회, @EntityGraph, batch_fetch_size 설정 등으로 Service 계층에서 필요한 데이터를 미리 로딩합니다. 엔티티 대신 DTO를 컨트롤러에 반환하는 것이 근본적인 해결입니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[lazy-and-eager-loading]]
- [[n-plus-one-and-fetch-join]]
- [[transaction-and-flush]]