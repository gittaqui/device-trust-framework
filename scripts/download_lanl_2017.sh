#!/usr/bin/env bash
set -euo pipefail

# Download bounded slices of the LANL Unified Host & Network Dataset (2017).
# Never commit the authenticated data-fence URL. Export it only in your shell:
#   export LANL_DATA_FENCE_ROOT='https://csr.lanl.gov/data-fence/<token>/unified-host-network-dataset-2017'
#
# Examples:
#   ./scripts/download_lanl_2017.sh host 1 1
#   ./scripts/download_lanl_2017.sh netflow 2 2
#   ./scripts/download_lanl_2017.sh host 1 3
#
# Files are stored under data/external/lanl-2017/raw/ and should remain ignored.

: "${LANL_DATA_FENCE_ROOT:?Set LANL_DATA_FENCE_ROOT to the authenticated LANL dataset root}"

kind="${1:-host}"
start_day="${2:-1}"
end_day="${3:-$start_day}"

case "$kind" in
  host)
    subdir="wls"
    prefix="wls_day"
    min_day=1
    ;;
  netflow)
    subdir="netflow"
    prefix="netflow_day"
    min_day=2
    ;;
  *)
    echo "Usage: $0 {host|netflow} START_DAY END_DAY" >&2
    exit 2
    ;;
esac

if (( start_day < min_day || end_day < start_day || end_day > 90 )); then
  echo "Invalid day range for $kind: $start_day..$end_day" >&2
  exit 2
fi

out_dir="data/external/lanl-2017/raw/$subdir"
mkdir -p "$out_dir"

for day in $(seq -w "$start_day" "$end_day"); do
  url="${LANL_DATA_FENCE_ROOT%/}/$subdir/${prefix}-$day.bz2"
  out="$out_dir/${prefix}-$day.bz2"
  echo "Downloading $kind day $day -> $out"
  wget -c "$url" -O "$out"
done
