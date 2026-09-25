#!/usr/bin/env bash
set -euo pipefail

# Run the frozen bounded LANL host-event summary without expanding the full archive.
# Usage:
#   ./scripts/run_lanl_2017_host_bounded.sh data/external/lanl-2017/raw/wls/wls_day-01.bz2 100000

archive="${1:?Provide a LANL wls_day-XX.bz2 file}"
max_rows="${2:-100000}"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

python - "$archive" "$max_rows" "$tmp_file" <<'PY'
import bz2
import sys

archive, max_rows, output = sys.argv[1], int(sys.argv[2]), sys.argv[3]
with bz2.open(archive, "rt", encoding="utf-8", errors="replace") as source, open(
    output, "w", encoding="utf-8"
) as target:
    for index, line in enumerate(source):
        if index >= max_rows:
            break
        target.write(line)
PY

python -m src.lanl_2017_host_adapter \
  --input "$tmp_file" \
  --max-rows "$max_rows"
