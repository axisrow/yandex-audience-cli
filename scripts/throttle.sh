#!/usr/bin/env bash
#
# throttle.sh — скользящее окно для лимита записи Audience API «10 записей/мин».
#
# throttle_write зовётся перед КАЖДЫМ write-запросом. Окно скользящее (60с); при его
# заполнении (10+ свежих записей) пауза — ровно до истечения СТАРЕЙШЕГО штампа окна
# (не плоские 60с: неиспользованный «кредит» окна не выбрасывается), после сна окно
# пересеивается — истёкшие штампы уходят, свежие сохраняются. Поэтому завышенный/заниженный
# THROTTLE_* извне не может ни отключить троттлинг, ни вернуть 429 — пороги захардкожены.
# Часы вынесены в _throttle_now: тесты подменяют дату, не трогая логику окна
# (см. tests/unit/test_live_smoke_throttle.py).
#
# Совместимо с macOS bash 3.2: раскрытие пустых массивов — через
# ${ARR[@]+"${ARR[@]}"} (иначе set -u роняет скрипт). Enforce'ится это только
# вручную на macOS (/bin/bash — 3.2): CI гоняет Linux с bash 5.
#
# ponytail: бюджет — в памяти процесса, без lockfile. Гарантия — ОДИН экземпляр
# live_smoke.sh на аккаунт; параллельные прогоны/CI-джобы суммарно дадут >10/мин
# → 429. Нужен конкурентный запуск — flock на фиксированный lockfile.

THROTTLE_LIMIT=10    # записей
THROTTLE_WINDOW=60   # секунд — лимит Audience API «10 записей/мин»

WRITE_STAMPS=()

# Часы окна. Отдельная функция — точка подмены в тестах.
_throttle_now() { date +%s; }

# Оставить только штампы младше окна (скользящий фильтр).
_throttle_fresh() {
  local now t
  local fresh=()
  now=$1
  for t in ${WRITE_STAMPS[@]+"${WRITE_STAMPS[@]}"}; do
    [ $((now - t)) -lt "$THROTTLE_WINDOW" ] && fresh+=("$t")
  done
  WRITE_STAMPS=(${fresh[@]+"${fresh[@]}"})
}

throttle_write() {
  local now oldest d
  now=$(_throttle_now)
  _throttle_fresh "$now"
  if [ "${#WRITE_STAMPS[@]}" -ge "$THROTTLE_LIMIT" ]; then
    oldest="${WRITE_STAMPS[0]}"
    d=$(( oldest + THROTTLE_WINDOW - now ))
    if [ "$d" -gt 0 ]; then
      printf '  … пауза %ss: лимит записи %s/мин Audience API\n' "$d" "$THROTTLE_LIMIT" >&2
      sleep "$d"
    fi
    now=$(_throttle_now)
  fi
  WRITE_STAMPS+=("$now")
}
