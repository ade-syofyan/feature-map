import os
import sys
import json

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "codex-skill",
        "feature-map",
        "scripts",
    ),
)
import feature_map_cli


def test_plugin_root_ignores_parent_directory_without_hooks(monkeypatch, tmp_path):
    parent = tmp_path / "claude-plugins"
    parent.mkdir()
    skill_root = tmp_path / "skill"
    monkeypatch.setattr(feature_map_cli, "REPO_PLUGIN_ROOT", parent)
    monkeypatch.setattr(feature_map_cli, "CODEX_SKILL_ROOT", skill_root)
    monkeypatch.setattr(feature_map_cli, "SOURCE_REPO_ROOT", tmp_path / "missing")
    monkeypatch.setattr(feature_map_cli, "latest_cache_root", lambda: None)
    monkeypatch.delenv("FEATURE_MAP_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    assert feature_map_cli.plugin_root() == skill_root


def test_plugin_root_ignores_invalid_env_root(monkeypatch, tmp_path):
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    skill_root = tmp_path / "skill"
    monkeypatch.setattr(feature_map_cli, "REPO_PLUGIN_ROOT", invalid)
    monkeypatch.setattr(feature_map_cli, "CODEX_SKILL_ROOT", skill_root)
    monkeypatch.setattr(feature_map_cli, "SOURCE_REPO_ROOT", tmp_path / "missing")
    monkeypatch.setattr(feature_map_cli, "latest_cache_root", lambda: None)
    monkeypatch.setenv("FEATURE_MAP_PLUGIN_ROOT", str(invalid))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    assert feature_map_cli.plugin_root() == skill_root


def test_plugin_root_finds_source_repo_hooks_before_cache(monkeypatch, tmp_path):
    source_root = tmp_path / "feature-map"
    hooks = source_root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "feature_map_hook.py").write_text("")
    cache_root = tmp_path / "cache"
    (cache_root / "hooks").mkdir(parents=True)
    (cache_root / "hooks" / "feature_map_hook.py").write_text("")
    monkeypatch.setattr(feature_map_cli, "REPO_PLUGIN_ROOT", tmp_path / "missing")
    monkeypatch.setattr(feature_map_cli, "SOURCE_REPO_ROOT", source_root)
    monkeypatch.setattr(feature_map_cli, "CODEX_SKILL_ROOT", tmp_path / "skill")
    monkeypatch.setattr(feature_map_cli, "latest_cache_root", lambda: cache_root)
    monkeypatch.delenv("FEATURE_MAP_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    assert feature_map_cli.plugin_root() == source_root


def test_plugin_root_uses_installed_marker_before_cache(monkeypatch, tmp_path):
    source_root = tmp_path / "feature-map"
    hooks = source_root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "feature_map_hook.py").write_text("")
    skill_root = tmp_path / "skill"
    skill_root.mkdir()
    (skill_root / "plugin-root.txt").write_text(str(source_root))
    cache_root = tmp_path / "cache"
    (cache_root / "hooks").mkdir(parents=True)
    (cache_root / "hooks" / "feature_map_hook.py").write_text("")
    monkeypatch.setattr(feature_map_cli, "CODEX_SKILL_ROOT", skill_root)
    monkeypatch.setattr(feature_map_cli, "REPO_PLUGIN_ROOT", tmp_path / "missing")
    monkeypatch.setattr(feature_map_cli, "SOURCE_REPO_ROOT", tmp_path / "missing-source")
    monkeypatch.setattr(feature_map_cli, "latest_cache_root", lambda: cache_root)
    monkeypatch.delenv("FEATURE_MAP_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    assert feature_map_cli.plugin_root() == source_root


def test_doctor_reports_install_health(monkeypatch, tmp_path, capsys):
    source_root = tmp_path / "feature-map"
    hooks = source_root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "feature_map_hook.py").write_text("")
    manifest = source_root / ".claude-plugin"
    manifest.mkdir()
    (manifest / "plugin.json").write_text('{"version": "0.10.3"}')
    monkeypatch.setattr(feature_map_cli, "SOURCE_REPO_ROOT", source_root)
    monkeypatch.setattr(feature_map_cli, "REPO_PLUGIN_ROOT", tmp_path / "missing")
    monkeypatch.setattr(feature_map_cli, "CODEX_SKILL_ROOT", tmp_path / "skill")
    monkeypatch.setattr(feature_map_cli, "latest_cache_root", lambda: None)
    monkeypatch.setattr(feature_map_cli, "add_plugin_hooks_to_path", lambda: source_root)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

    assert feature_map_cli.cmd_doctor(type("Args", (), {})()) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["plugin_root"] == str(source_root)
    assert payload["checks"]["hooks_available"] is True
    assert payload["checks"]["parser_sample"] is True
    assert payload["checks"]["blueprint_sample"] is True
    assert payload["version"] == "0.10.3"


def test_quality_report_flags_placeholder_dead_and_missing_rules(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text(
        'flows:\n'
        '  payroll:\n'
        '    description: "Payroll"\n'
        '    confidence: draft\n'
        '    touchpoints:\n'
        '      - path: "app/**/payroll/**"\n'
        '        role: backend-service\n'
        '        note: "Placeholder backend path"\n'
        '      - path: "resources/views/payroll/index.blade.php"\n'
        '        role: admin-view\n'
        '    invariants: []\n'
        '  attendance:\n'
        '    description: "Attendance"\n'
        '    touchpoints:\n'
        '      - path: "app/Attendance.php"\n'
        '        role: backend-service\n'
        '    invariants:\n'
        '      - "Attendance status must match reports"\n'
    )
    app = tmp_path / "app"
    app.mkdir()
    (app / "Attendance.php").write_text("<?php\n")

    assert feature_map_cli.cmd_quality(type("Args", (), {"root": str(tmp_path)})()) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert payload["flows"] == 2
    assert payload["summary"]["draft_flows"] == 1
    assert payload["summary"]["placeholder_touchpoints"] == 1
    assert payload["summary"]["dead_touchpoints"] == 2
    assert payload["summary"]["missing_invariants"] == 1


def test_quality_report_ok_for_resolved_map(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text(
        'flows:\n'
        '  attendance:\n'
        '    description: "Attendance"\n'
        '    policy: "Follow attendance policy"\n'
        '    touchpoints:\n'
        '      - path: "app/Attendance.php"\n'
        '        role: backend-service\n'
        '    invariants:\n'
        '      - "Attendance status must match reports"\n'
    )
    app = tmp_path / "app"
    app.mkdir()
    (app / "Attendance.php").write_text("<?php\n")

    assert feature_map_cli.cmd_quality(type("Args", (), {"root": str(tmp_path)})()) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["issues"] == []


def test_quality_report_requires_feature_map(tmp_path, capsys):
    assert feature_map_cli.cmd_quality(type("Args", (), {"root": str(tmp_path)})()) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert payload["error"] == "FEATURE-MAP.yaml not found"


def test_validate_report_flags_schema_errors(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text(
        'flows:\n'
        '  payroll:\n'
        '    description: "Payroll"\n'
        '    touchpoints:\n'
        '      - path: "app/Payroll.php"\n'
        '        role: service-ish\n'
        '      - role: backend-service\n'
        '    invariants: "not-a-list"\n'
    )

    assert feature_map_cli.cmd_validate(type("Args", (), {"root": str(tmp_path)})()) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert {"type": "invalid-role", "flow": "payroll", "role": "service-ish"} in payload["issues"]
    assert {"type": "missing-touchpoint-path", "flow": "payroll"} in payload["issues"]
    assert {"type": "invalid-list-field", "flow": "payroll", "field": "invariants"} in payload["issues"]


def test_validate_report_ok_for_supported_schema(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text(
        'flows:\n'
        '  attendance:\n'
        '    description: "Attendance"\n'
        '    touchpoints:\n'
        '      - path: "app/Attendance.php"\n'
        '        role: backend-service\n'
        '    invariants:\n'
        '      - "Attendance status must match reports"\n'
    )

    assert feature_map_cli.cmd_validate(type("Args", (), {"root": str(tmp_path)})()) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["issues"] == []


def test_extract_app_writes_laravel_migration_pack(tmp_path, capsys):
    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"php": "^8.2", "laravel/framework": "^11.0"}})
    )
    routes = tmp_path / "routes"
    routes.mkdir()
    (routes / "web.php").write_text(
        "<?php\n"
        "Route::middleware(['auth'])->group(function () {\n"
        "    Route::get('/pos', [PosController::class, 'index'])->name('pos.index');\n"
        "    Route::post('/pos', [PosController::class, 'store'])->name('pos.store');\n"
        "});\n"
    )
    controller = tmp_path / "app" / "Http" / "Controllers"
    controller.mkdir(parents=True)
    (controller / "PosController.php").write_text(
        "<?php\n"
        "class PosController {\n"
        "  public function index() { return view('page.pos.index'); }\n"
        "  public function store(StoreSaleRequest $request) { Sale::create($request->validated()); }\n"
        "}\n"
    )
    model = tmp_path / "app" / "Models"
    model.mkdir(parents=True)
    (model / "Sale.php").write_text(
        "<?php\n"
        "class Sale extends Model { protected $table = 'sales'; protected $casts = ['sold_at' => 'datetime']; }\n"
    )
    migrations = tmp_path / "database" / "migrations"
    migrations.mkdir(parents=True)
    (migrations / "2026_01_01_000000_create_sales_table.php").write_text(
        "<?php\n"
        "Schema::create('sales', function (Blueprint $table) {\n"
        "  $table->id();\n"
        "  $table->string('invoice_no');\n"
        "  $table->decimal('total', 12, 2);\n"
        "  $table->dateTime('sold_at');\n"
        "});\n"
    )
    view = tmp_path / "resources" / "views" / "page" / "pos"
    view.mkdir(parents=True)
    (view / "index.blade.php").write_text(
        "<form method=\"GET\" action=\"{{ route('pos.index') }}\">\n"
        "  <input name=\"search\">\n"
        "  <select name=\"status\"></select>\n"
        "</form>\n"
        "<form method=\"POST\" action=\"{{ route('pos.store') }}\">\n"
        "  <input name=\"invoice_no\">\n"
        "  <button type=\"submit\">Save</button>\n"
        "</form>\n"
    )

    out = tmp_path / "extract"
    args = type("Args", (), {
        "root": str(tmp_path),
        "output": str(out),
        "profile": "laravel",
        "module": "all",
    })()

    assert feature_map_cli.cmd_extract_app(args) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["output"] == str(out)
    assert (out / "index.json").is_file()
    assert (out / "index.md").is_file()
    assert (out / "modules" / "pos" / "overview.md").is_file()
    assert (out / "modules" / "pos" / "ui-actions.md").is_file()
    assert (out / "database" / "schema-summary.md").is_file()

    data = json.loads((out / "index.json").read_text())
    pos = data["modules"]["pos"]
    assert "/pos" in [route["uri"] for route in pos["routes"]]
    assert "auth" in pos["auth"]
    assert "search" in pos["ui"]["fields"]
    assert "status" in pos["ui"]["filters"]
    assert "sales" in pos["db_tables"]
    assert data["database"]["tables"]["sales"]["columns"]["total"]["type"] == "decimal"


def test_extract_app_supports_non_php_node_routes(tmp_path, capsys):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"express": "^4.18.0", "zod": "^3.0.0"}})
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.ts").write_text(
        "import express from 'express';\n"
        "const router = express.Router();\n"
        "router.get('/orders', listOrders);\n"
        "router.post('/orders/:id/approve', approveOrder);\n"
    )
    (src / "OrdersPage.tsx").write_text(
        "<form><input name=\"search\" /><button>Approve</button></form>"
    )
    out = tmp_path / "extract"
    args = type("Args", (), {
        "root": str(tmp_path),
        "output": str(out),
        "profile": "auto",
        "module": "all",
    })()

    assert feature_map_cli.cmd_extract_app(args) == 0
    payload = json.loads(capsys.readouterr().out)
    data = json.loads((out / "index.json").read_text())

    assert payload["ok"] is True
    assert data["profile"] == "express"
    assert "orders" in data["modules"]
    assert "/orders" in [route["uri"] for route in data["modules"]["orders"]["routes"]]
    assert "search" in data["modules"]["orders"]["ui"]["fields"]


def test_extract_app_laravel_does_not_leak_group_middleware_or_treat_controllers_as_views(tmp_path, capsys):
    (tmp_path / "composer.json").write_text(
        json.dumps({"require": {"laravel/framework": "^11.0"}})
    )
    routes = tmp_path / "routes"
    routes.mkdir()
    (routes / "web.php").write_text(
        "<?php\n"
        "Route::middleware(['auth'])->group(function () {\n"
        "    Route::get('/private', [PrivateController::class, 'index'])->name('private.index');\n"
        "});\n"
        "Route::get('/public', [PublicController::class, 'index'])->name('public.index');\n"
    )
    controller = tmp_path / "app" / "Http" / "Controllers"
    controller.mkdir(parents=True)
    (controller / "PublicController.php").write_text(
        "<?php\n"
        "class PublicController { public function index() { return '<input name=\"not_a_view\">'; } }\n"
    )
    view = tmp_path / "resources" / "views" / "page" / "private"
    view.mkdir(parents=True)
    (view / "index.blade.php").write_text("<input name=\"search\">")

    out = tmp_path / "extract"
    args = type("Args", (), {
        "root": str(tmp_path),
        "output": str(out),
        "profile": "laravel",
        "module": "all",
    })()

    assert feature_map_cli.cmd_extract_app(args) == 0
    data = json.loads((out / "index.json").read_text())
    public_route = next(route for route in data["routes"] if route["uri"] == "/public")

    assert public_route["middleware"] == []
    assert all("app/Http/Controllers/PublicController.php" != view["path"] for view in data["views"])
    assert "not_a_view" not in data["modules"]["public"]["ui"]["fields"]
