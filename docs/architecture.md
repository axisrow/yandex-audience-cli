# Архитектура

`yac` устроен так, чтобы соответствие CLI и API было **невозможно нарушить незаметно**. В основе —
реестр эндпоинтов как единственный источник правды.

## Реестр — единственный источник правды

`yac/registry/` — это **дерево «файл на эндпоинт»**: подкаталог на группу, внутри по файлу на каждый
из 28 эндпоинтов (`registry/segments/list.py`, `registry/grants/add.py`, …). Каждый файл объявляет
один объект `ENDPOINT`:

```python
# yac/registry/segments/list.py
ENDPOINT = Endpoint(GROUP_SEGMENTS, "list", "GET", "segments", "Список сегментов")
```

- **Имя файла** = имя операции (`op`).
- **Каталог** = группа.
- Список `registry.ENDPOINTS` собирается из дерева **автозагрузкой** — регистрировать эндпоинт
  где-то ещё не нужно.

`ls yac/registry/segments/` сразу показывает все 16 эндпоинтов группы — карта API наглядна прямо из
файловой системы.

**Ключевой инвариант:** имя `op` эндпоинта = имя метода класса ресурса = имя CLI-команды
(с заменой `_` ↔ `-`).

## Поток данных по слоям

Зависимости однонаправленные, цикла нет:

```
commands/<group>.py   Typer-команды: парсят аргументы, зовут render
        ↓
api/<group>.py        класс ресурса: метод на каждый op; зовёт self._call(op, ...)
        ↓
base.py Resource._call → registry.get(group, op) + registry.render_path(ep, **path_params)
        ↓
client.py Client.request   httpx: заголовок OAuth, base .../v1/management, pretty, multipart, 429
```

| Модуль | Роль |
|---|---|
| `cli.py` | корневой Typer-app, глобальные опции, регистрация групп |
| `config.py` | резолвинг токена и base-url |
| `context.py` | `AppState`, ленивое создание клиента, декоратор `handle_errors` |
| `client.py` | httpx-обёртка, `APIError`/`RateLimitError`, разбор ответа |
| `base.py` | `Resource._call` — мост реестр ↔ клиент |
| `registry/` | `ENDPOINTS`, модель `Endpoint`, `get`/`render_path`/`by_group` |
| `render.py` / `output.py` | вывод json/table |
| `inputs.py` | `parse_data` для `--data` (строка/`@файл`/`-`) |

## Машинная гарантия покрытия

Соответствие реестра, классов ресурсов и CLI-команд проверяется тестами — они **упадут**, если
рассинхронизировать:

- `tests/unit/test_registry_coverage.py` — у каждого эндпоинта есть и метод ресурса, и CLI-команда;
  счётчики по группам (16/3/5/1/3 = 28).
- `tests/unit/test_registry_tree.py` — имя файла = `op`, каталог = `group`, число файлов = числу
  эндпоинтов.
- Сама автосборка реестра падает громко при импорте, если файл не объявляет `ENDPOINT` или возник
  дубль `(group, op)`.

Поэтому «100% покрытие эндпоинтов» — не обещание, а инвариант, который держат тесты.

## Как добавить эндпоинт

1. Создать `yac/registry/<group>/<op>.py` с одним `ENDPOINT`.
2. Добавить метод с именем `op` в `yac/api/<group>.py` (тело — `self._call("op", ...)`).
3. Добавить команду с тем же именем (`_`→`-`) в `yac/commands/<group>.py`.
4. Обновить ожидаемые счётчики в `tests/unit/test_registry_coverage.py`.

Подробности — в `CLAUDE.md` репозитория.
