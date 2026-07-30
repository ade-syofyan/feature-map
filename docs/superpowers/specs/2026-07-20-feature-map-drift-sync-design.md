# feature-map: Semi-Automatic Drift Sync to FEATURE-MAP.yaml

## Problem

`feature_map_hook.py` (PostToolUse) currently only prints a read-only reminder
when a business-flow touchpoint is edited. It never captures *what* changed,
and there is no mechanism to turn that change into an updated `invariant`/
`policy` line in `FEATURE-MAP.yaml`. Unlike `code-review-graph`'s mechanical
re-index, this can't be fully automated because `FEATURE-MAP.yaml` content is
interpretive narrative prose, not a parse result — summarizing it requires an
LLM in the loop, not a hook script (hooks have no model access).

Goal: capture drift context as it happens, then let the agent (which does
have model access) turn that context into a proposed YAML update at a safe
point — end of turn, or on explicit request — instead of relying on the
human to remember to hand-edit `FEATURE-MAP.yaml`.

## Non-goals

- Hooks never call a model or write to `FEATURE-MAP.yaml` directly.
- No blocking/forcing behavior at Stop — the reminder is advisory.
- No cross-repo propagation of pending drift (existing `fm_registry`/
  `propagate_stale` stale-marking is unaffected and orthogonal to this).

## Components

### 1. `hooks/fm_pending.py` (new)

Same safety pattern as `fm_state.py` (all functions catch and swallow I/O
errors; atomic write via tempfile + `os.replace`).

```python
def pending_dir(root) -> str          # "<root>/.claude/feature-map-pending"
def sanitize_flow_id(name) -> str     # non [a-zA-Z0-9_-] -> "_"
def write_pending(root, flow_id, entry: dict) -> None   # overwrite file
def load_all_pending(root) -> dict[str, dict]           # {flow_id: entry}
def clear_pending(root, flow_id) -> None                # os.remove, best-effort
```

`write_pending` **overwrites** `<flow_id>.json` in place on every matching
edit (no accumulation across edits — confirmed simpler default). The file
content always reflects the *latest* touchpoint edit for that flow.

Pending entry schema:

```json
{
  "flow": "partner-registration",
  "file": "apps/mobile/lib/screens/PartnerForm.dart",
  "role": "client-form",
  "tool_name": "Edit",
  "diff": {"old_string": "...", "new_string": "..."},
  "formula_snippets": ["..."],
  "current_policy": "...",
  "current_invariants": ["..."],
  "current_mechanics_doc": "",
  "timestamp": "2026-07-20T12:00:00Z"
}
```

`diff` shape depends on `tool_name`:
- `Edit`: `{"old_string", "new_string"}` from `tool_input`.
- `MultiEdit`: `{"edits": [{"old_string","new_string"}, ...]}`.
- `Write`/`NotebookEdit`: `{"content_excerpt": <first/last ~40 lines>}` (full
  content can be large; excerpt keeps the pending file small — full file is
  still on disk at `file` if more context is needed later).
- `Bash`: `{"command": tool_input.get("command")}`.

`current_policy`/`current_invariants`/`current_mechanics_doc` are a snapshot
of the flow's current state *at capture time*, so `flow-sync-apply` doesn't
need to re-derive "was this already documented?" — it just diffs the
snapshot against whatever `FEATURE-MAP.yaml` says when the skill actually
runs (which may have changed since, e.g. from a prior sync).

### 2. `hooks/feature_map_hook.py` (extend)

In `handle()`, right after computing `hits` (the direct-edit reminder path),
for each matched flow call `fm_pending.write_pending(root, flow_id, entry)`
using data already available in that function (`tool_name`, `tool_input`,
`flow`, `matched_tp`, `formula_snippets`). No new parsing needed — this is
additive to the existing reminder-printing loop, not a new pass over the
file.

`.claude/feature-map-pending/` gets appended to `.gitignore` the same way
`fm_state._ensure_gitignore` does for `.feature-map/` (reuse that helper or
mirror it in `fm_pending.py` — mirror it, since `fm_state.py` shouldn't need
to know about the pending dir).

### 3. `hooks/feature_map_stop.py` (new) + `hooks.json` Stop entry

Registered as a `Stop` hook. Logic:

```python
def handle(payload):
    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    fm_path = find_feature_map(project_dir)   # reuse from feature_map_hook
    if not fm_path:
        return
    root = os.path.dirname(fm_path)
    pending = fm_pending.load_all_pending(root)
    if not pending:
        return
    flow_ids = sorted(pending)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": (
                f"[feature-map] {len(flow_ids)} flow(s) have pending drift not "
                f"yet reflected in FEATURE-MAP.yaml: {', '.join(flow_ids)}. "
                "Run /feature-map:flow-sync-apply to review and sync, or "
                "dismiss if the edit didn't actually require an invariant "
                "change."
            ),
        }
    }, ensure_ascii=False))
```

Non-blocking: no `decision: "block"`. `hooks.json` gets:

```json
"Stop": [
  {
    "matcher": "",
    "hooks": [
      {"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/feature_map_stop.py\""}
    ]
  }
]
```

### 4. `commands/flow-sync-apply.md` (new)

Same style/format as `commands/flow-audit.md`. Body instructs the agent to:

1. List `.claude/feature-map-pending/*.json` under the project's
   `FEATURE-MAP.yaml` root. If empty, tell the user there's nothing pending
   and stop.
2. For each pending entry: read it, and read the corresponding flow block in
   `FEATURE-MAP.yaml`.
3. Decide: does this diff actually change a business rule/policy/formula
   (invariant-worthy), or was it a non-semantic change (refactor, rename,
   formatting) that doesn't need a doc update? If the latter, say so and
   skip it (don't force an update).
4. For invariant-worthy changes, draft the new/revised `invariants:` line
   (and `policy:`/`mechanics_doc:` reference if warranted, per SKILL.md rule
   #8) and apply it with the `Edit` tool directly on `FEATURE-MAP.yaml`.
   The normal Claude Code permission prompt for that `Edit` call **is** the
   review gate — no separate custom confirmation flow.
5. On success, delete that flow's pending file
   (`fm_pending.clear_pending`) — simplest via a one-line inline Python
   invocation, consistent with how other commands in this plugin shell out
   to the hook helper modules.
6. Report a short summary: which flows were synced, which were skipped and
   why.

This same command works both for manual invocation (`/feature-map:flow-sync-apply`,
user wants to review before it's written — the `Edit` diff shown by Claude
Code is that review) and for agent-initiated invocation right after seeing
the Stop reminder.

### 5. `skills/feature-map/SKILL.md` (extend)

Add a rule (after existing rule #5, which documents `flow-audit`):

> Kalau ada reminder `[feature-map] N flow(s) have pending drift...` di akhir
> turn, jalankan `/feature-map:flow-sync-apply` untuk merangkum perubahan
> jadi invariant/policy baru di FEATURE-MAP.yaml sebelum menganggap task
> selesai — kecuali perubahannya memang bukan perubahan aturan bisnis
> (refactor murni, rename, dll), dalam hal ini boleh diabaikan.

## Data flow summary

```
Edit/Write/Bash touches touchpoint file
  -> feature_map_hook.py (PostToolUse): prints reminder (unchanged)
                                      + writes .claude/feature-map-pending/<flow>.json (new)
  -> ... more edits happen, pending files keep getting overwritten with latest ...
  -> Stop hook: sees pending files exist -> additionalContext reminder (new)
  -> agent runs /feature-map:flow-sync-apply (now, or later, or manually)
       -> reads pending + current FEATURE-MAP.yaml
       -> drafts invariant/policy text
       -> Edit tool writes FEATURE-MAP.yaml (user's permission mode gates this)
       -> deletes the pending file for synced flows
```

## Testing

- Unit test `fm_pending.py`: write/overwrite/load_all/clear round-trip,
  sanitize_flow_id edge cases (slashes, spaces, unicode).
- Unit test `feature_map_hook.py` extension: verify pending file is written
  with expected shape for Edit/MultiEdit/Write/Bash tool_input variants.
- Unit test `feature_map_stop.py`: no FEATURE-MAP.yaml -> no output; no
  pending -> no output; pending present -> correct additionalContext text.
- Manual smoke test: edit a touchpoint file in a test project with
  FEATURE-MAP.yaml, confirm pending JSON appears, confirm Stop hook fires
  reminder, run `/feature-map:flow-sync-apply` and confirm YAML edit +
  pending file cleanup.
