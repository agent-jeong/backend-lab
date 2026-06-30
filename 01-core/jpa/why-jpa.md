---
title: "JPA를 사용하는 이유"
description: JPA를 사용하는 이유와 JDBC 대비 실무 이점
---

# JPA를 사용하는 이유

## 한 줄 정의

JPA는 Java 객체와 관계형 데이터베이스 테이블 사이의 불일치를 자동으로 매핑해주는 ORM 표준이다.

## 실무에서 왜 중요한가

JPA 없이 JDBC만 사용하면 다음 문제가 반복된다.

- SQL을 직접 작성하고, 결과를 수동으로 객체에 매핑하는 boilerplate가 많다.
- 테이블 컬럼이 변경되면 관련 SQL과 매핑 코드를 모두 수정해야 한다.
- 객체 간의 참조 관계와 테이블의 외래 키 관계를 수동으로 맞춰야 한다.
- 같은 row를 여러 번 조회하면 매번 새로운 객체가 생성되어 동일성이 보장되지 않는다.
- 반복적인 CRUD SQL 작성에 시간을 빼앗긴다.

JPA는 이런 불일치를 영속성 컨텍스트, 변경 감지, 지연 로딩 등의 메커니즘으로 해결한다.

## JPA가 해결하는 문제

### 객체-관계 불일치 (Object-Relational Impedance Mismatch)

| 불일치 | 객체 | 테이블 |
|---|---|---|
| 상속 | 클래스 상속 | 슈퍼타입/서브타입 테이블 |
| 연관관계 | 참조 (`user.getTeam()`) | 외래 키 JOIN |
| 동일성 | `==` 또는 `equals()` | PK 기준 |
| 탐색 | `user.getTeam().getName()` | JOIN SQL 필요 |

JPA는 이 불일치를 매핑 어노테이션(`@Entity`, `@ManyToOne`, `@JoinColumn` 등)과 영속성 컨텍스트로 해소한다.

### JDBC 반복 코드 제거

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

### Spring Data JPA와의 관계

실무에서는 JPA를 직접 사용하기보다 Spring Data JPA를 통해 사용한다.

```
Spring Data JPA → JPA (표준 인터페이스) → Hibernate (구현체) → JDBC → DB
```

Spring Data JPA는 `JpaRepository` 인터페이스만 정의하면 기본 CRUD를 자동으로 제공한다.

```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}
```

## JPA가 만능이 아닌 이유

JPA는 단순 CRUD와 객체 그래프 탐색에 강하지만, 모든 상황에 적합하지는 않다.

| 상황 | JPA 적합성 |
|---|---|
| 단순 CRUD | 적합 |
| 객체 연관관계 탐색 | 적합 |
| 복잡한 통계 쿼리 | 부적합 - 네이티브 SQL이나 QueryDSL 고려 |
| 대량 데이터 일괄 처리 | 부적합 - 벌크 연산이나 JDBC batch 고려 |
| 동적 쿼리 조합 | 보통 - QueryDSL이 더 적합 |

실무에서는 JPA와 네이티브 SQL을 상황에 맞게 섞어 쓰는 것이 일반적이다.

## 자주 나는 실수

- JPA를 쓰면 SQL을 몰라도 된다고 생각한다.
- 모든 쿼리를 JPQL로 해결하려다 성능이 나빠진다.
- JPA 내부 동작(영속성 컨텍스트, flush, 지연 로딩)을 모르고 사용해서 예상과 다른 쿼리가 나간다.
- 대량 데이터를 JPA로 처리해서 메모리와 성능 문제가 생긴다.
- Hibernate와 JPA를 구분하지 못한다.

## 핵심 요약

JPA는 객체와 관계형 데이터베이스 사이의 불일치를 매핑해주는 ORM 표준입니다.
JDBC의 반복적인 SQL 작성과 수동 매핑을 줄이고, 영속성 컨텍스트를 통해 1차 캐시, 변경 감지, 동일성 보장 같은 기능을 제공합니다.

다만 JPA는 SQL을 없애는 도구가 아닙니다.
복잡한 통계 쿼리나 대량 데이터 처리에는 네이티브 SQL이나 벌크 연산이 더 적합합니다.

실무에서는 Spring Data JPA를 통해 사용하며, JPA 내부 동작 원리를 모르면 N+1, 불필요한 쿼리, 메모리 문제가 생기기 쉽습니다.

## 꼬리 질문

> [!question]- JPA와 Hibernate의 관계는?
> JPA는 Java ORM 표준 인터페이스이고, Hibernate는 그 구현체입니다. Spring Data JPA는 JPA를 더 쉽게 사용하기 위한 추상화 계층입니다.

> [!question]- JPA를 쓰면 SQL을 몰라도 되는가?
> 아닙니다. JPA가 생성하는 SQL을 이해하고, 성능 문제 시 직접 튜닝할 수 있어야 합니다. 복잡한 쿼리는 네이티브 SQL이 필요합니다.

> [!question]- JPA가 적합하지 않은 상황은?
> 복잡한 통계/집계 쿼리, 대량 데이터 일괄 처리, 다중 테이블 JOIN이 복잡한 경우에는 네이티브 SQL이나 QueryDSL이 더 적합합니다.

> [!question]- Spring Data JPA의 `JpaRepository`는 어떻게 구현 없이 동작하는가?
> Spring이 런타임에 프록시 객체를 생성하고, 메서드 이름을 파싱해서 JPQL을 자동 생성합니다. `findByEmail`은 `SELECT u FROM User u WHERE u.email = :email`이 됩니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA를 사용하는 핵심 이유로 가장 적절한 것은?</p>
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

## 관련 문서

- [[01-core/jpa/jpa|jpa]]
- [[persistence-context]]
- [[01-core/database/database|database]]