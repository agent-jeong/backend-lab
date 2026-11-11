---
title: Bean 생명주기와 Scope
description: Bean이 언제 만들어지고 정리되는지, Scope마다 무엇을 공유하는지
tags: [concept, spring]
---

# Bean 생명주기와 Scope

Spring Bean은 컨테이너가 만들고, 의존성을 넣고, 종료할 때 정리까지 해 주는 객체다. Scope는 그 인스턴스 하나를 누구와 나눠 쓰는지 정한다.

Bean 때문에 나는 사고는 대개 둘 중 하나다. singleton 서비스 필드에 주문 건수 같은 값을 넣었다가 동시 요청끼리 값이 섞이거나, 캐시를 채우고 커넥션을 닫는 코드가 생각한 시점에 돌지 않는다.

## 생명주기

```
1. Bean 인스턴스 생성 (생성자 호출)
2. 의존성 주입 (DI)
3. 초기화 콜백 (@PostConstruct)
4. 사용
5. 소멸 콜백 (@PreDestroy)
6. Bean 소멸
```

### 초기화 콜백

```java
@Component
public class CacheWarmer {

    private final ProductRepository productRepository;

    public CacheWarmer(ProductRepository productRepository) {
        this.productRepository = productRepository;
    }

    @PostConstruct
    public void init() {
        // 의존성 주입이 완료된 후 실행
        // 캐시 워밍, 외부 연결 초기화 등
    }
}
```

`@PostConstruct`는 의존성 주입이 끝난 뒤에 실행된다. 생성자에서 초기화하면 필드 주입이나 setter 주입으로 들어올 값이 아직 비어 있을 수 있다.

### 소멸 콜백

```java
@Component
public class ConnectionPool {

    @PreDestroy
    public void cleanup() {
        // 애플리케이션 종료 시 리소스 정리
        // 커넥션 반환, 파일 핸들 닫기 등
    }
}
```

`@PreDestroy`는 컨테이너가 정상 종료될 때만 호출된다. `kill -9`로 강제 종료하면 호출되지 않는다.

## Bean Scope

### singleton (기본값)

```java
@Component // 기본이 singleton
public class OrderService {
    // 애플리케이션 전체에서 하나의 인스턴스
}
```

- 컨테이너당 인스턴스가 하나다.
- 모든 요청이 그 인스턴스 하나를 같이 쓰므로 상태를 두면 안 된다(아래 「singleton에 상태를 두면」).

### prototype

```java
@Scope("prototype")
@Component
public class RequestContext {
    // 요청할 때마다 새 인스턴스 생성
}
```

- `getBean()`을 부를 때마다 새 인스턴스를 만든다.
- 컨테이너는 만들어 주기만 하고 이후는 관리하지 않는다. 그래서 `@PreDestroy`가 호출되지 않는다.
- 실무에서 직접 쓰는 일은 드물다.

### request / session (웹 스코프)

```java
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
@Component
public class RequestLog {
    // HTTP 요청마다 새 인스턴스
}
```

- `request`: HTTP 요청마다 생기고 요청이 끝나면 사라진다.
- `session`: HTTP 세션마다 생기고 세션이 끝나면 사라진다.
- singleton에 주입하려면 `proxyMode`를 줘야 한다. singleton이 만들어질 때는 아직 요청이 없으니, 일단 프록시를 넣어 두고 실제 요청이 들어왔을 때 진짜 객체를 찾게 한다.

### 한눈에 비교

| Scope | 인스턴스 수 | 소멸 관리 | 실무 사용 |
|---|---|---|---|
| singleton | 1개 | 컨테이너가 관리 | 대부분의 Bean |
| prototype | 매번 새로 생성 | 관리 안 됨 | 드물게 사용 |
| request | 요청당 1개 | 요청 종료 시 | 요청별 상태 필요 시 |
| session | 세션당 1개 | 세션 종료 시 | 세션별 상태 필요 시 |

## singleton에 상태를 두면

```java
// 위험: singleton에 상태를 저장
@Service
public class OrderService {

    private int orderCount = 0; // 모든 요청이 공유 → 동시성 문제

    public void createOrder() {
        orderCount++; // race condition
    }
}
```

동시 요청이 같은 필드를 함께 고치니 값이 섞인다. 요청마다 다른 값이면 메서드 지역 변수, ThreadLocal, request 스코프 Bean 중 하나에 둔다. 이 예시처럼 모든 요청이 정말 공유하는 카운터라면 `AtomicLong`을 쓰거나 DB, Redis에 둔다.

## prototype을 singleton에 주입하면

```java
@Component
@Scope("prototype")
public class PrototypeBean { }

@Service
public class SingletonService {

    private final PrototypeBean prototypeBean;

    public SingletonService(PrototypeBean prototypeBean) {
        this.prototypeBean = prototypeBean;
        // singleton 생성 시 한 번만 주입 → 이후 계속 같은 인스턴스
    }
}
```

prototype이라도 singleton이 만들어질 때 한 번만 생성되고, 그 뒤로는 같은 인스턴스를 계속 쓴다. 쓸 때마다 새 인스턴스가 필요하면 `ObjectProvider`로 그때그때 꺼낸다.

```java
@Service
public class SingletonService {

    private final ObjectProvider<PrototypeBean> prototypeBeanProvider;

    public SingletonService(ObjectProvider<PrototypeBean> prototypeBeanProvider) {
        this.prototypeBeanProvider = prototypeBeanProvider;
    }

    public void logic() {
        PrototypeBean prototypeBean = prototypeBeanProvider.getObject(); // 매번 새 인스턴스
    }
}
```

## 자주 깨지는 곳

- singleton 필드에 요청마다 다른 값을 두면, 동시 요청끼리 값이 섞인다.
- prototype을 singleton에 생성자로 주입하면, 새 인스턴스가 매번 생기지 않고 처음 하나를 계속 쓴다.
- 주입받은 의존성을 쓰는 초기화를 생성자에 넣으면, 아직 주입 전이라 필드가 비어 있을 수 있다. `@PostConstruct`로 옮긴다.
- prototype에 `@PreDestroy`를 달아 두면, 호출되지 않아 리소스가 정리되지 않는다. 정리는 쓰는 쪽이 직접 한다.
- 웹 스코프 Bean을 `proxyMode` 없이 singleton에 주입하면, 주입 시점에 요청이 없어 애플리케이션이 뜨지 않는다.

## 한 번에 설명하기

> Bean은 생성, 의존성 주입, `@PostConstruct` 초기화, 사용, `@PreDestroy` 소멸 순서로 관리됩니다. 주입받은 의존성을 쓰는 초기화는 생성자가 아니라 `@PostConstruct`에 둡니다.
>
> 기본 Scope인 singleton은 모든 요청이 인스턴스 하나를 같이 쓰기 때문에 상태를 두지 않습니다.
>
> prototype을 singleton에 주입하면 처음 하나만 만들어지니, 매번 새 인스턴스가 필요하면 `ObjectProvider`로 꺼냅니다.

## 꼬리 질문

> [!question]- singleton Bean에 상태를 저장하면 어떤 문제가 생기는가?
> 모든 요청이 같은 인스턴스를 쓰니까, 동시에 들어온 요청이 같은 필드를 고치면서 값이 섞입니다. race condition이죠. 상태가 필요하면 메서드 지역 변수나 request 스코프 Bean에 둡니다.

> [!question]- `@PostConstruct`와 생성자의 차이는?
> 생성자는 의존성 주입이 다 끝나기 전에 실행될 수 있고, `@PostConstruct`는 주입이 끝난 다음에 실행됩니다. 그래서 주입받은 의존성을 쓰는 초기화는 `@PostConstruct`에 둡니다.

> [!question]- prototype Bean의 `@PreDestroy`가 호출되지 않는 이유는?
> 컨테이너는 prototype Bean을 만들어 넘겨주기만 하고, 그 뒤로는 따라가지 않습니다. 그래서 리소스 정리는 쓰는 쪽이 직접 해야 합니다.

> [!question]- 웹 스코프 Bean에 `proxyMode`가 필요한 이유는?
> singleton Bean이 만들어질 때는 아직 HTTP 요청이 없어서 request 스코프 Bean을 바로 넣을 수 없습니다. 그래서 프록시를 대신 넣어 두고, 실제 요청이 오면 프록시가 그 요청의 Bean을 찾아 호출합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>singleton Bean에 요청별 상태를 필드로 저장하면 위험한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="singleton Bean은 여러 요청과 스레드가 공유하므로 사용자별 상태가 섞이거나 race condition이 발생할 수 있다." aria-pressed="false">A. 여러 요청이 같은 인스턴스를 공유해 상태가 섞일 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="singleton Bean은 기본적으로 하나의 인스턴스다." aria-pressed="false">B. 요청마다 새 인스턴스가 생성되어 메모리가 폭증한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문제는 컴파일이 아니라 런타임 공유 상태다." aria-pressed="false">C. 필드를 선언하면 컴파일이 실패한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>prototype Bean의 @PreDestroy는 컨테이너 종료 시 자동으로 항상 호출된다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="Spring은 prototype Bean 생성과 의존성 주입까지만 관리하고 이후 파괴 콜백은 자동 관리하지 않는다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="prototype Bean은 소멸 책임을 사용하는 쪽에서 관리해야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>웹 스코프 Bean을 singleton Bean에 주입할 때 proxyMode가 필요한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="singleton 생성 시점에는 요청 스코프 객체가 없으므로 프록시를 주입해 실제 요청 시점에 대상 객체를 찾게 한다." aria-pressed="false">A. 요청 시점에 실제 스코프 객체를 지연 조회하기 위해서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="proxyMode는 JSON 변환용 기능이 아니다." aria-pressed="false">B. HTTP 응답을 자동으로 JSON으로 바꾸기 위해서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="스코프 프록시는 DB 트랜잭션 커밋을 직접 수행하지 않는다." aria-pressed="false">C. DB 커밋 시점을 늦추기 위해서다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Framework: Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)
- [Spring Framework: Customizing the Nature of a Bean](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[aop]]