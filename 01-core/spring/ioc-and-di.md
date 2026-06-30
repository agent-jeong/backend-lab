---
title: IoC 컨테이너와 의존성 주입
description: Spring IoC 컨테이너의 동작 원리와 DI 방식별 특징
---

# IoC 컨테이너와 의존성 주입

## 한 줄 정의

IoC(Inversion of Control)는 객체의 생성과 의존성 관리를 프레임워크에 위임하는 설계 원칙이고, DI(Dependency Injection)는 외부에서 의존 객체를 주입받는 구현 방식이다.

## 실무에서 왜 중요한가

IoC와 DI를 이해하지 못하면 다음 문제가 생긴다.

- Bean 주입이 안 되는 원인(`@Component` 누락, 패키지 스캔 범위 등)을 파악하지 못한다.
- 생성자 주입과 필드 주입의 차이를 모르고 사용한다.
- 순환 참조가 발생했을 때 원인과 해결 방법을 모른다.
- 인터페이스 구현체가 여러 개일 때 어떤 Bean이 주입되는지 예측하지 못한다.
- 테스트에서 의존성을 교체하는 방법을 모른다.

## IoC 컨테이너의 동작

```
1. 애플리케이션 시작
2. @ComponentScan으로 Bean 대상 클래스 탐색
3. Bean 인스턴스 생성
4. 의존성 분석 후 DI 수행
5. 초기화 콜백 실행 (@PostConstruct 등)
6. 애플리케이션 동작
7. 종료 시 소멸 콜백 실행 (@PreDestroy 등)
```

Spring의 `ApplicationContext`가 IoC 컨테이너 역할을 한다. Bean의 생성, 주입, 소멸을 모두 관리한다.

## DI 방식 비교

### 생성자 주입 (권장)

```java
@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final PaymentService paymentService;

    public OrderService(OrderRepository orderRepository, PaymentService paymentService) {
        this.orderRepository = orderRepository;
        this.paymentService = paymentService;
    }
}
```

- `final` 필드 사용 가능 → 불변성 보장
- 필수 의존성 누락 시 컴파일 에러로 잡힌다.
- 생성자가 하나면 `@Autowired` 생략 가능 (Spring 4.3+)

### 필드 주입

```java
@Service
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;
}
```

- `final` 사용 불가 → 불변성 보장 안 됨
- 테스트에서 의존성 교체가 어렵다 (리플렉션 필요)
- 의존성이 숨겨져서 클래스만 보고 필요한 의존성을 파악하기 어렵다.

### setter 주입

```java
@Service
public class OrderService {

    private OrderRepository orderRepository;

    @Autowired
    public void setOrderRepository(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

- 선택적 의존성에 사용할 수 있다.
- 실무에서는 거의 사용하지 않는다.

### 방식별 비교

| 기준 | 생성자 주입 | 필드 주입 | setter 주입 |
|---|---|---|---|
| 불변성 | O (`final`) | X | X |
| 필수 의존성 보장 | O | X | X |
| 테스트 용이성 | O | X (리플렉션) | O |
| 순환 참조 감지 | 즉시 감지 | 런타임 감지 | 런타임 감지 |
| 실무 권장 | **권장** | 비권장 | 특수한 경우만 |

## 같은 타입의 Bean이 여러 개일 때

```java
public interface NotificationSender {
    void send(String message);
}

@Component
public class EmailSender implements NotificationSender { ... }

@Component
public class SmsSender implements NotificationSender { ... }
```

### 해결 방법

```java
// 1. @Primary: 기본 Bean 지정
@Primary
@Component
public class EmailSender implements NotificationSender { ... }

// 2. @Qualifier: 이름으로 지정
@Service
public class OrderService {

    public OrderService(@Qualifier("smsSender") NotificationSender sender) {
        this.sender = sender;
    }
}

// 3. List로 모두 주입
@Service
public class NotificationService {

    private final List<NotificationSender> senders;

    public NotificationService(List<NotificationSender> senders) {
        this.senders = senders; // 모든 구현체가 주입됨
    }
}
```

## 순환 참조

```java
@Service
public class ServiceA {
    public ServiceA(ServiceB serviceB) { }
}

@Service
public class ServiceB {
    public ServiceB(ServiceA serviceA) { }
}
```

생성자 주입에서는 애플리케이션 시작 시점에 즉시 실패한다. Spring Boot 2.6부터는 기본적으로 순환 참조를 허용하지 않는다.

**해결 방법:**
- 설계를 재검토해서 의존 방향을 단방향으로 바꾼다.
- 공통 로직을 별도 서비스로 분리한다.
- `@Lazy`로 지연 주입할 수 있지만 근본 해결은 아니다.

## 자주 나는 실수

- 필드 주입을 사용해서 테스트에서 의존성 교체가 어렵다.
- `@Component`를 빠뜨려서 Bean 등록이 안 된다.
- 패키지 스캔 범위 밖에 클래스를 두고 Bean이 등록되지 않는다.
- 인터페이스 구현체가 여러 개인데 `@Primary`나 `@Qualifier` 없이 사용한다.
- 순환 참조를 `@Lazy`로 회피하면서 설계 문제를 방치한다.

## 핵심 요약

IoC는 객체의 생성과 의존성 관리를 프레임워크에 위임하는 원칙이고, DI는 외부에서 의존 객체를 주입받는 구현 방식입니다.

Spring에서 DI 방식은 생성자 주입이 권장됩니다.
`final` 필드로 불변성을 보장하고, 필수 의존성 누락을 컴파일 시점에 잡을 수 있고, 순환 참조를 시작 시점에 감지합니다.

같은 타입의 Bean이 여러 개면 `@Primary`, `@Qualifier`, `List` 주입으로 해결합니다.
순환 참조는 설계를 재검토해서 의존 방향을 단방향으로 바꾸는 것이 근본 해결입니다.

## 꼬리 질문

> [!question]- 생성자 주입이 권장되는 이유는?
> `final` 필드로 불변성을 보장하고, 필수 의존성 누락 시 컴파일 에러로 잡히며, 순환 참조를 시작 시점에 감지할 수 있기 때문입니다.

> [!question]- `@Autowired`를 생략할 수 있는 조건은?
> 생성자가 하나뿐일 때 Spring 4.3부터 `@Autowired`를 생략할 수 있습니다. 생성자가 여러 개면 주입할 생성자에 `@Autowired`를 명시해야 합니다.

> [!question]- 순환 참조가 발생하면 어떻게 해결하는가?
> 설계를 재검토해서 의존 방향을 단방향으로 바꾸는 것이 근본 해결입니다. 공통 로직을 별도 서비스로 분리하거나, 이벤트 기반으로 간접 호출하는 방식을 사용합니다. `@Lazy`는 임시 회피이지 해결이 아닙니다.

> [!question]- `@Component`와 `@Service`, `@Repository`의 차이는?
> 기능적으로 모두 Bean 등록용 어노테이션입니다. `@Service`는 비즈니스 로직, `@Repository`는 데이터 접근 계층임을 명시하는 역할이고, `@Repository`는 추가로 persistence 예외를 Spring 예외로 변환합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>생성자 주입이 권장되는 가장 중요한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="필수 의존성을 객체 생성 시점에 보장하고, final 사용과 테스트가 쉬우며 순환 참조를 더 빨리 드러낸다." aria-pressed="false">A. 필수 의존성을 명확히 하고 불변성과 테스트 용이성을 높인다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="생성자 주입이 성능 최적화의 핵심 이유는 아니다." aria-pressed="false">B. 런타임 성능이 항상 필드 주입보다 압도적으로 빠르다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="생성자 주입도 순환 참조를 만들 수 있지만 더 명확히 실패한다." aria-pressed="false">C. 순환 참조가 있어도 항상 자동 해결된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>같은 타입의 Bean이 여러 개일 때 Spring은 항상 이름을 무시하고 무작위로 하나를 주입한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring은 타입으로 후보를 찾고, @Primary, @Qualifier, 이름 등을 통해 후보를 좁힌다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="무작위 주입이 아니라 명시적인 우선순위와 qualifier 기준을 사용한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>순환 참조가 발생했을 때 가장 먼저 검토할 해결 방향은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="두 객체가 서로 너무 많은 책임을 알고 있는지 확인하고 책임 분리나 중간 서비스 도입을 검토한다." aria-pressed="false">A. 설계를 재검토해 책임을 분리한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="lazy 주입은 우회일 수 있지만 근본 해결이 아닐 수 있다." aria-pressed="false">B. 모든 의존성에 @Lazy를 붙인다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="필드 주입은 순환 참조를 숨겨 설계 문제 발견을 늦출 수 있다." aria-pressed="false">C. 생성자 주입을 모두 필드 주입으로 바꾼다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[why-spring]]
- [[bean-lifecycle-and-scope]]
- [[aop]]