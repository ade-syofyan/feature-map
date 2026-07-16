import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import fm_registry
import fm_state

FM_A = """flows:
  daftar-kurir:
    description: "pendaftaran kurir"
    policy: "field KTP wajib"
    touchpoints:
      - path: "app/api/*.py"
        role: backend
      - path: "lib/screens/*.dart"
        role: mobile
        repo: payo-kurir
"""


def two_repos(tmp_path, monkeypatch, register=True):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "payo-kurir"
    repo_a.mkdir(); repo_b.mkdir()
    (repo_a / "FEATURE-MAP.yaml").write_text(FM_A)
    reg = tmp_path / "registry.json"
    if register:
        reg.write_text(json.dumps({"repos": {"payo-kurir": str(repo_b)}}))
    monkeypatch.setenv(fm_registry.REGISTRY_ENV, str(reg))
    return str(repo_a), str(repo_b)


def test_match_flows_ignores_remote_touchpoints():
    flows = hook.parse_feature_map(FM_A)
    # file dart cocok dengan touchpoint ber-repo -> tidak dianggap milik repo ini
    assert hook.match_flows(flows, ["lib/screens/reg.dart"]) == {}
    assert hook.match_flows(flows, ["app/api/couriers.py"]) == \
        {"daftar-kurir": ["app/api/couriers.py"]}


def test_edit_propagates_stale_to_other_repo(tmp_path, monkeypatch):
    repo_a, repo_b = two_repos(tmp_path, monkeypatch)
    hook.handle({"tool_input": {"file_path": os.path.join(repo_a, "app/api/couriers.py")},
                 "cwd": repo_a})
    state_b = fm_state.load_state(repo_b)
    assert state_b["flows"]["daftar-kurir"]["status"] == "stale"
    assert state_b["flows"]["daftar-kurir"]["dirty_files"] == \
        ["repo-a:app/api/couriers.py"]
    # repo sendiri juga stale
    assert fm_state.load_state(repo_a)["flows"]["daftar-kurir"]["status"] == "stale"


def test_reminder_mentions_resolved_repo_path(tmp_path, monkeypatch, capsys):
    repo_a, repo_b = two_repos(tmp_path, monkeypatch)
    hook.handle({"tool_input": {"file_path": os.path.join(repo_a, "app/api/couriers.py")},
                 "cwd": repo_a})
    out = capsys.readouterr().out
    assert "payo-kurir" in out
    assert repo_b in out


def test_reminder_suggests_register_when_unresolved(tmp_path, monkeypatch, capsys):
    repo_a, _ = two_repos(tmp_path, monkeypatch, register=False)
    hook.handle({"tool_input": {"file_path": os.path.join(repo_a, "app/api/couriers.py")},
                 "cwd": repo_a})
    out = capsys.readouterr().out
    assert "belum terdaftar" in out
