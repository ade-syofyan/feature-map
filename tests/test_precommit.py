import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import precommit_check

FM = """flows:
  checkout:
    description: "alur checkout"
    touchpoints:
      - path: "app/checkout/*.py"
        role: backend
      - path: "lib/screens/checkout/*.dart"
        role: mobile
"""


def flows():
    return hook.parse_feature_map(FM)


def test_warns_when_one_role_touched_other_untouched():
    warnings = precommit_check.check(flows(), staged=["app/checkout/cart.py"],
                                     changed_since_sync=["app/checkout/cart.py"])
    assert len(warnings) == 1
    assert "checkout" in warnings[0]
    assert "mobile" in warnings[0]


def test_silent_when_both_roles_staged():
    warnings = precommit_check.check(
        flows(),
        staged=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"],
        changed_since_sync=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"])
    assert warnings == []


def test_silent_when_other_role_changed_since_sync():
    # layer lain sudah diubah di commit sebelumnya (belum di-audit) — jangan berisik
    warnings = precommit_check.check(
        flows(), staged=["app/checkout/cart.py"],
        changed_since_sync=["app/checkout/cart.py", "lib/screens/checkout/cart.dart"])
    assert warnings == []


def test_silent_when_no_touchpoint_staged():
    warnings = precommit_check.check(flows(), staged=["README.md"],
                                     changed_since_sync=["README.md"])
    assert warnings == []


PRECOMMIT_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "hooks", "precommit_check.py")


def _init_repo(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    with open(os.path.join(root, "FEATURE-MAP.yaml"), "w") as f:
        f.write(FM)
    os.makedirs(os.path.join(root, "app", "checkout"), exist_ok=True)
    with open(os.path.join(root, "app", "checkout", "cart.py"), "w") as f:
        f.write("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)


def _stage_change(root, text):
    path = os.path.join(root, "app", "checkout", "cart.py")
    with open(path, "w") as f:
        f.write(text)
    subprocess.run(["git", "add", "app/checkout/cart.py"], cwd=root, check=True)


def _write_pending(root, flow_id="checkout"):
    d = os.path.join(root, ".claude", "feature-map-pending")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{flow_id}.json"), "w") as f:
        json.dump({"flow": flow_id}, f)


def test_blocks_commit_when_pending_drift(tmp_path):
    root = str(tmp_path)
    _init_repo(root)
    _stage_change(root, "x = 2\n")
    _write_pending(root)
    result = subprocess.run(["python3", PRECOMMIT_SCRIPT], cwd=root,
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert "Commit diblokir" in result.stdout


def test_ack_env_overrides_block(tmp_path):
    root = str(tmp_path)
    _init_repo(root)
    _stage_change(root, "x = 2\n")
    _write_pending(root)
    env = dict(os.environ, FEATURE_MAP_ACK="1")
    result = subprocess.run(["python3", PRECOMMIT_SCRIPT], cwd=root,
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0


def test_no_block_when_no_pending(tmp_path):
    root = str(tmp_path)
    _init_repo(root)
    _stage_change(root, "x = 2\n")
    result = subprocess.run(["python3", PRECOMMIT_SCRIPT], cwd=root,
                            capture_output=True, text=True)
    assert result.returncode == 0


def test_stale_pending_for_unrelated_flow_does_not_block(tmp_path):
    # Pending drift ada untuk 'checkout', tapi commit ini cuma menyentuh file
    # yang bukan touchpoint flow manapun -- jangan sampai commit tidak
    # berhubungan ini ikut diblokir oleh drift lama.
    root = str(tmp_path)
    _init_repo(root)
    with open(os.path.join(root, "README.md"), "w") as f:
        f.write("notes\n")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    _write_pending(root, flow_id="checkout")
    result = subprocess.run(["python3", PRECOMMIT_SCRIPT], cwd=root,
                            capture_output=True, text=True)
    assert result.returncode == 0


def test_orphaned_pending_flow_not_in_registry_does_not_block(tmp_path):
    # File pending untuk flow yang sudah tidak ada di FEATURE-MAP.yaml (mis.
    # flow dihapus/di-rename) tidak boleh memblokir commit lain selamanya.
    root = str(tmp_path)
    _init_repo(root)
    _stage_change(root, "x = 2\n")
    _write_pending(root, flow_id="flow-yang-sudah-dihapus")
    result = subprocess.run(["python3", PRECOMMIT_SCRIPT], cwd=root,
                            capture_output=True, text=True)
    assert result.returncode == 0
