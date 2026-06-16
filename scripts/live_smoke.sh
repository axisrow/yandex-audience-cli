#!/usr/bin/env bash
#
# live_smoke.sh — безопасный live-прогон ВСЕХ 28 эндпоинтов yac через реальный CLI.
#
# Принцип безопасности: скрипт сам создаёт все объекты, которые трогает, и сам их
# удаляет (EXIT-trap подстрахует даже при падении). Существующие боевые сегменты
# и пиксели НЕ затрагиваются — операции update/delete/grant идут ТОЛЬКО по id,
# созданным в этом прогоне. Все тестовые объекты помечаются префиксом "SMOKE yac".
#
# Токен берётся из .env (YANDEX_AUDIENCE_TOKEN); боевой base-url (не переопределяется).
# Внешне-зависимые эндпоинты (metrika/appmetrica/client-id) и кейсы с фейк-логином
# по умолчанию ОЖИДАЮТ ошибку API — это засчитывается как PASS (проверяем обработку).
# Передай SMOKE_COUNTER_ID / SMOKE_APP_ID / SMOKE_CLIENTID_SEG, чтобы прогнать их на успех.
#
# Использование:  bash scripts/live_smoke.sh
# Выход: 0 — все ожидаемые исходы совпали; 1 — есть FAIL.

set -uo pipefail   # НЕ set -e: ожидаемые ошибки (expect_err) обрабатываем сами

# --- расположение и токен -----------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ОШИБКА: нет $ENV_FILE — положи туда YANDEX_AUDIENCE_TOKEN." >&2
  exit 1
fi
# shellcheck disable=SC2046
export $(grep -v '^#' "$ENV_FILE" | grep -E '^[A-Z_]+=' | xargs)
if [ -z "${YANDEX_AUDIENCE_TOKEN:-}" ]; then
  echo "ОШИБКА: YANDEX_AUDIENCE_TOKEN пуст в .env." >&2
  exit 1
fi
echo "Токен загружен: длина ${#YANDEX_AUDIENCE_TOKEN}, префикс ${YANDEX_AUDIENCE_TOKEN:0:3}… (значение скрыто)"

TS="$(date +%s)"
FAKE_LOGIN="smoke-nonexistent-${TS}@yandex.ru"

# --- цвета и счётчики ---------------------------------------------------------
if [ -t 1 ]; then G=$'\e[32m'; R=$'\e[31m'; Y=$'\e[33m'; B=$'\e[1m'; N=$'\e[0m'; else G=; R=; Y=; B=; N=; fi
PASS=0; FAIL=0; SKIP=0
declare -a FAILURES=()

# --- трекеры созданного + cleanup-trap ----------------------------------------
declare -a SEG_IDS=()
declare -a PIXEL_IDS=()
declare -a TMP_FILES=()

track_seg()   { [ -n "${1:-}" ] && SEG_IDS+=("$1"); }
track_pixel() { [ -n "${1:-}" ] && PIXEL_IDS+=("$1"); }
track_tmp()   { [ -n "${1:-}" ] && TMP_FILES+=("$1"); }

cleanup_all() {
  echo ""
  echo "${B}── cleanup ──${N}"
  # сегменты — в обратном порядке (производные раньше источников)
  local i
  for (( i=${#SEG_IDS[@]}-1; i>=0; i-- )); do
    local sid="${SEG_IDS[$i]}"
    if yac segments delete "$sid" >/dev/null 2>&1; then
      echo "  segment $sid удалён"
    else
      echo "  segment $sid — уже удалён/не удалось (ок)"
    fi
  done
  for (( i=${#PIXEL_IDS[@]}-1; i>=0; i-- )); do
    local pid="${PIXEL_IDS[$i]}"
    if yac pixels delete "$pid" >/dev/null 2>&1; then
      echo "  pixel $pid удалён"
    else
      echo "  pixel $pid — уже удалён/не удалось (ок)"
    fi
  done
  for f in "${TMP_FILES[@]:-}"; do [ -n "$f" ] && rm -f "$f"; done
}
trap cleanup_all EXIT

# --- хелперы прогона ----------------------------------------------------------
# Гоняет `yac --output json <args>`; печатает компактно; кладёт stdout в LAST_OUT, код в LAST_RC.
LAST_OUT=""; LAST_RC=0
run_json() {
  LAST_OUT="$(yac --output json "$@" 2>&1)"; LAST_RC=$?
  return 0
}

# Извлечь id из LAST_OUT. $1 — путь: "segment"/"pixel" (объект {id}) ИЛИ
# "pixels[0]"/"segments[0]" (первый элемент массива). Пусто, если не найдено.
json_id() {
  JSON_PATH="$1" python3 -c "
import os,sys,json
try: d=json.loads(sys.stdin.read())
except Exception: sys.exit(0)
p=os.environ['JSON_PATH']
if p.endswith('[0]'):
    arr=d.get(p[:-3]) if isinstance(d,dict) else None
    o=arr[0] if isinstance(arr,list) and arr else None
else:
    o=d.get(p) if isinstance(d,dict) else None
if isinstance(o,dict) and o.get('id') is not None: print(o['id'])
" <<<"$LAST_OUT"
}

_ok()   { PASS=$((PASS+1)); printf '  %sPASS%s %s\n' "$G" "$N" "$1"; }
_fail() { FAIL=$((FAIL+1)); FAILURES+=("$1"); printf '  %sFAIL%s %s\n' "$R" "$N" "$1"; [ -n "${2:-}" ] && printf '       %s\n' "$2"; }
_skip() { SKIP=$((SKIP+1)); printf '  %sSKIP%s %s\n' "$Y" "$N" "$1"; }

# create_and_track <segment|pixel> "<desc>" <yac args...>
# Гоняет создающую команду, извлекает id, трекает для cleanup, печатает PASS/FAIL.
# Результат: id в CREATED_ID (или ""), код возврата 0 при успехе.
CREATED_ID=""
create_and_track() {
  local kind="$1" desc="$2"; shift 2
  run_json "$@"
  CREATED_ID=""
  if [ "$LAST_RC" -ne 0 ]; then
    _fail "$desc" "exit=$LAST_RC: $(head -c 200 <<<"$LAST_OUT")"; return 1
  fi
  CREATED_ID="$(json_id "$kind")"
  if [ -z "$CREATED_ID" ]; then
    _fail "$desc" "нет id: $(head -c 200 <<<"$LAST_OUT")"; return 1
  fi
  if [ "$kind" = pixel ]; then track_pixel "$CREATED_ID"; else track_seg "$CREATED_ID"; fi
  _ok "$desc → id=$CREATED_ID"
}

# make_data_file <txt|csv> <count> <start_index> — создать temp-файл синтетических
# email-данных (заголовок по типу), затрекать для удаления. Путь — в DATA_FILE
# (НЕ через stdout/subshell, иначе track_tmp потерялся бы в subshell'е).
DATA_FILE=""
make_data_file() {
  local ext="$1" count="$2" start="${3:-1}" i end
  DATA_FILE="$(mktemp "${TMPDIR:-/tmp}/smoke_${TS}.XXXXXX")"
  track_tmp "$DATA_FILE"
  end=$(( start + count - 1 ))
  if [ "$ext" = csv ]; then
    { echo "email,age,city"; for (( i=start; i<=end; i++ )); do echo "smoke_csv_${TS}_${i}@example.com,30,Moscow"; done; } > "$DATA_FILE"
  else
    { echo "email"; for (( i=start; i<=end; i++ )); do echo "smoke_${TS}_${i}@example.com"; done; } > "$DATA_FILE"
  fi
}

# expect_ok "<desc>" <yac args...>
expect_ok() {
  local desc="$1"; shift
  run_json "$@"
  if [ "$LAST_RC" -eq 0 ]; then _ok "$desc"; else _fail "$desc" "exit=$LAST_RC: $(head -c 200 <<<"$LAST_OUT")"; fi
}

# expect_err "<desc>" <yac args...> — PASS, если код != 0 И вывод содержит "Ошибка:" (а не traceback)
expect_err() {
  local desc="$1"; shift
  run_json "$@"
  if [ "$LAST_RC" -ne 0 ] && grep -q "Ошибка:" <<<"$LAST_OUT" && ! grep -q "Traceback" <<<"$LAST_OUT"; then
    _ok "$desc (ожидаемая ошибка API)"
  elif [ "$LAST_RC" -eq 0 ]; then
    _fail "$desc" "ожидалась ошибка, но команда успешна"
  else
    _fail "$desc" "exit=$LAST_RC, но нет чистого 'Ошибка:' / есть traceback: $(head -c 200 <<<"$LAST_OUT")"
  fi
}

# expect_any "<desc>" <yac args...> — любой исход без traceback засчитывается (нечего удалять и т.п.)
expect_any() {
  local desc="$1"; shift
  run_json "$@"
  if grep -q "Traceback" <<<"$LAST_OUT"; then _fail "$desc" "traceback: $(head -c 200 <<<"$LAST_OUT")"; else _ok "$desc (exit=$LAST_RC, допустимо)"; fi
}

phase() { echo ""; echo "${B}══ $1 ══${N}"; }

# =============================================================================
# Фаза A — read-only (5)
# =============================================================================
phase "A. Read-only"
expect_ok "accounts list"   accounts list
expect_ok "delegates list"  delegates list
expect_ok "pixels list"     pixels list
expect_ok "segments list"   segments list
# `segments list --pixel` — в фазе B, на пикселе, который мы сами создадим
# (без зависимости от наличия чужих пикселей в аккаунте).

# =============================================================================
# Фаза B — пиксели: полный жизненный цикл (create/update/delete/undelete)
# =============================================================================
phase "B. Пиксели (жизненный цикл)"
if create_and_track pixel "pixels create" pixels create --name "SMOKE yac pixel ${TS}"; then
  PIX_ID="$CREATED_ID"
  expect_ok "pixels update $PIX_ID"   pixels update "$PIX_ID" --name "SMOKE yac pixel ${TS} renamed"
  # segments list --pixel на СВОЁМ пикселе (фаза A не зависит от чужих данных)
  expect_ok "segments list --pixel $PIX_ID" segments list --pixel "$PIX_ID"
  expect_ok "pixels delete $PIX_ID"   pixels delete "$PIX_ID"
  expect_ok "pixels undelete $PIX_ID" pixels undelete "$PIX_ID"
  # финальное удаление — в cleanup-trap (PIX_ID отслеживается)
fi

# =============================================================================
# Фаза C — гео-сегменты + lookalike + reprocess
# =============================================================================
phase "C. Гео + lookalike + reprocess"

# create-geo (окружность). Рабочее тело выверено на боевом API:
#   geo_segment_type:1, radius на верхнем уровне, points:[{latitude,longitude}],
#   times_quantity, period_length. Точка в Москве, радиус 1 км.
if create_and_track segment "segments create-geo" \
     segments create-geo --data "{\"name\":\"SMOKE yac geo ${TS}\",\"geo_segment_type\":1,\"radius\":1000,\"points\":[{\"latitude\":55.7558,\"longitude\":37.6173}],\"times_quantity\":1,\"period_length\":1}"; then
  GEO_ID="$CREATED_ID"
  expect_ok "segments update-geo-points $GEO_ID" \
    segments update-geo-points "$GEO_ID" --data '[{"latitude":55.76,"longitude":37.62}]'
else
  GEO_ID=""
  _skip "segments update-geo-points (нет гео-сегмента)"
fi

# create-geo-polygon. Выверено: geo_segment_type:2, polygons:[{points:[...]}],
# контур ДОЛЖЕН быть замкнут (первая==последняя точка) и мал по площади (<~1 км²).
create_and_track segment "segments create-geo-polygon" \
  segments create-geo-polygon --data "{\"name\":\"SMOKE yac poly ${TS}\",\"geo_segment_type\":2,\"polygons\":[{\"points\":[{\"latitude\":55.7558,\"longitude\":37.6173},{\"latitude\":55.7558,\"longitude\":37.6213},{\"latitude\":55.7588,\"longitude\":37.6213},{\"latitude\":55.7588,\"longitude\":37.6173},{\"latitude\":55.7558,\"longitude\":37.6173}]}],\"times_quantity\":1,\"period_length\":1}"

# create-lookalike: источник — обработанный сегмент. Приоритет: env SMOKE_LOOKALIKE_SRC,
# иначе существующий swift 12834430 (свежий GEO ещё может быть незрелым для lookalike).
LAL_SRC="${SMOKE_LOOKALIKE_SRC:-12834430}"
if create_and_track segment "segments create-lookalike (src=$LAL_SRC)" \
     segments create-lookalike --data "{\"name\":\"SMOKE yac lal ${TS}\",\"lookalike_link\":${LAL_SRC},\"lookalike_value\":1,\"maintain_device_distribution\":true,\"maintain_geo_distribution\":true}"; then
  LAL_ID="$CREATED_ID"
  # reprocess: свежий lookalike сразу в статусе is_processed, API не даёт его
  # переобрабатывать → ожидаем доменную ошибку статуса (CLI-путь при этом проверен).
  # Передай SMOKE_REPROCESS_SEG (сегмент в подходящем статусе), чтобы ждать успех.
  if [ -n "${SMOKE_REPROCESS_SEG:-}" ]; then
    expect_ok  "segments reprocess $SMOKE_REPROCESS_SEG" segments reprocess "$SMOKE_REPROCESS_SEG"
  else
    expect_err "segments reprocess $LAL_ID (статус is_processed — переобработка запрещена)" segments reprocess "$LAL_ID"
  fi
else
  _skip "segments reprocess (нет lookalike-сегмента)"
fi

# =============================================================================
# Фаза D — файловый сегмент: upload → confirm → modify → grants + create-pixel
# =============================================================================
phase "D. Файлы (upload/confirm/modify) + grants + create-pixel"

# Синтетические email-файлы (используем --no-check-size, поэтому 100-минимум не нужен —
# хватает нескольких строк, чтобы проверить multipart-путь upload/confirm/modify).
make_data_file txt 10 1; EMAILS="$DATA_FILE"

if create_and_track segment "segments upload-file" segments upload-file "$EMAILS"; then
  UP_ID="$CREATED_ID"
  expect_ok "segments confirm $UP_ID" \
    segments confirm "$UP_ID" --data "{\"name\":\"SMOKE yac crm ${TS}\",\"content_type\":\"crm\",\"hashed\":false}" --no-check-size

  make_data_file txt 5 11; MORE="$DATA_FILE"
  # modify-data: только что confirm-нутый сегмент ещё не "processed" (обработка
  # асинхронна) → API отвергает изменение по статусу. Ожидаем доменную ошибку
  # (CLI multipart-путь при этом проверен). Передай SMOKE_MODIFY_SEG (уже
  # обработанный загруженный сегмент), чтобы прогнать modify-data на успех.
  if [ -n "${SMOKE_MODIFY_SEG:-}" ]; then
    expect_ok  "segments modify-data $SMOKE_MODIFY_SEG (addition)" \
      segments modify-data "$SMOKE_MODIFY_SEG" "$MORE" --modification-type addition --no-check-size
  else
    expect_err "segments modify-data $UP_ID (сегмент ещё не processed)" \
      segments modify-data "$UP_ID" "$MORE" --modification-type addition --no-check-size
  fi

  # grants на СВОЁМ сегменте, фейк-логин → ожидаем ошибку на add
  expect_err "grants add $UP_ID (фейк-логин)" grants add "$UP_ID" --user-login "$FAKE_LOGIN" --permission view --comment "smoke"
  expect_ok  "grants list $UP_ID"             grants list "$UP_ID"
  expect_any "grants remove $UP_ID (нечего удалять)" grants remove "$UP_ID" --user-login "$FAKE_LOGIN"
else
  _skip "segments confirm / modify-data / grants (нет загруженного сегмента)"
fi

# upload-csv-file — отдельный сегмент
make_data_file csv 10 1; CSV="$DATA_FILE"
create_and_track segment "segments upload-csv-file" segments upload-csv-file "$CSV"

# create-pixel: создаём свежий пиксель и сегмент на его основе
if create_and_track pixel "pixels create (для create-pixel)" pixels create --name "SMOKE yac pxsrc ${TS}"; then
  create_and_track segment "segments create-pixel" \
    segments create-pixel --data "{\"name\":\"SMOKE yac pxseg ${TS}\",\"pixel_id\":${CREATED_ID},\"period_length\":30}"
fi

# =============================================================================
# Фаза E — делегаты (фейк-логин)
# =============================================================================
phase "E. Делегаты"
expect_err "delegates add (фейк-логин)"    delegates add --user-login "$FAKE_LOGIN" --perm view --comment "smoke"
expect_ok  "delegates list"                delegates list
expect_any "delegates remove (нечего удалять)" delegates remove --user-login "$FAKE_LOGIN"

# =============================================================================
# Фаза F — внешне-зависимые 3 (по умолчанию expect_err, expect_ok с реальными ID)
# =============================================================================
phase "F. Внешние (metrika/appmetrica/client-id)"

# metrika/appmetrica: с реальным ID (env) ждём успех (create_and_track), иначе —
# ожидаемую ошибку (нет ресурса). Один и тот же путь, только источник counter/app разный.
if [ -n "${SMOKE_COUNTER_ID:-}" ]; then
  create_and_track segment "segments create-metrika (counter=$SMOKE_COUNTER_ID)" \
    segments create-metrika --data "{\"name\":\"SMOKE yac metrika ${TS}\",\"counter_id\":${SMOKE_COUNTER_ID}}"
else
  expect_err "segments create-metrika (без реального counter_id)" segments create-metrika --data "{\"name\":\"SMOKE yac metrika ${TS}\",\"counter_id\":0}"
fi

if [ -n "${SMOKE_APP_ID:-}" ]; then
  create_and_track segment "segments create-appmetrica (app=$SMOKE_APP_ID)" \
    segments create-appmetrica --data "{\"name\":\"SMOKE yac appm ${TS}\",\"app_id\":${SMOKE_APP_ID}}"
else
  expect_err "segments create-appmetrica (без реального app_id)" segments create-appmetrica --data "{\"name\":\"SMOKE yac appm ${TS}\",\"app_id\":0}"
fi

CIDSEG="${SMOKE_CLIENTID_SEG:-}"
if [ -n "$CIDSEG" ]; then
  expect_ok "segments confirm-client-id $CIDSEG" segments confirm-client-id "$CIDSEG" --data "{\"name\":\"SMOKE yac cid ${TS}\",\"source\":\"metrika\"}"
else
  expect_err "segments confirm-client-id (без реального ClientId-сегмента)" segments confirm-client-id 0 --data "{\"name\":\"SMOKE yac cid ${TS}\",\"source\":\"metrika\"}"
fi

# =============================================================================
# Итог
# =============================================================================
echo ""
echo "${B}══ Итог ══${N}"
printf '  %sPASS: %d%s   %sFAIL: %d%s   %sSKIP: %d%s\n' "$G" "$PASS" "$N" "$R" "$FAIL" "$N" "$Y" "$SKIP" "$N"
if [ "$FAIL" -gt 0 ]; then
  echo "  Провалы:"; for f in "${FAILURES[@]}"; do echo "   - $f"; done
fi
# cleanup_all выполнится через trap EXIT
[ "$FAIL" -eq 0 ]
