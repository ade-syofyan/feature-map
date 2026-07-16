import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_hook as hook
import fm_state

FM = """flows:
  checkout:
    description: "alur checkout"
    policy: "ongkir gratis di atas 100k"
    touchpoints:
      - path: "app/checkout/*.py"
        role: backend
      - path: "lib/screens/checkout/*.dart"
        role: mobile
"""


def make_repo(tmp_path):
    (tmp_path / "FEATURE-MAP.yaml").write_text(FM)
    return str(tmp_path)


def test_match_flows_maps_paths_to_flow():
    flows = hook.parse_feature_map(FM)
    hits = hook.match_flows(flows, ["app/checkout/cart.py", "README.md"])
    assert hits == {"checkout": ["app/checkout/cart.py"]}


def test_edit_event_marks_flow_stale(tmp_path, capsys):
    root = make_repo(tmp_path)
    payload = {
        "tool_input": {"file_path": os.path.join(root, "app/checkout/cart.py")},
        "cwd": root,
    }
    hook.handle(payload)
    state = fm_state.load_state(root)
    assert state["flows"]["checkout"]["status"] == "stale"
    assert "app/checkout/cart.py" in state["flows"]["checkout"]["dirty_files"]
    out = capsys.readouterr().out  # reminder lama tetap jalan
    assert "checkout" in out


def test_git_changed_files_detects_commits_and_worktree(tmp_path):
    root = make_repo(tmp_path)
    run = lambda *a: subprocess.run(a, cwd=root, check=True, capture_output=True)
    run("git", "init", "-q")
    run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
        "--allow-empty", "-m", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                          capture_output=True, text=True).stdout.strip()
    os.makedirs(os.path.join(root, "app/checkout"), exist_ok=True)
    with open(os.path.join(root, "app/checkout/cart.py"), "w") as f:
        f.write("x = 1\n")
    run("git", "add", ".")
    run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "c1")
    with open(os.path.join(root, "uncommitted.py"), "w") as f:
        f.write("y = 2\n")
    changed = hook.git_changed_files(root, base)
    assert "app/checkout/cart.py" in changed
    assert "uncommitted.py" in changed


def test_bash_event_initializes_sha_without_stale(tmp_path):
    root = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "base"],
                   cwd=root, check=True)
    hook.handle({"tool_input": {"command": "git pull"}, "cwd": root})
    state = fm_state.load_state(root)
    assert state["last_synced_sha"] is not None
    assert state["flows"] == {}


def test_git_changed_files_rejects_malicious_sha(tmp_path):
    root = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    # SHA berbahaya tidak boleh diteruskan sebagai argumen git
    changed = hook.git_changed_files(root, "--upload-pack=/bin/evil")
    assert isinstance(changed, list)
    assert hook.is_valid_sha("abc123")
    assert not hook.is_valid_sha("--upload-pack=/bin/evil")
    assert not hook.is_valid_sha("a" * 41)
