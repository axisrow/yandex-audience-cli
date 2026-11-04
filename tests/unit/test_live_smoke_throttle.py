"""Лимит записи Audience API «10 записей/мин» в live_smoke.sh.

Баг: live_smoke.sh делал ~30 write-запросов плотной чередой без учёта
бурст-лимита «10 записей/мин» → segments create-pixel ловил 429 → ложный FAIL.
Фикс: скользящее окно в scripts/throttle.sh (throttle_write): пауза — ровно до
истечения старейшего штампа окна, после сна окно пересеивается (свежие штампы
сохраняются — «кредит» не выбрасывается), пороги захардкожены; хуки на все
write-вызовы (run_json + cleanup-удаления) + runtime-гвард на загрузку.

Тесты гоняют throttle_write в bash с моками sleep/date: часы — файл
(date() зовётся из субшелла command substitution, обычная переменная не
пробрасывается родителю), а мок sleep двигает часы на длительность сна —
моделирует реальное время и делает наблюдаемыми мутантов вокруг пересечивки
часов/окна после сна. Сеть не нужна. Bash-3.2-совместимость enforce'ится
вручную на macOS (/bin/bash 3.2): CI — Linux с bash 5.
"""

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[2]
THROTTLE = REPO / "scripts" / "throttle.sh"
SMOKE = REPO / "scripts" / "live_smoke.sh"

# Управляемые часы в файле + sleep двигает часы (реальное время моделируется).
DRIVER = r"""
set -uo pipefail
echo 1000 > "{clock}"
sleep() {{
  local t
  t=$(cat "{clock}")
  echo "$((t + $1))" > "{clock}"
  echo "SLEEP:$*" >> "{log}"
}}
date() {{
  local t
  t=$(cat "{clock}")
  echo "$t"
  echo "$((t + {delay}))" > "{clock}"
}}
source "{throttle}"
for i in $(seq 1 {n}); do throttle_write; done
"""


def run_throttle(tmp_path: Path, n: int, delay: int) -> str:
    log = tmp_path / "sleep.log"
    clock = tmp_path / "clock"
    script = DRIVER.format(log=log, clock=clock, delay=delay, throttle=THROTTLE, n=n)
    p = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=30, check=False
    )
    assert p.returncode == 0, f"throttle скрипт упал: {p.stderr}"
    return log.read_text() if log.exists() else ""


class TestThrottleFunction:
    """Поведение throttle_write: скользящее окно 10/мин, пауза до истечения старейшего штампа."""

    def test_window_budget_pauses_pinned(self, tmp_path: Path):
        """21 запись с шагом 1с (второе «минутное» окно снова переполнено — вторая пауза
        законна): ровно паузы (50с, 50с) — до истечения старейшего штампа, не плоские 60с.
        Точная пара убивает мутантов: плоский sleep 60 → (50,60); отказ от пересечивки
        часов после сна (новый write штампуется устаревшим временем, бюджет возвращается
        рано) → вторая пауза пропадает вовсе (одна SLEEP:50 вместо двух)."""
        log = run_throttle(tmp_path, n=21, delay=1)
        assert (
            log == "SLEEP:50\nSLEEP:50\n"
        ), f"ожидались ровно паузы (50, 50), получил: {log!r}"

    def test_first_10_writes_no_sleep(self, tmp_path: Path):
        """10 вызовов подряд — ровно лимит, паузы ещё нет."""
        log = run_throttle(tmp_path, n=10, delay=0)
        assert log == "", "пауза сработала раньше лимита (10/мин)"

    def test_spread_writes_no_sleep(self, tmp_path: Path):
        """11 вызовов с шагом 7с (окно скользящее, 70с > 60с) — ни одной паузы."""
        log = run_throttle(tmp_path, n=11, delay=7)
        assert log == "", "пауза сработала, хотя записи разнесены шире окна"


class TestSmokeScriptWiring:
    """live_smoke.sh обязан АКТИВНО (не в комментарии) подключать throttle и звать
    throttle_write на всех write-путях; поломка source не должна быть молчаливой."""

    def test_sources_throttle_actively(self):
        src = SMOKE.read_text()
        assert (
            'source "$SCRIPT_DIR/throttle.sh"' in src
        ), "live_smoke.sh не источает scripts/throttle.sh (активный statement)"
        assert (
            "type -t throttle_write" in src
        ), "нет runtime-гварда: поломка source деградирует в молчаливый no-op"

    def test_calls_throttle_on_write_paths(self):
        """run_json троттлит write-опы (list пропускается), оба cleanup-удаления троттлятся."""
        src = SMOKE.read_text()
        assert (
            'case "${2:-}" in list) ;; *) throttle_write ;; esac' in src
        ), "run_json не троттлит write-опы"
        cleanup = src.split("cleanup_all() {")[1].split("trap ")[0]
        assert (
            cleanup.count("throttle_write") == 2
        ), "cleanup-удаления (segments/pixels delete) не троттлятся — риск 429 и сирот"

    def test_api_error_excludes_429(self):
        """429 — не «ожидаемый отказ домена», а голод по квоте: в expect_err/expect_any
        он обязан давать FAIL, а не маскироваться под PASS."""
        src = SMOKE.read_text()
        assert (
            'grep -q "HTTP 429"' in src
        ), "is_api_error не исключает 429 — троттлинг-сбой станет невидимым PASS'ом"
