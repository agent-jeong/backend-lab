---
title: "테이블 설계와 키 전략"
description: PK, FK, UK를 어떻게 잡고 컬럼 타입은 무엇으로 고르는지
tags: [concept, database]
---

# 테이블 설계와 키 전략

테이블은 데이터를 행(Row)과 열(Column)로 담는 구조다. Key는 행 하나를 콕 집어 가리키거나 테이블끼리 잇는 제약 조건이다.

키와 컬럼 타입은 데이터가 쌓인 뒤에는 바꾸기 비싸다. PK를 복합 키로 잡으면 JOIN과 인덱스가 복잡해지고, FK를 안 걸면 회원이 지워진 주문 같은 데이터가 남는다. 타입을 잘못 고르면 저장 공간도 더 쓰고 인덱스도 느려진다.

## 테이블 구조

```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| 구성 요소 | 뜻 |
|---|---|
| Row (행) | 데이터 한 건 |
| Column (열) | 데이터의 속성 하나 (필드) |
| Schema | 테이블이 어떻게 생겼는지 (컬럼명, 타입, 제약 조건) |

## Key 종류

### Primary Key (PK)

행 하나를 유일하게 가리키는 키다. NOT NULL과 UNIQUE가 저절로 붙는다.

```sql
-- 대리 키: 비즈니스 의미 없는 자동 증가 값
id BIGINT AUTO_INCREMENT PRIMARY KEY

-- 자연 키: 비즈니스 의미가 있는 값 (비권장)
email VARCHAR(255) PRIMARY KEY
```

PK는 업무와 상관없는 대리 키(surrogate key)로 잡는다. 이메일 같은 자연 키는 업무 규칙이 바뀌면 PK까지 바꿔야 한다.

### AUTO_INCREMENT vs UUID

| 기준 | AUTO_INCREMENT | UUID |
|---|---|---|
| 크기 | 8 bytes (BIGINT) | 16 bytes (BINARY) 또는 36자 (문자열) |
| 인덱스 성능 | 늘 맨 끝에 붙어서 B-Tree에 유리 | 무작위 UUID(v4)는 중간 아무 데나 끼어들어 꽉 찬 페이지를 둘로 쪼개는 일(페이지 분할)이 잦다 |
| 여러 서버 | DB 한 대 안에서만 유일 | 어디서 만들어도 유일 |
| 보안 | 다음 값을 짐작할 수 있음 | v4는 짐작할 수 없음 |

UUID 중에서도 앞부분에 밀리초 단위 시각을 담는 UUIDv7(RFC 9562)은 대체로 시간순으로 늘어나서, 새 키가 인덱스 끝 근처에 붙고 v4보다 페이지 분할이 적다. 같은 밀리초 안의 나머지 비트는 기본이 무작위라 AUTO_INCREMENT처럼 엄격한 순서는 아니다. 대신 생성 시각이 드러난다.

DB가 한 대면 AUTO_INCREMENT를 쓰고, 여러 서버에서 ID를 만들어야 하거나 ID를 밖에 보여 줘야 하면 UUID를 쓴다.

### Foreign Key (FK)

다른 테이블의 PK를 가리켜서 두 테이블을 잇는다.

```sql
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

FK가 있으면 없는 대상을 가리키는 데이터가 들어오지 못한다(참조 무결성). 존재하지 않는 `user_id`로 INSERT하면 DB가 거부한다.

### Unique Key (UK)

같은 값이 두 번 들어오면 안 되는 컬럼에 건다. PK와 달리 NULL은 허용할 수 있다.

```sql
ALTER TABLE users ADD UNIQUE KEY uk_email (email);
```

이메일, 전화번호처럼 업무상 겹치면 안 되는 값에 쓴다.

## 컬럼 타입 고르기

| 데이터 | 쓸 타입 | 조심할 점 |
|---|---|---|
| PK | BIGINT | INT는 약 21억이 끝이라, 데이터가 많은 서비스에서는 모자란다 |
| 금액 | DECIMAL | FLOAT/DOUBLE은 부동소수점 오차가 생긴다 |
| 상태값 | ENUM 또는 VARCHAR | ENUM은 값을 바꿀 때 DDL이 필요하다 |
| 날짜·시간 | DATETIME 또는 TIMESTAMP | MySQL TIMESTAMP는 2038-01-19 이후 값을 담지 못한다 |
| 긴 텍스트 | TEXT | 길이 제한이 큰 본문은 아주 긴 VARCHAR보다 TEXT가 맞다 (VARCHAR는 행 크기 제한 65,535바이트를 나눠 쓴다) |
| 불리언 | TINYINT(1) | MySQL에는 BOOLEAN 타입이 따로 없다 (내부적으로 TINYINT) |

## 자주 깨지는 곳

- PK를 복합 키로 만들면, JOIN 조건과 인덱스가 복잡해진다.
- 금액을 FLOAT로 저장하면, 소수점 오차가 생긴다.
- FK 없이 애플리케이션 코드로만 관계를 지키면, 부모가 지워진 고아 데이터가 남는다.
- PK를 INT로 잡으면, 21억 건을 넘는 순간 오버플로가 난다.
- UNIQUE 제약 없이 애플리케이션에서만 중복을 검사하면, 동시에 들어온 요청 둘이 모두 검사를 통과해 중복이 들어간다.

## 한 번에 설명하기

> 테이블은 데이터를 행과 열로 담고, Key는 행을 가리키거나 테이블끼리 잇는 데 씁니다.
>
> 저는 PK를 BIGINT AUTO_INCREMENT 대리 키로 잡고, 여러 서버에서 ID를 만들거나 ID를 밖에 보여 줘야 하면 UUID를 씁니다.
>
> 없는 대상을 가리키지 않게 하는 건 FK로, 이메일처럼 겹치면 안 되는 값은 UK로 DB가 막게 합니다. 금액은 부동소수점 오차가 없게 DECIMAL을 씁니다.

## 꼬리 질문

> [!question]- FK를 실무에서 안 거는 경우도 있는가?
> 있습니다. 규모가 큰 서비스에서는 쓰기 성능이나 운영 중 테이블을 다루기 편하려고 FK를 안 걸기도 합니다. 그때는 애플리케이션 코드에서 관계를 지키고, 고아 데이터는 배치로 정리합니다.

> [!question]- AUTO_INCREMENT PK가 보안에 취약한 이유는?
> 하나씩 늘어나니까 다른 사용자의 ID를 짐작할 수 있습니다. API에 PK를 그대로 드러내면, 남의 데이터를 ID만 바꿔 조회하는 IDOR(Insecure Direct Object Reference) 취약점이 될 수 있습니다.

> [!question]- 복합 PK를 피하는 이유는?
> JOIN 조건이 길어지고, FK도 여러 컬럼을 가리켜야 하고, JPA 매핑도 복잡해집니다. 행은 대리 키 하나로 가리키고, 업무상 겹치면 안 되는 값은 UK로 막는 편이 관리하기 쉽습니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [MySQL 8.4: Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- [MySQL 8.4: FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[db-index]]
