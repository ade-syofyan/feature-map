#!/usr/bin/env python3
"""Small Codex CLI adapter for the local feature-map plugin."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_PLUGIN_ROOT = Path("/Users/adesyofyan/Documents/MApp/claude-plugins")
CODEX_SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO_ROOT = CODEX_SKILL_ROOT.parent.parent
SUPPORTED_ROLES = {
    "client-form",
    "client-view",
    "backend-validation",
    "backend-service",
    "admin-view",
    "data-schema",
    "docs",
    "db-migration",
    "event-consumer",
}
LIST_FIELDS = ("touchpoints", "invariants", "impacts", "evidence", "history")
FILTER_FIELD_NAMES = {"q", "query", "search", "keyword", "status", "from", "to", "date", "start_date", "end_date"}


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


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _slug(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "app"


def _module_from_route(uri: str, name: str = "") -> str:
    if name:
        return _slug(name.split(".")[0])
    parts = [p for p in uri.strip("/").split("/") if p and not p.startswith("{")]
    return _slug(parts[0] if parts else "home")


def _detect_profile(root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if (root / "artisan").is_file() or (root / "composer.json").is_file():
        composer = _read_json(root / "composer.json")
        if "laravel/framework" in (composer.get("require") or {}):
            return "laravel"
    if (root / "package.json").is_file():
        package = _read_json(root / "package.json")
        deps = {**(package.get("dependencies") or {}), **(package.get("devDependencies") or {})}
        if "next" in deps:
            return "nextjs"
        if "@nestjs/core" in deps:
            return "nestjs"
        if "express" in deps:
            return "express"
        return "node"
    return "generic"


def _extract_routes(root: Path) -> list[dict]:
    routes = []
    middleware_stack: list[list[str]] = []
    for path in sorted((root / "routes").glob("*.php")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            stripped = line.strip()
            closes = stripped.count("}")
            if closes:
                middleware_stack = middleware_stack[:-closes] or []
            mw = re.search(r"Route::middleware\((.*?)\)", line)
            if mw:
                middleware_stack.append(re.findall(r"['\"]([^'\"]+)['\"]", mw.group(1)))
            route = re.search(r"Route::(get|post|put|patch|delete|resource)\(['\"]([^'\"]+)['\"](.*)", line)
            if not route:
                continue
            tail = route.group(3)
            name = ""
            found_name = re.search(r"->name\(['\"]([^'\"]+)['\"]\)", tail)
            if found_name:
                name = found_name.group(1)
            controller = ""
            found_controller = re.search(r"\[([A-Za-z0-9_\\\\]+)::class,\s*['\"]([^'\"]+)['\"]\]", tail)
            if found_controller:
                controller = f"{found_controller.group(1)}@{found_controller.group(2)}"
            route_mw = re.findall(r"->middleware\((.*?)\)", tail)
            middleware = [mw for stack in middleware_stack for mw in stack]
            for raw in route_mw:
                middleware.extend(re.findall(r"['\"]([^'\"]+)['\"]", raw))
            routes.append({
                "method": route.group(1).upper(),
                "uri": route.group(2),
                "name": name,
                "controller": controller,
                "middleware": sorted(set(middleware)),
                "module": _module_from_route(route.group(2), name),
                "source": str(path.relative_to(root)),
            })
    return routes


def _extract_generic_routes(root: Path) -> list[dict]:
    routes = []
    patterns = (
        r"\b(?:router|app)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)['\"]",
        r"@(Get|Post|Put|Patch|Delete)\(['\"]([^'\"]*)['\"]\)",
    )
    for rel in _repo_files(root):
        if not rel.endswith((".js", ".jsx", ".ts", ".tsx", ".py", ".rb", ".go", ".java", ".cs")):
            continue
        path = root / rel
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            for found in re.finditer(pattern, text):
                method = found.group(1).upper()
                uri = found.group(2) or "/"
                routes.append({
                    "method": method,
                    "uri": uri,
                    "name": "",
                    "controller": "",
                    "middleware": [],
                    "module": _module_from_route(uri),
                    "source": rel,
                })
    return routes


def _extract_views(root: Path, profile: str = "generic") -> list[dict]:
    views = []
    candidates = []
    bases = (root / "resources" / "views",) if profile == "laravel" else (
        root / "resources" / "views", root / "src", root / "app", root / "pages", root / "views"
    )
    for base in bases:
        if base.is_dir():
            candidates.extend(base.rglob("*"))
    for path in sorted(p for p in candidates if p.suffix in {".php", ".html", ".vue", ".jsx", ".tsx"} or p.name.endswith(".blade.php")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        fields = sorted(set(re.findall(r"\bname=['\"]([^'\"]+)['\"]", text)))
        route_refs = sorted(set(re.findall(r"route\(['\"]([^'\"]+)['\"]", text) + re.findall(r"\b(?:href|to)=['\"]([^'\"]+)['\"]", text)))
        buttons = sorted(set(re.findall(r"<button[^>]*>(.*?)</button>", text, re.I | re.S)))
        clean_buttons = [re.sub(r"<[^>]+>", "", b).strip() for b in buttons if re.sub(r"<[^>]+>", "", b).strip()]
        rel = path.relative_to(root)
        parts = rel.parts
        module = "ui"
        if len(parts) >= 5 and parts[:3] == ("resources", "views", "page"):
            module = _slug(parts[3])
        elif route_refs:
            module = _slug(route_refs[0].split(".")[0])
        elif path.stem:
            module = _slug(re.sub(r"(Page|View|Screen|Component)$", "", path.stem))
        views.append({
            "path": str(rel),
            "module": module,
            "fields": fields,
            "filters": [f for f in fields if f in FILTER_FIELD_NAMES],
            "route_refs": route_refs,
            "buttons": clean_buttons,
            "forms": len(re.findall(r"<form\b", text, re.I)),
        })
    return views


def _extract_database(root: Path) -> dict:
    tables = {}
    migration_dir = root / "database" / "migrations"
    for path in sorted(migration_dir.glob("*.php")) if migration_dir.is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        found = re.search(r"Schema::create\(['\"]([^'\"]+)['\"]", text)
        if not found:
            continue
        table = found.group(1)
        columns = {}
        for col in re.finditer(r"\$table->([A-Za-z0-9_]+)\(['\"]([^'\"]+)['\"]", text):
            columns[col.group(2)] = {"type": col.group(1)}
        if "$table->id()" in text:
            columns.setdefault("id", {"type": "id"})
        tables[table] = {"source": str(path.relative_to(root)), "columns": columns}
    return {"tables": tables}


def _extract_models(root: Path) -> dict:
    models = {}
    model_dir = root / "app" / "Models"
    for path in sorted(model_dir.glob("*.php")) if model_dir.is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        table = re.search(r"protected\s+\$table\s*=\s*['\"]([^'\"]+)['\"]", text)
        casts = re.findall(r"['\"]([^'\"]+)['\"]\s*=>\s*['\"]([^'\"]+)['\"]", text)
        models[path.stem] = {
            "source": str(path.relative_to(root)),
            "table": table.group(1) if table else _slug(path.stem) + "s",
            "casts": dict(casts),
            "soft_deletes": "SoftDeletes" in text,
        }
    return models


def _extract_controller_model_usage(root: Path) -> dict[str, list[str]]:
    usage = {}
    base = root / "app" / "Http" / "Controllers"
    for path in sorted(base.rglob("*.php")) if base.is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        models = sorted(set(re.findall(r"\b([A-Z][A-Za-z0-9_]*)::(?:query|create|where|find|with|updateOrCreate)\b", text)))
        usage[path.stem] = models
    return usage


def _extract_dependencies(root: Path) -> dict:
    composer = _read_json(root / "composer.json")
    package = _read_json(root / "package.json")
    return {
        "composer": sorted((composer.get("require") or {}).keys()),
        "composer_dev": sorted((composer.get("require-dev") or {}).keys()),
        "npm": sorted((package.get("dependencies") or {}).keys()),
        "npm_dev": sorted((package.get("devDependencies") or {}).keys()),
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _lines(title: str, items: list[str]) -> str:
    body = "\n".join(f"- {item}" for item in items) if items else "- Not detected"
    return f"# {title}\n\n{body}\n"


def cmd_extract_app(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(json.dumps({"ok": False, "error": f"app root not found: {root}"}, indent=2))
        return 1
    profile = _detect_profile(root, args.profile)

    out = Path(args.output).resolve()
    deps = _extract_dependencies(root)
    routes = _extract_routes(root) if profile == "laravel" else _extract_generic_routes(root)
    views = _extract_views(root, profile)
    database = _extract_database(root)
    models = _extract_models(root)
    controller_models = _extract_controller_model_usage(root)

    modules: dict[str, dict] = {}
    for route in routes:
        modules.setdefault(route["module"], {
            "routes": [], "views": [], "auth": [], "ui": {"fields": [], "filters": [], "buttons": [], "route_refs": []},
            "db_tables": [], "risks": [],
        })["routes"].append(route)
    for view in views:
        module = modules.setdefault(view["module"], {
            "routes": [], "views": [], "auth": [], "ui": {"fields": [], "filters": [], "buttons": [], "route_refs": []},
            "db_tables": [], "risks": [],
        })
        module["views"].append(view["path"])
        for key in ("fields", "filters", "buttons", "route_refs"):
            module["ui"][key] = sorted(set(module["ui"][key] + view[key]))
    for name, module in modules.items():
        auth = sorted({mw for route in module["routes"] for mw in route["middleware"]})
        module["auth"] = auth
        for model in models.values():
            guessed = model["table"].replace("_", "-").rstrip("s")
            if guessed in name or name in guessed:
                module["db_tables"].append(model["table"])
        for route in module["routes"]:
            controller = route.get("controller", "").split("@")[0]
            for model_name in controller_models.get(controller, []):
                if model_name in models:
                    module["db_tables"].append(models[model_name]["table"])
        module["db_tables"] = sorted(set(module["db_tables"]))
        if not module["db_tables"]:
            module["risks"].append("DB table relation is heuristic; verify controller queries and model usage.")

    if args.module != "all":
        modules = {k: v for k, v in modules.items() if k == args.module}

    payload = {
        "source_root": str(root),
        "profile": profile,
        "confidence": "static-scan",
        "dependencies": deps,
        "routes": routes,
        "views": views,
        "models": models,
        "controller_models": controller_models,
        "database": database,
        "modules": modules,
    }

    _write(out / "index.json", json.dumps(payload, indent=2, ensure_ascii=False))
    _write(out / "index.md", _lines("App Migration Extract", [
        f"Source: {root}",
        f"Profile: {profile}",
        f"Modules: {len(modules)}",
        "Scan mode: static read-only; no database connection was opened.",
    ]))
    _write(out / "discovery" / "tech-stack.md", _lines("Tech Stack", deps["composer"] + deps["npm"]))
    _write(out / "discovery" / "route-map.md", _lines("Route Map", [
        f"{r['method']} {r['uri']} -> {r['name'] or r['controller'] or 'unnamed'} [{r['source']}]" for r in routes
    ]))
    _write(out / "discovery" / "menu-map.md", _lines("Menu Map", [
        f"{v['module']}: {v['path']}" for v in views
    ]))
    _write(out / "database" / "schema-summary.md", _lines("Schema Summary", [
        f"{name}: {', '.join(table['columns'].keys()) or 'columns not detected'}"
        for name, table in database["tables"].items()
    ]))
    _write(out / "database" / "table-map.json", json.dumps(database, indent=2, ensure_ascii=False))

    for name, module in sorted(modules.items()):
        base = out / "modules" / name
        _write(base / "overview.md", _lines(f"Module {name}", [
            f"Routes: {len(module['routes'])}",
            f"Views: {len(module['views'])}",
            f"Auth/middleware: {', '.join(module['auth']) or 'not detected'}",
            f"DB tables: {', '.join(module['db_tables']) or 'needs verification'}",
        ]))
        _write(base / "route-flow.md", _lines("Route Flow", [
            f"{r['method']} {r['uri']} -> {r['name'] or r['controller'] or 'unnamed'}" for r in module["routes"]
        ]))
        _write(base / "ui-actions.md", _lines("UI Actions", module["ui"]["buttons"] + module["ui"]["route_refs"]))
        _write(base / "forms-filters.md", _lines("Forms And Filters", module["ui"]["fields"]))
        _write(base / "db-touchpoints.md", _lines("DB Touchpoints", module["db_tables"]))
        _write(base / "api-candidates.md", _lines("API Candidates", [
            f"{r['method']} {r['uri']} from {r['name'] or r['controller'] or 'unnamed'}" for r in module["routes"]
        ]))
        _write(base / "client-surfaces.md", _lines("Client Surfaces", module["views"]))
        _write(base / "risks-and-open-questions.md", _lines("Risks And Open Questions", module["risks"]))

    print(json.dumps({"ok": True, "output": str(out), "modules": len(modules)}, indent=2, ensure_ascii=False))
    return 0


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


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        root = git_root(args.root)
    except SystemExit:
        root = Path(args.root or os.getcwd()).resolve()
    if not (root / "FEATURE-MAP.yaml").is_file():
        print(json.dumps({
            "ok": False,
            "repo_root": str(root),
            "error": "FEATURE-MAP.yaml not found",
        }, indent=2, ensure_ascii=False))
        return 1

    add_plugin_hooks_to_path()
    flows = read_flows(root)
    issues = []
    for name, flow in sorted(flows.items()):
        if not isinstance(flow, dict):
            issues.append({"type": "invalid-flow", "flow": name})
            continue
        for field in LIST_FIELDS:
            if not isinstance(flow.get(field, []), list):
                issues.append({"type": "invalid-list-field", "flow": name, "field": field})
        for tp in flow.get("touchpoints", []):
            if not isinstance(tp, dict):
                issues.append({"type": "invalid-touchpoint", "flow": name})
                continue
            if not tp.get("path"):
                issues.append({"type": "missing-touchpoint-path", "flow": name})
            role = tp.get("role")
            if not role:
                issues.append({"type": "missing-touchpoint-role", "flow": name, "path": tp.get("path", "")})
            elif role not in SUPPORTED_ROLES:
                issues.append({"type": "invalid-role", "flow": name, "role": role})

    payload = {
        "ok": not issues,
        "repo_root": str(root),
        "flows": len(flows),
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

    validate = sub.add_parser("validate", help="Validate FEATURE-MAP.yaml schema shape.")
    validate.add_argument("root", nargs="?", default=None)
    validate.set_defaults(func=cmd_validate)

    extract_app = sub.add_parser("extract-app", help="Extract a read-only app migration pack from an existing codebase.")
    extract_app.add_argument("root")
    extract_app.add_argument("-o", "--output", required=True)
    extract_app.add_argument("--profile", default="auto", choices=["auto", "laravel", "express", "nestjs", "nextjs", "node", "generic"])
    extract_app.add_argument("--module", default="all")
    extract_app.set_defaults(func=cmd_extract_app)

    root = sub.add_parser("plugin-root", help="Print resolved plugin root.")
    root.set_defaults(func=lambda _args: print(plugin_root()) or 0)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
