---
title: Kafka 핵심 동작
description: 파티션과 키, 소비자 그룹, offset 커밋, acks 설정이 메시지 순서와 중복과 유실을 어떻게 가르는지
tags: [concept, messaging]
---

# Kafka 핵심 동작

Kafka는 메시지를 지우지 않고 파티션이라는 로그에 차례로 붙여 두고, 소비자가 "어디까지 읽었는지"를 offset으로 따로 기록하는 브로커다. 이 글의 기본값과 동작은 Apache Kafka 4.4 문서 기준이다.

주문 이벤트를 Kafka로 보내면 세 가지를 설정으로 정하게 된다. 같은 주문의 이벤트가 순서대로 처리되는지는 키와 파티션이 정한다. 소비자가 죽었을 때 이벤트가 두 번 처리되는지 빠지는지는 offset을 언제 커밋하느냐가 정한다. 브로커가 죽었을 때 보낸 이벤트가 남는지는 `acks`와 `min.insync.replicas`가 정한다.

## topic과 partition, 그리고 키

topic은 이벤트의 이름이고, 실제 데이터는 topic 아래 여러 파티션에 나뉘어 쌓인다. 순서는 파티션 하나 안에서만 지켜진다.

producer는 레코드를 보낼 때 파티션을 고른다. 4.4의 기본 동작은 이렇다.

1. 파티션을 직접 지정하면 그 파티션에 쓴다.
2. 키가 있으면 키의 해시로 파티션을 고른다. 같은 키는 같은 파티션으로 간다.
3. 키가 없으면 한 파티션에 `batch.size`만큼 쌓일 때까지 보내고 다음 파티션으로 넘어간다(sticky partition).

그래서 같은 주문의 "결제 완료"와 "주문 취소"를 순서대로 처리하려면 주문 id를 키로 보낸다. 키 없이 보내면 두 이벤트가 다른 파티션에 들어가고, 다른 소비자가 따로 읽어서 순서가 섞인다.

파티션 수를 나중에 늘리면 키와 파티션의 짝이 바뀐다. 해시를 파티션 수로 나누기 때문이다. 늘린 순간부터 같은 주문의 새 이벤트가 이전과 다른 파티션에 들어가고, Kafka는 기존 데이터를 옮겨 주지 않는다. 파티션 수를 줄이는 기능은 없다.

## consumer group과 리밸런싱

같은 `group.id`를 쓰는 소비자들이 하나의 consumer group이고, 그룹 안에서 파티션 하나는 한 시점에 소비자 하나만 읽는다.

파티션이 6개이고 소비자가 3대면 한 대가 파티션 2개씩 맡는다. 소비자를 6대로 늘리면 하나씩 맡는다. 7대로 늘리면 한 대는 받을 파티션이 없어 논다. 그래서 한 그룹의 병렬 처리 상한은 파티션 수다. 알림, 포인트, 정산이 같은 주문 이벤트를 각자 읽으려면 그룹을 셋 만든다. 그룹마다 offset을 따로 가진다.

소비자가 들어오거나 나가면 파티션을 다시 나눠 주는데, 이걸 리밸런싱이라고 한다. 소비자가 나갔다고 판단하는 기준은 두 가지다.

- heartbeat가 `session.timeout.ms`(기본 45초) 안에 오지 않으면 그룹에서 뺀다.
- `poll()`을 `max.poll.interval.ms`(기본 5분) 안에 다시 부르지 않으면 실패한 것으로 보고 파티션을 다른 소비자에게 넘긴다.

두 번째가 실무에서 자주 터진다. 한 번 가져온 레코드를 처리하다 외부 API가 느려져 5분을 넘기면, 처리 중이던 파티션이 다른 소비자에게 넘어가고 커밋 안 된 레코드를 그쪽이 다시 처리한다.

Kafka 4.0부터 새 리밸런싱 프로토콜(KIP-848)이 정식 기능이 됐다. 그룹 전체가 한꺼번에 맞추는 단계 없이 바뀐 몫만 조금씩 옮겨서 리밸런싱 시간이 줄어든다. 4.4 클라이언트의 `group.protocol` 기본값은 아직 `classic`이라, 쓰려면 `consumer`로 바꾼다. 새 프로토콜에서는 세션 타임아웃을 브로커 설정 `group.consumer.session.timeout.ms`가 정한다.

## offset 커밋 시점이 중복과 유실을 가른다

소비자는 파티션마다 "다음에 읽을 offset"을 커밋한다. 커밋을 처리 전에 하면 유실이 생기고, 처리 뒤에 하면 중복이 생긴다.

| 커밋 시점 | 커밋 뒤 처리 전에 죽으면 | 처리 뒤 커밋 전에 죽으면 | 결과 |
|---|---|---|---|
| 처리 전 커밋 | 그 레코드는 다시 오지 않는다 | 해당 없음 | at-most-once, 유실 |
| 처리 후 커밋 | 해당 없음 | 다시 와서 한 번 더 처리한다 | at-least-once, 중복 |
| 자동 커밋 | 다음 `poll()` 전에 처리를 다 끝내지 않았다면 다시 오지 않는다 | 다시 와서 한 번 더 처리한다 | 쓰는 방식에 따라 유실이 생긴다 |

Kafka 클라이언트의 `enable.auto.commit` 기본값은 `true`이고 `auto.commit.interval.ms` 기본값은 5초다. 자동 커밋은 처리가 끝났는지 모르고 `poll()`로 받아 간 위치까지 커밋한다. KafkaConsumer 문서는 자동 커밋도 at-least-once가 되려면 `poll()`로 받은 레코드를 다음 `poll()` 전에 모두 처리해야 한다고 적는다. 레코드를 다른 스레드에 넘기고 바로 다음 `poll()`을 부르면, 커밋 위치가 실제 처리보다 앞서 가고 그 사이에 죽으면 레코드가 빠진다. 그래서 처리 결과가 DB에 남아야 하는 소비자는 자동 커밋을 끄고 처리 뒤에 직접 커밋한다. 커밋 시점이 코드에 드러나야 장애 때 무엇이 다시 오는지 설명할 수 있다.

```java
consumer.subscribe(List.of("order-completed"));
while (running) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(500));
    for (ConsumerRecord<String, String> record : records) {
        orderEventHandler.handle(record.key(), record.value()); // 멱등하게 만든다
    }
    consumer.commitSync(); // 이번 poll로 받은 레코드를 모두 처리한 뒤 커밋한다
}
```

Spring Kafka 2.3부터는 따로 설정하지 않으면 `enable.auto.commit`을 `false`로 두고, 리스너 컨테이너가 커밋한다. 기본 `AckMode`는 `BATCH`로, `poll()`로 받은 레코드를 모두 처리한 뒤 커밋한다. 어느 쪽이든 처리 후 커밋은 at-least-once라서, 같은 레코드를 두 번 받는 경우가 남는다. 소비자는 [[message-consumer-idempotency|메시지 소비 멱등성]]의 방법으로 중복을 막는다.

## producer `acks`와 `min.insync.replicas`

`acks`는 producer가 "보냈다"고 판단하기 전에 몇 개의 복제본이 받았는지 기다리는 설정이다. 4.4의 기본값은 `all`이다.

| 설정 | 기다리는 것 | 잃는 경우 |
|---|---|---|
| `acks=0` | 기다리지 않는다 | 브로커가 못 받아도 모른다. 재시도도 하지 않는다 |
| `acks=1` | 리더가 자기 로그에 쓴 것 | 리더가 응답 직후 follower 복제 전에 죽으면 잃는다 |
| `acks=all` | ISR(동기화된 복제본) 전원 | ISR 중 하나라도 살아 있으면 잃지 않는다 |

`acks=all`에도 빈틈이 있다. ISR이 리더 하나로 줄어들면 "ISR 전원"이 리더 하나뿐이라 `acks=1`과 같아진다. 이걸 막는 것이 브로커와 토픽 설정 `min.insync.replicas`다. ISR이 이 값보다 적으면 `acks=all` 쓰기를 거절하고 producer는 `NotEnoughReplicas` 예외를 받는다. 기본값은 1이라 그대로 두면 막아 주지 않는다. 공식 문서가 드는 예시는 복제 계수 3, `min.insync.replicas=2`, `acks=all` 조합이다. 이러면 복제본 과반이 저장해야 쓰기가 성공한다.

`default.replication.factor`의 기본값도 1이다. 토픽을 자동 생성하거나 복제 계수를 지정하지 않으면 복제본이 하나뿐이라, 브로커 하나가 죽으면 그 파티션을 읽고 쓸 수 없다. 공식 문서는 복제 계수 2나 3을 권한다.

## idempotent producer

idempotent producer는 producer가 재시도하면서 같은 레코드를 로그에 두 번 쓰는 일을 막는다. 4.4에서 `enable.idempotence` 기본값은 `true`다.

브로커는 producer마다 id를 주고, producer가 레코드와 함께 보내는 sequence number로 중복을 걸러 낸다. 그래서 응답이 유실돼 producer가 같은 배치를 다시 보내도 로그에는 한 번만 남는다. 이 기능은 `acks=all`, `retries`가 0보다 큰 값, `max.in.flight.requests.per.connection`이 5 이하일 때만 켜진다. 이 중 하나와 충돌하는 설정을 넣고 idempotence를 명시하지 않으면 조용히 꺼진다. 명시했다면 `ConfigException`이 난다.

막는 범위는 producer 내부의 재시도까지다. 애플리케이션이 같은 이벤트로 `send()`를 두 번 부르면 다른 레코드라 둘 다 쓰인다. Outbox publisher가 발행 뒤 상태를 바꾸기 전에 죽어서 다시 보내는 경우가 그렇다. 이 중복은 소비자가 막는다.

## 파티션 수 정하기

파티션 수는 나중에 줄일 수 없고, 늘리면 키 배치가 바뀐다. 그래서 처음에 넉넉히 잡되 근거를 두고 정한다.

| 기준 | 보는 것 |
|---|---|
| 처리량 | 목표 초당 건수를 소비자 한 대가 초당 처리하는 건수로 나눈 값보다 많게 잡는다 |
| 소비자 수 | 한 그룹의 소비자 수 상한이 파티션 수다. 몰릴 때 늘릴 소비자 수를 미리 본다 |
| 키 순서 | 키 순서가 필요한 토픽은 나중에 늘리기 어렵다. 처음부터 여유 있게 잡는다 |
| 키 쏠림 | 특정 키에 트래픽이 몰리면 파티션을 늘려도 그 파티션 하나만 밀린다 |
| 서버 분산 | 파티션 하나는 서버 한 대에 통째로 들어간다. 파티션이 20개면 데이터와 읽기 쓰기 부하를 많아야 20대가 나눠 맡는다 |

브로커 설정 `num.partitions`의 기본값은 1이다. 자동 생성된 토픽은 파티션이 하나라 소비자를 몇 대 띄워도 한 대만 일한다.

## 자주 깨지는 곳

- 키 없이 이벤트를 보내면, 같은 주문의 취소 이벤트가 결제 완료보다 먼저 처리된다.
- 순서가 필요한 토픽의 파티션을 늘리면, 늘린 시점 전후로 같은 키의 이벤트가 다른 파티션에 있어서 순서가 섞인다.
- 자동 커밋을 켠 채 레코드를 다른 스레드에 넘기고 바로 다음 `poll()`을 부르면, 처리 전에 커밋된 레코드가 장애 때 사라진다.
- 한 번에 가져온 레코드 처리가 `max.poll.interval.ms`를 넘으면, 리밸런싱이 일어나고 같은 레코드를 다른 소비자가 다시 처리한다. 이게 반복되면 그룹이 계속 리밸런싱만 한다.
- `acks=all`만 켜고 `min.insync.replicas`를 1로 두면, ISR이 리더 하나로 줄었을 때 쓰기가 성공하고 그 리더가 죽으면 잃는다.
- idempotent producer를 켰으니 중복이 없다고 믿으면, Outbox 재발행이나 소비자 재처리로 생기는 중복을 놓친다.
- 파티션 수보다 소비자를 많이 띄우면, 남는 소비자는 일하지 않고 비용만 든다.
- 파티션이 늘어날 수 있는 토픽에서 `auto.offset.reset=latest`(기본값)를 쓰면, 새 파티션을 소비자가 알아채기 전에 들어온 레코드를 건너뛴다. 4.4 문서는 이 경우 `by_duration`을 권한다.

## 운영에서 볼 것

- consumer lag. 파티션마다 마지막 offset과 커밋된 offset의 차이다. `kafka-consumer-groups.sh --describe --group <그룹>`이 파티션별 `CURRENT-OFFSET`, `LOG-END-OFFSET`, `LAG`를 보여 준다.
- lag 합계보다 파티션별 lag을 본다. 한 파티션만 계속 늘면 키 쏠림이나 그 파티션을 맡은 소비자의 문제다.
- 리밸런싱 횟수와 소비자 로그의 `max.poll.interval.ms` 초과 경고. 잦으면 한 번에 가져오는 양을 줄이거나 처리 시간을 줄인다.
- producer 쪽 전송 실패와 `NotEnoughReplicas` 예외. ISR이 줄어든 신호다.
- 토픽의 복제 계수와 `min.insync.replicas`가 의도한 값인지 토픽 생성 직후 확인한다.

## 한 번에 설명하기

> Kafka에서 순서는 파티션 안에서만 지켜져서, 같은 주문의 이벤트는 주문 id를 키로 보내 같은 파티션에 모읍니다. 파티션 수를 늘리면 키 배치가 바뀌니 처음에 여유 있게 잡습니다.
>
> 소비 쪽은 자동 커밋을 끄고 처리 뒤에 offset을 커밋합니다. 이러면 메시지는 잃지 않지만 같은 메시지를 두 번 받을 수 있어서 소비자를 멱등하게 만듭니다.
>
> 보내는 쪽은 `acks=all`에 복제 계수 3, `min.insync.replicas=2`를 맞춰서 브로커 하나가 죽어도 확인받은 메시지를 잃지 않게 합니다. 운영에서는 파티션별 consumer lag과 리밸런싱 횟수를 봅니다.

## 꼬리 질문

> [!question]- 소비자를 늘렸는데 처리 속도가 그대로입니다. 왜 그런가요?
> 한 그룹에서 파티션 하나는 소비자 하나만 읽어서, 소비자 수가 파티션 수를 넘으면 남는 소비자는 놉니다. 파티션별 lag을 보고 한 파티션만 밀린다면 키 쏠림이라 소비자를 늘려도 풀리지 않습니다.

> [!question]- 같은 메시지가 두 번 처리됐습니다. 어디서 생겼을까요?
> 처리는 끝났는데 offset 커밋 전에 소비자가 죽었거나, 처리 시간이 `max.poll.interval.ms`를 넘어 리밸런싱이 일어난 경우가 먼저 의심됩니다. producer 쪽에서는 Outbox publisher가 같은 이벤트를 다시 보낸 경우가 있습니다. 어느 쪽이든 소비자가 event id로 중복을 거르게 합니다.

> [!question]- `acks=all`이면 메시지를 절대 잃지 않나요?
> 아닙니다. `acks=all`은 그 순간의 ISR 전원을 기다리는데, ISR이 리더 하나로 줄면 리더만 받고 성공합니다. 그래서 `min.insync.replicas`를 2 이상으로 둬서 ISR이 줄었을 때는 쓰기를 거절하게 합니다.

> [!question]- idempotent producer와 Kafka 트랜잭션은 무엇이 다른가요?
> idempotent producer는 한 producer가 재시도하면서 같은 레코드를 두 번 쓰는 것을 막습니다. 트랜잭션은 여러 파티션에 쓰는 레코드와 소비자 offset을 한꺼번에 커밋하거나 버리게 해서, Kafka에서 읽고 Kafka에 쓰는 처리를 한 번으로 만듭니다. 소비자가 DB에 쓰는 일은 둘 다 막아 주지 않습니다.

> [!question]- 파티션 수는 어떻게 정하나요?
> 목표 처리량을 소비자 한 대의 처리량으로 나눠 필요한 소비자 수를 구하고, 그보다 여유 있게 잡습니다. 줄일 수 없고 늘리면 키 배치가 바뀌니, 순서가 필요한 토픽일수록 처음에 넉넉히 둡니다. 파티션 하나는 서버 한 대에 들어가므로, 파티션 수는 이 토픽을 나눠 맡을 수 있는 서버 수의 상한이기도 합니다.

## 참고

2026년 11월에 확인한 공식 문서다.

- [Apache Kafka 4.4: Design](https://kafka.apache.org/44/design/design/)
- [Apache Kafka 4.4: KafkaConsumer Javadoc](https://kafka.apache.org/44/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html)
- [Spring Kafka: Message Listener Containers](https://docs.spring.io/spring-kafka/reference/kafka/receiving-messages/message-listener-container.html)

## 관련 문서

- [[02-practical-backend/messaging/messaging|messaging]]
- [[message-queue-basics]]
- [[message-consumer-idempotency]]
- [[compensation-and-outbox]]
- [[02-practical-backend/observability/observability|observability]]
