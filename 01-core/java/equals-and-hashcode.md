---
title: equals와 hashCode
description: Java equals와 hashCode의 실무 동등성 기준
---

# equals와 hashCode를 함께 재정의하는 이유

## 한 줄 정의

`equals()`는 두 객체가 의미상 같은지 판단하는 메서드이고, `hashCode()`는 `HashMap`, `HashSet` 같은 hash 기반 컬렉션에서 객체를 찾기 위해 사용하는 값이다.

## 실무에서 왜 중요한가

백엔드에서는 객체를 자주 key로 쓰고, 중복 제거하고, 캐시하고, 테스트에서 비교한다.

동등성 기준이 틀리면 같은 값인데도 `HashSet`에서 중복 제거가 안 되거나, `HashMap`에 넣은 값을 다시 찾지 못한다. JPA Entity에서는 id 할당 시점, 프록시, 연관관계 때문에 더 쉽게 문제가 생긴다.

## 반드시 기억할 규칙

| 규칙 | 의미 |
|---|---|
| `equals()`가 true이면 `hashCode()`도 같아야 한다 | hash 컬렉션에서 같은 bucket을 찾기 위해 필요 |
| `hashCode()`가 같아도 `equals()`가 true일 필요는 없다 | hash 충돌은 정상 |
| hash 계산에 쓰는 값은 변경되지 않아야 한다 | 저장 후 key를 찾지 못하는 문제를 막기 위해 필요 |

`HashMap`과 `HashSet`은 먼저 `hashCode()`로 위치를 찾고, 그 안에서 `equals()`로 최종 비교한다.

## 기본 동작

`equals()`를 재정의하지 않으면 보통 같은 인스턴스인지 비교한다.

```java
User a = new User(1L, "kim");
User b = new User(1L, "kim");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // equals를 재정의하지 않으면 false
```

실무에서는 서로 다른 객체여도 같은 `userId`를 가진 사용자를 같은 사용자로 볼 수 있다. 이 기준을 코드로 표현하는 것이 `equals()`다.

## 좋은 값 객체 예시

값 객체나 key 객체는 비교 기준을 작고 안정적으로 잡는다.

```java
import java.util.Objects;

public class UserKey {
    private final Long userId;

    public UserKey(Long userId) {
        this.userId = userId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (!(o instanceof UserKey other)) {
            return false;
        }
        return Objects.equals(userId, other.userId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(userId);
    }
}
```

Java 16 이상에서 값 전달이 목적이라면 `record`가 더 간단하다.

```java
public record UserKey(Long userId) {
}
```

단, `record`는 모든 컴포넌트를 기준으로 `equals()`와 `hashCode()`를 만든다. 일부 필드를 제외해야 한다면 직접 구현하거나 `record`가 맞는지 다시 확인한다.

## 가장 위험한 실수

hash 기반 컬렉션에 넣은 뒤, `hashCode()` 계산에 쓰이는 값을 바꾸면 안 된다.

```java
public class MutableUserKey {
    private Long userId;

    public MutableUserKey(Long userId) {
        this.userId = userId;
    }

    public void changeUserId(Long userId) {
        this.userId = userId;
    }

    // equals/hashCode가 userId 기준이라고 가정
}

Set<MutableUserKey> keys = new HashSet<>();

MutableUserKey key = new MutableUserKey(1L);
keys.add(key);

key.changeUserId(2L);

keys.contains(key); // false가 될 수 있다.
```

객체는 원래 bucket에 저장되어 있는데, 변경된 값으로는 다른 bucket을 찾기 때문이다.

## JPA Entity에서의 주의점

JPA Entity는 값 객체처럼 모든 필드로 `equals()`와 `hashCode()`를 만들면 위험하다.

주의해야 할 이유:

- 저장 전에는 id가 없을 수 있다.
- 같은 row를 가리키는 다른 객체나 프록시가 생길 수 있다.
- 연관관계를 포함하면 lazy loading, 순환 참조, 성능 문제가 생길 수 있다.
- Lombok `@Data`는 모든 필드 기준 메서드를 만들 수 있어 Entity에 부적합한 경우가 많다.

실무에서는 팀 규칙을 정해 id 기반 또는 비즈니스 key 기반으로 제한한다. 중요한 것은 “이 Entity를 무엇으로 같은 객체라고 볼 것인가”를 명확히 정하는 것이다.

## 실무 판단 기준

| 객체 종류 | 권장 기준 |
|---|---|
| 값 객체 | 변경 불가능한 핵심 필드 기준 |
| `HashMap` key | `String`, `Long`, enum, record처럼 안정적인 key 우선 |
| DTO | 꼭 필요할 때만 주요 필드 기준 비교 |
| JPA Entity | 모든 필드 자동 생성 금지, id 또는 비즈니스 key 기준 검토 |
| 테스트 객체 비교 | 필요하면 AssertJ recursive comparison 고려 |

## 자주 나는 실수

- `equals()`만 재정의하고 `hashCode()`를 재정의하지 않는다.
- mutable 필드를 `equals()`와 `hashCode()`에 포함한다.
- `HashSet`에 넣은 뒤 비교 기준 필드를 변경한다.
- 객체 내용을 `==`로 비교한다.
- `Long`, `Integer` 같은 wrapper type을 `==`로 비교한다.
- JPA Entity에 Lombok `@Data`를 붙인다.

## 확인 방법

- 같은 값의 새 객체로 `HashSet.contains()`가 true인지 확인한다.
- 같은 값의 새 key로 `HashMap.get()`이 되는지 확인한다.
- 비교 기준 필드를 변경할 수 있는지 확인한다.
- Entity라면 저장 전/후, 프록시, 연관관계 포함 여부를 확인한다.
- Lombok을 쓰면 `@EqualsAndHashCode`에 포함되는 필드를 확인한다.

## 핵심 요약

`equals()`와 `hashCode()`는 객체의 동등성 기준을 정하는 메서드다. 특히 `HashMap`, `HashSet`, 캐시 key, 중복 제거에서 반드시 함께 봐야 한다.

값 객체는 변경 불가능한 핵심 필드 기준으로 구현한다. hash 기반 컬렉션에 넣은 뒤 비교 기준 값이 바뀌면 조회와 삭제가 깨질 수 있다.

JPA Entity는 id 할당 시점, 프록시, 연관관계 때문에 모든 필드 기준 자동 생성이 위험하다. Entity 동등성은 팀 규칙에 맞게 id 또는 비즈니스 key 기준으로 제한한다.

## 꼬리 질문

> [!question]- `equals()`가 true이면 왜 `hashCode()`도 같아야 하는가?
> hash 기반 컬렉션은 `hashCode()`로 bucket을 먼저 찾습니다. hashCode가 다르면 같은 객체로 비교할 기회 자체가 없어집니다.

> [!question]- `hashCode()`가 같으면 `equals()`도 true인가?
> 아닙니다. hash 충돌은 정상입니다. 같은 bucket 안에서 `equals()`로 최종 판단합니다.

> [!question]- mutable 객체를 `HashMap` key로 쓰면 왜 위험한가?
> 저장 후 key 값이 바뀌면 hashCode가 달라져 기존 bucket에서 찾지 못할 수 있습니다.

> [!question]- JPA Entity에 Lombok `@Data`가 위험한 이유는?
> 모든 필드가 비교 기준에 포함되어 lazy loading, 순환 참조, 저장 전 id null 문제를 만들 수 있습니다.

> [!question]- `record`의 `equals/hashCode` 기준은 무엇인가?
> 선언된 모든 컴포넌트 기준으로 자동 생성됩니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>equals가 true인 두 객체는 hashCode도 반드시 같아야 한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="HashMap/HashSet은 hashCode로 버킷을 먼저 찾기 때문에 이 규칙이 깨지면 같은 객체를 찾지 못할 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="hashCode 계약상 equals가 true면 hashCode도 같아야 한다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>mutable 객체를 HashMap key로 쓰면 위험한 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="key의 hashCode나 equals 기준 값이 바뀌면 저장된 버킷과 조회 버킷이 달라질 수 있다." aria-pressed="false">A. 저장 후 key 값이 바뀌면 다시 조회하지 못할 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="HashMap이 key를 복사하지 않는 것이 핵심은 맞지만, 문제는 동등성 기준 변경이다." aria-pressed="false">B. HashMap이 key를 항상 deep copy하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="성능보다 정합성 문제가 더 중요하다." aria-pressed="false">C. HashMap이 자동으로 TreeMap으로 바뀌기 때문이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>JPA Entity에 Lombok @Data를 무심코 붙이면 생길 수 있는 문제는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@Data는 여러 메서드를 생성한다. 단순 getter 생성만의 문제가 아니다." aria-pressed="false">A. getter가 생성되지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="양방향 연관관계나 lazy 로딩 필드가 equals/toString에 포함되어 성능 문제나 순환 참조가 생길 수 있다." aria-pressed="false">B. equals, hashCode, toString이 연관관계까지 건드릴 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="컴파일 자체가 막히는 것이 아니라 런타임 동작과 설계 문제가 생긴다." aria-pressed="false">C. Entity 클래스는 Lombok을 전혀 사용할 수 없다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[primitive-and-reference-types]]
- [[hashmap]]
- [[class-interface-enum-record]]
- [[01-core/jpa/jpa|jpa]]
