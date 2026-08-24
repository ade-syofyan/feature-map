# feature-map benchmark notes

This file records lightweight, reproducible proof checks for `feature-map`.
It is not a universal performance benchmark. It is evidence that the CLI can
parse real projects and produce structured output without modifying the source
application.

For product positioning and adjacent-tool boundaries, see [POSITIONING.md](POSITIONING.md).

## App Migration Extractor

Command shape:

```bash
~/.codex/skills/feature-map/scripts/feature_map_cli.py extract-app /path/to/app -o app-migration-extract --profile auto
```

Expected guarantees:

- source app is scanned read-only
- output folder contains `index.json`, `index.md`, discovery docs, database docs, and module docs
- `index.json` is valid JSON
- Laravel and Node/Express fixture coverage exists in the test suite

Minimum output files:

```text
index.json
index.md
discovery/tech-stack.md
discovery/route-map.md
discovery/menu-map.md
database/schema-summary.md
database/table-map.json
modules/<module>/overview.md
modules/<module>/route-flow.md
modules/<module>/ui-actions.md
modules/<module>/forms-filters.md
modules/<module>/db-touchpoints.md
modules/<module>/api-candidates.md
modules/<module>/client-surfaces.md
modules/<module>/risks-and-open-questions.md
```

## Local Smoke: HRIS Laravel App

Environment:

- source app: local Laravel HRIS app
- scan mode: static read-only
- database connection: none
- output location: temporary folder under `/tmp`

Observed result from the smoke run:

```text
profile laravel
routes 32
views 346
tables 181
modules 161
index.json valid
```

Reproduction pattern:

```bash
out=$(mktemp -d /tmp/feature-map-hris-extract-smoke.XXXXXX)
python codex-skill/feature-map/scripts/feature_map_cli.py extract-app /path/to/HRIS-Intercom -o "$out" --profile auto
python -m json.tool "$out/index.json" >/dev/null
```

Interpretation:

- `routes` are statically detected route declarations
- `views` are detected UI/client files
- `tables` are detected from migrations
- `modules` are route/UI-based migration candidates

Limits:

- static analysis is intentionally conservative
- dynamic routes, runtime menus, policies, and DB relationships may need manual review
- these numbers will change as the target app changes
- this command does not replace domain validation by the team that owns the app

## Test Suite

Current local suite covers:

- CLI install health
- FEATURE-MAP schema validation
- FEATURE-MAP quality reporting
- blueprint import
- Laravel app extraction
- Node/Express app extraction
- Laravel middleware/view-scope regression checks

Latest verified command:

```text
make test PYTHON=/Users/adesyofyan/Documents/MApp/claude-plugins/.venv/bin/python
91 passed
```
