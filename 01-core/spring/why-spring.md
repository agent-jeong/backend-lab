---
title: Spring을 사용하는 이유
description: Spring이 대신 해 주는 일과, 그게 없으면 무엇을 직접 써야 하는지
tags: [concept, spring]
---

# Spring을 사용하는 이유

Spring은 객체를 만들고, 서로 연결하고, 종료할 때 정리하는 일을 대신 해 주는 애플리케이션 프레임워크다. 개발자는 주문을 받고 결제를 처리하는 코드에 손을 더 쓸 수 있다.

"편해서 쓴다"로는 부족하다. 왜 `new` 대신 Bean으로 등록하는지, Spring 없이 같은 일을 하려면 무엇을 직접 짜야 하는지 알아야 자동 설정이 말썽을 부릴 때 원인을 찾는다. 반대로 Spring 없이도 풀리는 문제까지 Spring에 기대는 일도 줄어든다.

## Spring이 해결하는 문제

### Spring 없이 개발하면

```java
public class OrderService {

    // 직접 의존 객체를 생성
    private final OrderRepository orderRepository = new JdbcOrderRepository(dataSource);
    private final PaymentService paymentService = new PaymentService(new PgClient());
    private final NotificationService notificationService = new NotificationService(new SmtpClient());
}
```

- 객체끼리 단단히 묶여 있어서, 구현체를 바꾸려면 이 코드를 직접 고쳐야 한다.
- 트랜잭션, 로깅, 예외 처리 같은 공통 코드를 메서드마다 직접 쓴다.
- 객체를 언제 만들고 언제 정리할지도 개발자가 챙긴다.
- 테스트에서 의존 객체를 가짜로 바꿔 끼우기 어렵다.

### Spring은 이렇게 푼다

| 문제 | Spring의 해결 |
|---|---|
| 객체 생성과 연결 | IoC 컨테이너가 Bean을 생성하고 DI로 주입 |
| 공통 관심사 중복 | AOP로 트랜잭션, 로깅 등을 분리 |
| 설정 복잡도 | Spring Boot 자동 설정으로 최소 설정 |
| 테스트 어려움 | DI로 Mock 객체 주입 가능 |
| 반복 코드 | Spring Data, Spring MVC 등으로 boilerplate 제거 |

## 받치고 있는 세 가지 원칙

### IoC (Inversion of Control)

객체를 만들고 연결하는 일을 개발자가 아니라 프레임워크가 한다. 누가 흐름을 쥐는지가 뒤집혀서 "제어의 역전"이라고 부른다.

```java
// 개발자가 제어: 직접 생성하고 연결
OrderService service = new OrderService(new JdbcOrderRepository());

// Spring이 제어: 프레임워크가 생성하고 주입
@Service
public class OrderService {

    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository; // Spring이 주입
    }
}
```

### DI (Dependency Injection)

필요한 객체를 밖에서 받는 패턴이다. 인터페이스에 의존하게 해 두면 구현체를 마음대로 바꿀 수 있다. 자세한 내용은 [[ioc-and-di]]에 있다.

### AOP (Aspect-Oriented Programming)

트랜잭션, 로깅, 보안처럼 여러 곳에 똑같이 붙는 코드를 비즈니스 로직에서 떼어 낸다. `@Transactional`이 가장 흔한 예다.

## Spring vs Spring Boot

| 구분 | Spring Framework | Spring Boot |
|---|---|---|
| 설정 방식 | XML 또는 Java Config 직접 작성 | 자동 설정 (Auto Configuration) |
| 서버 | 별도 WAS 필요 | 내장 톰캣 포함 |
| 의존성 관리 | 직접 버전 관리 | starter로 호환 버전 자동 관리 |
| 실무 사용 | 거의 사용하지 않음 | 대부분 Spring Boot 사용 |

Spring Boot는 Spring Framework 위에서 도는 도구다. IoC, DI, AOP는 그대로 두고, 설정과 실행만 간단하게 만들었다.

## 자주 깨지는 곳

- IoC와 DI를 모른 채 어노테이션만 쓰면, 주입이 실패했을 때 어디를 봐야 할지 모른다.
- Spring과 Spring Boot를 구분하지 못하면, 자동 설정이 한 일과 Spring 자체가 한 일이 섞여 원인을 엉뚱한 데서 찾는다.
- "편해서"라고만 답하면, 왜 써야 하는지 설명이 안 된다. 객체끼리 덜 묶이고, 공통 코드를 떼어 낼 수 있고, 테스트가 쉬워진다고 말해야 한다.
- 프레임워크가 해 주는 일을 나눠 보지 못하면, 객체 관리, AOP, 트랜잭션 중 어디서 문제가 났는지 좁히지 못한다.

## 한 번에 설명하기

> Spring은 객체를 만들고 연결하는 일을 대신 해 주는 IoC 컨테이너입니다. 직접 `new`로 만들어 연결하면 객체끼리 단단히 묶여서, 구현을 바꾸거나 테스트하기가 어렵습니다.
>
> Spring은 DI로 의존성을 밖에서 넣어 주고, AOP로 트랜잭션 같은 공통 코드를 떼어 냅니다.
>
> Spring Boot는 그 위에 자동 설정과 내장 서버를 얹은 도구입니다.

## 꼬리 질문

> [!question]- Spring과 Spring Boot의 관계는?
> Spring Boot는 Spring Framework 위에서 돕니다. IoC, DI, AOP는 Spring Framework의 것이고, Spring Boot는 거기에 자동 설정과 내장 서버를 붙여서 설정을 덜 하게 해 준 것입니다.

> [!question]- IoC와 DI의 차이는?
> IoC는 제어의 역전이라는 설계 원칙이고, DI는 그걸 실제로 구현하는 방법 중 하나입니다. Spring에서는 IoC 컨테이너가 Bean을 관리하고, DI로 의존 객체를 넣어 줍니다.

> [!question]- Spring 없이도 DI를 구현할 수 있는가?
> 됩니다. 생성자로 외부 객체를 받기만 해도 DI입니다. 다만 Spring은 객체 생성, 생명주기, 스코프까지 대신 챙겨 주니, 객체가 많아질수록 직접 관리하는 것보다 훨씬 편합니다.

> [!question]- Spring이 제공하는 가장 큰 가치는?
> 객체끼리 덜 묶이게 해 준다는 점입니다. 인터페이스에 의존하고 구현체를 밖에서 받으면, 코드를 고치지 않고 구현을 바꿀 수 있고 테스트에서 Mock도 쉽게 끼울 수 있습니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring이 백엔드 개발에서 주는 가치로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="객체 생성과 의존관계 관리를 컨테이너에 맡겨 애플리케이션 구조를 일관되게 만들고 확장 지점을 제공한다." aria-pressed="false">A. IoC 컨테이너를 통한 객체 관리와 일관된 확장 구조</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring이 SQL 튜닝을 자동으로 대체하지는 않는다." aria-pressed="false">B. 모든 DB 쿼리를 자동으로 최적화한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring은 HTTP 서버일 뿐 아니라 DI, AOP, 트랜잭션 등 애플리케이션 기반 구조를 제공한다." aria-pressed="false">C. 단순히 내장 톰캣만 제공한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>Spring Boot는 Spring을 대체하는 별도 프레임워크라기보다 Spring 애플리케이션 설정과 실행을 단순화한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Boot는 자동 설정, starter, 내장 서버 등으로 Spring 기반 애플리케이션 구성을 줄여준다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring Boot는 Spring 생태계 위에서 동작한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>IoC와 DI의 관계로 맞는 설명은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="IoC는 제어 흐름을 컨테이너가 가져가는 원칙이고, DI는 의존성 주입으로 이를 구현하는 대표 방식이다." aria-pressed="false">A. DI는 IoC를 구현하는 대표적인 방식이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="IoC와 DI는 연관되지만 완전히 같은 단어는 아니다." aria-pressed="false">B. IoC와 DI는 항상 완전히 같은 의미다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DI는 컴파일러 기능이 아니라 객체 관계 구성 방식이다." aria-pressed="false">C. DI는 Java 컴파일러가 자동 수행하는 기능이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework Overview](https://docs.spring.io/spring-framework/reference/overview.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[bean-lifecycle-and-scope]]
- [[aop]]