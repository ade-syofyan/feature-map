#!/usr/bin/env python3
"""Small Codex CLI adapter for the local feature-map plugin."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_PLUGIN_ROOT = Path("/Users/adesyofyan/Documents/MApp/claude-plugins/feature-map")
CODEX_SKILL_ROOT = Path(__file__).resolve().parents[1]


def latest_cache_root() -> Path | None:
    base = Path.home() / ".claude/plugins/cache/ade-plugins/feature-map"
    if not base.is_dir():
        return None
    versions = [p for p in base.iterdir() if p.is_dir()]
    if not versions:
        return None
    return sorted(versions, key=lambda p: p.name)[-1]


def plugin_root() -> Path:
    for raw in (os.environ.get("FEATURE_MAP_PLUGIN_ROOT"),
                os.environ.get("CLAUDE_PLUGIN_ROOT")):
        if raw and Path(raw).is_dir():
            return Path(raw)
    if REPO_PLUGIN_ROOT.is_dir():
        return REPO_PLUGIN_ROOT
    cached = latest_cache_root()
    if cached:
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

    root = sub.add_parser("plugin-root", help="Print resolved plugin root.")
    root.set_defaults(func=lambda _args: print(plugin_root()) or 0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
