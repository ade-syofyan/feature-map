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
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_registry
import fm_state


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
                                   "touchpoints": [], "invariants": [],
                                   "impacts": []}
            current_list = None
            continue
        if current_flow is None:
            continue

        flow = flows[current_flow]
        if indent == 4:
            if stripped.startswith(("touchpoints:", "invariants:", "impacts:")):
                key, _, val = stripped.partition(":")
                current_list = key.strip()
                current_item = None
                val = val.strip()
                if current_list == "impacts" and val.startswith("[") and val.endswith("]"):
                    flow["impacts"] = [unquote(x) for x in val[1:-1].split(",")
                                       if x.strip()]
                    current_list = None
            elif ":" in stripped:
                key, val = stripped.split(":", 1)
                if key.strip() in ("description", "policy"):
                    flow[key.strip()] = unquote(val)
                current_list = None
            continue

        if current_list and stripped.startswith("- "):
            body = stripped[2:].strip()
            if current_list in ("invariants", "impacts"):
                flow[current_list].append(unquote(body))
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


def match_flows(flows, rel_paths):
    """Petakan nama flow -> daftar rel_path yang cocok dengan touchpoint LOKAL
    (touchpoint ber-`repo:` milik repo lain, tidak dicocokkan di sini)."""
    hits = {}
    for name, flow in flows.items():
        for rel in rel_paths:
            if any("path" in tp and "repo" not in tp and match(rel, tp["path"])
                   for tp in flow["touchpoints"]):
                hits.setdefault(name, []).append(rel)
    return hits


def expand_impacts(flows, stale_hits, max_depth=5):
    """Kembangkan stale_hits dengan rantai `impacts` (BFS, batas kedalaman,
    aman siklus). Return (expanded_hits, chains)."""
    expanded = {k: list(v) for k, v in stale_hits.items()}
    chains = {}
    for origin in stale_hits:
        visited = set(stale_hits)
        queue = [(origin, 0)]
        chain = []
        while queue:
            cur, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for nxt in flows.get(cur, {}).get("impacts", []):
                if nxt in visited or nxt not in flows:
                    continue
                visited.add(nxt)
                chain.append(nxt)
                expanded.setdefault(nxt, []).append(f"via:{cur}")
                queue.append((nxt, depth + 1))
        if chain:
            chains[origin] = chain
    return expanded, chains


def propagate_stale(root, flows, stale_hits):
    """Tandai stale flow yang sama di state.json repo lain (via registry)."""
    src = fm_registry.default_repo_name(root)
    for name, files in stale_hits.items():
        seen = set()
        for tp in flows[name]["touchpoints"]:
            rname = tp.get("repo")
            if not rname or rname in seen:
                continue
            seen.add(rname)
            other = fm_registry.resolve(rname)
            if not other or os.path.abspath(other) == os.path.abspath(root):
                continue
            fm_state.mark_stale(other, {
                name: [f if f.startswith("via:") else f"{src}:{f}" for f in files]})


def is_valid_sha(sha):
    return bool(sha) and len(sha) <= 40 and all(c in "0123456789abcdef" for c in sha.lower())


def git_changed_files(root, last_sha):
    """Path relatif yang berubah sejak last_sha (commit) + working tree saat ini."""
    changed = set()
    if last_sha is not None and not is_valid_sha(last_sha):
        last_sha = None  # state korup/dimanipulasi — jangan sisipkan ke argumen git
    try:
        if last_sha:
            r = subprocess.run(["git", "diff", "--name-only", f"{last_sha}..HEAD"],
                               cwd=root, capture_output=True, text=True, timeout=10)
            changed.update(l for l in r.stdout.splitlines() if l.strip())
        r = subprocess.run(["git", "status", "--porcelain"],
                           cwd=root, capture_output=True, text=True, timeout=10)
        for line in r.stdout.splitlines():
            if len(line) > 3:
                changed.add(line[3:].split(" -> ")[-1].strip())
    except Exception:
        pass
    return sorted(changed)


def git_head(root):
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


def handle(payload):
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path")

    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    fm_path = find_feature_map(project_dir)
    if not fm_path:
        return
    root = os.path.dirname(fm_path)

    try:
        with open(fm_path, encoding="utf-8") as f:
            flows = parse_feature_map(f.read())
    except Exception:
        return

    if file_path:
        rel_paths = [os.path.relpath(os.path.abspath(file_path), root)]
    else:
        # Event Bash: deteksi perubahan via git (merge/pull/checkout dsb.)
        state = fm_state.load_state(root)
        if state["last_synced_sha"] is None:
            head = git_head(root)
            if head:
                state["last_synced_sha"] = head
                fm_state.save_state(root, state)
            return
        rel_paths = git_changed_files(root, state["last_synced_sha"])
        if not rel_paths:
            return

    stale_hits = match_flows(flows, rel_paths)
    chains = {}
    if stale_hits:
        expanded, chains = expand_impacts(flows, stale_hits)
        fm_state.mark_stale(root, expanded)
        propagate_stale(root, flows, expanded)

    if not file_path:
        return  # reminder detail hanya untuk edit langsung

    rel = rel_paths[0]
    hits = []
    for name, flow in flows.items():
        for tp in flow["touchpoints"]:
            if "path" in tp and "repo" not in tp and match(rel, tp["path"]):
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
                loc = ""
                rname = tp.get("repo")
                if rname:
                    local = fm_registry.resolve(rname)
                    if local:
                        loc = f" @ {rname} → {local}"
                    else:
                        loc = (f" @ {rname} (belum terdaftar — jalankan "
                               f"/feature-map:flow-repo-register di repo itu)")
                lines.append(f"    - {tp.get('path', '?')} ({tp.get('role', '?')}){loc}{note}")
        for inv in flow["invariants"]:
            lines.append(f"  Invariant: {inv}")
        lines.append("  Periksa apakah perubahan ini menuntut penyesuaian di touchpoint lain; "
                     "kalau ya, kerjakan atau laporkan gap-nya ke user. Kalau policy berubah, "
                     "update FEATURE-MAP.yaml.")

    for origin, chain in chains.items():
        lines.append(f"[feature-map] Perubahan flow '{origin}' berdampak ke: "
                     f"{' → '.join(chain)} — flow tersebut ikut ditandai stale.")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "\n".join(lines),
        }
    }, ensure_ascii=False))


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
