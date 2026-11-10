---
title: "테이블 설계와 키 전략"
description: 테이블 구조와 PK, FK, UK의 역할과 설계 기준
tags: [concept, database]
---

# 테이블 설계와 키 전략

테이블은 행(Row)과 열(Column)로 데이터를 저장하는 구조다. Key는 행을 식별하거나 테이블 사이 관계를 잇는 제약조건이다.

키와 컬럼 타입은 한번 정하면 바꾸기 비싸다. PK를 복합 키로 잡으면 JOIN과 인덱스가 복잡해지고, FK를 안 걸면 정합성이 깨지고, 타입을 잘못 고르면 저장 공간과 인덱스 성능이 같이 나빠진다.

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

| 구성 요소 | 의미 |
|---|---|
| Row (행) | 하나의 데이터 레코드 |
| Column (열) | 데이터의 속성 (필드) |
| Schema | 테이블의 구조 정의 (컬럼명, 타입, 제약조건) |

## Key 종류

### Primary Key (PK)

행을 유일하게 식별하는 키다. NOT NULL과 UNIQUE가 자동으로 붙는다.

```sql
-- 대리 키: 비즈니스 의미 없는 자동 증가 값
id BIGINT AUTO_INCREMENT PRIMARY KEY

-- 자연 키: 비즈니스 의미가 있는 값 (비권장)
email VARCHAR(255) PRIMARY KEY
```

PK는 대리 키(surrogate key)로 잡는다. 자연 키는 비즈니스 규칙이 바뀌면 같이 바뀌어야 한다.

### AUTO_INCREMENT vs UUID

| 기준 | AUTO_INCREMENT | UUID |
|---|---|---|
| 크기 | 8 bytes (BIGINT) | 16 bytes (BINARY) 또는 36자 (문자열) |
| 인덱스 성능 | 순차 삽입으로 B-Tree에 유리 | 랜덤 삽입으로 페이지 분할 발생 |
| 분산 환경 | 단일 DB에서만 유일 | 전역적으로 유일 |
| 보안 | 예측 가능 (순차) | 예측 불가 |

단일 DB면 AUTO_INCREMENT, 분산 환경이거나 ID를 외부에 노출해야 하면 UUID를 쓴다.

### Foreign Key (FK)

다른 테이블의 PK를 참조해 관계를 표현한다.

```sql
CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

FK가 있으면 참조 무결성이 보장된다. 존재하지 않는 `user_id`로 INSERT하면 DB가 거부한다.

### Unique Key (UK)

중복을 허용하지 않는 컬럼에 건다. PK와 달리 NULL을 허용할 수 있다.

```sql
ALTER TABLE users ADD UNIQUE KEY uk_email (email);
```

이메일, 전화번호, 주민번호 같은 비즈니스 유일값에 쓴다.

## 컬럼 타입 고르기

| 데이터 | 권장 타입 | 주의점 |
|---|---|---|
| PK | BIGINT | INT는 21억 한계, 대용량 서비스에서 부족 |
| 금액 | DECIMAL | FLOAT/DOUBLE은 부동소수점 오차 발생 |
| 상태값 | ENUM 또는 VARCHAR | ENUM은 변경 시 DDL 필요 |
| 날짜/시간 | DATETIME 또는 TIMESTAMP | TIMESTAMP는 2038년 문제 있음 (MySQL) |
| 긴 텍스트 | TEXT | VARCHAR(MAX)보다 TEXT가 적합 |
| 불리언 | TINYINT(1) | MySQL에 BOOLEAN 타입이 없음 (내부적으로 TINYINT) |

## 자주 깨지는 곳

- **PK를 복합 키로 만든다.** JOIN 조건과 인덱스 관리가 복잡해진다.
- **금액을 FLOAT로 저장한다.** 소수점 오차가 생긴다.
- **FK 없이 애플리케이션에서만 관계를 관리한다.** 부모가 지워진 고아 데이터가 남는다.
- **PK를 INT로 잡는다.** 21억 건을 넘으면 오버플로가 난다.
- **UNIQUE 제약 없이 애플리케이션에서만 중복을 검사한다.** 동시 요청이 둘 다 검사를 통과해 중복이 들어간다.

## 한 번에 설명하기

> 테이블은 행과 열로 데이터를 저장하고, Key는 행을 식별하거나 관계를 잇는 데 씁니다. 저는 PK를 BIGINT AUTO_INCREMENT 대리 키로 잡고, 분산 환경이나 외부 노출이 필요하면 UUID를 검토합니다. 참조 무결성은 FK로, 이메일 같은 비즈니스 유일값은 UK로 DB에서 보장합니다. 금액은 부동소수점 오차가 없도록 DECIMAL을 씁니다.

## 꼬리 질문

> [!question]- FK를 실무에서 안 거는 경우도 있는가?
> 대규모 서비스에서는 성능과 운영 유연성 때문에 FK를 걸지 않는 경우가 있습니다. 이 경우 애플리케이션 레벨에서 정합성을 관리하고, 배치로 고아 데이터를 정리합니다.

> [!question]- AUTO_INCREMENT PK가 보안에 취약한 이유는?
> 순차적으로 증가하기 때문에 다른 사용자의 ID를 예측할 수 있습니다. API에서 PK를 직접 노출하면 IDOR(Insecure Direct Object Reference) 취약점이 될 수 있습니다.

> [!question]- 복합 PK를 피하는 이유는?
> JOIN 조건이 복잡해지고, FK가 여러 컬럼을 참조해야 하며, JPA 매핑도 복잡해집니다. 대리 키 하나로 식별하고 비즈니스 유일성은 UK로 보장하는 것이 실무에서 관리하기 쉽습니다.

## 참고

공식 문서와 원문 자료다. 링크는 2026-11에 확인했다.

- [MySQL 8.4: Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- [MySQL 8.4: FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[db-index]]
