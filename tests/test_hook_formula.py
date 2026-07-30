import json
import os
import sys

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
