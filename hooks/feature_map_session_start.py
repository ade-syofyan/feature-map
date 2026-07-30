#!/usr/bin/env python3
"""SessionStart hook: kalau project punya FEATURE-MAP.yaml, cetak index ringan
(nama flow + deskripsi satu baris saja, bukan touchpoints/invariants penuh)
supaya AI tahu di awal sesi flow bisnis apa saja yang ada, lalu baca detail
spesifik lewat FEATURE-MAP.yaml begitu menyentuh file yang relevan.

Sengaja tidak mengirim isi lengkap (touchpoints/invariants/policy) di sini —
itu tugas feature_map_hook.py (PostToolUse) begitu file yang diedit match
salah satu flow, supaya konteks yang masuk tetap proporsional dengan file
yang benar-benar disentuh.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_map_hook import find_feature_map, parse_feature_map


def handle(payload):
    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    fm_path = find_feature_map(project_dir)
    if not fm_path:
        return

    try:
        with open(fm_path, encoding="utf-8") as f:
            flows = parse_feature_map(f.read())
    except Exception:
        return
    if not flows:
        return

    rel_fm = os.path.relpath(fm_path, project_dir)
    lines = [
        f"[feature-map] {rel_fm} terdaftar {len(flows)} flow bisnis lintas layer. "
        "Kalau task ini menyentuh file yang match salah satu flow di bawah, baca "
        "entri lengkapnya (touchpoints & invariants) di FEATURE-MAP.yaml SEBELUM mulai edit "
        "— jangan tunggu reminder PostToolUse.",
    ]
    for name, flow in sorted(flows.items()):
        desc = flow.get("description", "").strip()
        lines.append(f"  - {name}: {desc}" if desc else f"  - {name}")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }, ensure_ascii=False))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    try:
        handle(payload)
    except Exception:
        return


if __name__ == "__main__":
    main()
