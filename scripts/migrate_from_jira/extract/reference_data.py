"""Extractors for the small, global reference/config entities: statuses, priorities,
issue types, and issue link types. These upsert-merge onto our seeded reference rows by
`name` at load time (see load/loaders.py), rather than by jira_*_id, so a fresh prototype
that already ran seed_defaults.py doesn't end up with duplicate "Open"/"Bug"/etc rows."""
from scripts.migrate_from_jira.cache import load_or_fetch
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.jira_client import JiraClient


def fetch_statuses(client: JiraClient, config: MigrationConfig) -> list[dict]:
    return load_or_fetch(config, "statuses", lambda: client.get("/rest/api/3/status"))


def fetch_priorities(client: JiraClient, config: MigrationConfig) -> list[dict]:
    return load_or_fetch(
        config, "priorities", lambda: client.paginated_get("/rest/api/3/priority/search")
    )


def fetch_issue_types(client: JiraClient, config: MigrationConfig) -> list[dict]:
    return load_or_fetch(config, "issue_types", lambda: client.get("/rest/api/3/issuetype"))


def fetch_issue_link_types(client: JiraClient, config: MigrationConfig) -> list[dict]:
    def _fetch():
        return client.get("/rest/api/3/issueLinkType")["issueLinkTypes"]

    return load_or_fetch(config, "issue_link_types", _fetch)
