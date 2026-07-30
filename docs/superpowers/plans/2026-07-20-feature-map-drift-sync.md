# feature-map Semi-Automatic Drift Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture business-flow drift as it happens (PostToolUse) into a small pending-state store, remind the agent at end-of-turn (Stop) if anything is unsynced, and provide a `/feature-map:flow-sync-apply` command that turns pending drift into reviewed `FEATURE-MAP.yaml` edits.

**Architecture:** New `hooks/fm_pending.py` module (same load/save-safe pattern as `fm_state.py`) stores one JSON file per flow under `.claude/feature-map-pending/`. `feature_map_hook.py`'s existing PostToolUse `handle()` writes/overwrites that file whenever it finds a touchpoint hit. A new `feature_map_stop.py` Stop hook reads pending files and emits a reminder if any exist. A new `commands/flow-sync-apply.md` slash-command instructs the agent to read pending files, draft invariant/policy text, apply it via `Edit` on `FEATURE-MAP.yaml`, then delete the pending file.

**Tech Stack:** Python 3 stdlib only (json, os, tempfile) — no external dependencies, matching the rest of `hooks/`. Tests via pytest, matching `tests/test_fm_state.py` conventions.

## Global Constraints

- No hook script calls a model or writes to `FEATURE-MAP.yaml` directly — only the agent does that, via the `Edit` tool, per the spec's Safety section.
- Pending files use overwrite semantics — one file per flow, replaced (not appended) on each matching edit.
- `.claude/feature-map-pending/` must be added to `.gitignore` automatically, same as `fm_state.py` does for `.feature-map/`.
- All `fm_pending.py` functions must swallow I/O errors (never raise) — this runs inside a hook subprocess where an uncaught exception breaks the tool call.
- Stop hook must be non-blocking: never emit `"decision": "block"`.

---

### Task 1: `fm_pending.py` — pending-state storage module

**Files:**
- Create: `hooks/fm_pending.py`
- Test: `tests/test_fm_pending.py`

**Interfaces:**
- Produces (used by Task 2 and Task 3):
  - `fm_pending.pending_dir(root: str) -> str` — returns `<root>/.claude/feature-map-pending`
  - `fm_pending.sanitize_flow_id(name: str) -> str` — replaces any char outside `[A-Za-z0-9_-]` with `_`
  - `fm_pending.write_pending(root: str, flow_id: str, entry: dict) -> None` — atomic overwrite of `<flow_id>.json`, ensures `.gitignore` has `.claude/feature-map-pending/`
  - `fm_pending.load_all_pending(root: str) -> dict[str, dict]` — `{flow_id: entry}` for every valid JSON file in the pending dir; skips corrupt files
  - `fm_pending.clear_pending(root: str, flow_id: str) -> None` — best-effort `os.remove`, swallows `FileNotFoundError`/`OSError`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fm_pending.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_fm_pending.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'fm_pending'`

- [ ] **Step 3: Implement `hooks/fm_pending.py`**

```python
#!/usr/bin/env python3
"""State drift pending per-flow untuk feature-map: satu file JSON per flow di
.claude/feature-map-pending/<flow-id>.json. Dipakai PostToolUse hook untuk
menyimpan konteks perubahan, dan command /feature-map:flow-sync-apply untuk
membacanya lalu merangkum jadi invariant/policy baru di FEATURE-MAP.yaml.

Semua fungsi aman dipanggil dari hook: kegagalan I/O tidak melempar keluar.
"""
import json
import os
import re
import tempfile

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_-]")


def sanitize_flow_id(name):
    return _UNSAFE_CHARS.sub("_", name)


def pending_dir(root):
    return os.path.join(root, ".claude", "feature-map-pending")


def _ensure_gitignore(root):
    gi_path = os.path.join(root, ".gitignore")
    try:
        existing = ""
        if os.path.isfile(gi_path):
            with open(gi_path, encoding="utf-8") as f:
                existing = f.read()
        if ".claude/feature-map-pending/" in existing:
            return
        with open(gi_path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(".claude/feature-map-pending/\n")
    except Exception:
        pass


def write_pending(root, flow_id, entry):
    try:
        d = pending_dir(root)
        os.makedirs(d, exist_ok=True)
        _ensure_gitignore(root)
        safe_id = sanitize_flow_id(flow_id)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        os.replace(tmp, os.path.join(d, f"{safe_id}.json"))
    except Exception:
        pass


def load_all_pending(root):
    result = {}
    d = pending_dir(root)
    try:
        names = os.listdir(d)
    except Exception:
        return result
    for name in names:
        if not name.endswith(".json"):
            continue
        flow_id = name[:-len(".json")]
        try:
            with open(os.path.join(d, name), encoding="utf-8") as f:
                result[flow_id] = json.load(f)
        except Exception:
            continue
    return result


def clear_pending(root, flow_id):
    safe_id = sanitize_flow_id(flow_id)
    try:
        os.remove(os.path.join(pending_dir(root), f"{safe_id}.json"))
    except Exception:
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_fm_pending.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add hooks/fm_pending.py tests/test_fm_pending.py
git commit -m "feat: add fm_pending module for feature-map drift state"
```

---

### Task 2: Extend `feature_map_hook.py` to write pending drift on touchpoint hits

**Files:**
- Modify: `hooks/feature_map_hook.py:16-18` (imports), `hooks/feature_map_hook.py:329-378` (inside `handle()`, the `hits` loop)
- Test: `tests/test_hook_pending.py`

**Interfaces:**
- Consumes: `fm_pending.write_pending(root, flow_id, entry)` from Task 1.
- Produces: no new public function — `handle()` behavior extended. Later tasks (Stop hook, flow-sync-apply command) rely on the on-disk file shape written here: a dict with keys `flow`, `file`, `role`, `tool_name`, `diff`, `formula_snippets`, `current_policy`, `current_invariants`, `current_mechanics_doc`, `timestamp`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hook_pending.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_hook_pending.py -v`
Expected: FAIL — `AssertionError` (no pending entries written yet), since `feature_map_hook.py` doesn't call `fm_pending` yet.

- [ ] **Step 3: Implement the extension**

In `hooks/feature_map_hook.py`, add the import alongside the existing ones (line 16-18):

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_registry
import fm_state
import fm_pending
```

Also add `from datetime import datetime, timezone` to the top-level import block, right after `import sys` (line 14):

```python
import sys
from datetime import datetime, timezone
```

Add a helper function right after `detect_formula_change` (after line 71, before `def parse_feature_map`):

```python
def _pending_diff(tool_name, tool_input):
    """Ekstrak representasi diff ringkas dari tool_input untuk disimpan di
    pending state, sesuai tool. Return None kalau tool tidak relevan
    (mis. Bash tanpa file_path sudah difilter oleh caller)."""
    if tool_name == "Edit":
        return {
            "old_string": tool_input.get("old_string", ""),
            "new_string": tool_input.get("new_string", ""),
        }
    if tool_name == "MultiEdit":
        return {"edits": tool_input.get("edits") or []}
    if tool_name in ("Write", "NotebookEdit"):
        content = tool_input.get("content") or tool_input.get("new_source") or ""
        lines = content.splitlines()
        excerpt = lines[:40] if len(lines) <= 80 else lines[:20] + ["...", ] + lines[-20:]
        return {"content_excerpt": "\n".join(excerpt)}
    if tool_name == "Bash":
        return {"command": tool_input.get("command", "")}
    return {}
```

Then, inside `handle()`, right after the `hits` loop that builds `lines` (i.e. right after the `for name, flow, matched_tp in hits:` block ends, before the `for origin, chain in chains.items():` block at line 379), add pending-write logic. Insert this right before line 379 (`for origin, chain in chains.items():`):

```python
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    diff = _pending_diff(tool_name, tool_input)
    for name, flow, matched_tp in hits:
        fm_pending.write_pending(root, name, {
            "flow": name,
            "file": file_path,
            "role": matched_tp.get("role", ""),
            "tool_name": tool_name,
            "diff": diff,
            "formula_snippets": formula_snippets,
            "current_policy": flow.get("policy", ""),
            "current_invariants": list(flow.get("invariants", [])),
            "current_mechanics_doc": flow.get("mechanics_doc", ""),
            "timestamp": now,
        })
```

(The `from datetime import ...` mirrors the inline-import style already used for `subprocess` at module level; here it's fine as a top-of-function import since `handle()` is the only place needing it — but for consistency, move it to the top-level imports instead: add `from datetime import datetime, timezone` next to the other imports at the top of the file, and just use `datetime.now(timezone.utc)...` inline in `handle()` without the local import line.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_hook_pending.py tests/test_hook_formula.py tests/test_hook_stale.py tests/test_hook_multirepo.py -v`
Expected: all passed (confirms the extension doesn't break existing hook tests)

- [ ] **Step 5: Commit**

```bash
git add hooks/feature_map_hook.py tests/test_hook_pending.py
git commit -m "feat: write pending drift state on touchpoint edits"
```

---

### Task 3: `feature_map_stop.py` — Stop hook reminder + `hooks.json` registration

**Files:**
- Create: `hooks/feature_map_stop.py`
- Modify: `hooks/hooks.json`
- Test: `tests/test_hook_stop.py`

**Interfaces:**
- Consumes: `fm_pending.load_all_pending(root)` from Task 1; `find_feature_map` — duplicated locally (small, no need to import from `feature_map_hook.py` and couple the two hook processes together; matches this plugin's existing pattern where `precommit_check.py` is a separate script).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hook_stop.py
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import feature_map_stop as stop
import fm_pending


def test_no_feature_map_yaml_produces_no_output(tmp_path, capsys):
    stop.handle({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_no_pending_files_produces_no_output(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text("flows:\n")
    stop.handle({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_pending_files_produce_reminder(tmp_path, capsys):
    (tmp_path / "FEATURE-MAP.yaml").write_text("flows:\n")
    fm_pending.write_pending(str(tmp_path), "checkout", {"flow": "checkout"})
    fm_pending.write_pending(str(tmp_path), "attendance-recap", {"flow": "attendance-recap"})
    stop.handle({"cwd": str(tmp_path)})
    out = json.loads(capsys.readouterr().out)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "attendance-recap" in ctx
    assert "checkout" in ctx
    assert "flow-sync-apply" in ctx
    assert "decision" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_hook_stop.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'feature_map_stop'`

- [ ] **Step 3: Implement `hooks/feature_map_stop.py`**

```python
#!/usr/bin/env python3
"""Stop hook: kalau ada flow dengan pending drift (lihat fm_pending.py) yang
belum disinkronkan ke FEATURE-MAP.yaml, ingatkan agent untuk menjalankan
/feature-map:flow-sync-apply. Non-blocking -- hanya reminder, tidak pernah
mengembalikan decision:block, karena hook ini tidak punya akses model untuk
menilai apakah drift-nya memang perlu dicatat.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_pending


def find_feature_map(start_dir):
    d = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(d, "FEATURE-MAP.yaml")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def handle(payload):
    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    fm_path = find_feature_map(project_dir)
    if not fm_path:
        return
    root = os.path.dirname(fm_path)

    pending = fm_pending.load_all_pending(root)
    if not pending:
        return

    flow_ids = sorted(pending)
    message = (
        f"[feature-map] {len(flow_ids)} flow(s) have pending drift not yet "
        f"reflected in FEATURE-MAP.yaml: {', '.join(flow_ids)}. Run "
        "/feature-map:flow-sync-apply to review and sync, or dismiss if the "
        "edit didn't actually require an invariant change."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": message,
        }
    }, ensure_ascii=False))


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    try:
        handle(payload)
    except Exception:
        return


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/test_hook_stop.py -v`
Expected: 3 passed

- [ ] **Step 5: Register the Stop hook in `hooks/hooks.json`**

Replace the full file content with:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/feature_map_session_start.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/feature_map_hook.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/feature_map_stop.py\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Verify the hook script runs standalone without error**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && echo '{}' | python3 hooks/feature_map_stop.py; echo "exit=$?"`
Expected: `exit=0` with no output (no `cwd` in project with a FEATURE-MAP.yaml, so it returns early)

- [ ] **Step 7: Commit**

```bash
git add hooks/feature_map_stop.py hooks/hooks.json tests/test_hook_stop.py
git commit -m "feat: add Stop hook reminding to sync pending feature-map drift"
```

---

### Task 4: `/feature-map:flow-sync-apply` command

**Files:**
- Create: `commands/flow-sync-apply.md`
- Modify: `skills/feature-map/SKILL.md` (add rule referencing the new command)

**Interfaces:**
- Consumes: `fm_pending.load_all_pending(root)` / `fm_pending.clear_pending(root, flow_id)` (Task 1) — the command instructs the agent to invoke these via a one-line `python3 -c` shell call, matching how other commands in this plugin (e.g. `flow-sync-install.md`) reference hook helper scripts rather than importing them into command markdown.
- Produces: nothing consumed by other tasks — this is a leaf, user/agent-facing artifact. Verified by manual smoke test in Step 3 below (command markdown files aren't unit-tested elsewhere in this plugin — `commands/flow-audit.md`, `commands/flow-repo-register.md` etc. have no corresponding test files either).

- [ ] **Step 1: Write `commands/flow-sync-apply.md`**

```markdown
---
description: Rangkum drift bisnis yang tertunda jadi invariant/policy baru di FEATURE-MAP.yaml
---

Sinkronkan drift flow bisnis yang tertunda (dicatat otomatis oleh PostToolUse
hook feature-map di `.claude/feature-map-pending/`) ke `FEATURE-MAP.yaml`.
Langkah:

1. Tentukan root project: cari `FEATURE-MAP.yaml` mulai dari cwd naik ke
   parent (sama seperti hook lain di plugin ini). Kalau tidak ada, beri tahu
   user dan berhenti.
2. List file pending:
   `python3 -c "import sys; sys.path.insert(0,'<CLAUDE_PLUGIN_ROOT>/hooks'); import fm_pending, json; print(json.dumps(fm_pending.load_all_pending('<root>')))"`
   Kalau hasilnya `{}`, beri tahu user "tidak ada drift tertunda" dan
   berhenti.
3. Untuk tiap `flow_id` di hasil pending: baca entry-nya (`file`, `role`,
   `tool_name`, `diff`, `formula_snippets`, `current_policy`,
   `current_invariants`, `current_mechanics_doc`) dan baca blok flow yang
   sesuai di `FEATURE-MAP.yaml` saat ini (bisa saja sudah berubah sejak
   entry dicatat — pakai isi file `FEATURE-MAP.yaml` sekarang sebagai
   sumber kebenaran, `current_*` di entry pending cuma konteks "apa yang
   sudah tercatat waktu edit terjadi").
4. Nilai: apakah `diff` ini benar-benar perubahan aturan bisnis (formula,
   threshold, validasi, kondisi kelayakan) — atau cuma refactor/rename/
   format non-semantik? Kalau non-semantik: laporkan sebagai "dilewati,
   bukan perubahan aturan bisnis" dan lanjut ke flow_id berikutnya TANPA
   mengubah FEATURE-MAP.yaml maupun menghapus file pending-nya (biar tidak
   hilang kalau ternyata butuh dicek ulang manual).
5. Kalau memang perubahan aturan bisnis: rangkum jadi kalimat
   `invariants:` baru (revisi kalau menggantikan aturan lama, tambahan
   kalau melengkapi) dan, kalau relevan, update `policy:`. Kalau
   `formula_snippets` di entry menunjukkan rumus kompleks (banyak
   mode/kondisi) dan flow itu belum punya `mechanics_doc`, pertimbangkan
   sarankan (bukan buat otomatis) dokumen `docs/flows/<flow_id>.md`
   mengikuti aturan #8 di SKILL.md.
6. Terapkan perubahan dengan tool Edit langsung ke `FEATURE-MAP.yaml`.
   Prompt persetujuan Edit dari Claude Code itu sendiri adalah review
   gate-nya — jangan buat mekanisme konfirmasi terpisah.
7. Setelah Edit berhasil untuk flow tsb, hapus file pending-nya:
   `python3 -c "import sys; sys.path.insert(0,'<CLAUDE_PLUGIN_ROOT>/hooks'); import fm_pending; fm_pending.clear_pending('<root>', '<flow_id>')"`
8. Setelah semua flow diproses, laporkan ringkasan ke user: flow mana yang
   disinkronkan (dengan ringkasan perubahan), flow mana yang dilewati dan
   kenapa.
```

- [ ] **Step 2: Add SKILL.md rule referencing the command**

In `skills/feature-map/SKILL.md`, after rule #5 (the line starting with
`5. Audit menyeluruh satu flow: pakai command...`), insert a new rule,
renumbering the subsequent rules (old #6→#7, #7→#8, #8→#9):

```markdown
6. **Kalau ada reminder `[feature-map] N flow(s) have pending drift...`** di
   akhir turn: jalankan `/feature-map:flow-sync-apply` untuk merangkum
   perubahan jadi invariant/policy baru di `FEATURE-MAP.yaml` sebelum
   menganggap task selesai — kecuali perubahannya memang bukan perubahan
   aturan bisnis (refactor murni, rename, format), dalam hal ini boleh
   dilewati.
```

- [ ] **Step 3: Manual smoke test**

```bash
cd /Users/adesyofyan/Documents/MApp/claude-plugins
mkdir -p /tmp/fm-smoke/app
cat > /tmp/fm-smoke/FEATURE-MAP.yaml <<'EOF'
flows:
  attendance-recap:
    description: "rekap presensi"
    policy: "mode sales beda formula dari mode default"
    touchpoints:
      - path: "app/Recap.php"
        role: backend-service
    invariants:
      - "Sanksi = TUM + Alpa"
EOF
echo "<?php" > /tmp/fm-smoke/app/Recap.php
cd /tmp/fm-smoke
echo '{"cwd": "/tmp/fm-smoke", "tool_name": "Edit", "tool_input": {"file_path": "/tmp/fm-smoke/app/Recap.php", "old_string": "x", "new_string": "$sanksi = $tum + $alpa + $terlambat;"}}' | python3 /Users/adesyofyan/Documents/MApp/claude-plugins/hooks/feature_map_hook.py
cat /tmp/fm-smoke/.claude/feature-map-pending/attendance-recap.json
echo '{"cwd": "/tmp/fm-smoke"}' | python3 /Users/adesyofyan/Documents/MApp/claude-plugins/hooks/feature_map_stop.py
```

Expected: the first command prints the existing reminder JSON to stdout; the
`cat` shows a pending JSON file with `diff.new_string` containing the
formula; the last command prints a Stop reminder JSON mentioning
`attendance-recap` and `flow-sync-apply`. Clean up with `rm -rf /tmp/fm-smoke`
afterward.

- [ ] **Step 4: Commit**

```bash
git add commands/flow-sync-apply.md skills/feature-map/SKILL.md
git commit -m "feat: add /feature-map:flow-sync-apply command to sync pending drift"
```

---

### Task 5: Full test suite regression check

**Files:** none created/modified — verification only.

- [ ] **Step 1: Run the full test suite**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && .venv/bin/pytest tests/ -v`
Expected: all tests pass, including the pre-existing ones (`test_fm_state.py`,
`test_hook_formula.py`, `test_hook_stale.py`, `test_hook_multirepo.py`,
`test_fm_registry.py`, `test_fm_graph.py`, `test_fm_blueprint.py`,
`test_fm_rules_check.py`, `test_impacts_parser.py`, `test_impact_chain.py`,
`test_precommit.py`) plus the four new files added in Tasks 1-3.

- [ ] **Step 2: Verify hooks.json is valid JSON and both hook scripts are syntactically valid**

Run: `cd /Users/adesyofyan/Documents/MApp/claude-plugins && python3 -c "import json; json.load(open('hooks/hooks.json'))" && python3 -m py_compile hooks/feature_map_hook.py hooks/feature_map_stop.py hooks/fm_pending.py && echo OK`
Expected: `OK`
