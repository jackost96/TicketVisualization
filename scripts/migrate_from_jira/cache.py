import json
from pathlib import Path

from scripts.migrate_from_jira.config import MigrationConfig


def cache_path(config: MigrationConfig, entity: str) -> Path:
    path = config.scratch_dir / entity
    path.mkdir(parents=True, exist_ok=True)
    return path / "data.json"


def load_or_fetch(config: MigrationConfig, entity: str, fetch_fn) -> list[dict]:
    """Returns cached JSON for `entity` if present, else calls fetch_fn() (which should hit the
    Jira API), caches the result to scratch/jira_export/<entity>/data.json, and returns it.
    Lets migration mapping logic be iterated on locally without re-hitting the Jira API each run."""
    path = cache_path(config, entity)
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    data = list(fetch_fn())
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return data
