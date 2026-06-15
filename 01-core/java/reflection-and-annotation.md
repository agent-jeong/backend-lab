---
title: 리플렉션과 애노테이션 동작 원리
description: Spring, JPA, Jackson의 기반이 되는 Reflection과 Annotation의 실무 이해
---

# 리플렉션과 애노테이션 동작 원리

## 한 줄 정의

Reflection은 런타임에 클래스, 메서드, 필드 정보를 조회하거나 호출하는 기능이고, Annotation은 코드에 메타데이터를 붙여 프레임워크가 동작 기준으로 사용하게 하는 문법이다.

## 실무에서 왜 중요한가

Spring, JPA, Jackson은 Reflection과 Annotation을 기반으로 많은 자동화를 제공한다. 이 원리를 모르면 다음 상황을 설명하기 어렵다.

- Spring이 `@Component`, `@Service`, `@Autowired`를 어떻게 찾아 Bean으로 등록하는가
- JPA가 Entity 필드를 어떻게 읽고 프록시를 만드는가
- Jackson이 기본 생성자, getter, record constructor를 왜 요구하는가
- annotation을 붙였는데 runtime retention이 아니라서 동작하지 않는 이유
- reflection 기반 코드는 왜 컴파일 타임 안정성과 성능 측면에서 주의가 필요한가

## Annotation 기본

Annotation은 코드에 의미 있는 메타데이터를 붙인다.

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface TraceLog {
}
```

중요한 설정은 `@Target`과 `@Retention`이다.

| 설정 | 의미 |
|---|---|
| `@Target` | annotation을 붙일 수 있는 위치 |
| `@Retention` | annotation 정보가 유지되는 시점 |
| `SOURCE` | 컴파일 후 사라짐 |
| `CLASS` | class 파일에는 있지만 런타임 reflection에서 일반적으로 읽지 않음 |
| `RUNTIME` | 런타임 reflection으로 읽을 수 있음 |

Spring처럼 런타임에 annotation을 읽어 동작해야 한다면 보통 `RetentionPolicy.RUNTIME`이 필요하다.

## Reflection 기본

Reflection을 사용하면 런타임에 클래스 정보를 조회할 수 있다.

```java
Class<?> clazz = UserService.class;

for (Method method : clazz.getDeclaredMethods()) {
    if (method.isAnnotationPresent(TraceLog.class)) {
        System.out.println(method.getName());
    }
}
```

필드나 메서드 접근 제한을 우회할 수도 있다.

```java
Field field = User.class.getDeclaredField("name");
field.setAccessible(true);
Object value = field.get(user);
```

이 기능은 강력하지만 캡슐화를 깨고 런타임 오류를 만들 수 있으므로 일반 비즈니스 코드에서는 신중하게 사용한다.

## 프레임워크에서의 사용

| 프레임워크 | 사용 예 |
|---|---|
| Spring | classpath scanning, Bean 등록, AOP proxy, dependency injection |
| JPA | Entity field 접근, 기본 생성자, proxy 생성 |
| Jackson | JSON field 매핑, constructor/property 탐색 |
| Validation | `@NotNull`, `@Size` 같은 제약 조건 탐색 |

예를 들어 Spring은 특정 annotation이 붙은 클래스를 찾아 BeanDefinition을 만들고, 런타임에 객체를 생성해 컨테이너에 등록한다.

JPA는 Entity를 프록시로 감싸거나 필드 값을 읽어 변경 감지를 수행한다. 그래서 Entity에는 기본 생성자, 상속 가능한 class 구조, 적절한 접근 제어가 중요하다.

## 자주 나는 실수

- custom annotation에 `@Retention(RUNTIME)`을 붙이지 않아 런타임에 읽히지 않는다.
- reflection으로 private field를 직접 수정해 객체 불변식을 깨뜨린다.
- annotation만 붙이면 자동으로 동작한다고 생각하고 이를 처리하는 코드나 프레임워크 설정을 빠뜨린다.
- reflection 예외를 런타임에서야 발견한다.
- record, final class, private constructor가 프레임워크 요구사항과 충돌하는 이유를 이해하지 못한다.

## 실무 판단 기준

| 상황 | 판단 |
|---|---|
| Spring/JPA/Jackson 동작 원리 설명 | Reflection + Annotation 기반으로 설명 |
| 반복적인 횡단 관심사 | Annotation + AOP 검토 |
| 일반 비즈니스 로직 | Reflection 직접 사용 지양 |
| 런타임 annotation 처리 | `RetentionPolicy.RUNTIME` 필요 |
| 성능 민감 경로 | reflection 호출 비용과 캐싱 검토 |

## 확인 방법

- annotation이 런타임에 필요한지 `@Retention`을 확인한다.
- 프레임워크가 요구하는 생성자, 접근 제어자, final 여부를 확인한다.
- reflection 사용부는 테스트로 런타임 오류를 조기에 잡는다.
- 반복 호출되는 reflection metadata는 캐싱 여부를 확인한다.

## 핵심 요약

Reflection은 런타임에 클래스와 멤버 정보를 조회하거나 호출하는 기능이고, Annotation은 프레임워크가 읽을 수 있는 메타데이터를 코드에 붙이는 방식입니다.

Spring, JPA, Jackson은 annotation을 스캔하고 reflection으로 객체 생성, 필드 접근, 메서드 호출을 수행합니다.

런타임에 annotation을 읽어야 한다면 `RetentionPolicy.RUNTIME`이 필요합니다.

Reflection은 강력하지만 컴파일 타임 안정성이 약하고 캡슐화를 깨거나 성능 비용을 만들 수 있습니다.

면접에서는 annotation 자체가 동작하는 것이 아니라, annotation을 읽고 처리하는 프레임워크 코드가 있어야 동작한다고 설명하는 것이 중요합니다.

## 꼬리 질문

> [!question]- Reflection이란 무엇인가?
> 런타임에 클래스, 메서드, 필드 정보를 조회하고 필요하면 접근하거나 호출할 수 있게 해주는 기능입니다.

> [!question]- Annotation은 붙이기만 하면 동작하는가?
> 아닙니다. Annotation은 메타데이터일 뿐이고, 이를 읽고 처리하는 프레임워크나 코드가 있어야 동작합니다.

> [!question]- `RetentionPolicy.RUNTIME`은 왜 중요한가?
> 런타임에 reflection으로 annotation을 읽어야 하는 경우 annotation 정보가 런타임까지 유지되어야 하기 때문입니다.

> [!question]- Reflection의 단점은 무엇인가?
> 컴파일 타임 안정성이 낮고, 캡슐화를 깰 수 있으며, 일반 메서드 호출보다 비용이 크고 런타임 오류 가능성이 있습니다.

## 관련 문서

- [[java]]
- [[class-interface-enum-record]]
- [[serialization-and-jackson]]
- [[01-core/spring/ioc-and-di|ioc-and-di]]
- [[01-core/jpa/entity-table-mapping|entity-table-mapping]]
