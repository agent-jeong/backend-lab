---
title: NoSQL과 CAP 정리
description: NoSQL 데이터 모델 네 가지와, 데이터를 여러 노드에 나눠 담을 때 CAP과 PACELC가 말해 주는 포기의 선택
tags: [concept, database]
---

# NoSQL과 CAP 정리

NoSQL은 테이블과 SQL 대신 키-값, 문서, 와이드 컬럼, 그래프 같은 다른 모양으로 데이터를 담는 저장소를 묶어 부르는 말이다. 대부분 처음부터 데이터를 여러 노드에 나눠 담고 복제해서 늘리는 쪽으로 만들어졌다.

노드가 여러 대가 되면 노드끼리 연락이 끊기는 순간은 언젠가 온다. 장바구니 담기는 연락이 끊겨도 받아 주는 편이 낫지만, 재고 차감은 옛 값을 보고 처리하면 초과 판매가 난다. CAP 정리는 이 순간에 무엇을 포기하는지 말해 주고, 저장소를 고를 때 "빠르냐"보다 "끊겼을 때 어떻게 행동하냐"를 먼저 묻게 한다.

> [!tip] 함께 읽기
> - [[why-rdb]]: RDB가 트랜잭션으로 지켜 주는 것과 NoSQL을 고르는 기준
> - [[replication-and-sharding]]: 복제 지연과 샤드 키 고르기

## NoSQL 데이터 모델 네 가지

| 모델 | 담는 모양 | 맞는 데이터 | 약한 곳 | 예 |
|---|---|---|---|---|
| 키-값 | key 하나에 값 하나 | 세션, 캐시, 카운터, 장바구니 | key를 모르면 찾지 못한다 | Redis, DynamoDB |
| 문서 | JSON 같은 문서 하나에 연관 데이터를 같이 | 상품 상세, 사용자 설정처럼 한 번에 읽히는 묶음 | 문서끼리 JOIN이 약하고, 중복된 값을 맞추는 일이 생긴다 | MongoDB |
| 와이드 컬럼 | 파티션 키로 노드를 고르고, 그 안에서 정렬 키 순서로 행을 둔다 | 기기별 측정값, 사용자별 활동 로그처럼 쓰기가 많고 키 범위로 읽는 데이터 | 파티션 키 없는 조회는 전체를 훑는다 | Cassandra, HBase |
| 그래프 | 노드와 관계(edge) | 친구 관계, 추천, 권한 상속처럼 관계를 여러 단계 따라가는 조회 | 관계가 적은 데이터에는 이득이 없다 | Neo4j |

NoSQL은 조회 방식을 먼저 정하고 그에 맞춰 데이터를 미리 모양 짓는다. RDB는 정규화해 두고 조회할 때 JOIN으로 합치지만, NoSQL은 "사용자별 최근 주문 20개"처럼 자주 하는 조회가 key 하나로 끝나게 저장한다. 그래서 나중에 조회 방식이 바뀌면 데이터를 다시 만들어야 한다.

## CAP 정리가 실제로 말하는 것

CAP 정리는 네트워크 분할이 났을 때 일관성과 가용성을 둘 다 가질 수는 없다는 정리다. 2000년 Eric Brewer가 추측으로 내놓았고, 2002년 Gilbert와 Lynch가 증명했다.

| 글자 | 정리에서의 정의 | 흔히 착각하는 뜻 |
|---|---|---|
| C (Consistency) | 모든 읽기가 가장 최근에 완료된 쓰기를 본다. 복사본이 여러 개여도 하나처럼 보인다(atomic, 선형화 가능성) | ACID의 C(제약 조건이 깨지지 않음) |
| A (Availability) | 장애가 나지 않은 노드에 온 요청은 결국 모두 정상 응답을 받는다 | "99.9% 가동률" 같은 운영 지표 |
| P (Partition tolerance) | 노드 사이 메시지가 사라져도 시스템이 정의대로 동작한다 | 고를 수 있는 옵션 |

증명은 단순하다. 노드 p1과 p2 사이가 끊긴 상태에서 p1에 쓰기가 들어오고, 곧이어 p2에 읽기가 들어온다고 하자. p2는 p1에 무슨 값이 쓰였는지 알 길이 없다. 그러면 p2는 둘 중 하나를 해야 한다.

1. 가진 값으로 답한다. 응답은 했지만 옛 값일 수 있으니 C를 포기한 것이다.
2. 연락이 될 때까지 기다리거나 에러를 낸다. 최신 값을 지켰지만 응답을 못 했으니 A를 포기한 것이다.

### 흔한 오해

- "C, A, P 셋 중 둘을 고른다"는 틀린 설명이다. 여러 노드로 된 시스템에서 분할은 고르는 게 아니라 일어나는 사건이다. Brewer도 2012년 글에서 "셋 중 둘" 표현이 처음부터 오해를 부른다고 썼다. 분할이 없을 때는 C와 A를 둘 다 가질 수 있고, 정리가 막는 건 분할 중에 둘을 완벽하게 갖는 것뿐이다.
- "CA 시스템"은 노드가 하나일 때나 성립한다. 노드가 둘 이상이면 분할이 났을 때 어느 쪽인지 정해야 한다.
- CAP의 A는 운영에서 말하는 가용성보다 훨씬 엄격하다. 과반수 노드가 동의해야 쓰기를 받는 시스템은 분할 때 소수 쪽이 응답하지 못하니 CAP 기준으로는 A가 아니다. 그래도 과반수 쪽은 계속 돌아서 운영 체감은 꽤 높다.
- 저장소 하나를 통째로 CP나 AP로 부르기 어렵다. Cassandra는 쿼리마다 consistency level을 고르고, DynamoDB는 읽기마다 strongly consistent read를 켤지 고른다. 같은 저장소도 설정과 연산에 따라 위치가 바뀐다.

## PACELC는 평소의 선택까지 다룬다

CAP은 분할이 났을 때만 말한다. 그런데 분할은 드물고, 평소에도 복제를 하는 한 다른 선택을 계속 한다. Daniel Abadi는 이걸 PACELC로 묶었다.

```
if Partition  → Availability 와 Consistency 중 하나를 고른다
Else          → Latency 와 Consistency 중 하나를 고른다
```

평소의 선택은 복제 방식에서 나온다. 쓰기를 다른 노드까지 복제한 뒤에 응답하면 모든 노드가 같은 값을 보지만 쓰기마다 다른 노드를 기다린다(EC). 먼저 응답하고 나중에 복제하면 빠르지만 잠깐 옛 값이 보인다(EL). MySQL 비동기 복제에서 방금 쓴 글이 Replica에 안 보이는 일이 EL 쪽 대가다.

| 분류 | 분할 때 | 평소 | 논문(2012)이 든 예 |
|---|---|---|---|
| PA/EL | 가용성 | 지연 | Dynamo, Cassandra, Riak의 기본 설정 |
| PC/EC | 일관성 | 일관성 | VoltDB/H-Store, Megastore, BigTable/HBase |
| PC/EL | 일관성 | 지연 | Yahoo PNUTS |

이 분류는 논문이 쓰인 2012년 기준이다. 저장소 버전과 설정에 따라 달라지니 지금 쓰는 버전의 복제 설정을 직접 확인한다.

## 파티셔닝과 핫스팟

NoSQL은 파티션 키로 데이터를 노드에 나눈다. 나누는 방식은 범위와 해시 두 가지다. 샤딩 전략 전체 비교는 [[replication-and-sharding]]에 있다.

| 방식 | 동작 | 좋은 점 | 핫스팟이 생기는 곳 |
|---|---|---|---|
| 범위 | `user_id` 1~1000은 노드 A, 1001~2000은 노드 B | 범위 조회가 노드 하나에서 끝난다 | 시간이나 증가하는 ID를 키로 쓰면 새 쓰기가 마지막 범위에 몰린다 |
| 해시 | `hash(key)`로 노드를 고른다 | 키가 고르게 퍼진다 | 키 하나에 요청이 몰리면(인기 상품 하나) 해시로도 흩어지지 않는다 |

해시가 막아 주는 건 키가 몰리는 것이지 요청이 몰리는 게 아니다. 같은 키는 늘 같은 노드로 가기 때문에, 인기 상품 하나의 조회수 카운터는 노드 하나를 달군다. 이럴 때는 키 뒤에 `product:42:views:0`~`:9`처럼 번호를 붙여 쓰기를 여러 키로 나누고, 읽을 때 합친다.

## Consistent hashing이 옮기는 데이터를 줄이는 원리

`hash(key) % N`으로 노드를 고르면 노드 수가 바뀔 때 거의 모든 키의 위치가 바뀐다. 4대에서 5대로 늘리면 `k % 4`와 `k % 5`가 같은 키는 20개 중 4개뿐이라, 키의 약 80%를 옮겨야 한다.

Consistent hashing은 노드와 키를 같은 해시 공간(원)에 올린다. 키는 원을 시계 방향으로 돌다 처음 만나는 노드에 저장된다.

1. 노드를 추가하면 새 노드와 그 바로 앞 노드 사이 구간의 키만 새 노드로 옮긴다.
2. 노드가 빠지면 그 노드가 맡던 구간만 다음 노드로 넘어간다.
3. 나머지 노드의 키는 그대로다. Dynamo 논문은 이걸 "노드가 들어오고 나가도 바로 이웃만 영향을 받는다"고 적었다.

노드를 원 위에 한 자리씩만 두면 구간 크기가 들쭉날쭉하고, 노드 하나가 빠질 때 그 부하가 다음 노드 하나에 다 넘어간다. 그래서 노드 하나에 자리(가상 노드, 토큰)를 여러 개 준다. 빠진 노드의 구간이 여러 노드로 흩어지고, 서버 성능에 맞춰 자리 수를 다르게 줄 수도 있다.

```java
public final class HashRing {
    private final NavigableMap<Long, String> ring;

    public HashRing(List<String> nodes, int virtualNodesPerNode) {
        TreeMap<Long, String> map = new TreeMap<>();
        for (String node : nodes) {
            for (int i = 0; i < virtualNodesPerNode; i++) {
                map.put(hash(node + "#" + i), node);
            }
        }
        this.ring = Collections.unmodifiableNavigableMap(map);
    }

    public String nodeFor(String key) {
        Map.Entry<Long, String> entry = ring.ceilingEntry(hash(key));
        return (entry != null ? entry : ring.firstEntry()).getValue();
    }

    private static long hash(String value) {
        // 예시용이다. 실제로는 MurmurHash처럼 고르게 퍼지는 해시를 쓴다.
        return value.hashCode() & 0xffffffffL;
    }
}
```

`ceilingEntry`가 시계 방향으로 처음 만나는 노드를 찾고, 원의 끝을 넘으면 처음 노드로 돌아간다.

## 언제 무엇을 쓰나

| 상황 | 선택 | 이유 |
|---|---|---|
| 주문, 결제, 재고처럼 어긋나면 안 되는 원본 | RDB | 트랜잭션과 제약 조건이 지켜 준다 |
| 세션, 캐시, 카운터 | 키-값 | key 하나로 읽고 TTL을 건다 |
| 한 번에 통째로 읽는 상세 정보 | 문서 | JOIN 없이 한 번에 읽는다 |
| 쓰기가 매우 많고 키 범위로 읽는 로그 | 와이드 컬럼 | 노드를 늘려 쓰기를 나눈다 |
| 분할 중에도 쓰기를 받아야 하는 장바구니 | AP 쪽 설정 | 나중에 충돌을 합칠 방법이 있으면 응답을 우선한다 |
| 분할 중 옛 값을 보면 돈이 새는 데이터 | CP 쪽 설정 | 응답을 못 하더라도 틀린 값을 주지 않는다 |

## 자주 깨지는 곳

- CAP의 C를 ACID의 C로 이해하면, "NoSQL은 C를 포기했으니 제약 조건이 없다" 같은 엉뚱한 결론에 이른다.
- 저장소를 CP나 AP 딱지 하나로 고르면, 실제로는 쿼리마다 바꾼 consistency 설정 때문에 예상과 다르게 동작한다.
- 조회 방식을 정하지 않고 NoSQL에 데이터를 넣으면, 파티션 키 없는 조회가 생겨 전체 노드를 훑는다.
- 시간을 파티션 키 맨 앞에 두면, 최신 파티션 하나에 쓰기가 몰려 노드를 늘려도 빨라지지 않는다.
- `hash % N`으로 노드를 고르면, 노드를 하나 늘릴 때 대부분의 키가 옮겨지면서 캐시라면 miss가 한꺼번에 원본으로 몰린다.
- AP 쪽 설정을 고르고 충돌 해결 방법을 정하지 않으면, 분할이 풀린 뒤 같은 key의 두 값 가운데 하나가 조용히 사라진다.

## 운영에서 볼 것

- 노드별, 파티션별 요청 수와 저장 용량의 편차를 본다. 한 노드만 튀면 핫스팟이다.
- 키별 요청 수 상위 목록으로 hot key를 찾는다.
- 복제 지연과, 읽기 consistency 설정별 latency를 같이 본다.

## 한 번에 설명하기

> NoSQL은 키-값, 문서, 와이드 컬럼, 그래프처럼 조회 방식에 맞춘 모양으로 데이터를 담고, 노드를 늘려 확장합니다. 그래서 저는 저장소를 고를 때 데이터를 어떤 키로 읽을지부터 정합니다.
>
> CAP 정리는 노드 사이 연락이 끊겼을 때 최신 값을 지키려면 응답을 포기해야 하고, 응답을 하려면 옛 값을 줄 수 있다는 정리입니다. 셋 중 둘을 고르는 게 아니라 분할이 났을 때 C와 A 중 무엇을 포기할지 고르는 것입니다.
>
> 평소에는 PACELC가 말하듯 지연과 일관성 사이를 고르게 되고, 이건 복제를 동기로 하느냐 비동기로 하느냐로 드러납니다. 노드를 늘리고 줄일 때 데이터 이동을 줄이려고 consistent hashing과 가상 노드를 씁니다.

## 꼬리 질문

> [!question]- CAP에서 CA 시스템은 왜 없다고 하나?
> 노드가 둘 이상이면 노드 사이 연락이 끊기는 일은 막을 수 없습니다. 끊겼을 때 응답을 하면 C를, 응답을 안 하면 A를 포기한 것이니 둘을 동시에 지키는 선택지가 남지 않습니다. CA는 노드 하나짜리 DB처럼 분할이 일어날 수 없을 때만 성립합니다.

> [!question]- MySQL Primary-Replica 구성은 CAP과 PACELC에서 어디에 놓이나?
> 비동기 복제라면 평소에 Primary는 Replica를 기다리지 않고 응답하니 지연을 택한 EL 쪽입니다. Replica를 읽으면 옛 값이 보일 수 있습니다. 분할이 났을 때는 Primary에 닿지 않는 쪽에서 쓰기를 받지 못하니, 쓰기 기준으로는 일관성을 택한 쪽에 가깝습니다.

> [!question]- consistent hashing에서 가상 노드는 왜 쓰나?
> 노드마다 원 위에 한 자리만 주면 구간 크기가 고르지 않아 어떤 노드는 키를 훨씬 많이 맡습니다. 그리고 노드가 빠지면 그 부하가 다음 노드 하나에 몰립니다. 노드 하나에 자리를 여러 개 주면 구간이 고르게 섞이고, 빠진 노드의 키가 여러 노드로 흩어집니다.

> [!question]- 해시 파티셔닝을 썼는데도 한 노드만 바쁘면 무엇을 의심하나?
> hot key를 의심합니다. 해시는 키를 고르게 나눌 뿐이라 키 하나에 요청이 몰리면 그 키가 있는 노드만 바빠집니다. 읽기라면 앞단 캐시를 두고, 쓰기라면 키 뒤에 번호를 붙여 여러 키로 나눠 쓴 뒤 읽을 때 합칩니다.

## 참고

2026년 11월에 확인한 논문과 원저자 글이다.

- [Eric Brewer: CAP Twelve Years Later - How the "Rules" Have Changed](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)
- [Daniel Abadi: Consistency Tradeoffs in Modern Distributed Database System Design (PACELC)](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)
- [DeCandia et al.: Dynamo - Amazon's Highly Available Key-value Store](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)

## 관련 문서

- [[01-core/database/database|database]]
- [[why-rdb]]
- [[replication-and-sharding]]
- [[why-redis]]
- [[transaction-and-isolation]]
