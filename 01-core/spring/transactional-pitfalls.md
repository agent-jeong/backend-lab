---
title: "@Transactional 동작 실패 케이스"
description: "@Transactional 미적용 원인을 빠르게 진단하는 체크리스트"
---

# @Transactional 동작 실패 케이스

## 한 줄 정의

`@Transactional`은 AOP 프록시 기반이므로, 프록시를 우회하거나 프록시가 생성되지 않는 조건에서는 트랜잭션이 적용되지 않는다.

## 실무에서 왜 문제 되는가

- 데이터 정합성이 깨졌는데 `@Transactional`을 붙여놨기 때문에 원인을 못 찾는다.
- 코드 리뷰에서 걸러내기 어렵다 (컴파일 에러가 아니라 런타임에서만 드러남).
- 테스트 환경에서는 동작하지만 운영에서 데이터 불일치가 발생하는 원인이 된다.

## 미적용 원인 진단 체크리스트

### 1. 같은 클래스 내부 호출 (Self-Invocation)

```java
@Service
public class OrderService {

    public void process() {
        this.createOrder(); // ❌ 프록시를 거치지 않음
    }

    @Transactional
    public void createOrder() {
        // 트랜잭션 미적용
    }
}
```

**원인**: `this`는 프록시가 아닌 실제 객체를 가리킨다.

**해결**:
- 메서드를 **별도 클래스로 분리** (가장 권장)
- `ApplicationContext`에서 빈을 다시 가져와 호출 (비권장)

### 2. private 메서드

```java
@Transactional
private void internalProcess() { // ❌ CGLIB이 오버라이드 불가
    // 트랜잭션 미적용
}
```

**원인**: CGLIB 프록시는 상속 기반이라 `private`을 오버라이드할 수 없다.

**해결**: `public` 또는 `protected`로 변경.

### 3. final 클래스 또는 메서드

```java
@Service
public final class OrderService { // ❌ CGLIB이 상속 불가
    @Transactional
    public void createOrder() { }
}
```

**원인**: CGLIB은 클래스를 상속해서 프록시를 만드므로 `final`이면 불가.

### 4. checked 예외에서 롤백 안 됨

```java
@Transactional
public void process() throws IOException {
    throw new IOException(); // ❌ 기본 설정에서 롤백되지 않음
}
```

**원인**: Spring 기본 정책은 `RuntimeException`과 `Error`만 롤백.

**해결**: `@Transactional(rollbackFor = Exception.class)` 명시.

### 5. try-catch로 예외를 삼킴

```java
@Transactional
public void process() {
    try {
        riskyOperation();
    } catch (RuntimeException e) {
        log.error("에러 발생", e); // ❌ 예외가 프록시까지 전파되지 않음
    }
}
```

**원인**: 프록시는 메서드에서 예외가 던져져야 롤백을 판단한다. catch하면 프록시는 정상 완료로 인식해서 커밋한다.

**해결**:
- catch 후 `throw`로 다시 던진다
- `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()` 호출

### 6. REQUIRES_NEW를 내부 호출로 사용

```java
@Service
public class OrderService {

    @Transactional
    public void createOrder() {
        this.saveLog(); // ❌ 내부 호출 → REQUIRES_NEW 무시
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void saveLog() { }
}
```

**원인**: 내부 호출이므로 프록시를 거치지 않아 전파 설정이 무시된다.

**해결**: `saveLog()`를 별도 빈으로 분리.

## 빠른 진단 플로우

```
@Transactional이 안 먹힌다
  ├─ 호출 경로가 외부(다른 빈)에서 오는가?
  │   └─ 아니오 → 내부 호출 문제 (self-invocation)
  ├─ 메서드가 public인가?
  │   └─ 아니오 → private/final 문제
  ├─ 예외가 프록시까지 전파되는가?
  │   └─ 아니오 → try-catch로 삼키는 문제
  ├─ 예외가 RuntimeException인가?
  │   └─ 아니오 → checked 예외 롤백 정책 문제
  └─ 클래스가 Spring 빈으로 등록되어 있는가?
      └─ 아니오 → 프록시 자체가 생성되지 않음
```

## 자주 나는 실수

- 코드 리팩토링으로 메서드를 같은 클래스로 합쳤더니 트랜잭션이 깨진다.
- `@Transactional`이 붙어 있으니 당연히 동작한다고 가정한다.
- 테스트 환경에서는 동작하지만 운영에서 데이터 불일치가 발생한다 (catch 문제).
- Kotlin의 기본 `open` 클래스에서는 괜찮지만 `final` 메서드에서 문제가 된다.

## 핵심 요약

`@Transactional`이 동작하지 않는 원인은 대부분 프록시를 우회하는 호출 구조에 있습니다.
가장 흔한 원인은 같은 클래스 내부 호출(self-invocation)이고, 해결 방법은 메서드를 별도 빈으로 분리하는 것입니다.

checked 예외의 기본 미롤백과 try-catch로 예외를 삼키는 패턴도 실무에서 자주 발생합니다.
면접에서는 "원인 → 프록시 구조 → 해결 방법"을 연결해서 설명하면 됩니다.

## 꼬리 질문

> [!question]- 내부 호출 문제를 어떻게 발견할 수 있는가?
> 통합 테스트에서 예외 발생 후 DB에 데이터가 남아 있으면 의심합니다. 또는 트랜잭션 로그(`logging.level.org.springframework.transaction=DEBUG`)로 트랜잭션 시작/커밋 여부를 확인합니다.

> [!question]- `@Transactional`을 테스트에서 검증하는 방법은?
> 예외를 강제로 발생시킨 뒤 DB 상태를 확인합니다. 또는 `TransactionSynchronizationManager.isActualTransactionActive()`로 트랜잭션 활성 여부를 검증합니다.

## 관련 문서

- [[aop]]
- [[transaction-integration]]
- [[02-practical-backend/transaction/spring-transaction|spring-transaction]]