# Flow Sync Apply

Summarize pending business-flow drift into new/revised invariants and policy
in `FEATURE-MAP.yaml`. This is the Codex equivalent of the Claude command
`/feature-map:flow-sync-apply`.

Unlike the other Codex commands, this one has no PostToolUse/Stop hook to
trigger it automatically — Codex must check for pending drift itself, per
SKILL.md Core Rule 0a (before finishing any task that touched a repo with
`FEATURE-MAP.yaml`).

## Steps

1. List pending drift:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py pending-status <repo-root>
```

Prints `{}` if nothing is pending — stop here, nothing to do. Otherwise it
prints `{flow_id: {flow, file, role, tool_name, diff, formula_snippets,
current_policy, current_invariants, current_mechanics_doc, timestamp}}` for
every flow with unsynced drift.

2. For each `flow_id` in the result: read its entry, and read that flow's
   current block in `FEATURE-MAP.yaml` (the file may have changed since the
   entry was captured — treat the live YAML as the source of truth, and
   `current_policy`/`current_invariants` in the entry only as "what was
   already documented at edit time").
3. Decide: does `diff` represent an actual business-rule change (formula,
   threshold, validation, eligibility condition) or a non-semantic change
   (refactor, rename, formatting)? If non-semantic: note it as skipped, and
   clear that flow's pending file (see step 5 — same command handles both
   the synced and skipped path). Do not edit `FEATURE-MAP.yaml` for a
   skipped flow.
4. For a real business-rule change: write the new/revised `invariants:` line
   (and `policy:` if relevant) directly into `FEATURE-MAP.yaml` with your
   normal file-edit tool. If `formula_snippets` suggests a complex formula
   (several modes/conditions) and the flow has no `mechanics_doc` yet,
   suggest — don't create automatically — a `docs/flows/<flow_id>.md`
   companion doc per SKILL.md Core Rule 6.
5. Whether the flow was synced (step 4) or skipped (step 3), clear its
   pending file once you've finished deciding what to do with it:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py pending-clear <repo-root> <flow_id> [<flow_id>...]
```

A later edit to the same touchpoint will simply recreate the pending file
with a fresh diff — nothing is lost by clearing a decided flow.

6. Report a short summary: which flows were synced (with what changed),
   which were skipped and why.
