import json
import os
import sys
import types
import builtins

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook

FM = """flows:
  attendance-recap:
    description: "rekap presensi"
    policy: "mode sales beda formula dari mode default"
    mechanics_doc: "docs/flows/attendance-recap.md"
    touchpoints:
      - path: "app/Recap.php"
        role: backend-service
    invariants:
      - "Sanksi = TUM + Alpa"
"""


def test_parse_feature_map_reads_mechanics_doc():
    flows = hook.parse_feature_map(FM)
    assert flows["attendance-recap"]["mechanics_doc"] == "docs/flows/attendance-recap.md"


def test_parse_feature_map_defaults_mechanics_doc_to_empty():
    fm_no_doc = """flows:
  simple:
    description: "flow sederhana"
    policy: "tidak ada"
    touchpoints:
      - path: "app/Simple.php"
        role: backend-service
    invariants:
      - "aturan sederhana"
"""
    flows = hook.parse_feature_map(fm_no_doc)
    assert flows["simple"]["mechanics_doc"] == ""


def test_parse_feature_map_preserves_hash_inside_quoted_values():
    fm = """flows:
  quoted-hash:
    description: "demo # bukan komentar"
    policy: "A # B"
    touchpoints:
      - path: "app/#x.py"
        role: backend-service
        note: "note # tetap"
    invariants:
      - "hash # preserved"
"""

    flow = hook.parse_feature_map(fm)["quoted-hash"]

    assert flow["description"] == "demo # bukan komentar"
    assert flow["policy"] == "A # B"
    assert flow["touchpoints"][0]["note"] == "note # tetap"
    assert flow["invariants"] == ["hash # preserved"]


def test_parse_feature_map_uses_pyyaml_when_available(monkeypatch):
    fake_yaml = types.SimpleNamespace(
        safe_load=lambda text: {
            "flows": {
                "quoted-hash": {
                    "description": "demo # bukan komentar",
                    "touchpoints": [{"path": "app/#x.py", "role": "backend"}],
                    "invariants": ["hash # preserved"],
                }
            }
        }
    )
    monkeypatch.setitem(sys.modules, "yaml", fake_yaml)

    flow = hook.parse_feature_map("flows: {}")["quoted-hash"]

    assert flow["description"] == "demo # bukan komentar"
    assert flow["touchpoints"][0]["path"] == "app/#x.py"


def test_parse_feature_map_falls_back_without_pyyaml(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    flow = hook.parse_feature_map(FM)["attendance-recap"]

    assert flow["description"] == "rekap presensi"
    assert flow["invariants"] == ["Sanksi = TUM + Alpa"]


def test_parse_feature_map_fallback_unescapes_quoted_strings(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    flow = hook.parse_feature_map(
        'flows:\n  sample:\n    invariants:\n      - "Field \\"Tanggal Efektif\\" tetap sama"\n'
    )["sample"]

    assert flow["invariants"] == ['Field "Tanggal Efektif" tetap sama']


def test_detect_formula_change_finds_business_calculation():
    new_string = (
        "$salesTotals['tidak_hadir'] = $salesTotals['tum'] + $salesTotals['alpa'] "
        "+ $salesTotals['as'];\n"
        "$salesTotals['sanksi'] = $salesTotals['tum'] + $salesTotals['alpa'];\n"
        "$foo = $bar;\n"
    )
    hits = hook.detect_formula_change("Edit", {"new_string": new_string})
    assert len(hits) == 2
    assert all("tum" in h.lower() for h in hits)


def test_detect_formula_change_ignores_plain_assignment():
    hits = hook.detect_formula_change("Edit", {"new_string": "$foo = $bar;\n$name = 'John';"})
    assert hits == []


def test_detect_formula_change_reads_multiedit_edits():
    tool_input = {
        "edits": [
            {"new_string": "$x = 1;"},
            {"new_string": "$totalSanksi = $tum + $alpa;"},
        ]
    }
    hits = hook.detect_formula_change("MultiEdit", tool_input)
    assert len(hits) == 1
    assert "totalSanksi" in hits[0]


def test_detect_formula_change_no_tool_input_text_returns_empty():
    assert hook.detect_formula_change("Edit", {}) == []
    assert hook.detect_formula_change("Bash", {"command": "echo hi"}) == []


def test_handle_reminder_includes_mechanics_doc_and_formula_warning(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text(FM)
    file_path = tmp_path / "app" / "Recap.php"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("<?php\n")

    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(file_path),
            "new_string": "$salesTotals['sanksi'] = $salesTotals['tum'] + $salesTotals['alpa'];",
        },
    }
    hook.handle(payload)
    out = json.loads(capsys.readouterr().out)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "docs/flows/attendance-recap.md" in ctx
    assert "RUMUS/KALKULASI BISNIS" in ctx
