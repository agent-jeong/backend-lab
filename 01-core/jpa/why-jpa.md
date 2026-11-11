---
title: "JPA를 사용하는 이유"
description: JDBC 대신 JPA를 쓰면 무엇이 줄고, 무엇은 여전히 직접 챙겨야 하는지
tags: [concept, jpa]
---

# JPA를 사용하는 이유

JPA는 Java 객체와 DB 테이블을 서로 바꿔 주는 ORM 표준이다. 객체와 테이블은 생김새가 달라서 그대로는 안 맞는데, 그 차이를 JPA가 맞춰 준다.

JDBC만 쓰면 주문 하나 조회할 때마다 SQL을 쓰고 결과를 객체에 한 줄씩 옮겨 담는 코드를 반복한다. JPA는 이 반복을 영속성 컨텍스트, 변경 감지, 지연 로딩으로 덜어 준다. 다만 SQL이 사라지지는 않는다. JPA가 어떤 SQL을 만드는지 모르면 N+1, 쓸데없는 쿼리, 메모리 부족이 그대로 생긴다.

## JDBC만 쓰면 생기는 일

- SQL을 직접 쓰고 결과를 손으로 객체에 옮겨 담는 반복 코드(boilerplate)가 많다.
- 테이블 컬럼이 바뀌면 그 컬럼을 쓰는 SQL과 매핑 코드를 전부 고쳐야 한다.
- 객체끼리의 참조와 테이블의 외래 키를 손으로 맞춰야 한다.
- 같은 row를 여러 번 조회하면 매번 새 객체가 생겨서, 같은 데이터인데 `==`로 비교하면 다르다고 나온다.
- 비슷비슷한 CRUD SQL을 쓰는 데 시간을 쓴다.

```java
// JDBC 방식: 반복적인 boilerplate
String sql = "SELECT id, name, email FROM users WHERE id = ?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setLong(1, userId);
ResultSet rs = pstmt.executeQuery();
if (rs.next()) {
    User user = new User();
    user.setId(rs.getLong("id"));
    user.setName(rs.getString("name"));
    user.setEmail(rs.getString("email"));
}

// JPA 방식: 한 줄
User user = entityManager.find(User.class, userId);
```

## 객체와 테이블은 어디서 어긋나나

객체와 테이블이 어긋나는 문제(Object-Relational Impedance Mismatch)는 네 군데서 보인다.

| 불일치 | 객체 | 테이블 |
|---|---|---|
| 상속 | 클래스 상속 | 슈퍼타입/서브타입 테이블 |
| 연관관계 | 참조 (`user.getTeam()`) | 외래 키 JOIN |
| 동일성 | `==` 또는 `equals()` | PK 기준 |
| 탐색 | `user.getTeam().getName()` | JOIN SQL 필요 |

JPA는 매핑 어노테이션(`@Entity`, `@ManyToOne`, `@JoinColumn` 등)과 영속성 컨텍스트로 이 차이를 메운다. 영속성 컨텍스트는 1차 캐시를 두고, 바뀐 값을 찾아 UPDATE하고, 같은 row는 같은 객체로 돌려준다.

## Spring Data JPA와의 관계

실무에서는 JPA를 직접 부르기보다 Spring Data JPA를 거쳐서 쓴다.

```
Spring Data JPA → JPA (표준 인터페이스) → Hibernate (구현체) → JDBC → DB
```

`JpaRepository`를 상속한 인터페이스만 만들면 기본 CRUD가 저절로 생긴다.

```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}
```

## 언제 JPA가 맞지 않나

JPA는 단순 CRUD와 `order.getUser()`처럼 객체를 따라가는 조회에 강하다. 그 밖에서는 다른 도구를 섞는다.

| 상황 | JPA가 맞나 |
|---|---|
| 단순 CRUD | 맞다 |
| 연관된 객체 따라가기 | 맞다 |
| 복잡한 통계 쿼리 | 안 맞다. 네이티브 SQL이나 QueryDSL을 쓴다 |
| 대량 데이터 일괄 처리 | 안 맞다. 벌크 연산이나 JDBC batch를 쓴다 |
| 조건이 바뀌는 동적 쿼리 | 그럭저럭. QueryDSL이 더 낫다 |

실무에서는 JPA와 네이티브 SQL을 상황에 따라 섞어 쓰는 게 보통이다.

## 자주 깨지는 곳

- JPA를 쓰면 SQL을 몰라도 된다고 생각하면, 만들어진 SQL을 못 읽어서 느린 쿼리를 고칠 수 없다.
- 모든 쿼리를 JPQL로 풀려고 하면, 통계나 집계 쿼리가 느려진다.
- 영속성 컨텍스트, flush, 지연 로딩을 모르고 쓰면, 생각지 못한 쿼리가 나간다.
- 대량 데이터를 Entity로 하나씩 처리하면, 메모리가 모자라고 느려진다.
- Hibernate와 JPA를 구분하지 못하면, 표준이 정한 동작과 구현체가 하는 동작을 섞어 설명하게 된다.

## 한 번에 설명하기

> JPA는 객체와 관계형 DB 사이의 차이를 맞춰 주는 ORM 표준입니다. JDBC로 SQL을 쓰고 결과를 손으로 옮겨 담던 반복을 줄여 주고, 영속성 컨텍스트가 1차 캐시와 변경 감지를 해 주며 같은 row는 같은 객체로 돌려줍니다.
>
> 그렇다고 SQL이 사라지는 건 아니라서, 저는 JPA가 만드는 쿼리를 늘 확인합니다. 복잡한 통계 쿼리나 대량 처리에는 네이티브 SQL이나 벌크 연산을 씁니다.

## 꼬리 질문

> [!question]- JPA와 Hibernate의 관계는?
> JPA는 Java ORM의 표준 인터페이스이고, Hibernate는 그걸 구현한 라이브러리입니다. Spring Data JPA는 그 위에 얹어서 JPA를 더 쉽게 쓰게 해 주는 계층입니다.

> [!question]- JPA를 쓰면 SQL을 몰라도 되는가?
> 아닙니다. JPA가 만드는 SQL을 읽을 줄 알아야 느릴 때 직접 고칠 수 있습니다. 복잡한 쿼리는 결국 네이티브 SQL로 써야 하기도 합니다.

> [!question]- JPA가 적합하지 않은 상황은?
> 복잡한 통계나 집계 쿼리, 대량 데이터 일괄 처리, 여러 테이블을 복잡하게 JOIN하는 쿼리가 그렇습니다. 이런 건 네이티브 SQL이나 QueryDSL로 쓰는 게 낫습니다.

> [!question]- Spring Data JPA의 `JpaRepository`는 어떻게 구현 없이 동작하는가?
> Spring이 실행 중에 프록시 객체를 만들고, 메서드 이름을 읽어서 JPQL을 만들어 냅니다. 예를 들어 `findByEmail`은 `SELECT u FROM User u WHERE u.email = :email`이 됩니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA를 쓰는 이유로 맞는 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="객체 모델과 관계형 DB 사이의 반복 매핑을 줄이고, 영속성 컨텍스트와 변경 감지로 도메인 중심 개발을 돕는다." aria-pressed="false">A. 객체-관계 매핑과 영속성 컨텍스트 기반 변경 관리를 제공한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JPA를 써도 SQL과 실행 계획 이해는 여전히 필요하다." aria-pressed="false">B. SQL 지식을 완전히 대체한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JPA가 모든 쿼리를 최적화하지 않는다. 복잡한 조회는 직접 설계해야 한다." aria-pressed="false">C. 모든 조회 성능 문제를 자동 해결한다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>JPA는 표준 인터페이스이고 Hibernate는 대표적인 JPA 구현체다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="Spring Data JPA는 JPA/Hibernate 위에서 Repository 추상화를 제공하는 계층으로 이해하면 된다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="JPA와 Hibernate는 같은 층위의 동일한 개념이 아니다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA가 적합하지 않을 수 있는 상황은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="대량 배치, 복잡한 통계성 조회, DB 특화 SQL 최적화가 핵심인 경우에는 JDBC/QueryDSL/native query 등을 검토한다." aria-pressed="false">A. 대량 배치나 복잡한 통계성 조회가 핵심인 경우</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="단순 CRUD는 JPA가 강점을 보이는 영역이다." aria-pressed="false">B. 단순 CRUD 중심 도메인</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="트랜잭션이 필요하다고 JPA가 부적합한 것은 아니다." aria-pressed="false">C. 트랜잭션을 사용하는 서비스</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Jakarta Persistence 3.1](https://jakarta.ee/specifications/persistence/3.1/)
- [Spring Data JPA Reference](https://docs.spring.io/spring-data/jpa/reference/)

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[01-core/database/database|database]]