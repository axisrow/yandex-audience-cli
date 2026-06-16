# yandex-audience-cli

CLI для [Yandex Audience API](https://yandex.ru/dev/audience/), повторяющий структуру API **«1 в 1»** с гарантией 100% покрытия эндпоинтов.

## Структура API (3 уровня)

```
версия (v1) → пространство (management) → ресурс (5 групп)
```

База: `https://api-audience.yandex.ru/v1/management`. Авторизация: заголовок `Authorization: OAuth <token>`.
WSDL неприменим (REST/JSON, не SOAP). Реестр выверен 1:1 по официальному
[OpenAPI-справочнику Яндекса](https://yandex.com/dev/audience/en/ref/openapi/); единый источник правды —
[`yac/registry.py`](yac/registry.py) (**28 эндпоинтов** в 5 группах).

## Раскладка

Весь код — в пакете [`yac/`](yac/). Имена модулей живут в namespace `yac.*`, поэтому
не конфликтуют с чужими top-level модулями в глобальном `sys.path` (без venv и без
префиксов). Структура:

```
yac/
├── __init__.py      # реэкспорт app, __version__
├── __main__.py      # python -m yac
├── cli.py           # сборка корневого Typer-приложения
├── config.py  client.py  models.py  registry.py
├── base.py  context.py  render.py  inputs.py  output.py
├── api/             # HTTP-классы ресурсов, по файлу на группу
│   └── segments.py  grants.py  pixels.py  accounts.py  delegates.py
└── commands/        # Typer-команды, по файлу на группу
    └── segments.py  grants.py  pixels.py  accounts.py  delegates.py
```

По каждой группе API — пара `api/<group>.py` (HTTP-вызовы) и `commands/<group>.py`
(команды Typer).

| Группа | Эндпоинтов | Команды |
|---|---|---|
| `segments` | 16 | list, create-pixel, create-lookalike, create-metrika, create-appmetrica, create-geo, create-geo-polygon, upload-file, upload-csv-file, update-geo-points, modify-data, confirm, confirm-client-id, update, delete, reprocess |
| `grants` | 3 | list, add, remove |
| `pixels` | 5 | list, create, update, delete, undelete |
| `accounts` | 1 | list |
| `delegates` | 3 | list, add, remove |

> Метод «получить один сегмент» (`GET segment/{id}`) в Audience API **отсутствует** —
> по официальному справочнику доступен только список (`GET segments`). Поэтому такой команды нет.

## Установка

```bash
pip install -e ".[dev]"
```

## Токен

Любой из способов (по приоритету):

```bash
yac --token <OAUTH> ...
export YANDEX_AUDIENCE_TOKEN=<OAUTH>
echo <OAUTH> > ~/.config/yandex-audience-cli/token
```

Шаблон переменных — `.env.example`. `yac` не читает `.env` сам (нет `python-dotenv`);
экспортируйте переменные вручную: `cp .env.example .env`, затем
`set -a; . ./.env; set +a` (корректно с пробелами/кавычками; или через `direnv`).

Получить OAuth-токен: https://oauth.yandex.ru/ (права: создание/чтение сегментов).

## Примеры

```bash
yac segments list
yac segments list --pixel 12345 -o table
yac segments create-pixel --data '{"name":"my","pixel_id":1,"period_length":30}'
yac segments create-pixel --data @segment.json     # из файла
yac pixels create --name "Мой пиксель"
yac grants add 777 --user-login partner@yandex.ru --comment "доступ"
yac delegates list
```

Глобальные опции: `--token`, `--base-url`, `-o/--output json|table`, `--pretty`, `--version`.

## Гарантия покрытия

`tests/test_registry_coverage.py` падает, если в реестре есть эндпоинт без соответствующего
метода ресурса или команды CLI. Это машинная проверка структурного соответствия API.

```bash
pytest
```
