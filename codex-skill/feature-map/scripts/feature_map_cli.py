#!/usr/bin/env python3
"""Small Codex CLI adapter for the local feature-map plugin."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_PLUGIN_ROOT = Path("/Users/adesyofyan/Documents/MApp/claude-plugins")
CODEX_SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO_ROOT = CODEX_SKILL_ROOT.parent.parent


def latest_cache_root() -> Path | None:
    base = Path.home() / ".claude/plugins/cache/ade-plugins/feature-map"
    if not base.is_dir():
        return None
    versions = [p for p in base.iterdir() if p.is_dir()]
    if not versions:
        return None
    return sorted(versions, key=lambda p: p.name)[-1]


def plugin_root() -> Path:
    def usable(root: Path) -> bool:
        return (root / "hooks" / "feature_map_hook.py").is_file()

    for raw in (os.environ.get("FEATURE_MAP_PLUGIN_ROOT"),
                os.environ.get("CLAUDE_PLUGIN_ROOT")):
        if raw and usable(Path(raw)):
            return Path(raw)
    marker = CODEX_SKILL_ROOT / "plugin-root.txt"
    if marker.is_file():
        raw = marker.read_text(encoding="utf-8").strip()
        if raw and usable(Path(raw)):
            return Path(raw)
    for candidate in (REPO_PLUGIN_ROOT, SOURCE_REPO_ROOT):
        if usable(candidate):
            return candidate
    cached = latest_cache_root()
    if cached and usable(cached):
        return cached
    return CODEX_SKILL_ROOT


def add_plugin_hooks_to_path() -> Path:
    root = plugin_root()
    hooks = root / "hooks"
    if hooks.is_dir():
        sys.path.insert(0, str(hooks))
    return root


def git_root(start: str | None = None) -> Path:
    cwd = Path(start or os.getcwd()).resolve()
    cur = cwd
    while True:
        if (cur / "FEATURE-MAP.yaml").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    raise SystemExit("No git root or FEATURE-MAP.yaml found.")


def read_flows(root: Path) -> dict:
    add_plugin_hooks_to_path()
    from feature_map_hook import parse_feature_map

    fm = root / "FEATURE-MAP.yaml"
    if not fm.is_file():
        return {}
    return parse_feature_map(fm.read_text(encoding="utf-8"))


def cmd_status(args: argparse.Namespace) -> int:
    root = git_root(args.root)
    add_plugin_hooks_to_path()
    import fm_registry
    import fm_state

    flows = read_flows(root)
    state = fm_state.load_state(str(root))
    stale = {
        name: entry for name, entry in state.get("flows", {}).items()
        if entry.get("status") == "stale"
    }
    payload = {
        "repo_root": str(root),
        "plugin_root": str(plugin_root()),
        "registry_path": os.environ.get("FEATURE_MAP_REGISTRY")
        or str(Path.home() / ".claude/feature-maps/registry.json"),
        "registered_repos": fm_registry.load_registry().get("repos", {}),
        "flows": {
            name: {
                "description": flow.get("description", ""),
                "touchpoints": len(flow.get("touchpoints", [])),
                "invariants": len(flow.get("invariants", [])),
                "impacts": flow.get("impacts", []),
            }
            for name, flow in flows.items()
        },
        "last_synced_sha": state.get("last_synced_sha"),
        "stale": stale,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_mark_clean(args: argparse.Namespace) -> int:
    if not args.flows:
        raise SystemExit("mark-clean requires at least one flow name.")
    root = git_root(args.root)
    add_plugin_hooks_to_path()
    import fm_state

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    ).stdout.strip()
    fm_state.mark_clean(str(root), args.flows, head)
    print(f"Marked clean: {', '.join(args.flows)} at {head}")
    return 0


def cmd_repo_register(args: argparse.Namespace) -> int:
    add_plugin_hooks_to_path()
    import fm_registry

    reg = fm_registry.load_registry()
    repos = reg.setdefault("repos", {})

    if args.list:
        for name, path in sorted(repos.items()):
            suffix = "" if Path(path).is_dir() else " (missing)"
            print(f"{name}\t{path}{suffix}")
        return 0

    if args.remove:
        removed = repos.pop(args.remove, None)
        fm_registry.save_registry(reg)
        print(f"Removed {args.remove}: {removed}" if removed else f"No entry: {args.remove}")
        return 0

    root = git_root(args.root)
    name = args.name or fm_registry.default_repo_name(str(root))
    repos[name] = str(root)
    fm_registry.save_registry(reg)
    print(json.dumps(reg, indent=2, ensure_ascii=False))
    return 0


def cmd_rules_check(args: argparse.Namespace) -> int:
    root = git_root(args.root)
    add_plugin_hooks_to_path()
    import fm_rules_check

    flows = read_flows(root)
    if not (root / "FEATURE-MAP.yaml").is_file():
        print(json.dumps({"error": "FEATURE-MAP.yaml not found"}))
        return 1
    if args.flow not in flows:
        print(json.dumps({"error": f"flow '{args.flow}' not found",
                           "available_flows": sorted(flows.keys())}))
        return 1
    result = fm_rules_check.check_flow(str(root), args.flow, flows[args.flow])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_pending_status(args: argparse.Namespace) -> int:
    root = git_root(args.root)
    add_plugin_hooks_to_path()
    import fm_pending

    pending = fm_pending.load_all_pending(str(root))
    print(json.dumps(pending, indent=2, ensure_ascii=False))
    return 0


def cmd_pending_clear(args: argparse.Namespace) -> int:
    root = git_root(args.root)
    add_plugin_hooks_to_path()
    import fm_pending

    for flow in args.flows:
        fm_pending.clear_pending(str(root), flow)
    print(f"Cleared: {', '.join(args.flows)}")
    return 0


def cmd_import_doc(args: argparse.Namespace) -> int:
    add_plugin_hooks_to_path()
    import fm_blueprint

    rendered = fm_blueprint.generate_feature_map(args.document, args.source_path)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
        print(f"Wrote draft feature map: {args.output}")
    else:
        print(rendered, end="")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    root = add_plugin_hooks_to_path()
    checks = {
        "hooks_available": (root / "hooks" / "feature_map_hook.py").is_file(),
        "parser_sample": False,
        "blueprint_sample": False,
    }
    version = None
    try:
        manifest = root / ".claude-plugin" / "plugin.json"
        if manifest.is_file():
            version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except Exception:
        version = None

    try:
        from feature_map_hook import parse_feature_map
        flows = parse_feature_map(
            'flows:\n  sample:\n    description: "sample # quoted"\n'
            '    touchpoints:\n      - path: "app/#x.py"\n        role: backend\n'
            '    invariants:\n      - "hash # preserved"\n'
        )
        checks["parser_sample"] = (
            flows["sample"]["description"] == "sample # quoted"
            and flows["sample"]["touchpoints"][0]["path"] == "app/#x.py"
        )
    except Exception:
        pass

    try:
        import fm_blueprint
        with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8") as f:
            f.write("WORKFLOW PAYROLL Input: Attendance. Output: Payroll.")
            f.flush()
            checks["blueprint_sample"] = "payroll:" in fm_blueprint.generate_feature_map(f.name)
    except Exception:
        pass

    payload = {
        "ok": all(checks.values()),
        "plugin_root": str(root),
        "version": version,
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def _repo_files(root: Path) -> list[str]:
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {".git", "node_modules", "vendor", ".venv", "__pycache__"}
        ]
        for filename in filenames:
            result.append(os.path.relpath(os.path.join(dirpath, filename), root))
    return sorted(result)


def cmd_quality(args: argparse.Namespace) -> int:
    try:
        root = git_root(args.root)
    except SystemExit:
        root = Path(args.root or os.getcwd()).resolve()
    add_plugin_hooks_to_path()
    from feature_map_hook import match

    if not (root / "FEATURE-MAP.yaml").is_file():
        print(json.dumps({
            "ok": False,
            "repo_root": str(root),
            "error": "FEATURE-MAP.yaml not found",
        }, indent=2, ensure_ascii=False))
        return 1

    flows = read_flows(root)
    repo_files = _repo_files(root)
    issues = []
    summary = {
        "draft_flows": 0,
        "placeholder_touchpoints": 0,
        "dead_touchpoints": 0,
        "missing_invariants": 0,
        "missing_touchpoints": 0,
    }
    for name, flow in sorted(flows.items()):
        if flow.get("confidence") == "draft":
            summary["draft_flows"] += 1
            issues.append({"type": "draft-flow", "flow": name})
        if not flow.get("invariants"):
            summary["missing_invariants"] += 1
            issues.append({"type": "missing-invariants", "flow": name})
        touchpoints = flow.get("touchpoints", [])
        if not touchpoints:
            summary["missing_touchpoints"] += 1
            issues.append({"type": "missing-touchpoints", "flow": name})
        for tp in touchpoints:
            path = tp.get("path", "")
            note = tp.get("note", "")
            if not path or "repo" in tp:
                continue
            if "placeholder" in f"{path} {note}".lower():
                summary["placeholder_touchpoints"] += 1
                issues.append({"type": "placeholder-touchpoint", "flow": name, "path": path})
            if not any(match(rel, path) for rel in repo_files):
                summary["dead_touchpoints"] += 1
                issues.append({"type": "dead-touchpoint", "flow": name, "path": path})

    payload = {
        "ok": not issues,
        "repo_root": str(root),
        "flows": len(flows),
        "summary": summary,
        "issues": issues,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    status = sub.add_parser("status", help="Print feature-map orientation JSON.")
    status.add_argument("root", nargs="?", default=None)
    status.set_defaults(func=cmd_status)

    clean = sub.add_parser("mark-clean", help="Mark one or more flows clean.")
    clean.add_argument("root")
    clean.add_argument("flows", nargs="+")
    clean.set_defaults(func=cmd_mark_clean)

    reg = sub.add_parser("repo-register", help="Manage multi-repo registry.")
    reg.add_argument("name", nargs="?")
    reg.add_argument("--root", default=None)
    reg.add_argument("--list", action="store_true")
    reg.add_argument("--remove")
    reg.set_defaults(func=cmd_repo_register)

    rules_check = sub.add_parser("rules-check", help="Cross-check a flow's invariants against its test touchpoints' descriptions.")
    rules_check.add_argument("flow")
    rules_check.add_argument("--root", default=None)
    rules_check.set_defaults(func=cmd_rules_check)

    pending_status = sub.add_parser("pending-status", help="List flows with pending drift not yet synced to FEATURE-MAP.yaml.")
    pending_status.add_argument("root", nargs="?", default=None)
    pending_status.set_defaults(func=cmd_pending_status)

    pending_clear = sub.add_parser("pending-clear", help="Clear pending drift for one or more flows (after syncing or skipping).")
    pending_clear.add_argument("root")
    pending_clear.add_argument("flows", nargs="+")
    pending_clear.set_defaults(func=cmd_pending_clear)

    import_doc = sub.add_parser("import-doc", help="Generate draft FEATURE-MAP.yaml from blueprint/FRD/SRS/SOP documents.")
    import_doc.add_argument("document")
    import_doc.add_argument("-o", "--output")
    import_doc.add_argument("--source-path")
    import_doc.set_defaults(func=cmd_import_doc)

    doctor = sub.add_parser("doctor", help="Run a local feature-map install smoke test.")
    doctor.set_defaults(func=cmd_doctor)

    quality = sub.add_parser("quality", help="Report FEATURE-MAP.yaml quality issues.")
    quality.add_argument("root", nargs="?", default=None)
    quality.set_defaults(func=cmd_quality)

    root = sub.add_parser("plugin-root", help="Print resolved plugin root.")
    root.set_defaults(func=lambda _args: print(plugin_root()) or 0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
