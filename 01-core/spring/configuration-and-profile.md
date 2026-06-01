---
title: Configuration And Profile
description: Spring의 설정 관리와 Profile 기반 환경 분리
---

# Configuration And Profile

## 한 줄 정의

Spring의 Configuration은 Bean 등록과 외부 설정을 관리하는 메커니즘이고, Profile은 환경(dev, prod 등)별로 다른 설정을 적용하는 기능이다.

## 실무에서 왜 중요한가

설정 관리를 제대로 하지 않으면 다음 문제가 생긴다.

- 운영 환경 DB 정보가 코드에 하드코딩되어 보안 사고가 발생한다.
- 로컬에서 잘 되던 게 운영에서 다른 설정 때문에 실패한다.
- Profile 분리를 하지 않아서 개발 환경에서 운영 DB에 접근한다.
- `@Value`와 `@ConfigurationProperties`의 차이를 모르고 혼용한다.

## 설정 파일

### application.yml

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mydb
    username: root
    password: password

app:
  api:
    timeout: 3000
    max-retry: 3
```

### 설정 우선순위

Spring Boot는 다음 순서로 설정을 적용한다 (아래로 갈수록 우선순위 높음).

```
1. application.yml (기본)
2. application-{profile}.yml (프로파일별)
3. 환경 변수
4. 커맨드 라인 인자 (--server.port=9090)
```

우선순위가 높은 설정이 낮은 설정을 덮어쓴다.

## 설정값 주입

### @Value

```java
@Service
public class ApiClient {

    @Value("${app.api.timeout}")
    private int timeout;

    @Value("${app.api.max-retry:3}") // 기본값 설정
    private int maxRetry;
}
```

간단한 단일 값 주입에 사용한다.

### @ConfigurationProperties (권장)

```java
@ConfigurationProperties(prefix = "app.api")
public class ApiProperties {

    private int timeout;
    private int maxRetry;

    // getter, setter
}
```

```java
@Configuration
@EnableConfigurationProperties(ApiProperties.class)
public class AppConfig { }
```

- 관련 설정을 객체로 묶어서 타입 안전하게 관리한다.
- `@Value`보다 유지보수가 쉽다.
- 검증(`@Validated`), 리스트, 중첩 객체를 지원한다.

### 비교

| 기준 | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| 타입 안전성 | 낮음 (문자열 기반) | 높음 (객체 바인딩) |
| 관련 설정 그룹화 | 불가 | 가능 |
| 검증 | 불가 | `@Validated` 지원 |
| 적합한 경우 | 단순 단일 값 | 관련된 설정 묶음 |

## Profile

### 환경별 설정 분리

```yaml
# application.yml (공통)
spring:
  profiles:
    active: dev

# application-dev.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/devdb

# application-prod.yml
spring:
  datasource:
    url: jdbc:mysql://prod-server:3306/proddb
```

### Profile별 Bean 등록

```java
@Configuration
public class StorageConfig {

    @Bean
    @Profile("dev")
    public FileStorage localStorage() {
        return new LocalFileStorage();
    }

    @Bean
    @Profile("prod")
    public FileStorage s3Storage() {
        return new S3FileStorage();
    }
}
```

환경에 따라 다른 구현체를 사용해야 할 때 `@Profile`로 Bean을 분리한다.

### Profile 활성화 방법

```bash
# 환경 변수
SPRING_PROFILES_ACTIVE=prod

# 커맨드 라인
java -jar app.jar --spring.profiles.active=prod

# application.yml
spring:
  profiles:
    active: dev
```

운영 환경에서는 환경 변수나 커맨드 라인으로 Profile을 지정하는 것이 안전하다.

## @Configuration

```java
@Configuration
public class AppConfig {

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }
}
```

`@Configuration` 클래스는 CGLIB 프록시로 감싸져서 `@Bean` 메서드가 여러 번 호출되어도 같은 인스턴스를 반환한다 (singleton 보장). Spring Boot가 자동 등록하는 Bean(예: `ObjectMapper`)과 같은 타입을 `@Bean`으로 정의하면 자동 설정을 대체한다.

## 민감 정보 관리

```yaml
# 위험: 비밀번호를 설정 파일에 직접 작성
spring:
  datasource:
    password: real-password

# 안전: 환경 변수로 주입
spring:
  datasource:
    password: ${DB_PASSWORD}
```

- 비밀번호, API 키 등 민감 정보는 환경 변수나 외부 시크릿 관리 도구를 사용한다.
- 설정 파일에 민감 정보를 직접 작성하면 Git에 노출될 위험이 있다.

## 자주 나는 실수

- 민감 정보를 `application.yml`에 직접 작성하고 Git에 커밋한다.
- Profile 분리 없이 환경별 설정을 if문으로 분기한다.
- `@Value`로 모든 설정을 주입해서 관련 설정이 흩어진다.
- `@ConfigurationProperties`에 getter/setter를 빠뜨려서 바인딩이 안 된다.
- Profile을 지정하지 않아서 기본 설정으로 운영 환경이 실행된다.

## 핵심 요약

Spring의 설정은 `application.yml`에 작성하고, 환경별로 `application-{profile}.yml`로 분리합니다.
설정값 주입은 단일 값이면 `@Value`, 관련 설정 묶음이면 `@ConfigurationProperties`를 사용합니다.

Profile은 환경(dev, prod)별로 다른 설정과 Bean을 적용하는 기능입니다.
운영 환경에서는 환경 변수로 Profile을 활성화하고, 민감 정보는 설정 파일에 직접 작성하지 않아야 합니다.

## 꼬리 질문

> [!question]- `@Value`와 `@ConfigurationProperties`의 차이는?
> `@Value`는 단일 값을 문자열 키로 주입하고, `@ConfigurationProperties`는 관련 설정을 객체로 묶어서 타입 안전하게 바인딩합니다. 설정이 여러 개이거나 검증이 필요하면 `@ConfigurationProperties`가 적합합니다.

> [!question]- 설정 우선순위는 어떻게 되는가?
> `application.yml` < `application-{profile}.yml` < 환경 변수 < 커맨드 라인 인자 순으로 우선순위가 높아집니다. 우선순위가 높은 설정이 낮은 설정을 덮어씁니다.

> [!question]- 민감 정보는 어떻게 관리하는가?
> 환경 변수, Kubernetes Secret, AWS Parameter Store 같은 외부 시크릿 관리 도구를 사용합니다. 설정 파일에 직접 작성하면 Git을 통해 노출될 위험이 있습니다.

> [!question]- `@Configuration`의 CGLIB 프록시란?
> `@Configuration` 클래스는 CGLIB으로 프록시가 생성되어 `@Bean` 메서드를 여러 번 호출해도 같은 인스턴스를 반환합니다. 이를 통해 Bean의 singleton을 보장합니다.

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[bean-lifecycle-and-scope]]
- [[ioc-and-di]]