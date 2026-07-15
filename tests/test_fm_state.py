import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_state


def test_load_state_missing_returns_default(tmp_path):
    state = fm_state.load_state(str(tmp_path))
    assert state == {"last_synced_sha": None, "flows": {}}


def test_save_then_load_roundtrip(tmp_path):
    state = {"last_synced_sha": "abc123", "flows": {}}
    fm_state.save_state(str(tmp_path), state)
    assert fm_state.load_state(str(tmp_path)) == state
    assert (tmp_path / ".feature-map" / "state.json").is_file()


def test_save_adds_gitignore_entry(tmp_path):
    fm_state.save_state(str(tmp_path), {"last_synced_sha": None, "flows": {}})
    gi = (tmp_path / ".gitignore").read_text()
    assert ".feature-map/" in gi
    # tidak dobel kalau save lagi
    fm_state.save_state(str(tmp_path), {"last_synced_sha": None, "flows": {}})
    assert (tmp_path / ".gitignore").read_text().count(".feature-map/") == 1


def test_mark_stale_sets_status_and_dedupes_files(tmp_path):
    fm_state.mark_stale(str(tmp_path), {"checkout": ["a.dart"]})
    fm_state.mark_stale(str(tmp_path), {"checkout": ["a.dart", "b.py"]})
    flow = fm_state.load_state(str(tmp_path))["flows"]["checkout"]
    assert flow["status"] == "stale"
    assert sorted(flow["dirty_files"]) == ["a.dart", "b.py"]
    assert flow["marked_at"].endswith("Z")


def test_mark_clean_clears_and_updates_sha(tmp_path):
    fm_state.mark_stale(str(tmp_path), {"checkout": ["a.dart"]})
    fm_state.mark_clean(str(tmp_path), ["checkout"], "def456")
    state = fm_state.load_state(str(tmp_path))
    assert state["last_synced_sha"] == "def456"
    assert state["flows"]["checkout"]["status"] == "clean"
    assert state["flows"]["checkout"]["dirty_files"] == []


def test_load_corrupt_state_returns_default(tmp_path):
    d = tmp_path / ".feature-map"
    d.mkdir()
    (d / "state.json").write_text("{corrupt")
    assert fm_state.load_state(str(tmp_path)) == {"last_synced_sha": None, "flows": {}}
