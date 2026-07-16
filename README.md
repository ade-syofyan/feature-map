# feature-map

**Business-flow memory for AI coding agents.**

`feature-map` helps Claude Code and Codex keep cross-layer business behavior consistent. It maps the files that belong to the same business flow, reminds the agent when one touchpoint changes, and gives you an audit path before silent drift becomes a production bug.

Most code tools understand imports, callers, and symbols. Real product bugs often live somewhere else:

- a mobile form changed, but backend validation did not
- an admin approval page still shows the old status
- API docs promise a field that the service no longer accepts
- a payment rule changed, but reporting, notifications, and migration logic stayed behind

`feature-map` exists for that semantic layer.

## Available For

| Agent | Status | What it can do |
| --- | --- | --- |
| Claude Code | Available | Native plugin commands, PostToolUse reminders, pre-commit sync checks |
| Codex | Available | Skill adapter, flow audit workflow, registry helpers, shared source of truth |

The Claude plugin and Codex skill use the same `FEATURE-MAP.yaml` registry, so one project map can guide both agents.

## What It Does

- **Declares business flows** in `FEATURE-MAP.yaml`
- **Connects touchpoints** across UI, backend, services, docs, database migrations, and event consumers
- **Tracks invariants** that must stay consistent across those touchpoints
- **Marks flows stale** when a mapped file changes
- **Audits drift** with `GAP`, `DRIFT`, `IMPACT`, and `OK` findings
- **Supports multi-repo flows** through a local repo registry
- **Follows impact chains** with declared `impacts`
- **Uses call-graph blast radius** when `.code-review-graph/graph.db` is present

## Why This Matters

AI agents are fast, but speed can widen the gap between files that should change together. `feature-map` gives agents a lightweight memory of the product's business logic, not just the code graph.

The goal is simple:

> When one part of a business flow changes, the rest of the flow should not be forgotten.

This plugin is meant to grow into a shared safety layer for AI-assisted engineering: small enough to install anywhere, explicit enough to review in Git, and practical enough to help during real edits.

## Quick Example

```yaml
flows:
  partner-registration:
    description: "Partner signs up, gets validated, and is reviewed by admin"
    policy: "KTP is required before partner verification can be approved"
    touchpoints:
      - path: "mobile/**/PartnerRegistrationForm.*"
        role: client-form
      - path: "api/**/PartnerRegistrationController.*"
        role: backend-validation
      - path: "admin/**/PartnerVerificationPage.*"
        role: admin-view
      - path: "docs/api/partner-registration.md"
        role: docs
    invariants:
      - "KTP required/optional status must match client, backend, admin, and docs"
      - "Verification status values must be consistent across API and admin UI"
```

If an agent edits the mobile form, `feature-map` reminds it to inspect backend validation, admin verification, and API docs before calling the task done.

## Claude Code Usage

Install from a local marketplace:

```bash
claude plugin marketplace add ~/Documents/MApp/claude-plugins
claude plugin install feature-map@ade-plugins
```

Initialize a project:

```text
/flow-map-init
```

Audit stale flows:

```text
/flow-audit
```

Audit one flow:

```text
/flow-audit partner-registration
```

Register a related repo for multi-repo flows:

```text
/flow-repo-register backend-api
```

Install the non-blocking pre-commit warning hook:

```text
/flow-sync-install
```

Without `FEATURE-MAP.yaml`, the hook is a no-op and safe to keep installed globally.

## Codex Usage

`feature-map` also ships with a Codex skill adapter:

```text
codex-skill/feature-map
```

Install or sync it into Codex:

```bash
rsync -a --delete codex-skill/feature-map/ ~/.codex/skills/feature-map/
chmod +x ~/.codex/skills/feature-map/scripts/feature_map_cli.py
```

Then ask Codex naturally:

```text
Use feature-map to audit stale flows in this repo.
```

Useful helper commands:

```bash
~/.codex/skills/feature-map/scripts/feature_map_cli.py status .
~/.codex/skills/feature-map/scripts/feature_map_cli.py repo-register my-service
~/.codex/skills/feature-map/scripts/feature_map_cli.py mark-clean . partner-registration
```

## Findings

Audits classify results as:

- **GAP**: real inconsistency that can cause broken behavior
- **DRIFT**: registry, docs, or implementation no longer describe the same truth
- **IMPACT**: another flow is affected through declared impact or call graph
- **OK**: invariant was checked and is consistent

## Releases

### v0.4.0 — Impact Chain & Call Graph

- Added `impacts` for transitive flow impact tracking
- Marks downstream flows stale with `via:<flow>`
- Shows impact chains in reminders
- Integrates with `code-review-graph` for call-graph blast radius
- Reports undeclared cross-flow effects as **IMPACT**
- Adds Codex skill adapter support

### v0.3.0 — Multi-Repo Flow

- Added `repo: <name>` touchpoints
- Added local registry at `~/.claude/feature-maps/registry.json`
- Added repo register/list/remove command
- Audits touchpoints across registered repos
- Reports missing repo mappings as `UNRESOLVED`

### v0.2.0 — Stale Flow Detection

- Marks changed flows stale in `.feature-map/state.json`
- Adds non-blocking pre-commit warning hook
- Makes `/flow-audit` incremental by default
- Advances `last_synced_sha` after clean audits

## Schema Notes

The hook parser intentionally supports a small YAML subset without external dependencies. Avoid YAML anchors, multiline scalars, and complex nested structures. Keep the registry boring, explicit, and reviewable.

Supported touchpoint roles:

- `client-form`
- `client-view`
- `backend-validation`
- `backend-service`
- `admin-view`
- `docs`
- `db-migration`
- `event-consumer`

## Roadmap

- Better Codex-native workflow helpers
- Safer registry validation and formatting
- More examples for Laravel, mobile apps, monorepos, and service meshes
- Richer audit output for pull requests
- Better integration with code-review-graph and other dependency analyzers
- Portable installer for Claude + Codex in one command

## Contributing

Contributors are welcome.

Good first contributions:

- example `FEATURE-MAP.yaml` files from real project shapes
- better docs for multi-repo teams
- tests for tricky YAML subset cases
- improvements to Codex skill behavior
- integrations with other graph or review tools
- clearer audit report formats

The hope is for `feature-map` to become a practical shared language between humans and AI agents: product rules in one place, mapped to the code that must honor them.

If this idea matches a bug your team has seen before, open an issue, propose a flow pattern, or send a PR.
