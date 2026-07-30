import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_stop as stop
import fm_pending


def test_no_feature_map_yaml_produces_no_output(tmp_path, capsys):
    stop.handle({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_no_pending_files_produces_no_output(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text("flows:\n")
    stop.handle({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_pending_files_produce_reminder(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text("flows:\n")
    fm_pending.write_pending(str(tmp_path), "checkout", {"flow": "checkout"})
    fm_pending.write_pending(str(tmp_path), "attendance-recap", {"flow": "attendance-recap"})
    stop.handle({"cwd": str(tmp_path)})
    out = json.loads(capsys.readouterr().out)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "attendance-recap" in ctx
    assert "checkout" in ctx
    assert "flow-sync-apply" in ctx
    assert "decision" not in out
