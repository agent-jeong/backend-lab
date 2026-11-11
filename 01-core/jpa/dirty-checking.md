---
title: "변경 감지 동작 원리"
description: save() 없이 UPDATE가 나가는 이유와, 반대로 안 나가는 경우
tags: [concept, jpa]
---

# 변경 감지(Dirty Checking) 동작 원리

변경 감지(Dirty Checking)는 영속성 컨텍스트가 처음 읽어 둔 Entity의 사본(스냅샷)과 지금 값을 비교해서, 바뀐 Entity만 골라 UPDATE를 날리는 기능이다.

그래서 주문 상태를 바꿀 때 `save()`를 부르지 않아도 DB에 들어간다. 대신 트랜잭션 밖에서 고친 값은 들어가지 않고, 수천 건을 고치면 UPDATE가 한 건씩 나가서 느리다. 변경 감지는 영속 상태 Entity를 트랜잭션 안에서 고칠 때만 돈다.

## 동작

```
1. Entity 조회 → 영속성 컨텍스트에 스냅샷 저장
2. Entity 필드 변경
3. 트랜잭션 커밋 직전 → flush(쌓인 변경을 SQL로 DB에 보내는 일) 발생
4. 스냅샷과 현재 상태 비교
5. 바뀐 Entity마다 UPDATE SQL을 만들어 실행
6. 트랜잭션 커밋
```

```java
@Transactional
public void updateUserName(Long id, String newName) {
    User user = userRepository.findById(id).orElseThrow();
    user.setName(newName);
    // flush 시점에 스냅샷과 비교 → name이 변경됨 → UPDATE 실행
}
```

`userRepository.save(user)`를 부르지 않아도 커밋할 때 UPDATE가 나간다.

| 조건 | 필요한가 |
|---|---|
| Entity가 영속 상태(managed) | 꼭 필요 |
| `@Transactional` 안에서 수정 | 꼭 필요 |
| `save()` 호출 | 필요 없음 |
| setter 호출 | 필드 값만 바뀌면 된다 (setter가 아니어도 된다) |

## 동작하지 않는 경우

```java
// 트랜잭션 없음 → 준영속 상태 → 변경 감지 X
public void updateWithoutTransaction(Long id, String newName) {
    User user = userRepository.findById(id).orElseThrow();
    user.setName(newName);
    // UPDATE 실행되지 않음
}
```

```java
// 새로 생성한 객체 → 비영속 상태 → 변경 감지 X
@Transactional
public void createAndModify() {
    User user = new User("kim");
    user.setName("lee");
    // persist하지 않으면 아무 일도 안 일어남
}
```

## UPDATE 범위와 @DynamicUpdate

Hibernate는 기본으로 모든 컬럼을 UPDATE한다.

```sql
-- name만 바꿨지만 전체 컬럼이 UPDATE에 포함
UPDATE users SET name=?, email=?, status=?, updated_at=? WHERE id=?
```

바뀐 컬럼만 UPDATE하려면 `@DynamicUpdate`를 쓴다.

```java
@Entity
@DynamicUpdate
public class User {
    // 변경된 필드만 UPDATE SQL에 포함
}
```

대신 `@DynamicUpdate`는 SQL을 매번 새로 만들어서, 미리 만들어 둔 PreparedStatement를 재사용하는 이점이 줄어든다. 컬럼이 많은데 그중 몇 개만 자주 바뀔 때 쓴다.

## 대량 수정은 벌크 연산으로

변경 감지는 UPDATE를 한 건씩 실행한다. 많은 행을 한꺼번에 고칠 때는 벌크 연산이 낫다.

```java
// 변경 감지: 1000건이면 UPDATE 1000번
@Transactional
public void deactivateAll(List<Long> userIds) {
    for (Long id : userIds) {
        User user = userRepository.findById(id).orElseThrow();
        user.setStatus(UserStatus.INACTIVE);
    }
}

// 벌크 연산: UPDATE 1번
@Modifying(clearAutomatically = true)
@Query("UPDATE User u SET u.status = :status WHERE u.id IN :ids")
int bulkUpdateStatus(@Param("ids") List<Long> ids, @Param("status") UserStatus status);
```

벌크 연산은 영속성 컨텍스트를 거치지 않고 DB에 바로 간다. 그래서 `clearAutomatically = true`로 영속성 컨텍스트에 남은 옛 값을 비운다.

## 자주 깨지는 곳

- 트랜잭션 밖에서 Entity를 고치면, 준영속 상태라 UPDATE가 나가지 않는다.
- 반영이 안 될까 봐 `save()`를 습관처럼 부르면, 영속 상태에서는 쓸데없는 호출만 늘어난다.
- 대량 데이터를 변경 감지로 고치면, UPDATE 쿼리가 수천 번 나간다.
- 벌크 연산 뒤 영속성 컨텍스트를 비우지 않으면, 거기 남은 옛 데이터를 읽는다.
- `@DynamicUpdate`를 모든 Entity에 붙이면, 얻는 건 없이 PreparedStatement 재사용 이점만 잃는 경우가 많다.

## 한 번에 설명하기

> Dirty Checking은 영속 상태 Entity를 처음 읽었을 때의 스냅샷과 지금 값을 비교해서, 바뀐 것만 커밋할 때 UPDATE하는 기능입니다.
>
> 그래서 `@Transactional` 안에서 필드만 바꾸면 `save()` 없이도 DB에 들어가고, 트랜잭션 밖의 준영속 Entity는 바꿔도 안 들어갑니다.
>
> 많은 행을 고칠 때는 UPDATE가 한 건씩 나가니까 `@Modifying` 벌크 연산을 쓰고, 그 뒤에 영속성 컨텍스트를 비웁니다.

## 꼬리 질문

> [!question]- 변경 감지가 있는데 `save()`를 호출하면 어떻게 되는가?
> 이미 영속 상태인 Entity에 `save()`를 부르면 `merge()`가 실행되긴 하는데, 1차 캐시에 이미 있으니 SELECT가 더 나가지는 않습니다. 준영속(detached) Entity를 `merge()`할 때는 SELECT가 하나 더 나갑니다. 어쨌든 영속 상태라면 변경 감지가 알아서 하니 `save()`는 안 불러도 됩니다.

> [!question]- `@DynamicUpdate`를 항상 사용하면 안 되는 이유는?
> 바뀐 컬럼을 매번 확인해서 SQL을 새로 만들기 때문에, PreparedStatement를 재사용하는 이점이 줄어듭니다. 컬럼이 몇 개 없으면 전체를 UPDATE하는 쪽이 오히려 낫습니다.

> [!question]- 벌크 연산 후 영속성 컨텍스트를 비워야 하는 이유는?
> 벌크 연산은 영속성 컨텍스트를 건너뛰고 DB에 바로 실행됩니다. 영속성 컨텍스트에는 바뀌기 전 값이 그대로 남아 있어서, `clear()`하지 않으면 그 옛 값을 읽게 됩니다.

> [!question]- flush와 commit의 차이는?
> flush는 영속성 컨텍스트에 쌓인 변경을 SQL로 DB에 보내는 것이고, commit은 트랜잭션을 확정하는 겁니다. 그래서 flush한 뒤에도 rollback할 수 있습니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>변경 감지가 동작하는 핵심 조건은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="트랜잭션 안에서 영속 상태 Entity의 변경을 JPA가 스냅샷과 비교할 수 있어야 한다." aria-pressed="false">A. 트랜잭션 안의 영속 상태 Entity여야 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="준영속 Entity는 변경 감지 대상이 아니다." aria-pressed="false">B. 준영속 Entity면 자동으로 변경 감지된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="static 필드 변경은 Entity 상태 변경 감지와 무관하다." aria-pressed="false">C. Entity의 static 필드만 바꾸면 된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>벌크 update/delete 실행 후에는 영속성 컨텍스트의 Entity 상태와 DB 상태가 달라질 수 있다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="벌크 연산은 영속성 컨텍스트를 우회하므로 이후 조회/로직 전에 clear 또는 동기화 전략이 필요하다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="벌크 연산은 1차 캐시의 모든 Entity를 자동 갱신하지 않는다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@DynamicUpdate를 항상 쓰지 않는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="변경 컬럼만 UPDATE할 수 있지만 SQL이 다양해져 쿼리 캐시나 실행 계획 재사용에 불리할 수 있다." aria-pressed="false">A. SQL 형태가 다양해지는 비용이 생길 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@DynamicUpdate가 모든 UPDATE를 막는 기능은 아니다." aria-pressed="false">B. UPDATE가 절대 실행되지 않게 만든다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@DynamicUpdate는 연관관계 fetch 전략을 바꾸는 기능이 아니다." aria-pressed="false">C. 지연 로딩을 즉시 로딩으로 바꾼다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Flushing](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#flushing)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[transaction-and-flush]]