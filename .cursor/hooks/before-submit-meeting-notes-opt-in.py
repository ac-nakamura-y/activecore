#!/usr/bin/env python3
"""Enable or disable meeting notes sync for the current conversation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from meeting_notes_sync_state import (  # noqa: E402
    detect_action,
    log_line,
    set_enabled,
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = payload.get("prompt") or ""
    conversation_id = payload.get("conversation_id") or ""
    action = detect_action(prompt)

    if action and conversation_id:
        set_enabled(conversation_id, action == "enable")
        if action == "enable":
            pending = ROOT / "tmp" / "meeting-notes-sync-tick.pending"
            pending.parent.mkdir(parents=True, exist_ok=True)
            pending.write_text("enabled", encoding="utf-8")
            log_line(f"PENDING immediate sync after enable conversation_id={conversation_id}")

        message = (
            "Lumiere を有効化しました。"
            if action == "enable"
            else "Lumiere を無効化しました。"
        )
        print(json.dumps({"continue": False, "user_message": message}, ensure_ascii=False))
        return 0

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
