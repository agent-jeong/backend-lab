---
title: "영속성 컨텍스트의 역할과 생명주기"
description: JPA 영속성 컨텍스트의 동작 원리와 실무 영향
tags: [concept, jpa]
---

# 영속성 컨텍스트의 역할과 생명주기

영속성 컨텍스트는 JPA가 Entity를 관리하는 1차 캐시 공간이다. 동일성 보장, 쓰기 지연, 변경 감지가 모두 여기서 나온다.

이걸 모르면 JPA의 "이상한" 동작을 설명하지 못한다. 같은 id를 두 번 조회했는데 쿼리가 한 번만 나가고, `save()`를 안 불렀는데 UPDATE가 나가고, 트랜잭션 밖에서 고친 값은 DB에 안 들어간다. 모두 **Entity가 지금 영속성 컨텍스트 안에 있느냐**로 갈린다.

## 1차 캐시

```java
@Transactional
public void example() {
    User user1 = entityManager.find(User.class, 1L); // SELECT 쿼리 실행
    User user2 = entityManager.find(User.class, 1L); // 캐시에서 반환, 쿼리 없음

    System.out.println(user1 == user2); // true - 동일성 보장
}
```

같은 트랜잭션 안에서 같은 id로 조회하면 1차 캐시에서 돌려준다. DB 접근이 줄고, 같은 row를 가리키는 두 객체가 `==`로 true가 된다.

1차 캐시를 타는 건 `find()`(`findById()`)처럼 id로 찾을 때뿐이다. JPQL·QueryDSL 쿼리는 항상 DB에 SQL을 보내고, 결과 행 중 이미 영속성 컨텍스트에 있는 Entity는 DB 값이 아니라 기존 객체를 돌려준다.

## 쓰기 지연 (Transactional Write-Behind)

```java
@Transactional
public void example() {
    entityManager.persist(user1); // INSERT SQL을 쓰기 지연 저장소에 보관
    entityManager.persist(user2); // INSERT SQL을 쓰기 지연 저장소에 보관

    // 트랜잭션 커밋 시점에 모아둔 SQL을 한 번에 실행
}
```

`persist()` 시점에는 SQL이 나가지 않고, flush 시점에 모아서 실행한다.

예외: `@GeneratedValue(strategy = IDENTITY)`는 id를 DB가 만들기 때문에 `persist()` 즉시 INSERT가 나간다. MySQL auto_increment를 쓰면 쓰기 지연과 JDBC batch insert의 이점이 사라진다. 자세한 내용은 [[entity-table-mapping]].

## 변경 감지 (Dirty Checking)

트랜잭션 커밋 시 영속성 컨텍스트가 스냅샷과 현재 상태를 비교하고, 바뀐 게 있으면 UPDATE를 실행한다. 기본은 모든 컬럼을 UPDATE하고, `@DynamicUpdate`를 쓰면 바뀐 컬럼만 UPDATE한다. 영속 상태 Entity라면 `save()`를 부르지 않아도 변경이 반영된다.

자세한 동작과 주의점은 [[dirty-checking|Dirty Checking]]에 있다.

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

## 범위는 트랜잭션과 같다

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

`@Transactional`이 없는 메서드에서는 repository 호출마다 트랜잭션이 따로 열리고 닫힌다. 그래서 Entity는 조회 직후 준영속이 되고, 지연 로딩이 실패한다.

## 자주 깨지는 곳

- **트랜잭션 밖에서 Entity를 고치고 반영을 기대한다.** 준영속 Entity라 변경 감지가 돌지 않는다.
- **`@Transactional` 없는 메서드에서 지연 로딩을 한다.** `LazyInitializationException`이 난다.
- **1차 캐시를 모르고 같은 조회를 반복한다.** id 조회라면 이미 캐시에 있는 걸 다시 가져오려 한다.
- **대량 데이터를 영속성 컨텍스트에 올린다.** 메모리가 부족해진다.
- **배치에서 `clear()`를 하지 않는다.** 영속성 컨텍스트가 처리 건수만큼 계속 커진다.

## 한 번에 설명하기

> 영속성 컨텍스트는 Entity를 관리하는 1차 캐시 공간으로, 동일성 보장, 쓰기 지연, 변경 감지를 제공합니다. 같은 트랜잭션에서 같은 id로 조회하면 캐시에서 돌려주고, 필드를 바꾸면 커밋 시점에 UPDATE가 나갑니다. Spring에서는 범위가 `@Transactional`과 같아서, 트랜잭션 밖에서는 Entity가 준영속이 되어 변경 감지와 지연 로딩이 동작하지 않습니다. 대량 처리에서는 일정 건수마다 flush와 clear로 비워 줍니다.

## 꼬리 질문

> [!question]- 1차 캐시와 2차 캐시의 차이는?
> 1차 캐시는 영속성 컨텍스트(트랜잭션) 범위이고, 2차 캐시는 애플리케이션 범위입니다. 1차 캐시는 자동으로 동작하지만, 2차 캐시는 별도 설정이 필요합니다.

> [!question]- 준영속 상태에서 변경 감지가 안 되는 이유는?
> 변경 감지는 영속성 컨텍스트가 스냅샷과 현재 상태를 비교하는 메커니즘입니다. 준영속 Entity는 영속성 컨텍스트에서 분리되었으므로 비교 대상이 없습니다.

> [!question]- `entityManager.merge()`는 언제 사용하는가?
> 준영속 Entity를 다시 영속 상태로 만들 때 사용합니다. 새로운 영속 Entity를 반환하며, 원본 객체는 여전히 준영속입니다.

> [!question]- 대량 데이터 처리 시 영속성 컨텍스트를 어떻게 관리하는가?
> 일정 건수마다 `flush()`와 `clear()`를 호출해서 영속성 컨텍스트를 비워야 합니다. 그렇지 않으면 메모리 사용량이 계속 늘어납니다.

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

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [Hibernate ORM 6.6 User Guide: Persistence Context](https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#pc)
- [Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[dirty-checking]]
- [[transaction-and-flush]]
- [[lazy-and-eager-loading]]