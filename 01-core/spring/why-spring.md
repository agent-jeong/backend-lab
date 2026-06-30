---
title: Spring을 사용하는 이유
description: Spring Framework를 사용하는 이유와 핵심 설계 철학
---

# Spring을 사용하는 이유

## 한 줄 정의

Spring은 객체의 생성, 의존성 연결, 생명주기 관리를 프레임워크가 대신 처리해서 개발자가 비즈니스 로직에 집중할 수 있게 해주는 애플리케이션 프레임워크다.

## 실무에서 왜 중요한가

Spring을 사용하는 이유를 모르면 다음 상황에서 방향을 잃는다.

- 왜 `new`로 직접 객체를 만들지 않고 Bean으로 등록하는지 설명하지 못한다.
- Spring Boot의 자동 설정에 의존하면서 문제가 생기면 원인을 찾지 못한다.
- 프레임워크 없이 동일한 기능을 구현하려면 얼마나 많은 코드가 필요한지 모른다.
- Spring이 제공하는 이점을 모르면 프레임워크 없이 해결할 수 있는 문제에도 과도한 의존을 한다.

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

- 객체 간 결합도가 높아서 구현체를 바꾸려면 코드를 직접 수정해야 한다.
- 트랜잭션, 로깅, 예외 처리 같은 공통 관심사를 모든 메서드에 직접 작성해야 한다.
- 객체 생명주기를 개발자가 직접 관리해야 한다.
- 테스트 시 의존 객체를 교체하기 어렵다.

### Spring이 제공하는 해결

| 문제 | Spring의 해결 |
|---|---|
| 객체 생성과 연결 | IoC 컨테이너가 Bean을 생성하고 DI로 주입 |
| 공통 관심사 중복 | AOP로 트랜잭션, 로깅 등을 분리 |
| 설정 복잡도 | Spring Boot 자동 설정으로 최소 설정 |
| 테스트 어려움 | DI로 Mock 객체 주입 가능 |
| 반복 코드 | Spring Data, Spring MVC 등으로 boilerplate 제거 |

## Spring의 핵심 설계 원칙

### IoC (Inversion of Control)

객체의 생성과 의존성 연결을 개발자가 아닌 프레임워크가 담당한다. 제어의 흐름이 역전된다.

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

외부에서 의존 객체를 주입받는 패턴이다. 인터페이스에 의존하면 구현체를 자유롭게 교체할 수 있다.

### AOP (Aspect-Oriented Programming)

트랜잭션, 로깅, 보안 같은 공통 관심사를 비즈니스 로직과 분리한다. `@Transactional`이 대표적인 AOP 적용 사례다.

## Spring vs Spring Boot

| 구분 | Spring Framework | Spring Boot |
|---|---|---|
| 설정 방식 | XML 또는 Java Config 직접 작성 | 자동 설정 (Auto Configuration) |
| 서버 | 별도 WAS 필요 | 내장 톰캣 포함 |
| 의존성 관리 | 직접 버전 관리 | starter로 호환 버전 자동 관리 |
| 실무 사용 | 거의 사용하지 않음 | 대부분 Spring Boot 사용 |

Spring Boot는 Spring Framework 위에서 동작하는 도구다. Spring의 핵심 개념(IoC, DI, AOP)은 동일하고, 설정과 실행을 간소화한 것이다.

## 자주 나는 실수

- Spring을 사용하면서 IoC/DI 개념을 이해하지 않고 어노테이션만 사용한다.
- Spring과 Spring Boot의 차이를 설명하지 못한다.
- "편리해서" 외에 Spring을 사용하는 기술적 이유를 설명하지 못한다.
- 프레임워크가 해주는 일(객체 관리, AOP, 트랜잭션)을 구분하지 못한다.

## 핵심 요약

Spring은 객체의 생성과 의존성 연결을 프레임워크가 대신 관리하는 IoC 컨테이너입니다.
개발자가 직접 `new`로 객체를 만들고 연결하면 결합도가 높아지고, 테스트와 유지보수가 어렵습니다.

Spring은 DI로 의존성을 외부에서 주입하고, AOP로 공통 관심사를 분리합니다.
Spring Boot는 Spring의 핵심 위에 자동 설정과 내장 서버를 추가한 도구입니다.

## 꼬리 질문

> [!question]- Spring과 Spring Boot의 관계는?
> Spring Boot는 Spring Framework 위에서 동작하는 도구입니다. IoC, DI, AOP 같은 핵심 개념은 Spring Framework에 속하고, Spring Boot는 자동 설정과 내장 서버로 개발 편의성을 높인 것입니다.

> [!question]- IoC와 DI의 차이는?
> IoC는 제어의 역전이라는 설계 원칙이고, DI는 IoC를 구현하는 구체적인 방법입니다. Spring에서는 IoC 컨테이너가 Bean을 관리하고, DI를 통해 의존 객체를 주입합니다.

> [!question]- Spring 없이도 DI를 구현할 수 있는가?
> 가능합니다. 생성자에서 외부 객체를 받으면 DI입니다. 하지만 Spring은 객체 생성, 생명주기, 스코프 관리까지 자동으로 처리해주기 때문에 규모가 큰 애플리케이션에서 직접 관리하는 것보다 훨씬 효율적입니다.

> [!question]- Spring이 제공하는 가장 큰 가치는?
> 객체 간 결합도를 낮추는 것입니다. 인터페이스에 의존하고 구현체를 외부에서 주입받으면, 코드 변경 없이 구현을 교체할 수 있고 테스트에서 Mock을 쉽게 사용할 수 있습니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>Spring이 백엔드 개발에서 제공하는 핵심 가치로 가장 적절한 것은?</p>
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
    <p class="quiz-question"><span class="quiz-label">객관식</span>IoC와 DI의 관계로 가장 적절한 설명은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="IoC는 제어 흐름을 컨테이너가 가져가는 원칙이고, DI는 의존성 주입으로 이를 구현하는 대표 방식이다." aria-pressed="false">A. DI는 IoC를 구현하는 대표적인 방식이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="IoC와 DI는 연관되지만 완전히 같은 단어는 아니다." aria-pressed="false">B. IoC와 DI는 항상 완전히 같은 의미다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="DI는 컴파일러 기능이 아니라 객체 관계 구성 방식이다." aria-pressed="false">C. DI는 Java 컴파일러가 자동 수행하는 기능이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[bean-lifecycle-and-scope]]
- [[aop]]