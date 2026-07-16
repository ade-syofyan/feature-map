import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook


def test_impacts_inline_list():
    flows = hook.parse_feature_map(
        "flows:\n"
        "  lembur:\n"
        "    description: \"lembur\"\n"
        "    impacts: [pengajuan-approval, pembayaran-gaji]\n"
        "    touchpoints:\n"
        "      - path: \"a/*.py\"\n"
        "        role: backend\n")
    assert flows["lembur"]["impacts"] == ["pengajuan-approval", "pembayaran-gaji"]
    assert len(flows["lembur"]["touchpoints"]) == 1


def test_impacts_multiline_list():
    flows = hook.parse_feature_map(
        "flows:\n"
        "  lembur:\n"
        "    impacts:\n"
        "      - pengajuan-approval\n"
        "      - \"pembayaran-gaji\"\n"
        "    invariants:\n"
        "      - \"inv1\"\n")
    assert flows["lembur"]["impacts"] == ["pengajuan-approval", "pembayaran-gaji"]
    assert flows["lembur"]["invariants"] == ["inv1"]


def test_impacts_absent_defaults_empty():
    flows = hook.parse_feature_map(
        "flows:\n  checkout:\n    description: \"x\"\n")
    assert flows["checkout"]["impacts"] == []
