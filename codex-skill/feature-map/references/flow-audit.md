# Flow Audit

Audit consistency for one business flow based on `FEATURE-MAP.yaml`.

## Incremental Mode

1. Read `.feature-map/state.json` beside `FEATURE-MAP.yaml`.
2. If the user passes `--all` or state is absent, list flows and audit the selected flow(s).
3. If state exists and no flow is `stale`, report that all flows are clean since `last_synced_sha`.
4. If stale flows exist, audit only those unless the user named a flow. Use `dirty_files` as the starting point.

Entries like `<repo>:<path>` are cross-repo dirty files; resolve repo names through `~/.claude/feature-maps/registry.json`. Entries like `via:<flow>` are declarative impact markers, not files.

## Audit Steps

1. Read the target flow: `policy`, `touchpoints`, `invariants`, `impacts`, and `mechanics_doc` if present.
2. Resolve every touchpoint glob. If a glob matches nothing, report `DRIFT`.
3. For touchpoints with `repo: <name>`, resolve the repo path from the registry. If missing, report `UNRESOLVED` and continue.
4. Read all matched touchpoint files. If `mechanics_doc` is set, also read that file.
5. Compare implementation against policy and each invariant, focusing on validation, enum/status, API contract, UI copy, docs, migrations, and event consumers. If `mechanics_doc` exists, also compare its narrated formulas/modes/examples against the actual code — report `DRIFT` if the doc describes a formula or mode the code no longer has (or vice versa). If the flow clearly has multiple modes/variants or a multi-condition formula but has no `mechanics_doc`, note that as a gap and suggest adding one (see SKILL.md Core Rule 6) rather than silently skipping it.
6. If `.code-review-graph/graph.db` exists, run the plugin graph helper:

```bash
python3 <plugin-root>/hooks/fm_graph.py <repo-root> <dirty-file>...
```

Use callers as concrete audit checklist items. If a caller maps to another non-stale flow not declared in `impacts`, report `IMPACT` and suggest adding that flow to `impacts`.

7. If the flow has test touchpoints (path matches `tests/`, `Test.php`, `_test.py`, `.spec.ts`/`.spec.js`), run the rule-gap check:

```bash
python3 <plugin-root>/hooks/fm_rules_check.py <repo-root> <flow>
```

This extracts test description strings and flags ones whose content words barely overlap the flow's declared invariants — a signal a regression test encodes a business rule nobody wrote into the registry. For each flagged `possible_undocumented_rules[]` entry, read the actual test file before reporting — this is a keyword heuristic and can false-positive when an existing invariant just uses different words for the same rule. If it's a real gap, report `RULE-GAP` with a suggested invariant sentence for the user to review. If it's already covered, treat it as `OK` and move on.

## Reporting

Report findings ordered by severity:

- `GAP`: cite both sides with `file:line`.
- `DRIFT`: cite stale registry/doc/source facts.
- `IMPACT`: cite caller function and `file:line`.
- `RULE-GAP`: cite the test file and description, and the suggested invariant.
- `OK`: name verified invariant.

Do not immediately fix. Offer the fix after the report unless the user already asked for implementation.

## Marking Clean

After reporting, if no unresolved GAP remains:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py mark-clean <repo-root> <flow> [<flow>...]
```

If any GAP is intentionally left unresolved, ask before marking clean.
