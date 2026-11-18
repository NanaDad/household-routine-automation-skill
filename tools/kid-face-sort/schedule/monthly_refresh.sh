#!/usr/bin/env bash
# 월간 자동 보강: sort(dry) → refresh --apply. 경로를 본인 환경에 맞게 수정.
set -euo pipefail
D="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${KIDFACE_NAME:-지우}"; PHOTOS="${KIDFACE_PHOTOS:-$HOME/Pictures/kids}"
OUT="$HOME/.kidface/monthly/$(date +%Y%m)"; mkdir -p "$OUT"
"$D/kidface.sh" sort "$PHOTOS" -o "$OUT" --mode dry > "$OUT/sort.log" 2>&1
"$D/kidface.sh" refresh "$NAME" "$OUT/report.csv" --apply > "$OUT/refresh.log" 2>&1
