from scripts.migrate_from_jira.cache import load_or_fetch
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.jira_client import JiraClient


def fetch_users(client: JiraClient, config: MigrationConfig) -> list[dict]:
    def _fetch():
        for user in client.paginated_get("/rest/api/3/users/search"):
            # Filter out Jira's built-in app/bot accounts; keep real people only.
            if user.get("accountType") == "atlassian":
                yield user

    return load_or_fetch(config, "users", _fetch)
