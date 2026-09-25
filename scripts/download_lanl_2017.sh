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
  part="${out}.part"

  echo "Downloading $kind day $day -> $out"
  rm -f "$part"

  # --server-response makes authentication/WAF failures visible in logs.
  # --tries=3 handles transient transport failures without looping indefinitely.
  wget --server-response --tries=3 --timeout=60 -c "$url" -O "$part"

  # LANL source files are bzip2 archives. Reject HTML/WAF/login pages that may
  # otherwise be saved with a .bz2 suffix.
  magic="$(head -c 3 "$part" || true)"
  if [[ "$magic" != "BZh" ]]; then
    bytes="$(wc -c < "$part" | tr -d ' ')"
    echo "ERROR: LANL response is not a bzip2 archive (size=${bytes} bytes, magic='${magic}')." >&2
    echo "The signed data-fence URL may be expired/rejected, or an intermediary may have returned HTML." >&2
    rm -f "$part"
    exit 1
  fi

  if ! bzip2 -t "$part"; then
    echo "ERROR: bzip2 integrity test failed for day $day." >&2
    rm -f "$part"
    exit 1
  fi

  mv "$part" "$out"
  sha256sum "$out" > "${out}.sha256"
  echo "Validated: $out"
done
