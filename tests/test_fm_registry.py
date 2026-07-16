import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import fm_registry


def use_registry(tmp_path, monkeypatch, content=None):
    p = tmp_path / "registry.json"
    if content is not None:
        p.write_text(content)
    monkeypatch.setenv(fm_registry.REGISTRY_ENV, str(p))
    return p


def test_load_missing_returns_default(tmp_path, monkeypatch):
    use_registry(tmp_path, monkeypatch)
    assert fm_registry.load_registry() == {"repos": {}}


def test_load_corrupt_returns_default(tmp_path, monkeypatch):
    use_registry(tmp_path, monkeypatch, "{corrupt")
    assert fm_registry.load_registry() == {"repos": {}}


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    use_registry(tmp_path, monkeypatch)
    fm_registry.save_registry({"repos": {"payo-kurir": "/x/y"}})
    assert fm_registry.load_registry() == {"repos": {"payo-kurir": "/x/y"}}


def test_resolve_known_repo_with_existing_path(tmp_path, monkeypatch):
    repo_dir = tmp_path / "payo"
    repo_dir.mkdir()
    use_registry(tmp_path, monkeypatch,
                 json.dumps({"repos": {"payo-kurir": str(repo_dir)}}))
    assert fm_registry.resolve("payo-kurir") == str(repo_dir)


def test_resolve_unknown_or_missing_path_returns_none(tmp_path, monkeypatch):
    use_registry(tmp_path, monkeypatch,
                 json.dumps({"repos": {"gone": str(tmp_path / "hilang")}}))
    assert fm_registry.resolve("tak-ada") is None
    assert fm_registry.resolve("gone") is None


def test_default_repo_name():
    assert fm_registry.default_repo_name("/a/b/New Payo") == "new-payo"
    assert fm_registry.default_repo_name("/a/PayoKurir") == "payokurir"
