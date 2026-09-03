from scripts.migrate_from_jira.cache import load_or_fetch
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.jira_client import JiraClient


def fetch_projects(client: JiraClient, config: MigrationConfig) -> list[dict]:
    def _fetch():
        for project in client.paginated_get("/rest/api/3/project/search", params={"expand": "lead"}):
            if not config.project_keys or project["key"] in config.project_keys:
                yield project

    return load_or_fetch(config, "projects", _fetch)


def fetch_project_roles(client: JiraClient, config: MigrationConfig, project_key: str) -> dict:
    """Returns {role_name: [accountId, ...]} for a single project."""

    def _fetch():
        roles = client.get(f"/rest/api/3/project/{project_key}/role")
        result = {}
        for role_name, role_url in roles.items():
            role_id = role_url.rstrip("/").rsplit("/", 1)[-1]
            detail = client.get(f"/rest/api/3/project/{project_key}/role/{role_id}")
            result[role_name] = [
                actor["actorUser"]["accountId"]
                for actor in detail.get("actors", [])
                if "actorUser" in actor
            ]
        return [result]  # load_or_fetch caches a list; unwrap the single dict on read

    return load_or_fetch(config, f"project_roles_{project_key}", _fetch)[0]
