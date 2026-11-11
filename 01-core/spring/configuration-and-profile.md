---
title: 설정 관리와 Profile 분리
description: 설정값을 어디에 두고 어떻게 받는지, 환경마다 Profile로 나누는 법
tags: [concept, spring]
---

# 설정 관리와 Profile 분리

Spring에서 설정은 두 가지다. `@Configuration`으로 Bean을 등록하는 일과, `application.yml` 같은 파일에서 값을 읽어 오는 일이다. Profile은 dev, prod처럼 환경마다 다른 값을 쓰게 해 준다.

설정을 잘못 나누면 사고가 바로 난다. 운영 DB 비밀번호가 코드와 함께 Git에 올라가고, 개발 서버가 운영 DB에 붙고, 로컬에서 되던 결제 호출이 운영에서만 다른 타임아웃 값 때문에 실패한다.

## 설정 파일

### application.yml

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/mydb
    username: app_user
    password: ${DB_PASSWORD}

app:
  api:
    timeout: 3000
    max-retry: 3
```

### 설정 우선순위

아래로 갈수록 우선순위가 높다.

```
1. application.yml (기본)
2. application-{profile}.yml (프로파일별)
3. 환경 변수
4. 커맨드 라인 인자 (--server.port=9090)
```

높은 쪽이 낮은 쪽을 덮어쓴다. 그래서 같은 jar를 환경 변수나 실행 인자만 바꿔 여러 환경에 띄울 수 있다.

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

값 하나를 넣을 때 쓴다.

### @ConfigurationProperties (설정 묶음이면 이쪽)

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

관련 설정을 객체 하나에 묶어 타입에 맞게 받는다. 검증(`@Validated`), 리스트, 중첩 객체도 받을 수 있어서 `@Value`를 여기저기 흩어 두는 것보다 고치기 쉽다.

### 무엇을 쓸까

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
  application:
    name: example-service

# application-dev.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/devdb

# application-prod.yml
spring:
  datasource:
    url: jdbc:mysql://db.example.com:3306/app
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

로컬에서는 파일에, 운영에서는 S3에 저장하듯 환경마다 구현체가 달라야 하면 `@Profile`로 Bean을 나눈다. 코드 안에서 if문으로 환경을 가르지 않는다.

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

운영에서는 환경 변수나 커맨드 라인으로 지정한다. 공통 파일에 `active: dev`를 박아 두면, 운영에서 Profile 지정이 빠졌을 때 운영 서버가 dev 설정으로 떠서 개발 DB에 붙는다.

## @Configuration

```java
@Configuration
public class AppConfig {

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }

    @Bean
    public Clock clock() {
        return Clock.system(ZoneId.of("Asia/Seoul")); // 테스트에서 고정 시계로 바꿔 끼운다
    }
}
```

`@Configuration` 클래스는 CGLIB 프록시로 감싸진다. 그래서 `@Bean` 메서드를 여러 번 불러도 같은 인스턴스가 나오고, singleton이 지켜진다. Spring Boot가 자동으로 등록하는 Bean(예: `ObjectMapper`)과 같은 타입을 `@Bean`으로 직접 정의하면 자동 설정 대신 내 Bean이 쓰이고, Boot가 넣어 주던 기본값도 같이 사라진다. 일부만 바꾸려면 설정값이나 `...Customizer` 빈을 쓴다([[spring-boot-auto-configuration]]).

## 민감 정보 관리

```yaml
# 위험: 비밀번호를 설정 파일에 직접 작성
spring:
  datasource:
    password: plain-text-password

# 안전: 환경 변수로 주입
spring:
  datasource:
    password: ${DB_PASSWORD}
```

비밀번호와 API 키는 환경 변수나 외부 시크릿 관리 도구로 넣는다. 설정 파일에 직접 쓰면 Git 이력에 그대로 남는다.

## 자주 깨지는 곳

- 비밀번호를 `application.yml`에 쓰고 커밋하면, 저장소를 볼 수 있는 누구나 운영 비밀번호를 본다.
- Profile 대신 if문으로 환경을 가르면, 환경이 하나 늘 때마다 코드를 고쳐야 한다.
- 모든 설정을 `@Value`로 넣으면, 관련 설정이 클래스마다 흩어져 어디서 무엇을 읽는지 찾기 어렵다.
- `@ConfigurationProperties` 클래스에 setter를 빠뜨리면, 값이 바인딩되지 않는다. setter 없이 쓰려면 record나 생성자가 하나뿐인 불변 클래스로 만들어 생성자로 받는다.
- Profile을 지정하지 않고 띄우면, 운영 서버가 기본 설정으로 뜬다.

## 한 번에 설명하기

> 공통 설정은 `application.yml`에 두고, 환경마다 다른 값은 `application-{profile}.yml`로 나눕니다. 값 하나면 `@Value`로, 관련 설정이 여러 개면 `@ConfigurationProperties`로 묶어서 받습니다.
>
> 운영에서는 Profile을 환경 변수로 켭니다. 비밀번호 같은 값은 설정 파일에 쓰지 않고 환경 변수나 시크릿 관리 도구로 넣습니다.

## 꼬리 질문

> [!question]- `@Value`와 `@ConfigurationProperties`의 차이는?
> `@Value`는 값 하나를 문자열 키로 넣고, `@ConfigurationProperties`는 관련 설정을 객체 하나로 묶어서 타입에 맞게 받습니다. 설정이 여러 개거나 검증이 필요하면 `@ConfigurationProperties`를 씁니다.

> [!question]- 설정 우선순위는 어떻게 되는가?
> `application.yml` < `application-{profile}.yml` < 환경 변수 < 커맨드 라인 인자 순서로 높아지고, 높은 쪽 값이 낮은 쪽을 덮어씁니다.

> [!question]- 민감 정보는 어떻게 관리하는가?
> 환경 변수나 Kubernetes Secret, AWS Parameter Store 같은 시크릿 관리 도구로 넣습니다. 설정 파일에 직접 쓰면 Git 이력에 남아서, 나중에 지워도 이력에서 보입니다.

> [!question]- `@Configuration`의 CGLIB 프록시란?
> `@Configuration` 클래스는 CGLIB 프록시로 만들어집니다. 그래서 `@Bean` 메서드를 여러 번 불러도 새로 만들지 않고 이미 만든 인스턴스를 돌려줘서, Bean이 하나로 유지됩니다.

## 점검 퀴즈

선택지를 누르면 정답과 이유가 나온다.

<div class="quiz-list">
  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Value보다 @ConfigurationProperties가 유리한 대표 상황은?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="관련 설정을 타입 안전하게 묶고 validation을 적용하며 구조화된 설정으로 관리할 때 유리하다." aria-pressed="false">A. 여러 설정을 타입 안전한 객체로 묶어 관리할 때</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="@ConfigurationProperties가 모든 설정 누락을 자동 해결하지는 않는다." aria-pressed="false">B. 설정값이 없어도 자동으로 운영 기본값을 추론해야 할 때</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="민감 정보는 애노테이션 종류가 아니라 저장/주입 경로를 안전하게 관리해야 한다." aria-pressed="false">C. 비밀번호를 코드에 직접 넣기 위해서</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">OX</span>민감 정보는 application.yml에 직접 커밋하기보다 환경 변수나 secret manager 같은 외부 주입 방식을 사용해야 한다.</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="설정 파일이 Git에 남으면 토큰/비밀번호가 장기 노출될 수 있다." aria-pressed="false">O</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="민감 정보는 저장소에 남기지 않는 것이 기본이다." aria-pressed="false">X</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>

  <div class="quiz-card" data-quiz-card>
    <p class="quiz-question"><span class="quiz-label">객관식</span>@Configuration에 CGLIB 프록시가 붙는 이유는?</p>
    <div class="quiz-options">
      <button type="button" class="quiz-option" data-quiz-option data-correct="true" data-explanation="@Bean 메서드 간 호출에서도 singleton Bean이 중복 생성되지 않도록 프록시가 개입할 수 있다." aria-pressed="false">A. @Bean 메서드 호출 시 singleton 보장을 유지하기 위해서</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="CGLIB 프록시가 YAML을 암호화하는 기능은 아니다." aria-pressed="false">B. 설정 파일을 자동 암호화하기 위해서</button>
      <button type="button" class="quiz-option" data-quiz-option data-correct="false" data-explanation="프로파일 선택 자체는 별도 설정 메커니즘이다." aria-pressed="false">C. active profile을 무작위로 선택하기 위해서</button>
    </div>
    <p class="quiz-feedback" data-quiz-feedback aria-live="polite"></p>
  </div>
</div>

## 참고

2026년 11월에 확인한 공식 문서다.

- [Spring Boot: Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)
- [Spring Boot: Profiles](https://docs.spring.io/spring-boot/reference/features/profiles.html)

## 관련 문서

- [[01-core/spring/spring|spring]]
- [[bean-lifecycle-and-scope]]
- [[ioc-and-di]]
- [[spring-boot-auto-configuration]]
