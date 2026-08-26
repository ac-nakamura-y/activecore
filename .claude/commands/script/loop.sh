#!/usr/bin/env bash
set -euo pipefail

dir="$(cd "$(dirname "$0")" && pwd)"

while true; do
  sleep "$("$dir/next")"
  echo 'AGENT_LOOP_TICK_cogsworth {"prompt":"CLAUDE.md の Cogsworth > 同期 手順を実行。"}'
done
