import time
from collections.abc import Iterator

import httpx

from scripts.migrate_from_jira.config import MigrationConfig

_MAX_RETRIES = 5


class JiraClient:
    def __init__(self, config: MigrationConfig):
        self._config = config
        self._client = httpx.Client(
            base_url=config.jira_base_url.rstrip("/"),
            auth=(config.jira_email, config.jira_api_token),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        for attempt in range(_MAX_RETRIES):
            response = self._client.request(method, path, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                retry_after = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(retry_after)
                continue
            response.raise_for_status()
            return response
        response.raise_for_status()
        return response

    def get(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params).json()

    def post(self, path: str, json: dict | None = None) -> dict:
        return self._request("POST", path, json=json).json()

    def paginated_get(
        self, path: str, params: dict | None = None, page_size: int | None = None
    ) -> Iterator[dict]:
        """Pagination via startAt/maxResults/isLast|total, used by most Jira Cloud collection
        endpoints (project/search, users/search, priority/search, ...)."""
        params = dict(params or {})
        params["maxResults"] = page_size or self._config.batch_size
        start_at = 0
        while True:
            params["startAt"] = start_at
            page = self.get(path, params=params)
            values = page.get("values", page if isinstance(page, list) else [])
            yield from values
            if isinstance(page, dict):
                is_last = page.get("isLast")
                total = page.get("total")
                returned = len(values)
                if is_last is True or returned == 0:
                    break
                if total is not None and start_at + returned >= total:
                    break
                start_at += returned
            else:
                break

    def paginated_jql_search(
        self, jql: str, fields: list[str] | None = None, expand: str | None = None
    ) -> Iterator[dict]:
        """Pagination via nextPageToken, used by /rest/api/3/search/jql (the current
        Jira Cloud issue search endpoint; the old /search endpoint is deprecated)."""
        next_page_token = None
        while True:
            body = {
                "jql": jql,
                "maxResults": self._config.batch_size,
                "fields": fields or ["*all"],
            }
            if expand:
                body["expand"] = expand
            if next_page_token:
                body["nextPageToken"] = next_page_token
            page = self.post("/rest/api/3/search/jql", json=body)
            yield from page.get("issues", [])
            next_page_token = page.get("nextPageToken")
            if not next_page_token:
                break
