#!/usr/bin/env python3
"""State drift pending per-flow untuk feature-map: satu file JSON per flow di
.claude/feature-map-pending/<flow-id>.json. Dipakai PostToolUse hook untuk
menyimpan konteks perubahan, dan command /feature-map:flow-sync-apply untuk
membacanya lalu merangkum jadi invariant/policy baru di FEATURE-MAP.yaml.

Semua fungsi aman dipanggil dari hook: kegagalan I/O tidak melempar keluar.
"""
import json
import os
import re
import tempfile

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def sanitize_flow_id(name):
    return _UNSAFE_CHARS.sub("_", name)


def pending_dir(root):
    return os.path.join(root, ".claude", "feature-map-pending")


def _ensure_gitignore(root):
    gi_path = os.path.join(root, ".gitignore")
    try:
        existing = ""
        if os.path.isfile(gi_path):
            with open(gi_path, encoding="utf-8") as f:
                existing = f.read()
        if ".claude/feature-map-pending/" in existing:
            return
        with open(gi_path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(".claude/feature-map-pending/\n")
    except Exception:
        pass


def write_pending(root, flow_id, entry):
    try:
        d = pending_dir(root)
        os.makedirs(d, exist_ok=True)
        _ensure_gitignore(root)
        safe_id = sanitize_flow_id(flow_id)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        os.replace(tmp, os.path.join(d, f"{safe_id}.json"))
    except Exception:
        pass


def load_all_pending(root):
    result = {}
    d = pending_dir(root)
    try:
        names = os.listdir(d)
    except Exception:
        return result
    for name in names:
        if not name.endswith(".json"):
            continue
        flow_id = name[:-len(".json")]
        try:
            with open(os.path.join(d, name), encoding="utf-8") as f:
                result[flow_id] = json.load(f)
        except Exception:
            continue
    return result


def clear_pending(root, flow_id):
    safe_id = sanitize_flow_id(flow_id)
    try:
        os.remove(os.path.join(pending_dir(root), f"{safe_id}.json"))
    except Exception:
        pass
