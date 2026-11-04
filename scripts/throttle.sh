#!/usr/bin/env bash
#
# throttle.sh — скользящее окно для лимита записи Audience API «10 записей/мин».
#
# throttle_write зовётся перед КАЖДЫМ write-запросом. Окно 60с; при его заполнении
# (10+ записей) — пауза THROTTLE_WAIT (по умолч. 60с), после которой окно пусто
# целиком. Часы вынесены в _throttle_now, чтобы тесты подменяли дату, не трогая
# логику окна (см. tests/unit/test_live_smoke_throttle.py).
#
# Совместимо с macOS bash 3.2: раскрытие пустых массивов — через
# ${ARR[@]+"${ARR[@]}"} (иначе set -u роняет скрипт).

WRITE_STAMPS=()

# Часы окна. Отдельная функция — точка подмены в тестах.
_throttle_now() { date +%s; }

throttle_write() {
  local now max wait t
  local fresh=()
  now=$(_throttle_now)
  max="${THROTTLE_MAX:-10}"
  wait="${THROTTLE_WAIT:-60}"
  for t in ${WRITE_STAMPS[@]+"${WRITE_STAMPS[@]}"}; do
    [ $((now - t)) -lt 60 ] && fresh+=("$t")
  done
  WRITE_STAMPS=(${fresh[@]+"${fresh[@]}"})
  if [ "${#WRITE_STAMPS[@]}" -ge "$max" ]; then
    printf '  … пауза %ss: лимит записи %s/мин Audience API\n' "$wait" "$max" >&2
    sleep "$wait"
    WRITE_STAMPS=()
    now=$(_throttle_now)
  fi
  WRITE_STAMPS+=("$now")
}
