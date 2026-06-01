---
title: Equals And HashCode
description: Java equals와 hashCode의 실무 동등성 기준
---

# Equals And HashCode

## 한 줄 정의

`equals()`는 두 객체가 의미상 같은지 판단하는 메서드이고, `hashCode()`는 hash 기반 컬렉션에서 객체를 빠르게 찾기 위해 사용하는 정수 값이다.

## 실무에서 왜 중요한가

실무에서는 객체를 단순히 생성하고 비교하는 수준을 넘어, `HashMap`, `HashSet`, 중복 제거, DTO 변환, JPA Entity 비교에서 동등성 기준을 자주 다룬다.

이 기준이 틀리면 다음 문제가 생긴다.

- 같은 값인데 `HashSet`에서 중복 제거가 안 된다.
- `HashMap`에 넣은 값을 같은 id로 다시 찾지 못한다.
- 객체 비교가 참조 비교로 동작해서 조건문이 기대와 다르게 흐른다.
- JPA Entity 비교에서 영속 상태, 프록시, id 할당 시점 때문에 버그가 생긴다.
- 테스트에서는 통과했지만 실제 응답 조립이나 캐시 key 비교에서 값이 누락된다.

## 기본 개념

Java의 모든 객체는 `Object`를 상속하므로 기본적으로 `equals()`와 `hashCode()`를 가진다.

기본 구현은 보통 “같은 객체 인스턴스인가”에 가깝다.

```java
User a = new User(1L, "kim");
User b = new User(1L, "kim");

System.out.println(a == b);      // false
System.out.println(a.equals(b)); // equals를 재정의하지 않으면 false
```

실무에서는 `a`와 `b`가 서로 다른 객체여도 같은 `userId`를 가진 사용자를 같은 사용자로 볼 수 있다. 이때 의미상 같은 기준을 코드로 표현하는 것이 `equals()`다.

## hashCode와 함께 봐야 하는 이유

`HashMap`, `HashSet`은 먼저 `hashCode()`로 bucket을 찾고, 그 안에서 `equals()`로 같은 객체인지 확인한다.

그래서 아래 규칙이 중요하다.

| 규칙 | 의미 |
|---|---|
| `equals()`가 true인 두 객체는 같은 `hashCode()`를 가져야 한다 | hash 컬렉션에서 같은 위치를 찾기 위해 필요 |
| `hashCode()`가 같아도 `equals()`가 true일 필요는 없다 | hash 충돌은 가능하다 |
| 비교에 사용하는 필드는 가능하면 변경되지 않아야 한다 | 저장 후 hash 위치가 달라지는 문제를 막기 위해 필요 |

`equals()`만 재정의하고 `hashCode()`를 재정의하지 않으면 `HashSet`, `HashMap`에서 문제가 생긴다.

```java
Set<UserKey> keys = new HashSet<>();

keys.add(new UserKey(1L));

boolean exists = keys.contains(new UserKey(1L)); // false 가능
```

## 올바른 값 객체 예시

값 자체가 동등성 기준인 객체는 비교에 사용할 필드를 명확히 정한다.

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
        if (!(o instanceof UserKey userKey)) {
            return false;
        }
        return Objects.equals(userId, userKey.userId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(userId);
    }
}
```

Java 16 이상에서는 값 전달용 객체라면 `record`도 선택지가 될 수 있다.

```java
public record UserKey(Long userId) {
}
```

`record`는 주요 필드 기반의 `equals()`, `hashCode()`, `toString()`을 자동으로 제공한다. 단, 모든 필드가 동등성 기준에 포함되므로 의도에 맞는지 확인해야 한다.

## 자주 나는 실수

- `equals()`만 재정의하고 `hashCode()`를 재정의하지 않는다.
- mutable 필드를 `equals/hashCode`에 포함한다.
- `HashSet`에 넣은 뒤 동등성 기준 필드를 변경한다.
- `==`로 객체 내용을 비교한다.
- `Long`, `Integer` 같은 wrapper type을 `==`로 비교한다.
- JPA Entity에서 모든 필드를 기준으로 `equals/hashCode`를 만든다.
- Lombok `@Data`가 만들어주는 `equals/hashCode`를 아무 생각 없이 Entity에 사용한다.

## JPA Entity에서의 주의점

JPA Entity는 일반 값 객체보다 조심해야 한다.

Entity는 다음 특성이 있다.

- DB 저장 전에는 id가 없을 수 있다.
- 영속 상태에 따라 같은 row를 가리키는 다른 객체가 생길 수 있다.
- lazy loading proxy가 개입할 수 있다.
- 연관관계를 `equals/hashCode`에 포함하면 순환 참조나 불필요한 로딩이 생길 수 있다.

그래서 Entity에 `@Data`를 붙여 모든 필드 기준으로 `equals/hashCode`를 자동 생성하는 방식은 위험하다.

실무에서는 보통 아래 중 하나를 선택한다.

| 상황 | 기준 |
|---|---|
| DB id가 안정적으로 존재한다 | id 기반 비교를 고려 |
| 저장 전에도 동등성 판단이 필요하다 | 비즈니스 key를 명확히 둔다 |
| 단순 DTO나 값 객체다 | 주요 필드 전체 기준 비교 가능 |
| 연관관계가 많다 | 연관 필드는 비교 기준에서 제외 |

Entity의 동등성은 팀 규칙과 ORM 사용 방식에 따라 달라질 수 있으므로, 무조건 하나의 정답으로 외우지 않는 것이 좋다.

## 실무 판단 기준

| 객체 종류 | 권장 기준 |
|---|---|
| DTO | 필요한 경우 주요 필드 기준, 아니면 비교 로직을 만들지 않는다 |
| 값 객체 | 변경 불가능한 필드 기준으로 `equals/hashCode` 구현 |
| `HashMap` key | `String`, `Long`, enum, record처럼 안정적인 key 우선 |
| JPA Entity | 모든 필드 자동 생성 금지, id 또는 비즈니스 key 기준 검토 |
| 테스트 fixture | 비교 목적이 명확하면 AssertJ recursive comparison도 고려 |

객체 동등성은 “코드가 짧아지는가”보다 “이 객체를 무엇으로 같은 객체라고 볼 것인가”가 먼저다.

## 확인 방법

- 객체를 `HashSet`에 넣고 같은 값의 새 객체로 `contains()`가 true인지 확인한다.
- 객체를 `HashMap` key로 넣고 같은 값의 새 key로 조회되는지 확인한다.
- 비교 기준 필드를 변경한 뒤 collection 동작이 깨지지 않는지 본다.
- JPA Entity라면 저장 전/후, 프록시, 연관관계 포함 여부를 확인한다.
- Lombok을 쓰면 `@EqualsAndHashCode`에 포함되는 필드를 반드시 확인한다.

## 짧은 예제

mutable 필드를 key 기준에 넣으면 위험하다.

```java
Set<UserKey> keys = new HashSet<>();

UserKey key = new UserKey(1L);
keys.add(key);

key.changeUserId(2L);

boolean exists = keys.contains(key); // 기대와 다르게 false 가능
```

hash 기반 컬렉션에 넣은 뒤 `hashCode()` 계산에 쓰이는 값이 바뀌면, 객체가 저장된 bucket과 다시 찾는 bucket이 달라질 수 있다.

## 면접 답변 1분 버전

`equals()`는 두 객체가 의미상 같은지 판단하는 메서드이고, `hashCode()`는 `HashMap`, `HashSet` 같은 hash 기반 컬렉션에서 객체를 빠르게 찾기 위해 사용하는 값입니다. 중요한 규칙은 `equals()`가 true인 두 객체는 반드시 같은 `hashCode()`를 가져야 한다는 점입니다. 그렇지 않으면 같은 값처럼 보이는 객체를 `HashSet`에서 찾지 못하거나, `HashMap` key로 조회하지 못하는 문제가 생길 수 있습니다. 실무에서는 값 객체나 Map key는 변경 불가능한 필드를 기준으로 동등성을 정의하는 것이 안전합니다. 반면 JPA Entity는 id 할당 시점, 프록시, 연관관계 때문에 모든 필드를 기준으로 자동 생성하면 위험할 수 있어서 id나 비즈니스 key 기준을 팀 규칙에 맞게 정해야 합니다.

## 꼬리 질문

- `equals()`가 true이면 `hashCode()`도 반드시 같아야 하는 이유는 무엇인가?
- `hashCode()`가 같으면 `equals()`도 true인가?
- mutable 객체를 `HashMap` key로 쓰면 어떤 문제가 생기는가?
- JPA Entity에 Lombok `@Data`를 쓰면 왜 위험할 수 있는가?
- `record`의 `equals/hashCode`는 어떤 기준으로 생성되는가?

## 관련 문서

- [[01-core/java/java|java]]
- [[primitive-and-reference-types]]
- [[hashmap]]
- [[01-core/jpa/jpa|jpa]]
