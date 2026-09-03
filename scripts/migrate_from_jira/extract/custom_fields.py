from scripts.migrate_from_jira.cache import load_or_fetch
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.jira_client import JiraClient


def fetch_custom_fields(client: JiraClient, config: MigrationConfig) -> list[dict]:
    def _fetch():
        for f in client.get("/rest/api/3/field"):
            if f.get("custom"):
                yield f

    return load_or_fetch(config, "custom_fields", _fetch)
