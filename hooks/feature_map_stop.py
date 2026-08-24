#!/usr/bin/env python3
"""Stop hook: kalau ada flow dengan pending drift (lihat fm_pending.py) yang
belum disinkronkan ke FEATURE-MAP.yaml, ingatkan agent untuk menjalankan
/feature-map:flow-sync-apply. Non-blocking -- hanya reminder, tidak pernah
mengembalikan decision:block, karena hook ini tidak punya akses model untuk
menilai apakah drift-nya memang perlu dicatat.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_map_hook import find_feature_map
import fm_io
import fm_pending


def _reminded_marker_path(root, session_id):
    # Deliberately NOT inside fm_pending.pending_dir(root): that directory is
    # scanned by fm_pending.load_all_pending() for *.json files, so a marker
    # dropped there would get misread back as a pending drift flow itself.
    safe_session = fm_pending.sanitize_flow_id(session_id or "unknown")
    state_dir = os.path.join(root, ".claude", "feature-map-state")
    return os.path.join(state_dir, f"stop-reminded-{safe_session}.json")


def _load_reminded(marker_path):
    try:
        with open(marker_path, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_reminded(root, marker_path, flow_ids):
    try:
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)
        fm_io.append_gitignore(root, ".claude/feature-map-state/")
        with open(marker_path, "w", encoding="utf-8") as f:
            json.dump(sorted(flow_ids), f)
    except Exception:
        pass


def handle(payload):
    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    fm_path = find_feature_map(project_dir)
    if not fm_path:
        return
    root = os.path.dirname(fm_path)

    pending = fm_pending.load_all_pending(root)
    if not pending:
        return

    flow_ids = set(pending)

    # Only remind about flows we haven't already nagged about in this
    # session -- once told, the agent either syncs (clear_pending removes
    # the entry, so it drops out of `pending` next time) or explicitly
    # dismisses it. Repeating the identical reminder every single Stop
    # event reads as spam and adds nothing new for the agent to act on.
    marker_path = _reminded_marker_path(root, payload.get("session_id"))
    already_reminded = _load_reminded(marker_path)
    new_flow_ids = flow_ids - already_reminded
    if not new_flow_ids:
        return

    message = (
        f"[feature-map] {len(new_flow_ids)} flow(s) have pending drift not yet "
        f"reflected in FEATURE-MAP.yaml: {', '.join(sorted(new_flow_ids))}. Run "
        "/feature-map:flow-sync-apply to review and sync, or dismiss if the "
        "edit didn't actually require an invariant change."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": message,
        }
    }, ensure_ascii=False))
    _save_reminded(root, marker_path, already_reminded | new_flow_ids)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    try:
        handle(payload)
    except Exception:
        return


if __name__ == "__main__":
    main()
