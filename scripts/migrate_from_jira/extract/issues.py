from scripts.migrate_from_jira.cache import load_or_fetch
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.jira_client import JiraClient


def fetch_issues(client: JiraClient, config: MigrationConfig, project_key: str) -> list[dict]:
    def _fetch():
        jql = f"project = {project_key} ORDER BY created ASC"
        yield from client.paginated_jql_search(jql, fields=["*all"], expand="changelog")

    return load_or_fetch(config, f"issues_{project_key}", _fetch)


def fetch_comments_for_issue(client: JiraClient, config: MigrationConfig, issue_key: str) -> list[dict]:
    """Only needed as a fallback for issues whose inline `fields.comment.comments` page (returned
    with the issue search results) doesn't already contain every comment."""

    def _fetch():
        return client.paginated_get(f"/rest/api/3/issue/{issue_key}/comment")

    return load_or_fetch(config, f"comments_{issue_key}", _fetch)
