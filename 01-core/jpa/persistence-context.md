---
title: "영속성 컨텍스트의 역할과 생명주기"
description: 같은 조회가 쿼리를 한 번만 날리고, save() 없이 UPDATE가 나가는 이유
tags: [concept, jpa]
---

# 영속성 컨텍스트의 역할과 생명주기

영속성 컨텍스트는 JPA가 조회하거나 저장한 Entity를 담아 두고 관리하는 공간이다. 1차 캐시라고도 부른다. 같은 row를 같은 객체로 돌려주는 것, SQL을 모아 뒀다가 한꺼번에 보내는 것, 바뀐 값을 찾아 UPDATE하는 것이 모두 여기서 일어난다.

JPA가 가끔 이상하게 굴 때 원인은 대개 여기 있다. 같은 주문을 두 번 조회했는데 쿼리는 한 번만 나가고, `save()`를 안 불렀는데 UPDATE가 나가고, 트랜잭션 밖에서 고친 값은 DB에 안 들어간다. 모두 그 Entity가 지금 영속성 컨텍스트 안에 있느냐로 갈린다.

## 1차 캐시

```java
@Transactional
public void example() {
    User user1 = entityManager.find(User.class, 1L); // SELECT 쿼리 실행
    User user2 = entityManager.find(User.class, 1L); // 캐시에서 반환, 쿼리 없음

    System.out.println(user1 == user2); // true - 동일성 보장
}
```

같은 트랜잭션 안에서 같은 id로 조회하면 1차 캐시에서 꺼내 준다. DB에 덜 가고, 같은 row를 가리키는 두 변수가 `==`로 비교해도 true다.

1차 캐시에서 꺼내 주는 건 `find()`(`findById()`)처럼 id로 찾을 때뿐이다. JPQL이나 QueryDSL 쿼리는 늘 DB에 SQL을 보낸다. 다만 결과 행 중에 이미 영속성 컨텍스트에 있는 Entity가 있으면, DB에서 읽은 값이 아니라 원래 있던 객체를 돌려준다.

## 쓰기 지연 (Transactional Write-Behind)

```java
@Transactional
public void example() {
    entityManager.persist(user1); // INSERT SQL을 쓰기 지연 저장소에 보관
    entityManager.persist(user2); // INSERT SQL을 쓰기 지연 저장소에 보관

    // 트랜잭션 커밋 시점에 모아둔 SQL을 한 번에 실행
}
```

`persist()`를 부를 때는 SQL이 나가지 않고, flush할 때 모아서 실행한다.

예외가 하나 있다. `@GeneratedValue(strategy = IDENTITY)`는 id를 DB가 만들기 때문에 `persist()`하자마자 INSERT가 나간다. 그래서 MySQL auto_increment를 쓰면 쓰기 지연도 JDBC batch insert도 덕을 못 본다. 자세한 내용은 [[entity-table-mapping]]에 있다.

## 변경 감지 (Dirty Checking)

트랜잭션을 커밋할 때 영속성 컨텍스트가 처음 읽은 스냅샷과 지금 값을 비교해서, 바뀐 게 있으면 UPDATE를 날린다. 기본은 모든 컬럼을 UPDATE하고, `@DynamicUpdate`를 붙이면 바뀐 컬럼만 UPDATE한다. 영속 상태 Entity라면 `save()`를 안 불러도 바뀐 값이 들어간다.

자세한 동작과 주의점은 [[dirty-checking|Dirty Checking]]에 있다.

## Entity 생명주기

```
비영속 (new)  →  persist()  →  영속 (managed)
                                    ↕ flush/find
                              DB와 동기화
영속 (managed)  →  detach()/clear()  →  준영속 (detached)
영속 (managed)  →  remove()  →  삭제 (removed)
```

| 상태 | 뜻 | 변경 감지 |
|---|---|---|
| 비영속 (new) | `new`로 만들기만 했다 | X |
| 영속 (managed) | 영속성 컨텍스트가 관리하고 있다 | O |
| 준영속 (detached) | 영속성 컨텍스트에서 떨어져 나왔다 | X |
| 삭제 (removed) | 지워질 예정이다 | - |

## 범위는 트랜잭션과 같다

Spring에서는 기본으로 영속성 컨텍스트가 트랜잭션과 같이 열리고 같이 닫힌다.

```java
@Transactional
public void process() {
    // 여기서 영속성 컨텍스트 시작
    User user = userRepository.findById(1L).orElseThrow();
    user.setName("newName"); // 변경 감지 대상
    // 메서드 종료 시 트랜잭션 커밋 → flush → 영속성 컨텍스트 종료
}
```

OSIV가 꺼져 있을 때 `@Transactional`이 없는 메서드에서는 repository를 부를 때마다 트랜잭션과 영속성 컨텍스트가 따로 열리고 닫힌다. 그래서 Entity는 조회하자마자 준영속이 되고, 지연 로딩이 실패한다. OSIV가 켜져 있으면 요청이 끝날 때까지 영속성 컨텍스트가 살아 있어서 지연 로딩이 된다.

## 자주 깨지는 곳

- 트랜잭션 밖에서 Entity를 고치면, 준영속 Entity라 변경 감지가 돌지 않아서 DB에 안 들어간다.
- `@Transactional` 없는 메서드에서 지연 로딩을 하면, `LazyInitializationException`이 난다.
- 1차 캐시를 모르면, id로 이미 꺼내 둔 Entity를 굳이 다시 조회하는 코드를 쓰게 된다.
- 대량 데이터를 영속성 컨텍스트에 올리면, 메모리가 모자란다.
- 배치에서 `clear()`를 하지 않으면, 영속성 컨텍스트가 처리한 건수만큼 계속 커진다.

## 한 번에 설명하기

> 영속성 컨텍스트는 Entity를 담아 두고 관리하는 1차 캐시입니다. 같은 row는 같은 객체로 돌려주고, SQL은 모아 뒀다 보내고, 바뀐 값은 알아서 UPDATE합니다.
>
> 같은 트랜잭션에서 같은 id로 조회하면 캐시에서 꺼내 주고, 필드를 바꾸면 커밋할 때 UPDATE가 나갑니다.
>
> Spring에서는 영속성 컨텍스트가 `@Transactional`과 같이 열리고 닫혀서, 트랜잭션 밖에서는 Entity가 준영속이 되고 변경 감지도 지연 로딩도 안 됩니다. 대량 처리에서는 일정 건수마다 flush와 clear로 비워 줍니다.

## 꼬리 질문

> [!question]- 1차 캐시와 2차 캐시의 차이는?
> 1차 캐시는 영속성 컨텍스트, 그러니까 보통 트랜잭션 하나 안에서만 살아 있고, 2차 캐시는 애플리케이션 전체에서 공유합니다. 1차 캐시는 아무것도 안 해도 동작하지만, 2차 캐시는 따로 설정해야 켜집니다.

> [!question]- 준영속 상태에서 변경 감지가 안 되는 이유는?
> 변경 감지는 영속성 컨텍스트가 들고 있는 스냅샷과 지금 값을 비교하는 일입니다. 준영속 Entity는 영속성 컨텍스트에서 떨어져 나와서, 비교해 줄 주체가 없습니다.

> [!question]- `entityManager.merge()`는 언제 사용하는가?
> 준영속 Entity의 값을 다시 영속 상태로 들여올 때 씁니다. 이때 돌려받는 건 새 영속 Entity이고, 넘긴 원본 객체는 그대로 준영속으로 남습니다.

> [!question]- 대량 데이터 처리 시 영속성 컨텍스트를 어떻게 관리하는가?
> 일정 건수마다 `flush()`와 `clear()`를 불러서 영속성 컨텍스트를 비웁니다. 안 그러면 처리한 Entity가 계속 쌓여서 메모리가 끝없이 늘어납니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>영속성 컨텍스트의 1차 캐시가 의미하는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="같은 트랜잭션/영속성 컨텍스트 안에서 같은 식별자의 Entity를 한 인스턴스로 관리한다." aria-pressed="false">A. 같은 식별자의 Entity를 영속성 컨텍스트 안에서 재사용한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="1차 캐시는 애플리케이션 전체 공유 캐시가 아니다." aria-pressed="false">B. 모든 사용자 요청이 공유하는 전역 캐시다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="브라우저 캐시와는 관련이 없다." aria-pressed="false">C. HTTP 브라우저 캐시를 의미한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>준영속 상태의 Entity 값을 바꿔도 변경 감지는 동작하지 않는다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="변경 감지는 영속성 컨텍스트가 관리하는 managed Entity에 대해 동작한다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="준영속 객체는 영속성 컨텍스트가 snapshot을 관리하지 않는다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>대량 데이터 처리에서 영속성 컨텍스트를 주기적으로 flush/clear하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="관리 Entity가 계속 쌓이면 메모리 사용량이 증가하고 변경 감지 비용도 커질 수 있기 때문이다." aria-pressed="false">A. 메모리 사용량과 변경 감지 비용을 통제하기 위해서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="flush/clear가 DB 인덱스를 자동으로 생성하지 않는다." aria-pressed="false">B. DB 인덱스를 자동 생성하기 위해서다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="flush/clear는 네트워크 암호화 기능이 아니다." aria-pressed="false">C. JDBC 연결을 TLS로 바꾸기 위해서다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Hibernate ORM 6.6 User Guide: Persistence Context](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#pc)
- [Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[dirty-checking]]
- [[transaction-and-flush]]
- [[lazy-and-eager-loading]]