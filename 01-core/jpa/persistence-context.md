---
title: Persistence Context
description: JPA 영속성 컨텍스트의 동작 원리와 실무 영향
---

# Persistence Context

## 한 줄 정의

영속성 컨텍스트는 Entity를 관리하는 JPA의 1차 캐시 공간으로, 동일성 보장, 변경 감지, 쓰기 지연을 제공한다.

## 실무에서 왜 중요한가

영속성 컨텍스트를 모르면 다음 상황에서 원인을 파악할 수 없다.

- 같은 id로 두 번 조회했는데 쿼리가 한 번만 나간다.
- Entity 필드를 변경했는데 `save()`를 호출하지 않아도 UPDATE가 나간다.
- 트랜잭션 밖에서 Entity를 수정했는데 DB에 반영되지 않는다.
- `@Transactional`이 없는 메서드에서 지연 로딩이 실패한다.
- 같은 row를 가리키는 두 객체가 `==`로 true가 된다.

## 영속성 컨텍스트의 기능

### 1차 캐시

```java
@Transactional
public void example() {
    User user1 = entityManager.find(User.class, 1L); // SELECT 쿼리 실행
    User user2 = entityManager.find(User.class, 1L); // 캐시에서 반환, 쿼리 없음

    System.out.println(user1 == user2); // true - 동일성 보장
}
```

같은 트랜잭션 안에서 같은 id로 조회하면 1차 캐시에서 반환한다. DB 접근이 줄어들고 객체 동일성이 보장된다.

### 쓰기 지연 (Transactional Write-Behind)

```java
@Transactional
public void example() {
    entityManager.persist(user1); // INSERT SQL을 쓰기 지연 저장소에 보관
    entityManager.persist(user2); // INSERT SQL을 쓰기 지연 저장소에 보관

    // 트랜잭션 커밋 시점에 모아둔 SQL을 한 번에 실행
}
```

`persist()` 시점에 바로 SQL이 나가지 않고, flush 시점에 모아서 실행한다.

### 변경 감지 (Dirty Checking)

트랜잭션 커밋 시 영속성 컨텍스트가 스냅샷과 현재 상태를 비교해서 변경된 필드만 UPDATE한다. `save()`를 호출하지 않아도 영속 상태 Entity의 변경은 자동으로 반영된다.

자세한 동작 원리와 주의점은 [[dirty-checking|Dirty Checking]] 문서에서 다룬다.

## Entity 생명주기

```
비영속 (new)  →  persist()  →  영속 (managed)
                                    ↕ flush/find
                              DB와 동기화
영속 (managed)  →  detach()/clear()  →  준영속 (detached)
영속 (managed)  →  remove()  →  삭제 (removed)
```

| 상태 | 의미 | 변경 감지 |
|---|---|---|
| 비영속 (new) | `new`로 생성만 한 상태 | X |
| 영속 (managed) | 영속성 컨텍스트에 관리되는 상태 | O |
| 준영속 (detached) | 영속성 컨텍스트에서 분리된 상태 | X |
| 삭제 (removed) | 삭제 예정 상태 | - |

## 영속성 컨텍스트의 범위

Spring에서 영속성 컨텍스트의 생명주기는 기본적으로 트랜잭션과 같다.

```java
@Transactional
public void process() {
    // 여기서 영속성 컨텍스트 시작
    User user = userRepository.findById(1L).orElseThrow();
    user.setName("newName"); // 변경 감지 대상
    // 메서드 종료 시 트랜잭션 커밋 → flush → 영속성 컨텍스트 종료
}
```

`@Transactional`이 없는 메서드에서는 각 repository 호출마다 별도 트랜잭션이 열리고 닫힌다. 이 경우 Entity는 조회 직후 준영속 상태가 되어 지연 로딩이 실패한다.

## 자주 나는 실수

- 트랜잭션 밖에서 Entity를 수정하고 DB에 반영될 것으로 기대한다.
- `@Transactional`이 없는 메서드에서 지연 로딩을 시도해서 `LazyInitializationException`이 발생한다.
- 영속성 컨텍스트가 1차 캐시 역할을 하는 것을 모르고, 불필요한 조회를 반복한다.
- 대량 데이터를 영속성 컨텍스트에 올려서 메모리가 부족해진다.
- `clear()` 없이 배치 처리를 해서 영속성 컨텍스트가 계속 커진다.

## 핵심 요약

영속성 컨텍스트는 Entity를 관리하는 1차 캐시 공간으로, 동일성 보장, 쓰기 지연, 변경 감지를 제공합니다.

같은 트랜잭션 안에서 같은 id로 조회하면 캐시에서 반환하고, Entity 필드를 변경하면 커밋 시점에 자동으로 UPDATE가 실행됩니다.

Spring에서 영속성 컨텍스트의 범위는 `@Transactional`과 같습니다.
트랜잭션 밖에서는 Entity가 준영속 상태가 되어 변경 감지와 지연 로딩이 동작하지 않습니다.

## 꼬리 질문

> [!question]- 1차 캐시와 2차 캐시의 차이는?
> 1차 캐시는 영속성 컨텍스트(트랜잭션) 범위이고, 2차 캐시는 애플리케이션 범위입니다. 1차 캐시는 자동으로 동작하지만, 2차 캐시는 별도 설정이 필요합니다.

> [!question]- 준영속 상태에서 변경 감지가 안 되는 이유는?
> 변경 감지는 영속성 컨텍스트가 스냅샷과 현재 상태를 비교하는 메커니즘입니다. 준영속 Entity는 영속성 컨텍스트에서 분리되었으므로 비교 대상이 없습니다.

> [!question]- `entityManager.merge()`는 언제 사용하는가?
> 준영속 Entity를 다시 영속 상태로 만들 때 사용합니다. 새로운 영속 Entity를 반환하며, 원본 객체는 여전히 준영속입니다.

> [!question]- 대량 데이터 처리 시 영속성 컨텍스트를 어떻게 관리하는가?
> 일정 건수마다 `flush()`와 `clear()`를 호출해서 영속성 컨텍스트를 비워야 합니다. 그렇지 않으면 메모리 사용량이 계속 늘어납니다.

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[dirty-checking]]
- [[transaction-and-flush]]
- [[lazy-and-eager-loading]]