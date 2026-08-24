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

## Reproducible Fixtures

Run the synthetic Laravel, Node and Dart extractor tests in `tests/test_feature_map_cli.py`.
No customer repository is required. Outputs are checked in temporary directories.
Static route/table discovery does not prove runtime business behavior.

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
python3 -m pytest tests -q
```
