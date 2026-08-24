import os
import sys

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
