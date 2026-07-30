import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_pending


def test_sanitize_flow_id_replaces_unsafe_chars():
    assert fm_pending.sanitize_flow_id("partner/registration v2") == "partner_registration_v2"
    assert fm_pending.sanitize_flow_id("simple-flow") == "simple-flow"


def test_pending_dir_path(tmp_path):
    assert fm_pending.pending_dir(str(tmp_path)) == str(tmp_path / ".claude" / "feature-map-pending")


def test_write_then_load_all_pending_roundtrip(tmp_path):
    entry = {"flow": "checkout", "file": "app/Checkout.php", "tool_name": "Edit"}
    fm_pending.write_pending(str(tmp_path), "checkout", entry)
    loaded = fm_pending.load_all_pending(str(tmp_path))
    assert loaded == {"checkout": entry}


def test_write_pending_overwrites_not_appends(tmp_path):
    fm_pending.write_pending(str(tmp_path), "checkout", {"file": "a.php"})
    fm_pending.write_pending(str(tmp_path), "checkout", {"file": "b.php"})
    loaded = fm_pending.load_all_pending(str(tmp_path))
    assert loaded == {"checkout": {"file": "b.php"}}


def test_write_pending_adds_gitignore_entry(tmp_path):
    fm_pending.write_pending(str(tmp_path), "checkout", {"file": "a.php"})
    gi = (tmp_path / ".gitignore").read_text()
    assert ".claude/feature-map-pending/" in gi
    fm_pending.write_pending(str(tmp_path), "other", {"file": "b.php"})
    assert (tmp_path / ".gitignore").read_text().count(".claude/feature-map-pending/") == 1


def test_load_all_pending_empty_dir_returns_empty_dict(tmp_path):
    assert fm_pending.load_all_pending(str(tmp_path)) == {}


def test_load_all_pending_skips_corrupt_file(tmp_path):
    fm_pending.write_pending(str(tmp_path), "checkout", {"file": "a.php"})
    d = fm_pending.pending_dir(str(tmp_path))
    with open(os.path.join(d, "broken.json"), "w") as f:
        f.write("{not json")
    loaded = fm_pending.load_all_pending(str(tmp_path))
    assert loaded == {"checkout": {"file": "a.php"}}


def test_clear_pending_removes_file(tmp_path):
    fm_pending.write_pending(str(tmp_path), "checkout", {"file": "a.php"})
    fm_pending.clear_pending(str(tmp_path), "checkout")
    assert fm_pending.load_all_pending(str(tmp_path)) == {}


def test_clear_pending_missing_file_does_not_raise(tmp_path):
    fm_pending.clear_pending(str(tmp_path), "nonexistent")  # must not raise
