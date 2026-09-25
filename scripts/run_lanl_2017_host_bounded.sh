#!/usr/bin/env bash
set -euo pipefail

# Run the frozen bounded LANL host-event summary without expanding the full archive.
# Usage:
#   ./scripts/run_lanl_2017_host_bounded.sh data/external/lanl-2017/raw/wls/wls_day-01.bz2 100000

archive="${1:?Provide a LANL wls_day-XX.bz2 file}"
max_rows="${2:-100000}"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

bzcat "$archive" | head -n "$max_rows" > "$tmp_file"

python -m src.lanl_2017_host_adapter \
  --input "$tmp_file" \
  --max-rows "$max_rows"
