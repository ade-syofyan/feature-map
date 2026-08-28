---
name: feature-map
description: Maintain and audit FEATURE-MAP.yaml business-flow registries from the Claude feature-map plugin in Codex. Use when the user asks Codex to use feature-map, run flow-audit, flow-map-init, flow-repo-register, install/check feature-map hooks, inspect stale flows, or keep cross-layer business touchpoints consistent across files, repos, services, UI, backend, docs, or migrations.
---

# Feature Map for Codex

Use this skill as the Codex adapter for the local `feature-map` plugin. The canonical plugin source is usually:

`/Users/adesyofyan/Documents/MApp/claude-plugins`

If that path does not exist, resolve the plugin root in this order:

1. `$FEATURE_MAP_PLUGIN_ROOT`
2. `$CLAUDE_PLUGIN_ROOT`
3. `~/.claude/plugins/cache/ade-plugins/feature-map/<latest-version>`

## Core Rules

When editing a repo that has `FEATURE-MAP.yaml`, treat it as the source of truth for business-flow coupling:

0. **Before touching any file** (not just before finishing), run `python3 <plugin-root>/codex-skill/feature-map/scripts/feature_map_cli.py status <repo-root>` once at the start of the task if the repo has `FEATURE-MAP.yaml`. This is cheap (flow names + one-line descriptions + counts only) and tells you upfront which business flows exist, so you can read the full entry for a relevant flow before writing code — don't wait until after editing to discover a file was a touchpoint.
1. If a touched file matches a flow touchpoint, inspect the other touchpoints in that flow before finishing.
2. If a policy or invariant changes, update `FEATURE-MAP.yaml` in the same change.
   - **A formula or calculation change is a policy change.** If the diff adds or modifies a
     calculation, threshold, or business condition (not just a rename/refactor), write the full
     formula (operands and order, not just a function name) as a new invariant. This applies even
     when the task is only "audit" or "fix a bug" — don't wait for the user to ask "is this
     documented?"; by then it's already a miss.
   - If the PostToolUse reminder includes a `FORMULA/CALCULATION DETECTED` line, that's an
     automatic heuristic (can false-positive) — verify whether the flagged line is really a
     business formula, and if so write the invariant immediately, not at the end of the session.
   - **Codex has no automatic reminder for this.** In Claude Code, a PostToolUse hook captures
     drift context on every touchpoint edit and a Stop hook reminds at the end of the turn if
     anything is unsynced. Codex has neither — so before finishing any task that touched a repo
     with `FEATURE-MAP.yaml`, run `python3 <plugin-root>/codex-skill/feature-map/scripts/feature_map_cli.py pending-status <repo-root>`.
     If it prints anything other than `{}`, follow `references/flow-sync-apply.md` to summarize
     the drift into `FEATURE-MAP.yaml` (or explicitly skip non-semantic changes) before reporting
     the task done.
3. If adding a new cross-layer feature, add or extend the relevant flow.
4. If moving or deleting a touchpoint file, update its path glob.
5. If flow state exists in `.feature-map/state.json`, audit stale flows first unless the user names a specific flow.
6. **If the business rule is complex** (many modes/variants, a formula with several conditions,
   many edge cases — e.g. default vs. sales attendance recap, a Sanksi formula vs. a Tidak Hadir
   formula, per-position exceptions, partner/mitra-type rules) — a single `invariants:` line isn't
   enough. Write a separate markdown doc (`docs/flows/<flow-name>.md`, or wherever fits the repo)
   with the full narrative: how each mode works, the formula with real numeric examples, a
   comparison table of variants, and exception conditions. Register its path under the flow's
   `mechanics_doc` field. `invariants:` stays mandatory (quick summary for the reminder hook);
   `mechanics_doc` is the companion for detail that doesn't fit one line. Update it in the same
   change whenever the formula/modes/exceptions change — don't let it go stale while `invariants:`
   moves on.

## Commands in Codex

Claude slash commands are Markdown instructions under `commands/`. Codex must translate them to normal tool work:

- `/flow-audit <flow|--all>`: read `references/flow-audit.md`, then audit and report. Do not auto-fix; offer fixes after reporting.
- `/flow-map-init [focus]`: read `references/flow-map-init.md`, then draft or extend `FEATURE-MAP.yaml`.
- `/flow-map-from-doc <document> [output]`: use `scripts/feature_map_cli.py import-doc <document> -o <output>` to generate a draft map from blueprint/FRD/SRS/SOP/workflow documents. Review before replacing `FEATURE-MAP.yaml`.
- `/flow-repo-register [name|--list|--remove name]`: use `scripts/feature_map_cli.py repo-register ...`.
- `/flow-sync-install`: read `references/flow-sync-install.md`, then install the git pre-commit hook using the resolved plugin root.
- `/feature-map:flow-sync-apply`: read `references/flow-sync-apply.md`, then summarize pending drift (from `pending-status`) into `FEATURE-MAP.yaml`. Also run this proactively before finishing any task per Core Rule 2's Codex note above — don't wait for the user to type the slash command.

Run at the start of any task touching a repo with `FEATURE-MAP.yaml` (see Core Rule 0), and again before semantic audits:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py status <repo-root>
```

This prints detected flows, stale state, registry path, and plugin root. Use it as orientation up front, not as the final audit.

When auditing a flow that has test touchpoints (path matches `tests/`, `Test.php`, `_test.py`, `.spec.ts`/`.spec.js`), also run the rule-gap check before declaring the audit done — see `references/flow-audit.md` for how to interpret the output:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py rules-check <flow> --root <repo-root>
```

This extracts test description strings from the flow's test touchpoints and flags ones whose content words barely overlap the flow's declared invariants — a signal that a regression test encodes a business rule nobody wrote into the registry yet. Heuristic only: read the flagged test before reporting it as a real gap.

## Registry Schema

`FEATURE-MAP.yaml` uses the plugin's small YAML subset:

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    confidence: draft
    policy: "kebijakan bisnis saat ini"
    business_aspects:
      - status
      - validation
    mechanics_doc: "docs/flows/nama-flow-kebab.md"   # optional, see Core Rule 6
    evidence:
      - source: "docs/blueprint.pdf"
        page: 12
        section: "WORKFLOW ABSENSI"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form
        note: "opsional"
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
    impacts:
      - flow-lain
```

`mechanics_doc` is optional — a path relative to the repo root pointing to a markdown file that
narrates "how it works and what the rules are" for that flow (see Core Rule 6). Free-form
content, but at minimum should cover: a summary of each mode/variant, the full formula with real
numeric examples (not just variable names), and a list of exceptions/edge cases with their
business reasoning.

`business_aspects` is optional — a lightweight tag list for the kind of business rule being
protected, not another file location. Supported values: `formula`, `status`, `validation`,
`permission`, `eligibility`, `visibility`, `report`, `export`, `notification`, `scheduler`,
and `migration`. Use it for rules that are easy to miss, such as frontend button visibility,
status lifecycle, scheduled reminders, report/export semantics, historical imports, and payroll
calculation engines.

Supported touchpoint roles include `client-form`, `client-view`, `backend-validation`, `backend-service`, `admin-view`, `data-schema`, `docs`, `db-migration`, and `event-consumer`.

For multi-repo touchpoints, `repo: <name>` resolves through `~/.claude/feature-maps/registry.json` unless `FEATURE_MAP_REGISTRY` is set.

For blueprint imports, use:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py import-doc <document.pdf|txt> -o FEATURE-MAP.draft.yaml
```

Generated maps are `confidence: draft`; bind placeholder paths to real files before relying on reminders.

## Audit Output

Report findings in this order:

- `GAP`: real inconsistency likely to cause bugs or stuck users; cite file and line on both sides.
- `DRIFT`: registry or docs no longer match implementation.
- `IMPACT`: call graph or declared `impacts` shows another flow is affected.
- `RULE-GAP`: a test description encodes a business rule not reflected in any invariant (from the rule-gap check).
- `OK`: invariant verified consistent.

After an audit with no remaining unresolved GAP, mark audited flows clean with:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py mark-clean <repo-root> <flow> [<flow>...]
```

If there is an unresolved GAP, ask before marking clean.
