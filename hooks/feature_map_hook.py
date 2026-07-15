#!/usr/bin/env python3
"""PostToolUse hook: kalau file yang diedit terdaftar sebagai touchpoint di
FEATURE-MAP.yaml project, inject reminder berisi flow terkait, touchpoint lain,
dan invariants yang harus dijaga.

Tidak butuh dependency eksternal — memakai parser YAML-subset untuk skema
FEATURE-MAP.yaml yang terdokumentasi (lihat skill feature-map).
"""
import fnmatch
import json
import os
import sys


def parse_feature_map(text):
    """Parse subset YAML sesuai skema FEATURE-MAP.yaml.

    Skema yang didukung:
      flows:
        <nama-flow>:
          description: <teks>
          policy: <teks>
          touchpoints:
            - path: "<glob>"
              role: <teks>
              note: <teks opsional>
          invariants:
            - "<teks>"
    """
    flows = {}
    current_flow = None
    current_list = None  # "touchpoints" | "invariants"
    current_item = None
    in_flows = False

    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if indent == 0:
            in_flows = stripped == "flows:"
            current_flow = None
            continue
        if not in_flows:
            continue

        if indent == 2 and stripped.endswith(":"):
            current_flow = stripped[:-1].strip()
            flows[current_flow] = {"description": "", "policy": "",
                                   "touchpoints": [], "invariants": []}
            current_list = None
            continue
        if current_flow is None:
            continue

        flow = flows[current_flow]
        if indent == 4:
            if stripped.startswith(("touchpoints:", "invariants:")):
                current_list = stripped.split(":", 1)[0]
                current_item = None
            elif ":" in stripped:
                key, val = stripped.split(":", 1)
                if key.strip() in ("description", "policy"):
                    flow[key.strip()] = unquote(val)
                current_list = None
            continue

        if current_list and stripped.startswith("- "):
            body = stripped[2:].strip()
            if current_list == "invariants":
                flow["invariants"].append(unquote(body))
            else:
                current_item = {}
                flow["touchpoints"].append(current_item)
                if ":" in body:
                    k, v = body.split(":", 1)
                    current_item[k.strip()] = unquote(v)
            continue

        if current_list == "touchpoints" and current_item is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            current_item[k.strip()] = unquote(v)

    return flows


def unquote(val):
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        val = val[1:-1]
    return val


def find_feature_map(start_dir):
    d = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(d, "FEATURE-MAP.yaml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def match(rel_path, pattern):
    if fnmatch.fnmatch(rel_path, pattern):
        return True
    # dukung pola "dir/**/file" untuk file yang berada langsung di dir/
    if "/**/" in pattern and fnmatch.fnmatch(rel_path, pattern.replace("/**/", "/")):
        return True
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        return

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    fm_path = find_feature_map(project_dir)
    if not fm_path:
        return
    root = os.path.dirname(fm_path)

    try:
        with open(fm_path, encoding="utf-8") as f:
            flows = parse_feature_map(f.read())
    except Exception:
        return

    rel = os.path.relpath(os.path.abspath(file_path), root)
    hits = []
    for name, flow in flows.items():
        for tp in flow["touchpoints"]:
            if "path" in tp and match(rel, tp["path"]):
                hits.append((name, flow, tp))
                break
    if not hits:
        return

    lines = []
    for name, flow, matched_tp in hits:
        lines.append(f"[feature-map] File yang baru diedit adalah touchpoint "
                     f"'{matched_tp.get('role', '?')}' dari flow bisnis '{name}'.")
        if flow["policy"]:
            lines.append(f"  Policy saat ini: {flow['policy']}")
        others = [tp for tp in flow["touchpoints"] if tp is not matched_tp]
        if others:
            lines.append("  Touchpoint lain yang mungkin harus ikut disesuaikan:")
            for tp in others:
                note = f" — {tp['note']}" if tp.get("note") else ""
                lines.append(f"    - {tp.get('path', '?')} ({tp.get('role', '?')}){note}")
        for inv in flow["invariants"]:
            lines.append(f"  Invariant: {inv}")
        lines.append("  Periksa apakah perubahan ini menuntut penyesuaian di touchpoint lain; "
                     "kalau ya, kerjakan atau laporkan gap-nya ke user. Kalau policy berubah, "
                     "update FEATURE-MAP.yaml.")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(lines),
        }
    }))


if __name__ == "__main__":
    main()
