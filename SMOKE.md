# Smoke Test

Use this before publishing or after changing hook/CLI behavior.

## Codex

```bash
tmp=$(mktemp -d)
make install-codex CODEX_SKILL_DIR="$tmp"
"$tmp/scripts/feature_map_cli.py" doctor
make smoke
python3 codex-skill/feature-map/scripts/feature_map_cli.py plugin-root
python3 codex-skill/feature-map/scripts/feature_map_cli.py doctor
python3 codex-skill/feature-map/scripts/feature_map_cli.py status .
```

Expected:

- `plugin-root` points to a directory containing `hooks/feature_map_hook.py`.
- `doctor` returns JSON with `"ok": true`.
- Temporary `make install-codex` writes `plugin-root.txt` and the installed CLI doctor resolves this checkout.
- `make smoke` runs `doctor` and a tiny blueprint import without leaving a draft file in the repo.
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

## Target Repository

Use a trusted repository with a reviewed map:

```bash
python3 codex-skill/feature-map/scripts/feature_map_cli.py status /path/to/app
python3 codex-skill/feature-map/scripts/feature_map_cli.py pending-status /path/to/app
python3 codex-skill/feature-map/scripts/feature_map_cli.py quality /path/to/app
```

Expected:

- `status` parses `FEATURE-MAP.yaml` and prints flow counts.
- `pending-status` exits 0.
- `quality` exits 0 when the map has no draft flows, placeholder/dead local touchpoints, or missing invariants.
- Keep the target repository unchanged during smoke checks.
