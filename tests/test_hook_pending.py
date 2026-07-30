import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import fm_pending

FM = """flows:
  attendance-recap:
    description: "rekap presensi"
    policy: "mode sales beda formula dari mode default"
    touchpoints:
      - path: "app/Recap.php"
        role: backend-service
    invariants:
      - "Sanksi = TUM + Alpa"
"""


def _setup(tmp_path):
    (tmp_path / "FEATURE-MAP.yaml").write_text(FM)
    file_path = tmp_path / "app" / "Recap.php"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("<?php\n")
    return file_path


def test_handle_writes_pending_entry_for_edit(tmp_path, capsys):
    file_path = _setup(tmp_path)
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(file_path),
            "old_string": "$x = 1;",
            "new_string": "$x = 2;",
        },
    }
    hook.handle(payload)
    capsys.readouterr()  # drain stdout reminder, not under test here

    pending = fm_pending.load_all_pending(str(tmp_path))
    assert "attendance-recap" in pending
    entry = pending["attendance-recap"]
    assert entry["file"] == str(file_path)
    assert entry["role"] == "backend-service"
    assert entry["tool_name"] == "Edit"
    assert entry["diff"] == {"old_string": "$x = 1;", "new_string": "$x = 2;"}
    assert entry["current_policy"] == "mode sales beda formula dari mode default"
    assert entry["current_invariants"] == ["Sanksi = TUM + Alpa"]
    assert entry["timestamp"].endswith("Z")


def test_handle_overwrites_pending_entry_on_second_edit(tmp_path):
    file_path = _setup(tmp_path)
    payload1 = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(file_path), "old_string": "a", "new_string": "b"},
    }
    payload2 = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(file_path), "old_string": "b", "new_string": "c"},
    }
    hook.handle(payload1)
    hook.handle(payload2)
    pending = fm_pending.load_all_pending(str(tmp_path))
    assert pending["attendance-recap"]["diff"] == {"old_string": "b", "new_string": "c"}


def test_handle_pending_entry_for_multiedit(tmp_path):
    file_path = _setup(tmp_path)
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": str(file_path),
            "edits": [{"old_string": "a", "new_string": "b"}],
        },
    }
    hook.handle(payload)
    pending = fm_pending.load_all_pending(str(tmp_path))
    assert pending["attendance-recap"]["diff"] == {"edits": [{"old_string": "a", "new_string": "b"}]}


def test_handle_pending_entry_for_bash_no_file_path_skips(tmp_path):
    _setup(tmp_path)
    payload = {"cwd": str(tmp_path), "tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    hook.handle(payload)
    assert fm_pending.load_all_pending(str(tmp_path)) == {}


def test_handle_no_touchpoint_hit_writes_no_pending(tmp_path):
    (tmp_path / "FEATURE-MAP.yaml").write_text(FM)
    other = tmp_path / "unrelated.php"
    other.write_text("<?php\n")
    payload = {
        "cwd": str(tmp_path),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(other), "old_string": "a", "new_string": "b"},
    }
    hook.handle(payload)
    assert fm_pending.load_all_pending(str(tmp_path)) == {}
