---
title: "트랜잭션과 flush 시점"
description: flush와 commit은 어떻게 다르고, @Transactional이 안 걸리는 경우는 언제인지
tags: [concept, jpa]
---

# 트랜잭션과 flush 시점

트랜잭션은 주문 저장과 재고 차감처럼 함께 성공하거나 함께 취소돼야 하는 작업을 하나로 묶는 단위다. flush는 영속성 컨텍스트에 쌓인 변경을 SQL로 DB에 보내는 일이다.

둘은 다르다. flush는 SQL을 보낼 뿐 확정하지 않고, 확정은 commit이 한다. 그리고 Spring의 `@Transactional`은 프록시를 거쳐 호출될 때만 걸린다. 이 두 가지를 모르면 바꾼 값이 왜 안 들어갔는지, 왜 롤백이 안 됐는지 설명하지 못한다.

## @Transactional은 프록시로 동작한다

```
호출자 → 프록시 → 트랜잭션 시작 → 실제 메서드 실행 → 커밋/롤백
```

```java
@Service
public class UserService {

    @Transactional
    public void updateUser(Long id, String name) {
        User user = userRepository.findById(id).orElseThrow();
        user.setName(name);
        // 메서드 종료 → 트랜잭션 커밋 → flush → UPDATE 실행
    }
}
```

같은 클래스 안에서 부르면 프록시를 거치지 않아서 트랜잭션이 걸리지 않는다. private 메서드에 붙여도 마찬가지다.

```java
@Service
public class UserService {

    public void outer() {
        inner(); // 같은 클래스 내부 호출 → 프록시를 거치지 않음
    }

    @Transactional
    public void inner() {
        // @Transactional이 동작하지 않음
    }
}
```

## 롤백 규칙

| 예외 종류 | 기본으로 롤백하나 |
|---|---|
| Unchecked (`RuntimeException`) | 롤백 |
| Checked (`Exception`) | 커밋 |
| `Error` | 롤백 |

checked exception에서도 롤백하려면 `rollbackFor`를 적는다.

```java
// checked exception에서도 롤백이 필요하면
@Transactional(rollbackFor = Exception.class)
public void process() throws IOException {
    // IOException 발생 시에도 롤백
}
```

## Flush

flush는 영속성 컨텍스트에 쌓인 변경을 SQL로 DB에 보내는 것이다. 커밋까지 하지는 않는다. flush한 뒤에 롤백하면 DB 변경은 취소된다.

| 언제 | 왜 |
|---|---|
| 트랜잭션을 커밋할 때 | 바뀐 내용을 DB에 넣어야 하니까 |
| JPQL 쿼리를 실행하기 전 | 영속성 컨텍스트와 DB 내용을 맞춰 놓고 조회하려고 |
| `entityManager.flush()`를 직접 부를 때 | 직접 시켰으니까 |

JPQL을 실행하기 전에 자동으로 flush(auto flush)하기 때문에, 방금 `persist()`한 데이터가 JPQL 결과에 들어 있다.

```java
@Transactional
public void example() {
    User user = new User("kim");
    entityManager.persist(user); // 아직 INSERT 안 함

    // JPQL 실행 전에 auto flush → INSERT 실행
    List<User> users = entityManager
        .createQuery("SELECT u FROM User u", User.class)
        .getResultList();
    // kim이 결과에 포함됨
}
```

## @Transactional(readOnly = true)

```java
@Transactional(readOnly = true)
public List<UserResponse> getUsers() {
    return userRepository.findAll().stream()
        .map(UserResponse::from)
        .toList();
}
```

| 효과 | 설명 |
|---|---|
| flush 생략 | 변경 감지용 스냅샷 비교와 flush를 건너뛴다 |
| DB 힌트 | DB에 따라 읽기 전용으로 더 가볍게 처리한다 |
| 실수 방지 | 읽기만 하는 메서드에서 실수로 데이터를 바꾸는 걸 막는다 |

읽기만 하는 작업에는 늘 `readOnly = true`를 붙인다.

## 트랜잭션 전파 (Propagation)

| 전파 옵션 | 동작 |
|---|---|
| `REQUIRED` (기본) | 이미 트랜잭션이 있으면 거기 끼고, 없으면 새로 만든다 |
| `REQUIRES_NEW` | 늘 새 트랜잭션을 만들고, 기존 트랜잭션은 잠시 멈춰 둔다 |
| `SUPPORTS` | 이미 트랜잭션이 있으면 거기 끼고, 없으면 트랜잭션 없이 실행한다 |

```java
@Transactional
public void order() {
    orderRepository.save(order);
    try {
        notificationService.sendNotification(order);
    } catch (NotificationException e) {
        log.warn("Notification failed. orderId={}", order.getId(), e); // 잡아야 주문이 유지된다
    }
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification(Order order) {
        // 별도 트랜잭션 → 여기서 예외 발생해도 주문 트랜잭션에 영향 없음
    }
}
```

`REQUIRES_NEW`가 떼어 주는 건 트랜잭션뿐이다. 알림 쪽에서 난 예외는 그대로 `order()`까지 올라오기 때문에, 위처럼 잡지 않으면 주문 트랜잭션도 롤백된다.

`REQUIRES_NEW`는 DB 커넥션을 하나 더 쓴다. 기존 트랜잭션이 커넥션을 쥔 채로 멈춰 있기 때문이다.

## 자주 깨지는 곳

- 같은 클래스 안에서 `@Transactional` 메서드를 부르면, 프록시를 거치지 않아서 트랜잭션이 없다.
- private 메서드에 `@Transactional`을 붙이면, 마찬가지로 걸리지 않는다.
- `@Transactional`을 아예 빠뜨리면, 변경 감지가 돌지 않는다.
- checked exception도 롤백된다고 믿으면, 예외가 났는데 그대로 커밋된다.
- 읽기만 하는 메서드에 `readOnly = true`를 빠뜨리면, 쓸데없는 스냅샷 비교와 flush가 돈다.
- `REQUIRES_NEW`를 여기저기 쓰면, 트랜잭션과 커넥션이 필요 이상으로 늘어난다.
- auto flush를 모르면, 방금 바꾼 데이터가 JPQL 결과에 왜 들어 있는지 헷갈린다.

## 한 번에 설명하기

> Spring의 `@Transactional`은 AOP 프록시로 동작해서, 같은 클래스 안에서 부르거나 private 메서드에 붙이면 걸리지 않습니다.
>
> 기본으로는 unchecked exception만 롤백하니까, checked exception에서도 롤백하려면 `rollbackFor`를 적어 둡니다.
>
> flush는 바뀐 내용을 SQL로 보내는 것이지 확정하는 게 아니고, 커밋할 때와 JPQL을 실행하기 전에 자동으로 일어납니다. 읽기만 하는 작업에는 `readOnly = true`를 붙여서 쓸데없는 flush를 막습니다.

## 꼬리 질문

> [!question]- `@Transactional`이 같은 클래스 내부 호출에서 동작하지 않는 이유는?
> Spring AOP가 프록시로 동작해서입니다. 같은 클래스 안에서 부르면 프록시를 거치지 않고 `this`로 바로 부르니까, 트랜잭션을 여는 코드가 끼어들 틈이 없습니다.

> [!question]- flush와 commit의 차이는?
> flush는 SQL을 DB에 보내는 것이고, commit은 트랜잭션을 확정하는 겁니다. 그래서 flush한 뒤라도 트랜잭션이 롤백되면 DB 변경은 취소됩니다.

> [!question]- `REQUIRES_NEW`를 사용하면 어떤 일이 생기는가?
> 기존 트랜잭션을 잠시 멈추고 새 트랜잭션을 엽니다. 새 트랜잭션이 롤백돼도 기존 트랜잭션은 그대로입니다. 대신 DB 커넥션을 하나 더 씁니다.

> [!question]- JPQL 실행 전에 flush가 발생하는 이유는?
> JPQL은 DB에 바로 조회하는데, 영속성 컨텍스트에 아직 DB로 안 보낸 변경이 있으면 결과가 실제와 달라집니다. 그래서 JPA가 JPQL을 실행하기 전에 먼저 flush합니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>flush와 commit의 차이로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="flush는 영속성 컨텍스트 변경을 DB에 SQL로 반영하는 과정이고, commit은 트랜잭션을 확정한다." aria-pressed="false">A. flush는 SQL 반영, commit은 트랜잭션 확정이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="flush가 항상 commit을 의미하지 않는다." aria-pressed="false">B. flush가 발생하면 즉시 commit까지 완료된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="commit 시점에 flush가 발생할 수 있다." aria-pressed="false">C. commit은 flush와 전혀 무관하다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>JPQL 실행 전에 flush가 발생할 수 있는 이유는 쿼리 결과가 영속성 컨텍스트 변경분과 모순되지 않게 하기 위해서다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="FlushMode.AUTO에서는 쿼리 실행 전 변경사항을 DB에 반영해 조회 결과 정합성을 맞출 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JPQL 전 flush는 조회 정합성과 관련된 동작이다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>같은 클래스 내부 호출에서 @Transactional이 동작하지 않을 수 있는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Spring 트랜잭션은 프록시 기반 AOP로 적용되므로 this 호출은 프록시를 거치지 않는다." aria-pressed="false">A. self-invocation이 프록시를 우회하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="메서드 이름이 원인이 아니다." aria-pressed="false">B. 메서드 이름에 Transaction이 들어가지 않아서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="파라미터 개수와 직접 관련이 없다." aria-pressed="false">C. 파라미터가 없으면 트랜잭션이 적용되지 않는다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Flushing](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#flushing)
- [Spring Framework: Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[dirty-checking]]
- [[02-practical-backend/transaction/transaction|transaction]]