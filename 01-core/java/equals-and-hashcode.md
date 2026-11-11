---
title: equals와 hashCode
description: 두 객체를 언제 같다고 볼지 정하는 equals와 hashCode, 그리고 Entity에서 깨지는 경우
tags: [concept, java]
---

# equals와 hashCode를 함께 재정의하는 이유

`equals()`는 두 객체를 같은 것으로 볼지 정하고, `hashCode()`는 `HashMap`이나 `HashSet`이 객체를 찾을 때 쓰는 숫자를 돌려준다. 둘은 같은 필드를 기준으로 함께 재정의해야 한다.

백엔드 코드는 객체를 map의 key로 쓰고, 중복을 걸러 내고, 캐시하고, 테스트에서 비교하는 일이 많다. 같다고 보는 기준이 어긋나면 같은 주문 번호인데 `HashSet`에서 중복이 안 걸러지거나, `HashMap`에 넣은 값을 다시 못 꺼낸다. JPA Entity는 id가 언제 채워지는지, 프록시인지, 연관관계를 어떻게 다루는지에 따라 더 쉽게 깨진다.

## 지켜야 할 규칙

| 규칙 | 이유 |
|---|---|
| `equals()`가 true이면 `hashCode()`도 같아야 한다 | hash 컬렉션이 같은 bucket을 찾아야 하므로 |
| `hashCode()`가 같아도 `equals()`가 true일 필요는 없다 | hash 충돌은 정상이다 |
| hash 계산에 쓰는 값은 바뀌면 안 된다 | 바뀌면 저장한 key를 다시 못 찾는다 |

`HashMap`과 `HashSet`은 먼저 `hashCode()`로 위치를 찾고, 그 위치 안에서 `equals()`로 마지막 비교를 한다.

## 재정의하지 않으면

`equals()`를 재정의하지 않으면 보통 같은 인스턴스인지만 본다.

```java
User a = new User(1L, "kim");
User b = new User(1L, "kim");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // equals를 재정의하지 않으면 false
```

실무에서는 객체가 달라도 `userId`가 같으면 같은 사용자로 보고 싶을 때가 많다. 그 기준을 코드로 적는 곳이 `equals()`다.

## 값 객체는 작고 바뀌지 않는 필드로

값 객체나 key 객체는 비교 기준을 적은 수의, 바뀌지 않는 필드로 잡는다.

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

Java 16 이상이고 값을 옮기는 게 목적이면 `record`가 더 간단하다.

```java
public record UserKey(Long userId) {
}
```

`record`는 모든 컴포넌트로 `equals()`와 `hashCode()`를 만든다. 일부 필드를 빼야 한다면 직접 구현하거나, 애초에 `record`가 맞는지 다시 본다.

## 넣은 뒤 key를 바꾸면 못 찾는다

hash 기반 컬렉션에 넣은 뒤에는 `hashCode()` 계산에 쓰는 값을 바꾸면 안 된다.

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

객체는 처음 넣은 bucket에 그대로 있는데, 바뀐 값으로 계산하면 다른 bucket을 뒤지기 때문이다.

## JPA Entity

Entity를 값 객체처럼 모든 필드로 `equals()`와 `hashCode()`를 만들면 위험하다.

- 저장하기 전에는 id가 비어 있을 수 있다.
- 같은 row를 가리키는 다른 객체나 프록시가 생길 수 있다.
- 연관관계까지 비교하면 lazy loading, 순환 참조, 성능 문제가 생긴다.
- Lombok `@Data`는 모든 필드로 메서드를 만들어서 Entity에는 맞지 않는 경우가 많다.

실무에서는 팀 규칙으로 id 기준이나 비즈니스 key 기준 중 하나만 쓰게 한다. 결국 "이 Entity는 무엇이 같으면 같은 객체인가"를 미리 정해 두는 일이다.

## 객체 종류별 기준

| 객체 종류 | 권장 기준 |
|---|---|
| 값 객체 | 바뀌지 않는 핵심 필드 |
| `HashMap` key | `String`, `Long`, enum, record처럼 안정적인 key 우선 |
| DTO | 꼭 필요할 때만 주요 필드로 비교 |
| JPA Entity | 모든 필드 자동 생성 금지, id 또는 비즈니스 key 기준 검토 |
| 테스트 객체 비교 | 필요하면 AssertJ recursive comparison |

## 자주 깨지는 곳

- `equals()`만 재정의하면, `hashCode()`가 달라서 hash 컬렉션은 두 객체를 비교해 볼 기회조차 없다.
- 바뀔 수 있는 필드를 비교 기준에 넣으면, `HashSet`에 넣은 뒤 그 필드를 바꾸는 순간 조회와 삭제가 안 된다.
- 객체 내용을 `==`로 비교하면 틀린다. `Long`, `Integer` 같은 wrapper도 마찬가지다.
- JPA Entity에 Lombok `@Data`를 붙이면, 연관관계와 저장 전의 null id까지 비교 기준에 들어간다.

## 테스트로 확인할 것

- 같은 값으로 새로 만든 객체로 `HashSet.contains()`가 true인가.
- 같은 값으로 새로 만든 key로 `HashMap.get()`이 되는가.
- 비교 기준 필드를 밖에서 바꿀 수 있게 열어 두지 않았는가.
- Entity라면 저장 전과 후, 프록시일 때, 연관관계를 포함할 때도 기준이 그대로인가.
- Lombok을 쓴다면 `@EqualsAndHashCode`에 어떤 필드가 들어가는가.

## 한 번에 설명하기

> equals와 hashCode는 두 객체를 같다고 볼 기준을 정하는 메서드입니다. HashMap, HashSet, 캐시 key, 중복 제거가 전부 이 둘에 기대기 때문에 항상 같이 봅니다.
>
> 값 객체는 바뀌지 않는 필드로 구현합니다. hash 컬렉션에 넣은 뒤 기준 값이 바뀌면 조회와 삭제가 안 되기 때문입니다.
>
> JPA Entity는 id가 채워지는 시점, 프록시, 연관관계 때문에 모든 필드로 자동 생성하면 위험합니다. 그래서 팀 규칙으로 id나 비즈니스 key 중 하나를 기준으로 정합니다.

## 꼬리 질문

> [!question]- `equals()`가 true이면 왜 `hashCode()`도 같아야 하나?
> hash 컬렉션은 `hashCode()`로 bucket부터 찾습니다. hashCode가 다르면 다른 bucket을 보게 되니까, equals로 비교해 볼 기회 자체가 없습니다.

> [!question]- `hashCode()`가 같으면 `equals()`도 true인가?
> 아닙니다. hash 충돌은 원래 생기는 일입니다. 같은 bucket 안에서 `equals()`로 최종 판단합니다.

> [!question]- 바뀔 수 있는 객체를 `HashMap` key로 쓰면 왜 위험한가?
> 넣은 뒤에 key 값이 바뀌면 hashCode가 달라져서, 원래 들어 있던 bucket에서 못 찾을 수 있습니다.

> [!question]- JPA Entity에 Lombok `@Data`를 붙이면 왜 위험한가?
> 모든 필드가 비교 기준에 들어갑니다. 그래서 lazy loading이 일어나거나, 순환 참조가 생기거나, 저장 전 id가 null인 문제가 생길 수 있습니다.

> [!question]- `record`의 `equals/hashCode`는 무엇을 기준으로 하나?
> 선언한 컴포넌트 전부를 기준으로 자동으로 만들어집니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

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
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="HashMap이 key를 복사하지 않는 건 맞다. 하지만 문제는 넣은 뒤 동등성 기준이 바뀌는 것이다." aria-pressed="false">B. HashMap이 key를 항상 deep copy하기 때문이다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="성능보다 정합성이 먼저 깨진다." aria-pressed="false">C. HashMap이 자동으로 TreeMap으로 바뀌기 때문이다.</button>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: Object.equals / hashCode](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html)

## 관련 문서

- [[01-core/java/java|java]]
- [[primitive-and-reference-types]]
- [[hashmap]]
- [[class-interface-enum-record]]
- [[01-core/jpa/jpa|jpa]]
