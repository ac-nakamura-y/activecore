#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOOP="$ROOT/bin/meeting-notes-sync-loop"

# sessionStart: stale PID を掃除し、停止中ならログに記録する。
# 監視シェル付き supervisor の起動は Agent が ensure 失敗時に行う。
"$LOOP" ensure >>"$ROOT/tmp/meeting-notes-sync.log" 2>&1 || true
exit 0
