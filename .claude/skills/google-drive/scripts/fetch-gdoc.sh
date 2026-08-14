#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: fetch-gdoc.sh FILE_ID [FILE_ID ...]" >&2
  exit 1
fi

DOWNLOADS="${HOME}/Downloads"
OPEN_WAIT="${OPEN_WAIT:-3}"
EXPORT_WAIT="${EXPORT_WAIT:-4}"

latest_txt_after() {
  local since="$1"
  local newest="" newest_mtime=0
  local p mtime
  for p in "$DOWNLOADS"/*.txt; do
    [[ -f "$p" ]] || continue
    mtime=$(stat -f '%m' "$p")
    if (( mtime >= since )) && (( mtime > newest_mtime )); then
      newest="$p"
      newest_mtime=$mtime
    fi
  done
  printf '%s' "$newest"
}

fetch_one() {
  local file_id="$1"
  local edit_url="https://docs.google.com/document/d/${file_id}/edit"
  local export_url="https://docs.google.com/document/d/${file_id}/export?format=txt"
  local since downloaded

  since=$(date +%s)

  osascript <<EOF
tell application "Google Chrome"
  activate
  if (count of windows) = 0 then make new window
  tell front window
    set URL of active tab to "${edit_url}"
  end tell
end tell
EOF

  sleep "$OPEN_WAIT"

  osascript <<EOF
tell application "Google Chrome"
  tell front window
    set URL of active tab to "${export_url}"
  end tell
end tell
EOF

  sleep "$EXPORT_WAIT"

  downloaded=$(latest_txt_after "$since")
  if [[ -z "$downloaded" ]]; then
    echo "error: no .txt downloaded for ${file_id}" >&2
    return 1
  fi

  echo "$downloaded"
}

for file_id in "$@"; do
  fetch_one "$file_id"
done
