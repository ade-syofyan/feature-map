# Flow Sync Install

Install the feature-map pre-commit warning hook in the current git repo.

1. Verify git repo:

```bash
git rev-parse --git-dir
```

2. Verify `FEATURE-MAP.yaml` exists at the repo root. If absent, run flow-map-init first.
3. Resolve plugin root, then use:

```bash
python3 "<plugin-root>/hooks/precommit_check.py" || true  # feature-map
```

4. If `.git/hooks/pre-commit` does not exist, create it with `#!/bin/sh` and the line above, then `chmod +x`.
5. If it exists and already contains `# feature-map`, report already installed.
6. If it exists without feature-map, append the line. Preserve existing hook content.
7. Verify:

```bash
python3 "<plugin-root>/hooks/precommit_check.py" < /dev/null
```

The hook warns only; it should not block commit.
