---
title: Bean 생명주기와 Scope
description: Spring Bean의 생명주기와 Scope별 동작 차이
---

# Bean 생명주기와 Scope

Spring Bean은 IoC 컨테이너가 생성부터 소멸까지 관리하는 객체다. Scope는 그 인스턴스를 어디까지 공유하는지 정한다.

실무 사고는 대개 둘 중 하나다. singleton에 상태를 넣어 동시 요청끼리 데이터가 섞이거나, 초기화와 정리 코드가 기대한 시점에 돌지 않는다.

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

`@PostConstruct`는 의존성 주입이 끝난 뒤 실행된다. 생성자에서 초기화하면 아직 주입되지 않은 필드가 있을 수 있다.

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
- 모든 요청이 그 인스턴스를 공유하므로 상태를 두면 안 된다(아래 「singleton에 상태를 두면」).

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
- singleton에 주입하려면 `proxyMode`를 줘야 한다. singleton이 만들어질 때는 아직 요청이 없어서, 프록시를 넣어 두고 실제 요청 시점에 대상을 찾게 한다.

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

동시 요청이 같은 필드를 고치므로 값이 섞인다. 상태가 필요하면 메서드 지역 변수, ThreadLocal, request 스코프 Bean 중 하나에 둔다.

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

prototype은 singleton이 만들어질 때 한 번만 생성되고, 이후 계속 같은 인스턴스가 쓰인다. 매번 새 인스턴스가 필요하면 `ObjectProvider`로 꺼낸다.

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

- **singleton 필드에 요청별 상태를 둔다.** 동시 요청끼리 값이 섞인다.
- **prototype을 singleton에 생성자로 주입한다.** 새 인스턴스가 매번 생기지 않고 처음 하나가 계속 쓰인다.
- **의존성이 필요한 초기화를 생성자에 넣는다.** 주입 전이라 필드가 비어 있을 수 있다. `@PostConstruct`로 옮긴다.
- **prototype의 `@PreDestroy`를 믿는다.** 호출되지 않는다. 정리는 쓰는 쪽이 직접 한다.
- **웹 스코프 Bean을 `proxyMode` 없이 singleton에 주입한다.** 주입 시점에 요청이 없어 실패한다.

## 면접에서 말하기

> Bean은 생성, 의존성 주입, `@PostConstruct` 초기화, 사용, `@PreDestroy` 소멸 순으로 관리됩니다. 주입된 의존성을 쓰는 초기화는 생성자가 아니라 `@PostConstruct`에 둡니다. 기본 Scope인 singleton은 모든 요청이 한 인스턴스를 공유하므로 상태를 두지 않습니다. prototype을 singleton에 주입하면 처음 하나만 생성되기 때문에, 매번 새 인스턴스가 필요하면 `ObjectProvider`를 씁니다.

## 꼬리 질문

> [!question]- singleton Bean에 상태를 저장하면 어떤 문제가 생기는가?
> 모든 요청이 같은 인스턴스를 공유하므로 동시 요청끼리 데이터가 섞이는 race condition이 생깁니다. 상태가 필요하면 메서드 지역 변수나 request 스코프를 씁니다.

> [!question]- `@PostConstruct`와 생성자의 차이는?
> 생성자는 의존성 주입 전에 실행될 수 있지만, `@PostConstruct`는 DI가 완료된 후 실행됩니다. 주입된 의존성을 쓰는 초기화는 `@PostConstruct`에 둡니다.

> [!question]- prototype Bean의 `@PreDestroy`가 호출되지 않는 이유는?
> 컨테이너가 prototype Bean은 생성까지만 관리하고 이후 생명주기를 추적하지 않기 때문입니다. 리소스 정리는 쓰는 쪽이 직접 해야 합니다.

> [!question]- 웹 스코프 Bean에 `proxyMode`가 필요한 이유는?
> singleton Bean이 생성되는 시점에는 아직 HTTP 요청이 없어서 request 스코프 Bean을 바로 주입할 수 없습니다. 프록시가 실제 요청 시점에 Bean을 가져오도록 위임합니다.

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

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[aop]]