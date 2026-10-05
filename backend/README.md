# Kafka integration

## Архитектура

```text
REST
  └─────────────┐
                v
          route_payload()
                ^
                |
DICOMREPORTNOTIFY
        |
     consumer
        |
        +--> route_payload()
                |
                +--> CLINICALROUTINGNOTIFY
                |
                +--> CLINICALROUTINGDLQ (при ошибке)
```

REST и Kafka не имеют отдельных медицинских алгоритмов:
оба используют `app.routing_service.route_payload()`.

## Топики

- `DICOMREPORTNOTIFY` — входящий JSON от upstream radiology AI / ERIS.
- `CLINICALROUTINGNOTIFY` — результат маршрутизации.
- `CLINICALROUTINGDLQ` — неуспешно обработанные сообщения.

Kafka key: `studyIUID`.

## Гарантия обработки

Worker использует `enable.auto.commit=false`.

Offset входящего сообщения commit'ится только после:
1. успешного routing;
2. успешной публикации результата в `CLINICALROUTINGNOTIFY`.

Если routing неуспешен после retry:
1. сообщение публикуется в DLQ;
2. после подтверждения DLQ offset commit'ится.

Если недоступен даже DLQ — offset не commit'ится.

Это даёт практическую at-least-once обработку для MVP.

## Запуск

Создать `.env`:

```bash
cp .env.example .env
```

Заполнить Yandex credentials, затем:

```bash
docker compose up --build
```

Сервисы:

- API: http://127.0.0.1:8081
- Swagger: http://127.0.0.1:8081/docs
- Kafka UI: http://127.0.0.1:8082
- Kafka host listener: localhost:9092

## Smoke test Kafka

В отдельном терминале:

```bash
docker compose exec api \
  python scripts/kafka_send_test.py test_kafka_payload.json
```

Посмотреть результат:

```bash
docker compose exec api \
  python scripts/kafka_read.py --topic output
```

Посмотреть DLQ:

```bash
docker compose exec api \
  python scripts/kafka_read.py --topic dlq
```

Также сообщения удобно смотреть через Kafka UI:
http://127.0.0.1:8082

## Формат output

```json
{
  "studyIUID": "1.2.643....",
  "routingResult": {
    "status": "ok",
    "recommendations": [],
    "missing_data": [],
    "warnings": []
  }
}
```
