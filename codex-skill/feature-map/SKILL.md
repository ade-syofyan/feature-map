---
name: feature-map
description: Maintain and audit FEATURE-MAP.yaml business-flow registries from the Claude feature-map plugin in Codex. Use when the user asks Codex to use feature-map, run flow-audit, flow-map-init, flow-repo-register, install/check feature-map hooks, inspect stale flows, or keep cross-layer business touchpoints consistent across files, repos, services, UI, backend, docs, or migrations.
---

# Feature Map for Codex

Use this skill as the Codex adapter for the local `feature-map` plugin. The canonical plugin source is usually:

`/Users/adesyofyan/Documents/MApp/claude-plugins/feature-map`

If that path does not exist, resolve the plugin root in this order:

1. `$FEATURE_MAP_PLUGIN_ROOT`
2. `$CLAUDE_PLUGIN_ROOT`
3. `~/.claude/plugins/cache/ade-plugins/feature-map/<latest-version>`

## Core Rules

When editing a repo that has `FEATURE-MAP.yaml`, treat it as the source of truth for business-flow coupling:

1. If a touched file matches a flow touchpoint, inspect the other touchpoints in that flow before finishing.
2. If a policy or invariant changes, update `FEATURE-MAP.yaml` in the same change.
3. If adding a new cross-layer feature, add or extend the relevant flow.
4. If moving or deleting a touchpoint file, update its path glob.
5. If flow state exists in `.feature-map/state.json`, audit stale flows first unless the user names a specific flow.

## Commands in Codex

Claude slash commands are Markdown instructions under `commands/`. Codex must translate them to normal tool work:

- `/flow-audit <flow|--all>`: read `references/flow-audit.md`, then audit and report. Do not auto-fix; offer fixes after reporting.
- `/flow-map-init [focus]`: read `references/flow-map-init.md`, then draft or extend `FEATURE-MAP.yaml`.
- `/flow-repo-register [name|--list|--remove name]`: use `scripts/feature_map_cli.py repo-register ...`.
- `/flow-sync-install`: read `references/flow-sync-install.md`, then install the git pre-commit hook using the resolved plugin root.

Before semantic audits, run:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py status <repo-root>
```

This prints detected flows, stale state, registry path, and plugin root. Use it as orientation, not as the final audit.

## Registry Schema

`FEATURE-MAP.yaml` uses the plugin's small YAML subset:

```yaml
flows:
  nama-flow-kebab:
    description: "satu kalimat"
    policy: "kebijakan bisnis saat ini"
    touchpoints:
      - path: "glob/relatif/dari/root/**/File*.kt"
        role: client-form
        note: "opsional"
    invariants:
      - "aturan yang harus konsisten antar touchpoint"
    impacts:
      - flow-lain
```

Supported touchpoint roles include `client-form`, `client-view`, `backend-validation`, `backend-service`, `admin-view`, `docs`, `db-migration`, and `event-consumer`.

For multi-repo touchpoints, `repo: <name>` resolves through `~/.claude/feature-maps/registry.json` unless `FEATURE_MAP_REGISTRY` is set.

## Audit Output

Report findings in this order:

- `GAP`: real inconsistency likely to cause bugs or stuck users; cite file and line on both sides.
- `DRIFT`: registry or docs no longer match implementation.
- `IMPACT`: call graph or declared `impacts` shows another flow is affected.
- `OK`: invariant verified consistent.

After an audit with no remaining unresolved GAP, mark audited flows clean with:

```bash
python3 /Users/adesyofyan/.codex/skills/feature-map/scripts/feature_map_cli.py mark-clean <repo-root> <flow> [<flow>...]
```

If there is an unresolved GAP, ask before marking clean.
