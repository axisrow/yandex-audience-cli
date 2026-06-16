# delegates — представители (3 эндпоинта)

Управление доверенными представителями (делегатами) аккаунта: добавить, удалить, посмотреть список.

Пути даны относительно `https://api-audience.yandex.ru/v1/management`.

## Сводка

| Команда | Метод | Путь | Назначение |
|---|---|---|---|
| `list` | GET | `delegates` | Список представителей |
| `add` | PUT | `delegate` | Добавить представителя |
| `remove` | DELETE | `delegate` | Удалить представителя |

## `list`

```bash
yac delegates list
```

Без аргументов. Пустой ответ (`{"delegates": []}`) — валиден.

## `add`

Добавляет представителя. CLI собирает тело `{"delegate": {…}}` из опций.

```bash
yac delegates add --user-login colleague@yandex.ru
yac delegates add --user-login colleague@yandex.ru --perm edit --comment "временный доступ"
```

| Опция | Тип | Назначение |
|---|---|---|
| `--user-login` (обязателен) | строка | логин представителя |
| `--perm` | `view` \| `edit` | уровень доступа (опц.) |
| `--comment` | строка | комментарий (опц.) |

!!! note "`--perm`, не `--permission`"
    У `delegates add` опция называется `--perm` (в отличие от `grants add`, где `--permission`).

## `remove`

Удаляет представителя (логин — query-параметр `?user_login=…`).

```bash
yac delegates remove --user-login colleague@yandex.ru
```

| Опция | Назначение |
|---|---|
| `--user-login` (обязателен) | логин представителя |
