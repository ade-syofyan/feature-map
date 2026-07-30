#!/usr/bin/env python3
"""Pre-commit: peringatkan kalau sebuah flow tersentuh di satu role/layer
tapi role lain tidak ikut berubah (heuristik path, banyak false-positive --
selalu non-blocking).

Selain itu, MEMBLOKIR commit (exit 1) kalau ada pending drift bisnis
(.claude/feature-map-pending/*.json, ditulis oleh PostToolUse hook waktu
Claude session mendeteksi rumus/kondisi bisnis berubah) yang belum
disinkronkan ke FEATURE-MAP.yaml lewat /feature-map:flow-sync-apply. Sinyal
ini lebih pasti daripada heuristik path di atas karena sudah melalui deteksi
formula_change, jadi layak jadi gate sungguhan. Override: FEATURE_MAP_ACK=1
git commit ... (atau --no-verify seperti hook git lain)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feature_map_hook as hook
import fm_pending
import fm_state


def check(flows, staged, changed_since_sync):
    changed_all = set(staged) | set(changed_since_sync)
    warnings = []
    for name, flow in flows.items():
        roles = {}
        for tp in flow["touchpoints"]:
            if "path" in tp:
                roles.setdefault(tp.get("role", "?"), []).append(tp)
        if len(roles) < 2:
            continue
        touched = {r for r, tps in roles.items()
                   if any(hook.match(p, tp["path"]) for p in staged for tp in tps)}
        if not touched:
            continue
        untouched = []
        for role, tps in roles.items():
            if role in touched:
                continue
            if any(hook.match(p, tp["path"]) for p in changed_all for tp in tps):
                continue
            paths = ", ".join(tp["path"] for tp in tps)
            untouched.append(f"{role} ({paths})")
        if untouched:
            warnings.append(
                f"[feature-map] flow '{name}' berubah di {', '.join(sorted(touched))} "
                f"tapi {'; '.join(untouched)} tidak ikut — pastikan konsisten "
                f"atau abaikan jika memang satu sisi saja.")
    return warnings


def _git_lines(root, *args):
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                           text=True, timeout=10)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def main():
    try:
        root_dir = os.getcwd()
        fm_path = hook.find_feature_map(root_dir)
        if not fm_path:
            return
        root = os.path.dirname(fm_path)
        with open(fm_path, encoding="utf-8") as f:
            flows = hook.parse_feature_map(f.read())
        staged = _git_lines(root, "diff", "--cached", "--name-only")
        if not staged:
            return
        last_sha = fm_state.load_state(root)["last_synced_sha"]
        changed = _git_lines(root, "diff", "--name-only", f"{last_sha}..HEAD") \
            if last_sha and hook.is_valid_sha(last_sha) else []
        for w in check(flows, staged, changed):
            print(w)

        pending = fm_pending.load_all_pending(root)
        if pending:
            # Batasi ke flow yang memang tersentuh oleh commit ini -- pending drift
            # lama (sesi lalu, flow yang sudah tidak disentuh lagi, atau sudah
            # dihapus dari FEATURE-MAP.yaml) tidak boleh memblokir commit yang
            # tidak berhubungan sama sekali.
            staged_flow_names = set(hook.match_flows(flows, staged))
            blocking = {k: v for k, v in pending.items() if k in staged_flow_names}
            if blocking and os.environ.get("FEATURE_MAP_ACK") != "1":
                print(f"[feature-map] Commit diblokir: {len(blocking)} flow bisnis punya "
                      f"drift belum disinkronkan ke FEATURE-MAP.yaml: "
                      f"{', '.join(sorted(blocking))}.")
                print("[feature-map] Jalankan /feature-map:flow-sync-apply dulu, atau kalau "
                      "memang bukan perubahan aturan bisnis: FEATURE_MAP_ACK=1 git commit ...")
                sys.exit(1)
    except SystemExit:
        raise
    except Exception:
        pass


if __name__ == "__main__":
    main()
