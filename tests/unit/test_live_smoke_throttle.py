"""Лимит записи Audience API «10 записей/мин» в live_smoke.sh.

Баг: live_smoke.sh делает ~30 write-запросов плотной чередой без учёта
бурст-лимита «10 записей/мин» → segments create-pixel ловит 429 → ложный FAIL.
Фикс: скользящее окно в scripts/throttle.sh (throttle_write), хуки на все
write-вызовы (run_json + cleanup-удаления).

Тест гоняет throttle_write в bash с моками sleep/date (управляемые часы) —
сеть не нужна.
"""

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[2]
THROTTLE = REPO / "scripts" / "throttle.sh"
SMOKE = REPO / "scripts" / "live_smoke.sh"

# Управляемые часы: состояние — в файле (date() зовётся из субшелла command
# substitution, присваивания из него родителю не пробрасываются — обычная
# переменная не годится). sleep пишет в лог вместо реальной паузы.
DRIVER = r"""
set -uo pipefail
echo 1000 > "{clock}"
sleep() {{ echo "SLEEP:$*" >> "{log}"; }}
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
    """Поведение throttle_write: скользящее окно 10/мин, пауза 60с при переполнении."""

    def test_burst_11th_write_sleeps_once(self, tmp_path: Path):
        """11-12 вызовов в одну минуту → ровно ОДНА пауза 60с: на 11-м, окно после неё сброшено."""
        log = run_throttle(tmp_path, n=12, delay=0)
        assert (
            log == "SLEEP:60\n"
        ), f"ожидалась ровно одна пауза 60с (на 11-м write'е), получил: {log!r}"

    def test_first_10_writes_no_sleep(self, tmp_path: Path):
        """10 вызовов подряд — ровно лимит, паузы ещё нет."""
        log = run_throttle(tmp_path, n=10, delay=0)
        assert log == "", "пауза сработала раньше лимита (10/мин)"

    def test_spread_writes_no_sleep(self, tmp_path: Path):
        """11 вызовов с шагом 7с (окно 70с > 60с) — ни одной паузы."""
        log = run_throttle(tmp_path, n=11, delay=7)
        assert log == "", "пауза сработала, хотя окно скользящее и записи разнесены"


class TestSmokeScriptWiring:
    """live_smoke.sh обязан источать throttle.sh и звать throttle_write на write-путях."""

    def test_sources_throttle(self):
        assert (
            "throttle.sh" in SMOKE.read_text()
        ), "live_smoke.sh не подключает scripts/throttle.sh"

    def test_calls_throttle_on_write_paths(self):
        """Минимум два хука: в run_json (все write-опы) и в cleanup-удалениях."""
        src = SMOKE.read_text()
        assert (
            src.count("throttle_write") >= 2
        ), "throttle_write не вызывается на всех write-путях (run_json + cleanup)"
