# Smoke Test

Use this before publishing or after changing hook/CLI behavior.

## Codex

```bash
python3 codex-skill/feature-map/scripts/feature_map_cli.py plugin-root
python3 codex-skill/feature-map/scripts/feature_map_cli.py doctor
python3 codex-skill/feature-map/scripts/feature_map_cli.py status .
```

Expected:

- `plugin-root` points to a directory containing `hooks/feature_map_hook.py`.
- `doctor` returns JSON with `"ok": true`.
- `status` exits 0. In this plugin repo it may show no flows because the repo itself does not need a `FEATURE-MAP.yaml`.

## Blueprint Import

```bash
tmp=$(mktemp)
printf 'WORKFLOW PAYROLL Input: Attendance. Output: Payroll.\n' > "$tmp"
python3 hooks/fm_blueprint.py "$tmp" -o FEATURE-MAP.draft.yaml
```

Expected:

- Exit 0.
- `FEATURE-MAP.draft.yaml` contains a `payroll` flow with evidence, placeholder touchpoints, and invariants.
- Remove the draft after inspection unless you intentionally want to keep it.

## Claude Code

Ask Claude:

```text
Smoke test feature-map. Verify plugin commands are visible, run /feature-map:flow-map-from-doc on a tiny text document, and run a non-destructive hook/precommit smoke. Report commands, key output, and errors only. Do not change business logic.
```

Expected:

- Commands such as `/feature-map:flow-map-from-doc`, `/feature-map:flow-audit`, and `/feature-map:flow-sync-install` are visible.
- Importing a tiny workflow document succeeds without a stack trace.
- Hook/precommit smoke exits 0 or emits only the expected feature-map reminder.

## HRIS-Intercom

Use this only when the local HRIS checkout exists:

```bash
python3 codex-skill/feature-map/scripts/feature_map_cli.py status /Users/adesyofyan/Documents/MApp/web/HRIS-Intercom
python3 codex-skill/feature-map/scripts/feature_map_cli.py pending-status /Users/adesyofyan/Documents/MApp/web/HRIS-Intercom
python3 codex-skill/feature-map/scripts/feature_map_cli.py quality /Users/adesyofyan/Documents/MApp/web/HRIS-Intercom
```

Expected:

- `status` parses `FEATURE-MAP.yaml` and prints flow counts.
- `pending-status` exits 0.
- `quality` exits 0 when the map has no draft flows, placeholder/dead local touchpoints, or missing invariants.
- Do not edit HRIS business logic during smoke. If you stage a temporary hook test, revert it immediately and verify the HRIS worktree is clean.
