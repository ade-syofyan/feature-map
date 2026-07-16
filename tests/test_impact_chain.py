import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import fm_registry
import fm_state

FM = """flows:
  lembur:
    policy: "lembur >2 jam butuh approval"
    impacts: [approval]
    touchpoints:
      - path: "hr/lembur/*.py"
        role: backend
  approval:
    impacts: [pembayaran]
    touchpoints:
      - path: "hr/approval/*.py"
        role: backend
  pembayaran:
    impacts: [lembur]
    touchpoints:
      - path: "fin/pay/*.py"
        role: backend
        repo: payo-fin
"""


def test_expand_impacts_transitive_with_via():
    flows = hook.parse_feature_map(FM)
    expanded, chains = hook.expand_impacts(flows, {"lembur": ["hr/lembur/calc.py"]})
    assert expanded["lembur"] == ["hr/lembur/calc.py"]
    assert expanded["approval"] == ["via:lembur"]
    assert expanded["pembayaran"] == ["via:approval"]
    assert chains == {"lembur": ["approval", "pembayaran"]}


def test_expand_impacts_cycle_safe_and_unknown_skipped():
    flows = hook.parse_feature_map(
        "flows:\n"
        "  a:\n    impacts: [b, tak-dikenal]\n"
        "  b:\n    impacts: [a]\n")
    expanded, chains = hook.expand_impacts(flows, {"a": ["x.py"]})
    assert set(expanded) == {"a", "b"}
    assert chains == {"a": ["b"]}


def test_expand_impacts_depth_capped():
    text = "flows:\n"
    for i in range(8):
        text += f"  f{i}:\n    impacts: [f{i+1}]\n"
    text += "  f8:\n    description: \"ujung\"\n"
    flows = hook.parse_feature_map(text)
    expanded, _ = hook.expand_impacts(flows, {"f0": ["x.py"]})
    # kedalaman 5: f0 (asal) + f1..f5
    assert set(expanded) == {"f0", "f1", "f2", "f3", "f4", "f5"}


def test_edit_marks_impact_chain_stale_and_propagates_repo(tmp_path, monkeypatch, capsys):
    repo_a = tmp_path / "repo-a"
    repo_fin = tmp_path / "payo-fin"
    repo_a.mkdir(); repo_fin.mkdir()
    (repo_a / "FEATURE-MAP.yaml").write_text(FM)
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"repos": {"payo-fin": str(repo_fin)}}))
    monkeypatch.setenv(fm_registry.REGISTRY_ENV, str(reg))

    hook.handle({"tool_input": {"file_path": os.path.join(str(repo_a), "hr/lembur/calc.py")},
                 "cwd": str(repo_a)})

    state_a = fm_state.load_state(str(repo_a))
    assert state_a["flows"]["lembur"]["status"] == "stale"
    assert state_a["flows"]["approval"]["dirty_files"] == ["via:lembur"]
    assert state_a["flows"]["pembayaran"]["dirty_files"] == ["via:approval"]
    # flow turunan 'pembayaran' ber-touchpoint repo payo-fin -> ikut dipropagasi
    state_fin = fm_state.load_state(str(repo_fin))
    assert state_fin["flows"]["pembayaran"]["status"] == "stale"
    # reminder menyebut rantai dampak
    out = capsys.readouterr().out
    assert "berdampak ke: approval → pembayaran" in out
