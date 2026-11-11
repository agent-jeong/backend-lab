---
title: Spring Boot 자동 설정
description: 의존성만 추가했는데 빈이 생기는 원리와, 내가 등록한 빈 때문에 자동 설정이 물러나는 조건
tags: [concept, spring]
---

# Spring Boot 자동 설정

자동 설정(auto-configuration)은 클래스패스에 어떤 라이브러리가 있는지, 내가 어떤 빈을 이미 등록했는지, 어떤 설정값이 있는지를 보고 Spring Boot가 기본 빈을 대신 등록해 주는 기능이다. `spring-boot-starter-web`만 추가해도 내장 Tomcat, DispatcherServlet, JSON 변환기가 준비되는 이유가 이것이다.

편한 만큼 모르고 있다가 당한다. 날짜 포맷을 하나 바꾸려고 `ObjectMapper`를 직접 등록했더니 주문 API 응답의 `LocalDateTime`이 배열로 바뀌고, 결제 콜백 JSON에 모르는 필드가 하나 늘자 역직렬화가 실패하기 시작한다. 자동 설정이 "내 빈이 있으면 물러난다"는 규칙으로 돈다는 걸 알면 이런 일을 미리 막고, 터졌을 때 어디를 볼지도 안다.

이 노트는 Spring Boot 3.x 기준이다.

## starter와 자동 설정은 하는 일이 다르다

starter는 라이브러리 묶음이고, 자동 설정은 그 라이브러리를 보고 빈을 만드는 코드다. 둘을 나눠 보면 원인을 찾을 때 덜 헤맨다.

- `spring-boot-starter-web`은 Spring MVC, 내장 Tomcat, Jackson 같은 jar를 한꺼번에 끌어온다. starter 자체에는 빈을 만드는 코드가 거의 없다.
- 빈을 만드는 쪽은 `spring-boot-autoconfigure` jar에 들어 있는 `@AutoConfiguration` 클래스들이다. 이 클래스들은 "이 클래스가 클래스패스에 있으면"이라는 조건을 달고 있다.
- 그래서 starter를 빼도 같은 라이브러리를 직접 추가하면 자동 설정은 똑같이 켜진다. 반대로 의존성 하나를 추가했을 뿐인데 동작이 바뀌기도 한다. `spring-boot-starter-security`를 넣는 순간 모든 웹 요청에 인증이 걸리는 게 그 예다.

## @SpringBootApplication이 하는 일

`@SpringBootApplication`은 애노테이션 세 개를 합친 것이다.

| 애노테이션 | 하는 일 |
|---|---|
| `@SpringBootConfiguration` | 이 클래스를 설정 클래스로 등록한다 |
| `@ComponentScan` | 이 클래스가 있는 패키지와 하위 패키지에서 `@Component`를 찾는다 |
| `@EnableAutoConfiguration` | 자동 설정 후보를 읽어 조건에 맞는 것만 등록한다 |

메인 클래스를 최상위 패키지에 두라는 말은 `@ComponentScan` 때문이다. 메인 클래스를 하위 패키지에 두면 그 바깥의 내 빈은 스캔되지 않는다.

## 자동 설정 후보를 찾는 방식

Spring Boot는 클래스패스의 모든 jar에서 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 파일을 읽는다. 이 파일에는 자동 설정 클래스 이름이 한 줄에 하나씩 적혀 있다.

```text
# META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.payment.autoconfigure.PaymentClientAutoConfiguration
```

예전에는 `META-INF/spring.factories`의 `EnableAutoConfiguration` 키에 같은 목록을 적었다. Spring Boot 2.7이 imports 파일을 추가했고, 3.0에서 `spring.factories`로 자동 설정을 등록하는 방식이 빠졌다. 2.x 시절에 만든 사내 공용 라이브러리를 Boot 3로 올렸는데 자동 설정이 안 켜진다면 이 파일부터 확인한다. `spring.factories`의 다른 키(리스너 등록 같은 것)는 그대로 동작한다.

후보 목록에 있다고 다 켜지지는 않는다. 각 클래스의 조건을 평가해서 통과한 것만 빈으로 등록된다. 그리고 자동 설정은 내가 등록한 빈 정의가 모두 들어온 뒤에 처리된다. 이 순서 덕분에 "내 빈이 있으면 물러난다"가 성립한다.

## 조건 애노테이션

자동 설정 클래스는 거의 항상 조건을 단다. 직접 공용 라이브러리를 만든다면 아래처럼 쓴다.

```java
@AutoConfiguration
@ConditionalOnClass(PaymentClient.class)
@ConditionalOnProperty(prefix = "example.payment", name = "enabled", havingValue = "true", matchIfMissing = true)
@EnableConfigurationProperties(PaymentClientProperties.class)
public class PaymentClientAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public PaymentClient paymentClient(PaymentClientProperties properties) {
        return new PaymentClient(properties.baseUrl(), properties.timeout());
    }
}
```

| 조건 | 언제 켜지나 | 자주 쓰는 곳 |
|---|---|---|
| `@ConditionalOnClass` | 지정한 클래스가 클래스패스에 있을 때 | 라이브러리가 있을 때만 설정 |
| `@ConditionalOnMissingBean` | 같은 타입의 빈이 아직 없을 때 | 사용자가 직접 등록하면 물러나기 |
| `@ConditionalOnBean` | 지정한 빈이 이미 있을 때 | 다른 빈에 기대는 설정 |
| `@ConditionalOnProperty` | 설정값이 있고 `false`가 아닐 때(기본) | 기능 켜고 끄기 |
| `@ConditionalOnWebApplication` | 웹 애플리케이션일 때 | 서블릿, 리액티브 전용 설정 |

`@ConditionalOnProperty`는 `havingValue`와 `matchIfMissing`으로 기준을 바꾼다. 위 예시는 `example.payment.enabled`를 적지 않으면 켜지고, `false`로 적으면 꺼진다.

## 내가 빈을 등록하면 자동 설정이 물러난다

같은 타입의 빈을 내가 등록하면 `@ConditionalOnMissingBean`이 걸린 자동 설정 빈은 만들어지지 않는다. Boot 문서는 이것을 "back off"라고 부른다. `DataSource`를 직접 등록하면 기본 내장 DB 설정이 빠지고, `SecurityFilterChain`을 등록하면 Boot의 기본 웹 보안 설정이 빠진다.

물러나는 단위는 빈 하나다. 그 빈에 걸려 있던 기본값도 같이 사라진다. 이 점을 놓치면 아래 사고가 난다.

```java
@Configuration
public class JacksonConfig {

    // Boot가 만들던 ObjectMapper가 통째로 빠진다
    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper().registerModule(new JavaTimeModule());
    }
}
```

Boot가 만드는 `ObjectMapper`는 `WRITE_DATES_AS_TIMESTAMPS`와 `FAIL_ON_UNKNOWN_PROPERTIES`를 꺼 둔다. 직접 만든 `ObjectMapper`는 Jackson 기본값이라 둘 다 켜져 있다. 그래서 `LocalDateTime`이 `[2024, 1, 15, 10, 30]` 같은 배열로 나가고, 외부 결제사가 응답에 필드를 하나 추가하면 역직렬화가 실패한다. `application.yml`에 적은 `spring.jackson.*` 설정도 더는 적용되지 않는다. Spring MVC의 JSON 변환기는 컨텍스트의 `ObjectMapper` 빈을 쓰므로, 이 변경은 모든 API 응답에 한꺼번에 퍼진다.

기본값을 유지한 채 일부만 바꾸려면 빈을 갈아 끼우지 말고 덧붙인다.

```java
@Configuration
public class JacksonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> builder.serializationInclusion(JsonInclude.Include.NON_NULL);
    }
}
```

`spring.jackson.*` 설정으로 되는 일은 설정 파일에서 하고, 코드가 필요하면 `Jackson2ObjectMapperBuilderCustomizer`를 쓴다. 다른 자동 설정도 대부분 `...Customizer` 빈이나 설정값으로 일부만 바꾸는 길을 열어 둔다. Jackson 3로 바뀐 Boot 4의 이름 차이는 [[serialization-and-jackson]]에 있다.

## 어떻게 바꾸나

| 하고 싶은 일 | 방법 | 결과 |
|---|---|---|
| 기본값 일부만 바꾸기 | `spring.*` 설정값 | 자동 설정은 그대로 켜져 있다 |
| 코드로 일부 바꾸기 | `...Customizer` 빈 | 자동 설정이 만든 빈에 내 설정이 더해진다 |
| 빈을 통째로 바꾸기 | 같은 타입의 `@Bean` 등록 | 자동 설정 빈이 물러나고 기본값도 사라진다 |
| 자동 설정 자체를 끄기 | `@SpringBootApplication(exclude = ...)` 또는 `spring.autoconfigure.exclude` | 그 클래스의 빈이 하나도 안 생긴다 |

## 자주 깨지는 곳

- `ObjectMapper`, `RestTemplate` 빌더, `DataSource` 같은 빈을 "설정 하나만 바꾸려고" 직접 등록하면, 자동 설정이 넣어 주던 다른 기본값까지 같이 사라진다.
- 의존성을 추가하면서 자동 설정을 확인하지 않으면, 의도하지 않은 빈이 켜진다. Spring Security를 넣으면 모든 엔드포인트에 인증이 걸리고 기동 로그에 임시 비밀번호가 찍힌다.
- Boot 2.x 공용 라이브러리를 `spring.factories`만 둔 채로 Boot 3에서 쓰면, 오류 없이 자동 설정이 조용히 빠진다.
- 직접 만든 `@Configuration`에 `@ConditionalOnMissingBean`을 달면, 빈 정의가 들어오는 순서에 따라 결과가 바뀐다. Boot 문서도 이 조건은 자동 설정 클래스에서만 쓰라고 권한다.
- `@Bean` 메서드의 반환 타입을 인터페이스로 적으면, 조건 평가가 메서드 시그니처의 타입만 보기 때문에 구현 타입 기준의 `@ConditionalOnMissingBean`이 기대와 다르게 판정된다.
- 직접 만든 자동 설정 클래스가 컴포넌트 스캔 범위 안에 있으면, 일반 설정 클래스처럼 사용자 빈과 같은 시점에 등록되어 "사용자 빈 뒤에 평가된다"는 전제가 깨진다. 자동 설정 클래스는 스캔되지 않는 패키지에 두고 imports 파일로만 등록한다.

## 운영에서 볼 것

어떤 자동 설정이 켜졌고 왜 꺼졌는지는 조건 평가 리포트(conditions evaluation report)가 보여 준다.

- 로컬에서는 `--debug`로 띄운다. 기동 로그에 `Positive matches`(켜진 것)와 `Negative matches`(꺼진 것, 꺼진 이유)가 찍힌다.

```bash
java -jar example-service.jar --debug
```

- 떠 있는 서버에서는 actuator의 `conditions` 엔드포인트를 연다. 웹으로는 기본으로 `health`만 열려 있으므로 노출 목록에 넣어야 한다.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,conditions
```

- `GET /actuator/conditions` 응답의 `negativeMatches`에서 `JacksonAutoConfiguration` 항목을 찾으면, 직접 등록한 `ObjectMapper` 때문에 자동 설정의 `ObjectMapper` 빈이 빠졌는지와 그 이유가 보인다.
- `conditions`는 애플리케이션 내부 구성을 보여 주므로 운영에서는 내부망이나 인증 뒤에서만 연다.
- 자동 설정을 만드는 쪽이라면 `ApplicationContextRunner` 테스트로 "사용자 빈이 있으면 물러나는지"를 확인한다.

## 한 번에 설명하기

> 자동 설정은 클래스패스의 라이브러리, 이미 등록된 빈, 설정값을 보고 Spring Boot가 기본 빈을 대신 등록하는 기능입니다. Boot 3에서는 jar 안의 `AutoConfiguration.imports` 파일에서 후보를 읽고, `@ConditionalOnClass`나 `@ConditionalOnMissingBean` 같은 조건을 통과한 것만 등록합니다.
>
> 자동 설정은 사용자 빈이 다 등록된 뒤에 평가되기 때문에, 같은 타입의 빈을 직접 등록하면 자동 설정 빈은 물러납니다. 이때 그 빈에 붙어 있던 기본값도 같이 사라집니다.
>
> 그래서 저는 기본값 일부만 바꿀 때는 빈을 갈아 끼우지 않고 설정값이나 Customizer 빈을 씁니다. 동작이 이상하면 `--debug`나 actuator `conditions`로 어떤 자동 설정이 왜 꺼졌는지부터 봅니다.

## 꼬리 질문

> [!question]- starter와 자동 설정은 무엇이 다른가?
> starter는 함께 쓰는 라이브러리를 한 번에 끌어오는 의존성 묶음이고, 자동 설정은 그 라이브러리가 클래스패스에 있는지 보고 빈을 등록하는 코드입니다. 빈을 실제로 만드는 쪽은 `@AutoConfiguration` 클래스입니다.

> [!question]- `ObjectMapper`를 직접 빈으로 등록하면 무엇이 바뀌나?
> Boot의 `ObjectMapper` 자동 설정이 물러납니다. Boot가 꺼 두던 `WRITE_DATES_AS_TIMESTAMPS`와 `FAIL_ON_UNKNOWN_PROPERTIES`가 Jackson 기본값으로 돌아가고, `spring.jackson.*` 설정도 적용되지 않습니다. 일부만 바꾸려면 `Jackson2ObjectMapperBuilderCustomizer`를 씁니다.

> [!question]- Boot 3로 올렸더니 사내 라이브러리의 자동 설정이 안 켜진다. 어디를 보나?
> 라이브러리가 자동 설정을 `spring.factories`에만 등록했는지 봅니다. Boot 3.0부터는 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 파일에 적힌 클래스만 자동 설정으로 읽습니다.

> [!question]- 어떤 자동 설정이 켜졌는지 어떻게 확인하나?
> 로컬에서는 `--debug`로 띄워 조건 평가 리포트를 봅니다. 떠 있는 서버라면 actuator `conditions` 엔드포인트를 노출해서 각 자동 설정이 어떤 조건 때문에 켜지거나 꺼졌는지 확인합니다.

> [!question]- 자동 설정을 아예 끄려면?
> `@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)`처럼 애노테이션에 적거나 `spring.autoconfigure.exclude` 설정에 클래스 이름을 적습니다. 빈 하나만 바꾸고 싶다면 끄지 말고 같은 타입의 빈을 등록하는 편이 범위가 좁습니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Boot 3.5: Auto-configuration](https://docs.spring.io/spring-boot/3.5/reference/using/auto-configuration.html)
- [Spring Boot 3.5: Creating Your Own Auto-configuration](https://docs.spring.io/spring-boot/3.5/reference/features/developing-auto-configuration.html)
- [Spring Boot 3.5: Customize the Jackson ObjectMapper](https://docs.spring.io/spring-boot/3.5/how-to/spring-mvc.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[ioc-and-di]]
- [[configuration-and-profile]]
- [[serialization-and-jackson]]
- [[spring-security-flow]]
