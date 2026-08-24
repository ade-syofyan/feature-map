#!/usr/bin/env python3
"""State stale per-flow untuk feature-map: .feature-map/state.json.

Semua fungsi aman dipanggil dari hook: kegagalan I/O tidak melempar keluar.
"""
import json
import os
import tempfile
from datetime import datetime, timezone

import fm_io

DEFAULT = {"last_synced_sha": None, "flows": {}}


def _state_path(root):
    return os.path.join(root, ".feature-map", "state.json")


def load_state(root):
    try:
        with open(_state_path(root), encoding="utf-8") as f:
            state = json.load(f)
        if not isinstance(state, dict):
            return dict(DEFAULT)
        state.setdefault("last_synced_sha", None)
        state.setdefault("flows", {})
        return state
    except Exception:
        return {"last_synced_sha": None, "flows": {}}


def save_state(root, state):
    try:
        d = os.path.join(root, ".feature-map")
        os.makedirs(d, exist_ok=True)
        fm_io.append_gitignore(root, ".feature-map/")
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, _state_path(root))
    except Exception:
        pass


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mark_stale(root, flow_files):
    state = load_state(root)
    for name, files in flow_files.items():
        entry = state["flows"].get(name) or {"status": "clean", "dirty_files": []}
        merged = set(entry.get("dirty_files") or []) | set(files)
        state["flows"][name] = {
            "status": "stale",
            "dirty_files": sorted(merged),
            "marked_at": _now(),
        }
    save_state(root, state)


def mark_clean(root, flow_names, head_sha):
    state = load_state(root)
    for name in flow_names:
        state["flows"][name] = {
            "status": "clean",
            "dirty_files": [],
            "marked_at": _now(),
        }
    state["last_synced_sha"] = head_sha
    save_state(root, state)
