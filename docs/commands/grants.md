# grants — доступы к сегментам (3 эндпоинта)

Управление разрешениями на сегмент: выдать доступ другому пользователю Яндекса, забрать,
посмотреть список.

Пути даны относительно `https://api-audience.yandex.ru/v1/management`.

## Сводка

| Команда | Метод | Путь | Назначение |
|---|---|---|---|
| `list` | GET | `segment/{id}/grants` | Список разрешений сегмента |
| `add` | PUT | `segment/{id}/grant` | Выдать доступ к сегменту |
| `remove` | DELETE | `segment/{id}/grant` | Забрать доступ |

## `list`

```bash
yac grants list 57172765
```

| Аргумент | Назначение |
|---|---|
| `SEGMENT_ID` (позиционный) | id сегмента |

## `add`

Выдаёт доступ пользователю. CLI сам собирает тело `{"grant": {…}}` из опций.

```bash
yac grants add 57172765 --user-login partner@yandex.ru
yac grants add 57172765 --user-login partner@yandex.ru --permission edit --comment "доступ для партнёра"
```

| Опция | Тип | Назначение |
|---|---|---|
| `SEGMENT_ID` (позиционный) | int | id сегмента |
| `--user-login` (обязателен) | строка | логин получателя доступа |
| `--permission` | `edit` \| `view` | уровень доступа (опц.) |
| `--comment` | строка | комментарий (опц.) |

## `remove`

Забирает доступ (логин передаётся как query-параметр `?user_login=…`).

```bash
yac grants remove 57172765 --user-login partner@yandex.ru
```

| Опция | Назначение |
|---|---|
| `SEGMENT_ID` (позиционный) | id сегмента |
| `--user-login` (обязателен) | логин, у которого забрать доступ |
