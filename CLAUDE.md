# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Что это

CLI `yac` — обёртка над Yandex Audience API, зеркалящая структуру API **1:1**: версия (`v1`) →
пространство (`management`) → 5 ресурсных групп (segments, grants, pixels, accounts, delegates),
28 эндпоинтов. Команды строятся как `yac <группа> <операция>` (`yac segments list`, `yac grants add ...`).

Справочник API: живая локаль — **`ru`**, англоязычный путь `/en/ref/openapi/` сейчас отдаёт 404.
Единого OpenAPI-файла НЕТ; справочник — Diplodoc, по странице на метод. У каждой есть исходный
Markdown по детерминированному URL `https://yandex.ru/dev/audience/ru/ref/openapi/<группа>/<slug>.md`
(метод + полный URL ресурса внутри `.md` парсятся машинно) — это первоисточник для сверки реестра.

## Команды

```bash
pip install -e ".[dev]"     # установка editable + dev-зависимости (pytest, respx)
pytest                       # все тесты (192)
pytest tests/test_resources.py::test_... -q   # один тест (по узлу <файл>::<тест>)
pytest -k "<подстрока>"      # один тест/группа по имени без указания файла
yac --help                   # справка; глобальные опции ДО группы: yac --token X segments list
python -m yac --help         # эквивалент консольного скрипта
```

Тесты не требуют установки: `pyproject.toml` задаёт `pythonpath = ["."]`, поэтому `import yac`
резолвится по корню репо. Тесты бьют по HTTP через **respx** (моки httpx) — реальный токен не нужен.

## Архитектура: реестр — единственный источник правды

`yac/registry/` — **дерево «файл на эндпоинт»**: подкаталог на группу, в нём по файлу на каждый из
28 `Endpoint` (`registry/segments/list.py`, `registry/grants/add.py`, ...). Имя файла = `op`,
каталог = `group`, переменная в файле всегда `ENDPOINT`. `ls registry/segments/` показывает все
эндпоинты группы. Дерево — единственный источник строк путей; `registry.ENDPOINTS` собирается из
него **автозагрузкой** (`_core._load` через `pkgutil`; порядок групп — `GROUPS`, внутри группы —
алфавит по имени файла). `registry/_core.py` держит `Endpoint` (frozen dataclass: `group`, `op`,
`method`, `path`, `summary`, `multipart`, `unverified`, `path_params`), `GROUP_*`, `GROUPS` и
функции; `registry/__init__.py` — фасад, реэкспортирующий публичный контракт (`ENDPOINTS`, `get`,
`by_group`, `render_path`, `Endpoint`, `GROUP_*`, `GROUPS`), поэтому `from . import registry` и
`from ..registry import GROUP_SEGMENTS` работают как раньше. **Всё остальное произрастает из реестра.**
Ключевой инвариант: имя `op` эндпоинта = имя метода класса ресурса = имя команды CLI (через `_`→`-`).

Поток данных слоями (зависимости однонаправленные, цикла нет):

```
commands/<group>.py  (Typer-команды; парсят аргументы, зовут render)
        ↓
api/<group>.py       (класс ресурса; метод на op; зовёт self._call(op, ...))
        ↓
base.py Resource._call → registry.get(group, op) + registry.render_path(ep, **path_params)
        ↓
client.py Client.request  (httpx; Authorization: OAuth <token>, base .../v1/management, pretty, multipart, 429)
```

`context.py` хранит глобальные опции в `ctx.obj` (`AppState`), лениво создаёт `Client` через
`load_config()`, и даёт декоратор `handle_errors` (ConfigError/APIError → `exit(1)` без трейсбека).
`cli.py` собирает корневой Typer-app (`add_typer` по группам) и держит `__version__`;
`__init__.py` реэкспортирует `app` — отсюда работает entry point `yac = "yac:app"`.

Резолвинг токена (`config.py`, по приоритету): `--token` → env `YANDEX_AUDIENCE_TOKEN` →
файл `~/.config/yandex-audience-cli/token`. Base-url переопределяется `--base-url`/`YANDEX_AUDIENCE_BASE_URL`
(нужно тестам/прокси). API имеет только `v1`/`management` — это зафиксировано, не параметризуется.

## Как добавлять/менять эндпоинты

1. Создай файл `yac/registry/<group>/<op>.py` с одним `ENDPOINT = Endpoint(GROUP_<GROUP>, "<op>", ...)`
   (имя файла = `op`, каталог = группа; импорт `from .._core import Endpoint, GROUP_<GROUP>`).
   Это единственное место со строками путей; список собирается автозагрузкой — больше нигде не
   регистрировать.
2. Добавь метод с именем = `op` в соответствующий `yac/api/<group>.py` (тело — `self._call("op", ...)`).
3. Добавь команду с тем же именем (`_`→`-`) в `yac/commands/<group>.py`.
4. Обнови `EXPECTED_PER_GROUP` в `tests/test_registry_coverage.py` (итог `EXPECTED_TOTAL` = `sum(...)`,
   **не хардкодь итоговое число**).

Машинные гарантии (тесты упадут при нарушении): `tests/test_registry_coverage.py` — у эндпоинта нет
метода ресурса ИЛИ команды CLI; `tests/test_registry_tree.py` — имя файла ≠ `op`, каталог ≠ `group`,
число файлов ≠ числу эндпоинтов. Сама автосборка (`_core._load`) падает громко при импорте, если файл
не объявляет `ENDPOINT` или возникает дубль `(group, op)`.

## Раскладка и окружение (важная причина текущей структуры)

Весь код — в пакете `yac/` (подпакеты `api/`, `commands/`; остальные модули плоско в корне
пакета). Это **намеренно**: проект ставится глобально (`pip install -e .`, **без venv**), и плоские
top-level имена (`config`, `registry`, ...) раньше конфликтовали с одноимёнными модулями других
editable-проектов в общем `sys.path`. Namespace `yac.*` устраняет коллизию без venv и без префиксов.

- Импорты **внутри пакета — относительные** (`from .config import`, `from . import registry`,
  `from ..base import Resource`). `import registry` записывается как `from . import registry`,
  чтобы `registry.get()`/`registry.ENDPOINTS` в телах работали дословно.
- Импорты **в тестах — абсолютные пакетные** (`from yac.api.segments import Segments`).
- Не клади голые `.py` в корень репо: editable-`.pth` добавляет корень репо в `sys.path`
  (т.к. `yac/` лежит в корне, не в `src/`), и такой файл снова станет глобальным top-level именем.

## Грабли Typer/тестов

- Современный Typer **не экспортирует** `click` как модуль — в тестах используй `typer.main.get_command`,
  а не `import click`.
- Команды извлекай через корневой app: `typer.main.get_command(root_app).commands[group].commands`
  (под-app с одной командой, как accounts, не имеет `.commands` напрямую).
- hatchling требует существующий `README.md` для сборки.
