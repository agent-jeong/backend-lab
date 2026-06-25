---
title: "String 리터럴 vs new vs intern"
description: String 리터럴 할당과 new 할당의 차이, String Pool과 intern 메서드의 동작 원리
---

# String 리터럴 vs new vs intern의 차이

## 한 줄 정의

String 리터럴은 String Pool에서 재사용되고, `new String()`은 항상 Heap에 새 객체를 만들며, `intern()`은 Pool에 등록하거나 기존 참조를 반환하는 메서드다.

## 실무에서 왜 중요한가

- `==`와 `equals()`의 차이를 이해하지 못하면 문자열 비교 버그가 생긴다.
- 대량의 동일 문자열을 `new String()`으로 생성하면 메모리가 낭비된다.
- `intern()`을 무분별하게 사용하면 String Pool이 비대해져 GC 부담이 커진다.
- String Pool과 Heap의 관계를 모르면 메모리 사용 패턴을 예측할 수 없다.

## 동작 원리

### String Pool (String Constant Pool)

String Pool은 JVM이 문자열 리터럴을 저장하는 특수 영역이다. Java 7+부터 **Heap 영역** 안에 존재한다 (이전에는 PermGen).

```
Heap
┌────────────────────────────────────────┐
│                                        │
│   String Pool                          │
│   ┌──────────────────────┐             │
│   │ "hello" (0x100)      │             │
│   │ "world" (0x200)      │             │
│   └──────────────────────┘             │
│                                        │
│   일반 Heap 객체                        │
│   ┌──────────────────────┐             │
│   │ new String("hello")  │ (0x300)     │
│   └──────────────────────┘             │
│                                        │
└────────────────────────────────────────┘
```

### 리터럴 할당 vs new 할당

```java
String s1 = "hello";          // String Pool에서 참조
String s2 = "hello";          // 같은 Pool 객체를 참조
String s3 = new String("hello"); // Heap에 새 객체 생성

System.out.println(s1 == s2);      // true  (같은 Pool 참조)
System.out.println(s1 == s3);      // false (다른 객체)
System.out.println(s1.equals(s3)); // true  (값은 같다)
```

| 방식 | 객체 위치 | 동일 문자열 재사용 | 객체 수 |
|---|---|---|---|
| 리터럴 `"hello"` | String Pool | O (같은 참조) | 1개 |
| `new String("hello")` | Heap (Pool 밖) | X (매번 새 객체) | Pool 1개 + Heap 1개 |

### intern() 메서드

```java
String s3 = new String("hello");
String s4 = s3.intern();

System.out.println(s4 == "hello"); // true (Pool의 참조를 반환)
System.out.println(s3 == s4);      // false (s3은 여전히 Heap 객체)
```

`intern()` 동작:
1. String Pool에 동일한 값의 문자열이 **있으면** → Pool의 참조를 반환
2. String Pool에 동일한 값의 문자열이 **없으면** → Pool에 등록하고 그 참조를 반환

### 내부 구현

String Pool은 내부적으로 **HashTable** 구조다. `-XX:StringTableSize`로 버킷 수를 조정할 수 있다.

```bash
# String Pool HashTable 크기 설정 (기본값: 65536, Java 11+)
java -XX:StringTableSize=120011 -jar app.jar
```

## 실무 판단 기준

| 상황 | 선택 | 이유 |
|---|---|---|
| 코드에서 문자열을 직접 쓸 때 | 리터럴 | Pool에서 자동 재사용 |
| 외부 입력 문자열 비교 | `equals()` | 참조가 아닌 값 비교 필수 |
| 대량 중복 문자열 메모리 절감 | `intern()` 검토 | Pool 재사용으로 메모리 절약 |
| 고유한 문자열이 대량 생성 | `intern()` 사용 금지 | Pool만 비대해지고 GC 부담 증가 |

## 자주 나는 실수

- `==`로 문자열을 비교해서 외부 입력이나 `new String()`과 비교 시 false가 나온다.
- `intern()`을 무분별하게 호출해서 String Pool이 커지고 GC pause가 증가한다.
- Java 6 이전의 "PermGen에 String Pool이 있다"는 정보를 현재 버전에 적용한다.
- `new String("hello")`가 객체를 2개 만들 수 있다는 사실을 모른다 (Pool 1개 + Heap 1개).

## 핵심 요약

String 리터럴은 String Pool에 저장되어 같은 값이면 같은 참조를 반환합니다.
`new String()`은 항상 Heap에 새 객체를 만들므로 `==` 비교 시 false가 됩니다.

`intern()`은 문자열을 Pool에 등록하거나 기존 Pool 참조를 반환하는 메서드입니다.
대량 중복 문자열에서 메모리 절감 효과가 있지만, 고유 문자열이 많으면 오히려 부담이 됩니다.

Java 7+에서 String Pool은 Heap에 존재하므로 GC 대상이 됩니다.
문자열 비교는 항상 `equals()`를 사용하는 것이 안전합니다.

## 꼬리 질문

> [!question]- `new String("hello")`는 객체를 몇 개 만드는가?
> 최대 2개입니다. "hello" 리터럴이 처음 등장하면 Pool에 1개, `new`로 Heap에 1개가 생성됩니다. 이미 Pool에 "hello"가 있으면 Heap에 1개만 추가됩니다.

> [!question]- `intern()`을 언제 쓰면 유용한가?
> 외부에서 읽어온 문자열 중 중복이 매우 많은 경우(예: CSV 파싱에서 반복되는 상태값)에 메모리 절감 효과가 있습니다. 단, 고유 문자열이 많으면 역효과입니다.

> [!question]- String Pool이 Heap으로 옮겨진 이유는?
> Java 6까지는 PermGen에 있어서 크기가 고정되었고, 많은 문자열을 intern하면 `OutOfMemoryError: PermGen space`가 발생했습니다. Java 7+에서 Heap으로 이동하면서 GC 대상이 되어 메모리 관리가 유연해졌습니다.

> [!question]- `==`와 `equals()`를 구분하지 않으면 어떤 버그가 생기는가?
> 리터럴끼리 비교할 때는 `==`가 동작하지만, 외부 입력(HTTP 파라미터, DB 조회 결과 등)은 `new String()`과 동일하게 Heap 객체이므로 `==`로 비교하면 false가 됩니다.

## 면접 대비 퀴즈

아래 문항은 기술면접에서 답변의 깊이가 갈리는 지점을 점검하기 위한 것이다. 선택지를 누르면 정답 여부와 이유가 표시된다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>new String(&quot;hello&quot;)가 불필요한 이유로 가장 적절한 것은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="리터럴은 이미 String Pool을 사용할 수 있는데 new String은 별도 객체 생성을 유발한다." aria-pressed="false">A. 이미 존재할 수 있는 리터럴과 별개 객체를 만들 수 있다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="new String도 문자열 값을 표현한다. 문제는 불필요한 객체와 참조 비교 혼동이다." aria-pressed="false">B. 문자열 내용이 저장되지 않는다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="equals 비교가 불가능해지는 것은 아니다." aria-pressed="false">C. equals를 사용할 수 없게 된다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>String 값 비교는 ==보다 equals를 사용하는 것이 원칙이다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="==는 참조 비교라 pool/intern 여부에 따라 결과가 달라질 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="문자열 값 비교는 equals가 기준이다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>intern()을 실무에서 신중하게 써야 하는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="중복 문자열을 줄일 수 있지만 pool 관리 비용과 메모리 압박이 생길 수 있어 측정 기반으로 써야 한다." aria-pressed="false">A. 메모리 절감 가능성과 pool 부담을 함께 검토해야 한다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="intern이 모든 성능 문제를 해결하지 않는다." aria-pressed="false">B. 호출하면 항상 GC 비용이 0이 된다.</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="intern은 문자열 pool과 관련된 기능이다." aria-pressed="false">C. 숫자 wrapper 캐시를 제어하는 기능이다.</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[equals-and-hashcode]]
- [[gc-and-tuning]]