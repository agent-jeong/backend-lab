---
title: Dirty Checking
description: JPA 변경 감지의 동작 원리와 실무에서의 주의점
---

# Dirty Checking

## 한 줄 정의

Dirty Checking은 영속성 컨텍스트가 Entity의 스냅샷과 현재 상태를 비교해서, 변경된 필드를 자동으로 UPDATE하는 메커니즘이다.

## 실무에서 왜 중요한가

변경 감지를 모르면 다음 상황에서 혼란이 생긴다.

- `save()`를 호출하지 않았는데 UPDATE가 실행된다.
- Entity를 수정했는데 DB에 반영되지 않는다 (트랜잭션 밖).
- 의도하지 않은 필드까지 UPDATE에 포함된다.
- 대량 데이터를 수정할 때 한 건씩 UPDATE가 나가서 성능이 나빠진다.

## 동작 원리

```
1. Entity 조회 → 영속성 컨텍스트에 스냅샷 저장
2. Entity 필드 변경
3. 트랜잭션 커밋 → flush 발생
4. 스냅샷과 현재 상태 비교
5. 변경된 Entity에 대해 UPDATE SQL 생성 및 실행
```

```java
@Transactional
public void updateUserName(Long id, String newName) {
    User user = userRepository.findById(id).orElseThrow();
    user.setName(newName);
    // flush 시점에 스냅샷과 비교 → name이 변경됨 → UPDATE 실행
}
```

`userRepository.save(user)`를 호출하지 않아도 트랜잭션 커밋 시 자동으로 UPDATE가 실행된다.

## 변경 감지가 동작하는 조건

| 조건 | 필요 여부 |
|---|---|
| Entity가 영속 상태(managed) | 필수 |
| `@Transactional` 안에서 수정 | 필수 |
| `save()` 호출 | 불필요 |
| setter 호출 | 필드 값이 바뀌면 됨 (setter가 아니어도 가능) |

## 변경 감지가 동작하지 않는 경우

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

## UPDATE 범위

Hibernate의 기본 동작은 모든 컬럼을 UPDATE한다.

```sql
-- name만 바꿨지만 전체 컬럼이 UPDATE에 포함
UPDATE users SET name=?, email=?, status=?, updated_at=? WHERE id=?
```

변경된 컬럼만 UPDATE하려면 `@DynamicUpdate`를 사용한다.

```java
@Entity
@DynamicUpdate
public class User {
    // 변경된 필드만 UPDATE SQL에 포함
}
```

단, `@DynamicUpdate`는 매번 SQL을 새로 생성하므로 PreparedStatement 캐시 효과가 줄어든다. 컬럼 수가 많고 일부만 자주 변경되는 경우에 고려한다.

## 대량 수정 시 주의점

변경 감지는 한 건씩 UPDATE를 실행한다. 대량 수정에는 벌크 연산이 효율적이다.

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

벌크 연산은 영속성 컨텍스트를 거치지 않으므로 `clearAutomatically = true`로 캐시를 비워야 한다.

## 자주 나는 실수

- 트랜잭션 밖에서 Entity를 수정하고 반영될 것으로 기대한다.
- `save()`를 호출하지 않아서 반영이 안 된다고 생각하고, 불필요하게 `save()`를 호출한다.
- 대량 데이터를 변경 감지로 수정해서 UPDATE 쿼리가 수천 번 나간다.
- 벌크 연산 후 영속성 컨텍스트를 비우지 않아서 캐시된 이전 데이터를 읽는다.
- `@DynamicUpdate`를 무조건 좋은 것으로 생각하고 모든 Entity에 적용한다.

## 핵심 요약

Dirty Checking은 영속 상태 Entity의 스냅샷과 현재 상태를 비교해서 변경된 필드를 자동으로 UPDATE하는 메커니즘입니다.
`@Transactional` 안에서 Entity 필드를 수정하면 `save()` 호출 없이도 커밋 시 UPDATE가 실행됩니다.

변경 감지가 동작하려면 Entity가 영속 상태여야 하고 트랜잭션 안에서 수정해야 합니다.

대량 수정에는 변경 감지 대신 벌크 연산(`@Modifying` + JPQL)을 사용하고, 벌크 연산 후에는 영속성 컨텍스트를 반드시 비워야 합니다.

## 꼬리 질문

> [!question]- 변경 감지가 있는데 `save()`를 호출하면 어떻게 되는가?
> 이미 영속 상태인 Entity에 `save()`를 호출하면 `merge()`가 실행되지만, 1차 캐시에 이미 있으므로 추가 SELECT는 발생하지 않습니다. 다만 준영속(detached) 상태의 Entity를 `merge()`하면 SELECT가 추가됩니다. 영속 상태에서는 변경 감지가 자동으로 동작하므로 `save()` 호출이 불필요합니다.

> [!question]- `@DynamicUpdate`를 항상 사용하면 안 되는 이유는?
> 매번 변경된 컬럼을 확인하고 SQL을 새로 생성하므로 PreparedStatement 캐시 효과가 줄어듭니다. 컬럼 수가 적으면 전체 UPDATE가 오히려 효율적입니다.

> [!question]- 벌크 연산 후 영속성 컨텍스트를 비워야 하는 이유는?
> 벌크 연산은 DB에 직접 실행되어 영속성 컨텍스트를 거치지 않습니다. 캐시에는 이전 상태가 남아있으므로 `clear()`하지 않으면 변경 전 데이터를 읽게 됩니다.

> [!question]- flush와 commit의 차이는?
> flush는 영속성 컨텍스트의 변경 내용을 DB에 SQL로 전송하는 것이고, commit은 트랜잭션을 확정하는 것입니다. flush 후에도 rollback이 가능합니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[transaction-and-flush]]