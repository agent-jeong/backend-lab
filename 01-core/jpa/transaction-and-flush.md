---
title: "트랜잭션과 flush 시점"
description: JPA 트랜잭션 경계와 flush 동작의 실무 이해
---

# 트랜잭션과 flush 시점

## 한 줄 정의

트랜잭션은 데이터 일관성을 보장하는 작업 단위이고, flush는 영속성 컨텍스트의 변경 내용을 DB에 SQL로 전송하는 동작이다.

## 실무에서 왜 중요한가

트랜잭션과 flush를 모르면 다음 문제가 생긴다.

- `@Transactional`을 붙이지 않아서 변경 감지가 동작하지 않는다.
- `@Transactional`을 private 메서드나 같은 클래스 내부 호출에 붙여서 동작하지 않는다.
- checked exception에서 롤백이 안 되는 이유를 모른다.
- JPQL 쿼리 실행 전에 flush가 자동으로 발생하는 것을 모르고 혼란이 생긴다.
- 읽기 전용 작업에 `readOnly = true`를 설정하지 않아 불필요한 flush가 발생한다.

## @Transactional 동작 원리

Spring의 `@Transactional`은 AOP 프록시를 통해 동작한다.

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

### 동작하지 않는 경우

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

`@Transactional`은 외부에서 프록시를 통해 호출해야 동작한다.

## 롤백 규칙

| 예외 종류 | 기본 롤백 여부 |
|---|---|
| Unchecked (`RuntimeException`) | 롤백 |
| Checked (`Exception`) | 커밋 |
| `Error` | 롤백 |

```java
// checked exception에서도 롤백이 필요하면
@Transactional(rollbackFor = Exception.class)
public void process() throws IOException {
    // IOException 발생 시에도 롤백
}
```

## Flush 동작

flush는 영속성 컨텍스트의 변경 내용을 DB에 SQL로 보내는 것이다. **트랜잭션을 커밋하는 것이 아니다.**

### flush가 발생하는 시점

| 시점 | 이유 |
|---|---|
| 트랜잭션 커밋 시 | 변경 내용을 DB에 반영하기 위해 |
| JPQL 쿼리 실행 전 | 영속성 컨텍스트와 DB의 일관성을 맞추기 위해 |
| `entityManager.flush()` 직접 호출 | 명시적 flush |

### JPQL 실행 전 auto flush

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

JPA는 JPQL 실행 전에 자동으로 flush해서 영속성 컨텍스트의 변경 내용이 쿼리 결과에 반영되도록 한다.

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
| flush 생략 | 변경 감지를 위한 스냅샷 비교와 flush를 생략 |
| DB 힌트 | DB에 따라 읽기 전용 최적화 적용 |
| 실수 방지 | 읽기 전용 메서드에서 실수로 데이터를 변경하는 것을 방지 |

읽기 전용 작업에는 항상 `readOnly = true`를 설정하는 것이 좋다.

## 트랜잭션 전파 (Propagation)

| 전파 옵션 | 동작 |
|---|---|
| `REQUIRED` (기본) | 기존 트랜잭션이 있으면 참여, 없으면 새로 생성 |
| `REQUIRES_NEW` | 항상 새 트랜잭션 생성, 기존 트랜잭션 일시 중지 |
| `SUPPORTS` | 기존 트랜잭션이 있으면 참여, 없으면 트랜잭션 없이 실행 |

```java
@Transactional
public void order() {
    orderRepository.save(order);
    notificationService.sendNotification(order); // 알림 실패해도 주문은 유지
}

@Service
public class NotificationService {

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void sendNotification(Order order) {
        // 별도 트랜잭션 → 여기서 예외 발생해도 주문 트랜잭션에 영향 없음
    }
}
```

## 자주 나는 실수

- 같은 클래스 내부에서 `@Transactional` 메서드를 호출해서 트랜잭션이 동작하지 않는다.
- private 메서드에 `@Transactional`을 붙인다.
- checked exception에서 롤백이 안 되는 것을 모른다.
- 읽기 전용 메서드에 `readOnly = true`를 설정하지 않는다.
- `REQUIRES_NEW`를 남용해서 트랜잭션이 너무 많이 생성된다.
- flush 시점을 모르고 JPQL 쿼리 결과에 방금 변경한 데이터가 포함되는지 혼동한다.

## 핵심 요약

Spring의 `@Transactional`은 AOP 프록시를 통해 동작하므로, 같은 클래스 내부 호출이나 private 메서드에서는 동작하지 않습니다.

기본적으로 unchecked exception에서만 롤백하고, checked exception에서는 커밋합니다.
checked exception에서도 롤백이 필요하면 `rollbackFor`를 명시해야 합니다.

flush는 영속성 컨텍스트의 변경 내용을 DB에 SQL로 전송하는 동작이며, 트랜잭션 커밋 시와 JPQL 실행 전에 자동으로 발생합니다.
읽기 전용 작업에는 `@Transactional(readOnly = true)`를 설정해서 불필요한 flush를 방지합니다.

## 꼬리 질문

> [!question]- `@Transactional`이 같은 클래스 내부 호출에서 동작하지 않는 이유는?
> Spring AOP는 프록시 기반으로 동작합니다. 같은 클래스 내부 호출은 프록시를 거치지 않고 직접 호출되므로 트랜잭션 AOP가 적용되지 않습니다.

> [!question]- flush와 commit의 차이는?
> flush는 SQL을 DB에 전송하는 것이고, commit은 트랜잭션을 확정하는 것입니다. flush 후에도 트랜잭션이 롤백되면 DB 변경이 취소됩니다.

> [!question]- `REQUIRES_NEW`를 사용하면 어떤 일이 생기는가?
> 기존 트랜잭션을 일시 중지하고 새 트랜잭션을 시작합니다. 새 트랜잭션이 롤백되어도 기존 트랜잭션에 영향을 주지 않습니다. 단, DB 커넥션을 추가로 사용합니다.

> [!question]- JPQL 실행 전에 flush가 발생하는 이유는?
> 영속성 컨텍스트에 아직 DB에 반영되지 않은 변경이 있으면, JPQL 결과와 불일치가 생깁니다. 이를 방지하기 위해 JPA가 JPQL 실행 전에 자동으로 flush합니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>flush와 commit의 차이로 가장 적절한 것은?</p>
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

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[dirty-checking]]
- [[02-practical-backend/transaction/transaction|transaction]]