---
title: Bean 생명주기와 Scope
description: Spring Bean의 생명주기와 Scope별 동작 차이
---

# Bean 생명주기와 Scope

## 한 줄 정의

Spring Bean은 IoC 컨테이너가 생성부터 소멸까지 관리하는 객체이며, Scope에 따라 인스턴스가 공유되는 범위가 달라진다.

## 실무에서 왜 중요한가

Bean 생명주기와 Scope를 모르면 다음 문제가 생긴다.

- 초기화 로직을 생성자에 넣었는데 의존성 주입이 아직 안 된 상태에서 실행된다.
- singleton Bean에 상태를 저장해서 동시 요청 간 데이터가 섞인다.
- prototype Bean을 singleton에 주입해서 매번 새 인스턴스가 생성되지 않는다.
- `@PreDestroy`가 호출되지 않는 원인을 모른다.

## Bean 생명주기

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

`@PostConstruct`는 의존성 주입이 완료된 후 실행된다. 생성자에서 초기화 로직을 실행하면 주입이 아직 안 된 필드가 있을 수 있다.

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

`@PreDestroy`는 컨테이너가 정상 종료될 때 호출된다. `kill -9`로 강제 종료하면 호출되지 않는다.

## Bean Scope

### singleton (기본값)

```java
@Component // 기본이 singleton
public class OrderService {
    // 애플리케이션 전체에서 하나의 인스턴스
}
```

- 컨테이너당 하나의 인스턴스만 생성된다.
- 모든 요청이 같은 인스턴스를 공유한다.
- **상태를 가지면 안 된다** (동시 요청 시 데이터 충돌).

### prototype

```java
@Scope("prototype")
@Component
public class RequestContext {
    // 요청할 때마다 새 인스턴스 생성
}
```

- `getBean()` 호출마다 새 인스턴스를 생성한다.
- 컨테이너가 생성 후 관리하지 않는다 → `@PreDestroy`가 호출되지 않는다.
- 실무에서 직접 사용하는 경우는 드물다.

### request / session (웹 스코프)

```java
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
@Component
public class RequestLog {
    // HTTP 요청마다 새 인스턴스
}
```

- `request`: HTTP 요청마다 생성되고 요청 종료 시 소멸
- `session`: HTTP 세션마다 생성되고 세션 종료 시 소멸
- `proxyMode` 설정이 필요하다 (singleton에서 주입받으려면 프록시가 필요)

### Scope별 비교

| Scope | 인스턴스 수 | 소멸 관리 | 실무 사용 |
|---|---|---|---|
| singleton | 1개 | 컨테이너가 관리 | 대부분의 Bean |
| prototype | 매번 새로 생성 | 관리 안 됨 | 드물게 사용 |
| request | 요청당 1개 | 요청 종료 시 | 요청별 상태 필요 시 |
| session | 세션당 1개 | 세션 종료 시 | 세션별 상태 필요 시 |

## singleton Bean의 상태 문제

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

singleton Bean은 상태를 가지면 안 된다. 상태가 필요하면 메서드 지역 변수나 ThreadLocal, 또는 request 스코프 Bean을 사용한다.

## prototype Bean과 singleton 주입 문제

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

singleton Bean에 prototype Bean을 주입하면 최초 한 번만 생성된다. 매번 새 인스턴스가 필요하면 `ObjectProvider`를 사용한다.

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

## 자주 나는 실수

- singleton Bean에 인스턴스 변수로 상태를 저장해서 동시성 문제가 생긴다.
- prototype Bean을 singleton에 직접 주입해서 매번 새 인스턴스가 생성되지 않는다.
- `@PostConstruct`가 아닌 생성자에서 의존성이 필요한 초기화를 실행한다.
- `@PreDestroy`가 prototype Bean에서는 호출되지 않는 것을 모른다.
- 웹 스코프 Bean을 `proxyMode` 없이 singleton에 주입하려 한다.

## 핵심 요약

Spring Bean의 생명주기는 생성 → DI → 초기화(`@PostConstruct`) → 사용 → 소멸(`@PreDestroy`) 순서입니다.
초기화 로직은 생성자가 아닌 `@PostConstruct`에 작성해야 의존성 주입이 완료된 상태에서 실행됩니다.

기본 Scope는 singleton으로 애플리케이션 전체에서 하나의 인스턴스를 공유합니다.
singleton Bean은 상태를 가지면 안 됩니다. 동시 요청이 같은 인스턴스를 사용하기 때문입니다.

prototype Bean을 singleton에 주입하면 최초 한 번만 생성되므로, 매번 새 인스턴스가 필요하면 `ObjectProvider`를 사용합니다.

## 꼬리 질문

> [!question]- singleton Bean에 상태를 저장하면 어떤 문제가 생기는가?
> 모든 요청이 같은 인스턴스를 공유하기 때문에 동시 요청 시 데이터가 섞이는 race condition이 발생합니다. 상태가 필요하면 메서드 지역 변수나 request 스코프를 사용해야 합니다.

> [!question]- `@PostConstruct`와 생성자의 차이는?
> 생성자는 의존성 주입 전에 실행될 수 있지만, `@PostConstruct`는 DI가 완료된 후 실행됩니다. 주입된 의존성을 사용하는 초기화 로직은 `@PostConstruct`에 작성해야 합니다.

> [!question]- prototype Bean의 `@PreDestroy`가 호출되지 않는 이유는?
> 컨테이너가 prototype Bean은 생성까지만 관리하고 이후 생명주기를 추적하지 않기 때문입니다. 리소스 정리가 필요하면 직접 관리해야 합니다.

> [!question]- 웹 스코프 Bean에 `proxyMode`가 필요한 이유는?
> singleton Bean이 생성되는 시점에는 아직 HTTP 요청이 없어서 request 스코프 Bean을 바로 주입할 수 없습니다. 프록시가 실제 요청 시점에 Bean을 가져오도록 위임합니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[aop]]