# segments — сегменты (16 эндпоинтов)

Управление сегментами аудиторий: создание (из пикселя, Метрики, AppMetrica, гео, lookalike,
файла), загрузка данных, подтверждение, изменение, удаление, переобработка.

Пути даны относительно `https://api-audience.yandex.ru/v1/management`.

## Сводка

| Команда | Метод | Путь | Назначение |
|---|---|---|---|
| `list` | GET | `segments` | Список сегментов |
| `create-pixel` | POST | `segments/create_pixel` | Сегмент на основе пикселя |
| `create-lookalike` | POST | `segments/create_lookalike` | Lookalike-сегмент (похожая аудитория) |
| `create-metrika` | POST | `segments/create_metrika` | Сегмент из Яндекс.Метрики |
| `create-appmetrica` | POST | `segments/create_appmetrica` | Сегмент из AppMetrica |
| `create-geo` | POST | `segments/create_geo` | Гео-сегмент (окружность) |
| `create-geo-polygon` | POST | `segments/create_geo_polygon` | Гео-сегмент (полигон) |
| `upload-file` | POST | `segments/upload_file` | Загрузить файл данных (multipart) |
| `upload-csv-file` | POST | `segments/upload_csv_file` | Загрузить CSV-файл (multipart) |
| `update-geo-points` | POST | `segment/{id}/update_geo_points` | Изменить координаты гео-окружности |
| `modify-data` | POST | `segment/{id}/modify_data` | Изменить данные файлового сегмента (multipart) |
| `confirm` | POST | `segment/{id}/confirm` | Подтвердить/сохранить загруженный сегмент |
| `confirm-client-id` | POST | `segment/client_id/{id}/confirm` | Сохранить сегмент из ClientId Метрики |
| `update` | PUT | `segment/{id}` | Изменить сегмент |
| `delete` | DELETE | `segment/{id}` | Удалить сегмент |
| `reprocess` | PUT | `segment/{id}/reprocess` | Переобработать сегмент |

## Чтение

### `list`

```bash
yac segments list
yac segments list --pixel 724143      # фильтр по id пикселя
yac segments list --limit 50 --offset 100
yac -o table segments list
```

| Опция | Тип | Назначение |
|---|---|---|
| `--pixel` | int | фильтр по id пикселя |
| `--limit` | int | сколько вернуть (по умолчанию 10000) |
| `--offset` | int | смещение пагинации |

## Создание сегментов

Все `create-*` принимают `--data` с внутренним объектом сегмента (см. [Использование](../usage.md#data-json)).

### `create-pixel`

```bash
yac segments create-pixel --data '{"name":"из пикселя","pixel_id":724143,"period_length":30}'
```

### `create-lookalike`

Похожая аудитория на основе существующего сегмента-источника.

```bash
yac segments create-lookalike --data '{"name":"похожие","lookalike_link":12834430,"lookalike_value":1,"maintain_device_distribution":true,"maintain_geo_distribution":true}'
```

### `create-metrika`

Требует реального счётчика Яндекс.Метрики.

```bash
yac segments create-metrika --data '{"name":"из метрики","counter_id":123456}'
```

### `create-appmetrica`

Требует реального приложения AppMetrica.

```bash
yac segments create-appmetrica --data '{"name":"из appmetrica","app_id":999888}'
```

### `create-geo`

Гео-сегмент в виде окружности. `geo_segment_type` — число `1`, `radius` на верхнем уровне.

```bash
yac segments create-geo --data '{"name":"вокруг точки","geo_segment_type":1,"radius":1000,"points":[{"latitude":55.7558,"longitude":37.6173}],"times_quantity":1,"period_length":1}'
```

### `create-geo-polygon`

Гео-сегмент в виде полигона. `geo_segment_type` — число `2`, контур замкнут (первая точка =
последней), небольшой площади.

```bash
yac segments create-geo-polygon --data '{"name":"полигон","geo_segment_type":2,"polygons":[{"points":[{"latitude":55.7558,"longitude":37.6173},{"latitude":55.7558,"longitude":37.6213},{"latitude":55.7588,"longitude":37.6213},{"latitude":55.7588,"longitude":37.6173},{"latitude":55.7558,"longitude":37.6173}]}],"times_quantity":1,"period_length":1}'
```

### `update-geo-points`

Изменить координаты существующего гео-сегмента (окружности). В `--data` — JSON-массив точек;
CLI оборачивает его в `{"points": […]}`.

```bash
yac segments update-geo-points 57172765 --data '[{"latitude":55.76,"longitude":37.62}]'
```

| Аргумент/опция | Назначение |
|---|---|
| `SEGMENT_ID` (позиционный) | id гео-сегмента |
| `--data` | JSON-массив точек (строка, `@файл` или `-`) |

## Загрузка данных из файла

### `upload-file` / `upload-csv-file`

Загружают файл (`multipart/form-data`). Поддерживаются email, телефоны, IDFA/GAID, MAC, client_id.
Возвращают сегмент в неподтверждённом состоянии — далее его нужно `confirm`.

```bash
yac segments upload-file ./crm.txt
yac segments upload-csv-file ./users.csv
```

### `confirm`

Подтверждает (сохраняет) загруженный сегмент.

```bash
yac segments confirm 57172765 --data '{"name":"мой CRM","content_type":"crm","hashed":false}'
yac segments confirm 57172765 --data '{...}' --no-check-size   # отключить проверку минимума записей
```

| Аргумент/опция | Назначение |
|---|---|
| `SEGMENT_ID` (позиционный) | id загруженного сегмента |
| `--data` | объект сегмента: `name`, `content_type` (`crm`/`idfa_gaid`/`mac`/`client_id`), `hashed` |
| `--check-size` / `--no-check-size` | проверять минимум ~100 записей |

### `modify-data`

Изменяет данные уже сохранённого файлового сегмента (`multipart`). Сегмент должен быть в статусе
`processed`.

```bash
yac segments modify-data 57172765 ./more.txt --modification-type addition
yac segments modify-data 57172765 ./remove.txt --modification-type subtraction --no-check-size
```

| Аргумент/опция | Назначение |
|---|---|
| `SEGMENT_ID`, `FILE` (позиционные) | id сегмента и путь к файлу |
| `--modification-type` | `addition` \| `subtraction` \| `replace` |
| `--check-size` / `--no-check-size` | проверка минимума записей |

## Метрика ClientId

### `confirm-client-id`

Сохраняет сегмент из ClientId Яндекс.Метрики (сегмент создаётся в интерфейсе Метрики).

```bash
yac segments confirm-client-id 77788 --data '{"name":"clientid","source":"metrika"}'
```

## Изменение и удаление

### `update`

```bash
yac segments update 57172765 --data '{"name":"новое имя"}'
```

### `delete`

```bash
yac segments delete 57172765
```

!!! warning "Удаление сегмента"
    У сегментов нет отдельной операции восстановления (в отличие от пикселей). Удаляйте осознанно.

### `reprocess`

Переобработать (пересчитать) сегмент. Применимо к сегменту в подходящем статусе.

```bash
yac segments reprocess 57172765
```
