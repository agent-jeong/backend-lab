---
title: IoC 컨테이너와 의존성 주입
description: 컨테이너가 Bean을 만들고 넣어 주는 방식과, 주입이 실패하는 흔한 이유
tags: [concept, spring]
---

# IoC 컨테이너와 의존성 주입

IoC(Inversion of Control)는 객체를 내가 `new`로 만들지 않고 프레임워크가 만들어 넘겨주게 하는 설계 원칙이다. DI(Dependency Injection)는 그 방법으로, 필요한 객체를 밖에서 넣어 준다.

실제로 부딪히는 건 원칙보다 주입 실패다. `OrderService`에 넣을 Bean을 못 찾았다며 애플리케이션이 안 뜨고, 알림 구현체가 이메일과 SMS 두 개라 어느 쪽을 넣을지 몰라 멈추고, 두 서비스가 서로를 참조해서 시작부터 실패한다. 테스트에서 결제 모듈을 가짜로 바꿔 끼우기 쉬운지도 주입 방식에 달렸다.

## 컨테이너가 하는 일

```
1. 애플리케이션 시작
2. @ComponentScan으로 Bean 대상 클래스 탐색
3. Bean 인스턴스 생성
4. 의존성 분석 후 DI 수행
5. 초기화 콜백 실행 (@PostConstruct 등)
6. 애플리케이션 동작
7. 종료 시 소멸 콜백 실행 (@PreDestroy 등)
```

Spring에서는 `ApplicationContext`가 IoC 컨테이너다. Bean을 만들고, 주입하고, 종료할 때 정리하는 일을 모두 한다.

## 주입 방식

### 생성자 주입 (기본으로 쓴다)

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

- `final` 필드를 쓸 수 있어 한 번 넣은 의존성이 바뀌지 않는다.
- 직접 `new`로 만들 때(테스트 등) 인자를 빠뜨리면 컴파일 에러가 나고, 컨테이너에 넣을 Bean이 없으면 애플리케이션이 뜰 때 바로 실패한다.
- 생성자가 하나면 `@Autowired`를 생략할 수 있다(Spring 4.3+).

### 필드 주입

```java
@Service
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;
}
```

- `final`을 쓸 수 없어 나중에 값이 바뀌어도 막을 수 없다.
- 테스트에서 의존성을 바꾸려면 리플렉션이 필요하다.
- 생성자에 드러나지 않아서 클래스 선언만 보고는 무엇이 필요한지 알기 어렵다.

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

없어도 되는 의존성에 쓸 수 있지만 실무에서는 거의 쓰지 않는다.

### 한눈에 비교

| 기준 | 생성자 주입 | 필드 주입 | setter 주입 |
|---|---|---|---|
| 불변성 | O (`final`) | X | X |
| 필수 의존성 보장 | O | X | X |
| 테스트 용이성 | O | X (리플렉션) | O |
| 순환 참조 감지 | 기동 시 실패(우회 불가) | 기동 시 실패(Boot 2.6+, 허용 설정으로 우회 가능) | 기동 시 실패(Boot 2.6+, 허용 설정으로 우회 가능) |
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

### 고르는 방법

```java
// 1. @Primary: 기본 Bean 지정
@Primary
@Component
public class EmailSender implements NotificationSender { ... }

// 2. @Qualifier: 이름으로 지정
@Service
public class OrderService {

    private final NotificationSender sender;

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

생성자 주입이면 애플리케이션 시작 시점에 바로 실패한다. Spring Boot 2.6부터는 기본 설정에서 순환 참조를 허용하지 않는다.

의존 방향을 한쪽으로만 흐르게 바꿔서 고친다. 두 서비스가 함께 쓰는 로직을 별도 서비스로 떼어 내면 대개 풀린다. `@Lazy`로 주입을 미루면 애플리케이션은 뜨지만, 서로 물고 있는 구조는 그대로 남는다.

## 자주 깨지는 곳

- 필드 주입을 쓰면, 테스트에서 의존성을 가짜로 바꾸기 어렵다.
- `@Component`를 빠뜨리거나 클래스를 패키지 스캔 범위 밖에 두면, Bean이 등록되지 않아 주입이 실패한다.
- 구현체가 여러 개인데 `@Primary`나 `@Qualifier`가 없고 파라미터 이름으로도 고를 수 없으면, 어느 Bean을 넣을지 몰라 시작이 실패한다.
- 순환 참조를 `@Lazy`로 덮으면, 당장은 뜨지만 서로 물고 있는 구조가 그대로 남는다.

## 한 번에 설명하기

> IoC는 객체를 직접 만들지 않고 프레임워크가 만들어 넘겨주게 하는 원칙이고, DI는 필요한 객체를 밖에서 넣어 주는 방식입니다.
>
> 저는 생성자 주입을 기본으로 씁니다. `final`로 의존성이 바뀌지 않게 할 수 있고, 빠진 의존성과 순환 참조가 애플리케이션이 뜰 때 바로 드러나기 때문입니다.
>
> 같은 타입 Bean이 여러 개면 `@Primary`, `@Qualifier`, `List` 주입 중 하나로 고르고, 순환 참조는 의존 방향을 한쪽으로 바꿔서 풉니다.

## 꼬리 질문

> [!question]- 생성자 주입이 권장되는 이유는?
> `final` 필드라 한 번 넣은 의존성이 바뀌지 않고, 테스트에서 직접 만들 때 인자를 빠뜨리면 컴파일 에러가 납니다. 넣을 Bean이 없거나 순환 참조가 있으면 애플리케이션이 뜰 때 바로 실패해서 알 수 있습니다.

> [!question]- `@Autowired`를 생략할 수 있는 조건은?
> Spring 4.3부터는 생성자가 하나뿐이면 생략해도 됩니다. 생성자가 여러 개면 어느 생성자로 주입할지 `@Autowired`를 붙여 알려 줘야 합니다.

> [!question]- 순환 참조가 발생하면 어떻게 해결하는가?
> 의존 방향을 한쪽으로만 흐르게 바꿔야 풀립니다. 둘이 같이 쓰는 로직을 별도 서비스로 떼어 내거나, 이벤트를 발행해서 직접 호출을 끊습니다. `@Lazy`는 당장 뜨게만 해 줄 뿐 고친 게 아닙니다.

> [!question]- `@Component`와 `@Service`, `@Repository`의 차이는?
> 셋 다 Bean으로 등록한다는 점은 같습니다. `@Service`는 비즈니스 로직, `@Repository`는 데이터 접근 계층이라고 표시하는 이름이고, `@Repository`는 여기에 더해 persistence 예외를 Spring 예외로 바꿔 줍니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>생성자 주입을 권하는 이유는?</p>
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
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring은 타입으로 후보를 찾고, @Primary, @Qualifier, 이름으로 후보를 좁힌다." aria-pressed="false">O</button>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: The IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html)
- [Spring Framework: Dependency Injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[why-spring]]
- [[bean-lifecycle-and-scope]]
- [[aop]]