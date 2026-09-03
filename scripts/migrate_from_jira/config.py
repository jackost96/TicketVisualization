from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings

SCRATCH_DIR = Path(__file__).resolve().parents[2] / "scratch" / "jira_export"


@dataclass
class MigrationConfig:
    jira_base_url: str = settings.jira_base_url
    jira_email: str = settings.jira_email
    jira_api_token: str = settings.jira_api_token
    project_keys: list[str] = field(default_factory=list)  # empty = all projects
    dry_run: bool = False
    batch_size: int = 100
    scratch_dir: Path = SCRATCH_DIR

    def __post_init__(self):
        if not self.dry_run and not (self.jira_base_url and self.jira_email and self.jira_api_token):
            raise ValueError(
                "JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set (see .env.example) "
                "unless running with --dry-run against cached data only"
            )
