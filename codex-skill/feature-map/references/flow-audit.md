# Flow Audit

Audit consistency for one business flow based on `FEATURE-MAP.yaml`.

## Incremental Mode

1. Read `.feature-map/state.json` beside `FEATURE-MAP.yaml`.
2. If the user passes `--all` or state is absent, list flows and audit the selected flow(s).
3. If state exists and no flow is `stale`, report that all flows are clean since `last_synced_sha`.
4. If stale flows exist, audit only those unless the user named a flow. Use `dirty_files` as the starting point.

Entries like `<repo>:<path>` are cross-repo dirty files; resolve repo names through `~/.claude/feature-maps/registry.json`. Entries like `via:<flow>` are declarative impact markers, not files.

## Audit Steps

1. Read the target flow: `policy`, `touchpoints`, `invariants`, and `impacts`.
2. Resolve every touchpoint glob. If a glob matches nothing, report `DRIFT`.
3. For touchpoints with `repo: <name>`, resolve the repo path from the registry. If missing, report `UNRESOLVED` and continue.
4. Read all matched touchpoint files.
5. Compare implementation against policy and each invariant, focusing on validation, enum/status, API contract, UI copy, docs, migrations, and event consumers.
6. If `.code-review-graph/graph.db` exists, run the plugin graph helper:

```bash
python3 <plugin-root>/hooks/fm_graph.py <repo-root> <dirty-file>...
```

Use callers as concrete audit checklist items. If a caller maps to another non-stale flow not declared in `impacts`, report `IMPACT` and suggest adding that flow to `impacts`.

## Reporting

Report findings ordered by severity:

- `GAP`: cite both sides with `file:line`.
- `DRIFT`: cite stale registry/doc/source facts.
- `IMPACT`: cite caller function and `file:line`.
- `OK`: name verified invariant.

Do not immediately fix. Offer the fix after the report unless the user already asked for implementation.

## Marking Clean

After reporting, if no unresolved GAP remains:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py mark-clean <repo-root> <flow> [<flow>...]
```

If any GAP is intentionally left unresolved, ask before marking clean.
