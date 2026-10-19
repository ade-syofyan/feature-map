"""Public usage examples must not depend on a developer's personal machine."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_distributed_guides_and_cli_have_no_absolute_user_home_paths():
    names = [Path(x) for x in ('README.md', 'BENCHMARK.md', 'SMOKE.md')]
    names += list((ROOT / 'codex-skill/feature-map').rglob('*.md'))
    names += [Path('codex-skill/feature-map/scripts/feature_map_cli.py')]
    for name in names:
        assert not re.search(r'/(?:Users|home)/[^/\s]+/', (ROOT / name).read_text()), name
