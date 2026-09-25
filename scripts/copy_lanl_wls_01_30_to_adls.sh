#!/usr/bin/env bash
set -euo pipefail

: "${LANL_WLS_ADLS_SAS_URL:?Set LANL_WLS_ADLS_SAS_URL to the directory-scoped SAS URI}"

SOURCE_BASE="https://lanl.ma.ic.ac.uk/data/2017/wls"
DIR_URL="${LANL_WLS_ADLS_SAS_URL%%\?*}"
SAS_QUERY="${LANL_WLS_ADLS_SAS_URL#*\?}"
BLOB_DIR_URL="${DIR_URL/.dfs.core.windows.net/.blob.core.windows.net}"

if [[ "$DIR_URL" == "$LANL_WLS_ADLS_SAS_URL" ]]; then
  echo "ERROR: LANL_WLS_ADLS_SAS_URL does not contain a SAS query string." >&2
  exit 2
fi

if ! command -v azcopy >/dev/null 2>&1; then
  echo "ERROR: azcopy is required. Azure Cloud Shell normally includes it." >&2
  exit 3
fi

for cmd in curl bzip2 md5sum sha256sum python3 stat; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "ERROR: required command not found: $cmd" >&2
    exit 3
  }
done

declare -A MD5=(
  [01]=36cfb5acfac150608132d6a8b029e3b1
  [02]=c3d52dd8f1c6a4312e7c7fb22467d7dd
  [03]=a484041e9ade52ea72c2e68f32daadbf
  [04]=8fd1d325d36afc731348f5c52f950619
  [05]=c1f6954d3231dbf435390d2f6c03c86c
  [06]=7d1e8f2488a79289426b7dfe9934531b
  [07]=d1b586bae8a6dd7ef0bb8bbc05649c67
  [08]=7b59c55a98f6363ff47ea20226f808ba
  [09]=ce3a44872c142fc793e053087c342277
  [10]=2f04aa1c9f4397aec4f7bed7f4e48979
  [11]=a39abf68c64f9868cd6e5609e96feb2e
  [12]=e1a68a8ea447f1668c531bf1ffd5e1b6
  [13]=48b4cec60ba0882202ab84cf02a8283e
  [14]=e9f4773a9f33b4e99c9b3bfdd02165e3
  [15]=0b7f29d7a930706688c2d23f4b8d4e48
  [16]=2351a4507dcbfdeb05c91ae19406c3ec
  [17]=eeb5a848b39730b43a1919aa2b962354
  [18]=8f8ebb3ef4aa1dfbec1867dc7f7e90cd
  [19]=dfc21fb5efd9541379879714a918b724
  [20]=5ba38780a7add588601ea6868497c34d
  [21]=31c833c776c5471c0e43a78257f9e10a
  [22]=90d8aa4b055035b06164a379429b5e97
  [23]=1689dccf7ce615cf414bd3f143fd4a07
  [24]=835bdaf69e0e9cdf12f4d1fbbcae31f4
  [25]=19e3499ee5d0561c353041a79281e8b5
  [26]=1b9aac4383dc04cc5e03a61cff408242
  [27]=c66eb39c86f89a4272c6344f58caa805
  [28]=71fe3ba109a13051e95a600c6d80e79f
  [29]=ba50e9feee8dc886206867110f5c3e42
  [30]=07487360ed50b4cf38cf75ff049b6f1e
)

declare -A SHA256=(
  [01]=65621c6bf500bd69ff24104cae8540fa6e24a70546acbbd802a40bf934b23643
  [02]=e6faf4c57f688d60403111000787b855604e3c188d1e58a3e020ef5811e32527
  [03]=6700881bf9f40153902dd3cfb8d245cd1e6a11290420d80a0a4eef88b428e759
  [04]=150f131b2340835d6ff960c35f407a76ec1224201bd656d8fe12383cea2625f6
  [05]=966fcb1b98b3f3e63ffb8d8061a186e46db5487759645016269772b1551e0d87
  [06]=7b6d93b50b2d885c076e0cc21f2c29e1623d51ec0c72e0f8ea968fa005523a78
  [07]=0141ed32126d4862d1205e191b2d9f4d032b10828ed9cf3d219115a4552617c4
  [08]=e59a11647bc7a01c46ae86b80042dc8c21519798feb944dd57ccf10403176d93
  [09]=019cc649653cd05d71a9b6f2b77859ef95845e3f0b126a6eea9f6e37a54b5089
  [10]=211f734049fce066014d9ab52cbffe4b0241a4eac5a60c3add35cec6047d9280
  [11]=9694f4be994d7ad23f2ef2c188d3ea7b5a782d6d46513252ca23e81cc8aaa352
  [12]=94ee8d508753cec2046a782465bab824af339f0b42e9a4623b324471f5f81d84
  [13]=a08491db173abcf384fabfcd61226b78b40bbe05923212e17524c5ea0435d8bb
  [14]=0186a002ef5bd9a7caffb2ff06ad79aecf17c3368059e4dab57e6535c7c173a0
  [15]=9e7682de02868639a0f2180916eaacd9441abf13ee03fce051dd4d518dfdf9da
  [16]=8f2f6d05393f0065ff3860d0611b445cd0d93a4cb1ab696ac2fca86b950bea4f
  [17]=c883b8ed5fa7d09d151c502af42f74c7f30015da60c32c1a4ba4a7750cffb5f8
  [18]=18c90798fcc9afd736d5679a7dd388d1d84cac1082f6801e42afc083818c718b
  [19]=5c90b2c0251f753560a2b697d84e9d73512fc427863d22ba658798dcfe642460
  [20]=1e75bc7eadf5c39fdf9d96af365faf71e53c22bbbfba8a7e9cc6d8d0d6e30401
  [21]=1d4f10826fac4c817a167c23c331ec3605568b346eeb88f7f173f1752217d353
  [22]=5e68cacdde82c7845110e8e1e1f07fff12b784ae90097cebe5f5a2956eb00a7d
  [23]=be08503796abcbcdd6bdb04d46fd0125015b47bac33ea7a1771025fddae65e6d
  [24]=75cd6f9490c5c0513e3724c703d89e61525f10f6f8f94a070264dadf1d67a48f
  [25]=6a67bf921c2b0b435a0bc25b80f01b436035c07f01f7746934b98ac34f1aadf8
  [26]=f5c89efac71d9197b82384b0cb59cf4ecde81b9e6141fec025b897ecc7e967de
  [27]=c98eca07e5a39c8c893e5681f00794233f51755163dc4d35361c2c7d145a1950
  [28]=caae622e71a8b509f41e9aa970463ade6637555665c48ead06224801143ea138
  [29]=e856d99d73fef8e306db14685cfdbc87a60cc729d70b0ada47a36adb72df0530
  [30]=ac09fe5502d1f90b8bd259548c8fea4c95cb6df5f0d26b9ef880d894ad7775c3
)

MAX_PARALLEL="${LANL_UPLOAD_PARALLEL:-4}"
if ! [[ "$MAX_PARALLEL" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: LANL_UPLOAD_PARALLEL must be a positive integer." >&2
  exit 4
fi

available_kb="$(df -Pk /tmp | awk 'NR==2 {print $4}')"
if (( available_kb < 2500000 )) && [[ -z "${LANL_UPLOAD_PARALLEL+x}" ]]; then
  MAX_PARALLEL=2
  echo "Low /tmp free space detected; automatically reducing parallelism to 2."
fi

export AZCOPY_JOB_PLAN_LOCATION="/tmp/azcopy-plans"
export AZCOPY_LOG_LOCATION="/tmp/azcopy-logs"
export AZCOPY_CONCURRENCY_VALUE="${AZCOPY_CONCURRENCY_VALUE:-16}"
mkdir -p "$AZCOPY_JOB_PLAN_LOCATION" "$AZCOPY_LOG_LOCATION"

work_dir="$(mktemp -d /tmp/lanl-wls-upload.XXXXXX)"
manifest="$work_dir/wls_days_01_30_transfer_manifest.csv"
trap 'rm -rf "$work_dir"' EXIT

head_md5() {
  local url="$1"
  curl --silent --fail --head "$url" 2>/dev/null     | awk 'BEGIN{IGNORECASE=1} /^Content-MD5:/ {gsub(/\r/, "", $2); print $2}'     | tail -1
}

process_day() (
  set -euo pipefail
  local day_num="$1"
  local day file source_url dest_url expected_md5_hex expected_sha256 expected_md5_b64
  local existing_md5 tmp_file actual_md5 actual_sha256 actual_size row_file

  day="$(printf '%02d' "$day_num")"
  file="wls_day-${day}.bz2"
  source_url="${SOURCE_BASE}/${file}"
  dest_url="${BLOB_DIR_URL}/${file}?${SAS_QUERY}"
  expected_md5_hex="${MD5[$day]}"
  expected_sha256="${SHA256[$day]}"
  row_file="$work_dir/${day}.csv"

  expected_md5_b64="$(python3 - "$expected_md5_hex" <<'PY'
import base64, binascii, sys
print(base64.b64encode(binascii.unhexlify(sys.argv[1])).decode("ascii"))
PY
)"

  echo "[$day] checking destination"
  existing_md5="$(head_md5 "$dest_url" || true)"
  if [[ "$existing_md5" == "$expected_md5_b64" ]]; then
    echo "[$day] already present and verified"
    printf '%s,%s,%s,%s,%s,%s,%s\n'       "$day" "$file" "$source_url" "" "$expected_md5_hex" "$expected_sha256" "existing_verified"       > "$row_file"
    exit 0
  fi

  tmp_file="$(mktemp "/tmp/${file}.XXXXXX")"
  trap 'rm -f "$tmp_file"' EXIT

  echo "[$day] downloading"
  curl     --fail     --location     --silent     --show-error     --retry 5     --retry-all-errors     --retry-delay 3     --output "$tmp_file"     "$source_url"

  [[ "$(head -c 3 "$tmp_file")" == "BZh" ]] || {
    echo "[$day] ERROR: missing BZh magic" >&2
    exit 21
  }

  echo "[$day] validating archive"
  bzip2 -t "$tmp_file"

  actual_size="$(stat -c%s "$tmp_file")"
  actual_md5="$(md5sum "$tmp_file" | awk '{print $1}')"
  actual_sha256="$(sha256sum "$tmp_file" | awk '{print $1}')"

  [[ "$actual_md5" == "$expected_md5_hex" ]] || {
    echo "[$day] ERROR: MD5 mismatch; expected $expected_md5_hex got $actual_md5" >&2
    exit 22
  }

  [[ "$actual_sha256" == "$expected_sha256" ]] || {
    echo "[$day] ERROR: SHA-256 mismatch; expected $expected_sha256 got $actual_sha256" >&2
    exit 23
  }

  echo "[$day] uploading $actual_size bytes"
  azcopy cp     "$tmp_file"     "$dest_url"     --from-to=LocalBlob     --overwrite=true     --put-md5     --log-level=ERROR     --output-type=text

  existing_md5="$(head_md5 "$dest_url" || true)"
  [[ "$existing_md5" == "$expected_md5_b64" ]] || {
    echo "[$day] ERROR: destination Content-MD5 verification failed" >&2
    exit 24
  }

  printf '%s,%s,%s,%s,%s,%s,%s\n'     "$day" "$file" "$source_url" "$actual_size" "$expected_md5_hex" "$expected_sha256" "uploaded_verified"     > "$row_file"

  echo "[$day] COMPLETE"
)

echo "LANL WLS days 01-30 -> ADLS"
echo "Parallel workers: $MAX_PARALLEL"
echo "AzCopy concurrency per worker: $AZCOPY_CONCURRENCY_VALUE"
echo

failed=0
pids=()
days=()

wait_batch() {
  local i
  for i in "${!pids[@]}"; do
    if ! wait "${pids[$i]}"; then
      echo "Day $(printf '%02d' "${days[$i]}") FAILED." >&2
      failed=1
    fi
  done
  pids=()
  days=()
}

for day_num in $(seq 1 30); do
  process_day "$day_num" &
  pids+=("$!")
  days+=("$day_num")

  if (( ${#pids[@]} >= MAX_PARALLEL )); then
    wait_batch
    if (( failed )); then
      echo "Stopping after this batch. Rerun after correcting the error; verified days will be skipped." >&2
      exit 30
    fi
  fi
done

if (( ${#pids[@]} > 0 )); then
  wait_batch
fi

if (( failed )); then
  echo "One or more days failed. Rerun; completed verified days will be skipped." >&2
  exit 30
fi

printf 'day,filename,source_url,size_bytes,expected_md5,expected_sha256,status\n' > "$manifest"
for day_num in $(seq 1 30); do
  day="$(printf '%02d' "$day_num")"
  cat "$work_dir/${day}.csv" >> "$manifest"
done

manifest_url="${BLOB_DIR_URL}/wls_days_01_30_transfer_manifest.csv?${SAS_QUERY}"
azcopy cp   "$manifest"   "$manifest_url"   --from-to=LocalBlob   --overwrite=true   --log-level=ERROR   --output-type=text

echo
echo "SUCCESS: all 30 WLS archives are in ADLS and checksum-verified."
echo "Manifest: wls_days_01_30_transfer_manifest.csv"
