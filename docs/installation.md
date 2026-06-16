# Установка

## Требования

- **Python ≥ 3.9**
- Доступ к интернету (CLI обращается к `api-audience.yandex.ru`)

## Установка из исходников

```bash
git clone https://github.com/axisrow/yandex-audience-cli.git
cd yandex-audience-cli
pip install -e ".[dev]"
```

`-e` (editable) ставит проект ссылкой на исходники — правки в коде применяются без переустановки.
Группа `[dev]` добавляет `pytest` и `respx` для запуска тестов; для самого CLI достаточно
`pip install -e .`.

!!! info "Без venv"
    Проект рассчитан на установку без виртуального окружения. Код живёт в namespace-пакете `yac.*`,
    что исключает конфликт имён с другими top-level модулями в общем `sys.path`.

## Зависимости

Рантайм: [`typer`](https://typer.tiangolo.com/), [`httpx`](https://www.python-httpx.org/),
[`rich`](https://rich.readthedocs.io/) — все ставятся автоматически.

## Проверка

После установки доступны два способа запуска:

```bash
yac --version           # консольный скрипт
python -m yac --version # эквивалент через модуль
yac --help              # справка по группам и глобальным опциям
```

Ожидаемый вывод `--version`: `yandex-audience-cli 0.1.0`.

## Дальше

Чтобы команды заработали с реальным API, нужен OAuth-токен — см. [Аутентификация](authentication.md).
