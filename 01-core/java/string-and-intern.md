---
title: "String 리터럴 vs new vs intern"
description: 문자열을 리터럴로 만들 때와 new로 만들 때 무엇이 다르고, String Pool과 intern()은 어떻게 동작하는지
tags: [concept, java]
---

# String 리터럴 vs new vs intern의 차이

String 리터럴은 String Pool에 하나만 두고 같이 쓰고, `new String()`은 매번 Heap에 새 객체를 만든다. `intern()`은 Pool에 같은 값이 있으면 그 참조를 돌려주고, 없으면 Pool에 넣은 뒤 그 참조를 돌려준다.

이 차이를 모르면 `==`와 `equals()`를 헷갈려 문자열 비교 버그를 만든다. 같은 문자열을 `new String()`으로 대량으로 만들면 메모리가 낭비된다. 반대로 `intern()`을 아무 데나 쓰면 String Pool이 불어나 GC 부담이 커진다. Pool과 Heap이 어떻게 연결되는지 알아야 메모리가 어떻게 쓰일지 예상할 수 있다.

## String Pool

String Pool(String Constant Pool)은 JVM이 문자열 리터럴을 모아 두는 곳이다. Java 7부터는 Heap 안에 있다. 그 전에는 PermGen에 있었다.

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

## 리터럴과 new

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

## intern()

```java
String s3 = new String("hello");
String s4 = s3.intern();

System.out.println(s4 == "hello"); // true (Pool의 참조를 반환)
System.out.println(s3 == s4);      // false (s3은 여전히 Heap 객체)
```

1. Pool에 같은 값의 문자열이 있으면 Pool의 참조를 돌려준다.
2. 없으면 Pool에 등록하고 그 참조를 돌려준다.

String Pool은 내부적으로 HashTable이다. 버킷 수는 `-XX:StringTableSize`로 바꾼다.

```bash
# String Pool HashTable 크기 설정 (기본값: 65536, Java 11+)
java -XX:StringTableSize=120011 -jar app.jar
```

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 코드에 문자열을 직접 쓸 때 | 리터럴 | Pool에서 자동 재사용 |
| 외부 입력 문자열 비교 | `equals()` | 참조가 아니라 값을 비교해야 한다 |
| 대량 중복 문자열 메모리 절감 | `intern()` 검토 | Pool 재사용으로 메모리 절약 |
| 고유한 문자열이 대량 생성 | `intern()` 쓰지 않음 | Pool만 커지고 GC 부담 증가 |

## 자주 깨지는 곳

- 문자열을 `==`로 비교하면, 외부 입력이나 `new String()`으로 만든 값과는 내용이 같아도 false가 나온다.
- `intern()`을 아무 데나 부르면, String Pool이 커지고 GC pause가 늘어난다.
- "String Pool은 PermGen에 있다"는 Java 6 이전 설명을 그대로 믿으면 틀린다. Java 7부터는 Heap에 있고 GC 대상이다.
- `new String("hello")`는 객체를 2개까지 만든다. Pool에 1개, Heap에 1개다.

## 한 번에 설명하기

> String 리터럴은 String Pool에 저장돼서 값이 같으면 같은 참조를 받습니다. `new String()`은 매번 Heap에 새 객체를 만들기 때문에 `==`로 비교하면 false가 나옵니다.
>
> `intern()`은 문자열을 Pool에 넣거나 이미 있는 Pool 참조를 돌려줍니다. 같은 값이 많이 반복되면 메모리를 아낄 수 있지만, 값이 전부 제각각이면 오히려 부담만 늘어납니다.
>
> Java 7부터 Pool은 Heap에 있어서 GC 대상입니다. 저는 문자열 비교는 항상 `equals()`로 합니다.

## 꼬리 질문

> [!question]- `new String("hello")`는 객체를 몇 개 만드나?
> 최대 2개입니다. "hello" 리터럴이 처음 나오면 Pool에 1개, `new`로 Heap에 1개가 생깁니다. Pool에 "hello"가 이미 있으면 Heap에 1개만 더 생깁니다.

> [!question]- `intern()`은 언제 쓸모가 있나?
> 밖에서 읽어 온 문자열에 같은 값이 아주 많이 반복될 때입니다. 예를 들어 CSV를 파싱하는데 상태값 몇 개가 계속 반복되면 메모리를 꽤 아낍니다. 값이 대부분 제각각이면 역효과가 납니다.

> [!question]- String Pool은 왜 Heap으로 옮겨졌나?
> Java 6까지는 PermGen에 있어서 크기가 고정이었고, 문자열을 많이 intern하면 `OutOfMemoryError: PermGen space`가 났습니다. Java 7부터 Heap으로 옮기면서 GC 대상이 됐고, 메모리를 더 유연하게 쓸 수 있게 됐습니다.

> [!question]- `==`와 `equals()`를 구분하지 않으면 어떤 버그가 생기나?
> 리터럴끼리는 같은 Pool 객체라서 `==`로 비교해도 true가 나옵니다. 하지만 HTTP 파라미터나 DB 조회 결과 같은 외부 입력은 `new String()`처럼 따로 만든 Heap 객체라서, `==`로 비교하면 false가 나옵니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>new String(&quot;hello&quot;)가 불필요한 이유는?</p>
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

## 참고

2026년 11월에 확인한 공식 문서다.

- [Java SE 21 API: String.intern](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html)
- [JLS 21: String Literals](https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html#jls-3.10.5)

## 관련 문서

- [[01-core/java/java|java]]
- [[jvm-memory-structure]]
- [[equals-and-hashcode]]
- [[gc-and-tuning]]