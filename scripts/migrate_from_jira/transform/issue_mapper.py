def adf_to_text(adf: dict | str | None) -> str | None:
    """Flattens Atlassian Document Format (the JSON structure Jira Cloud v3 uses for rich-text
    fields like description/comment body) down to plain text. Lossy by design for a prototype —
    formatting/mentions/attachments in the ADF tree are dropped, only text content is kept."""
    if adf is None:
        return None
    if isinstance(adf, str):
        return adf

    parts: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []) or []:
                walk(child)
            if node.get("type") in ("paragraph", "heading"):
                parts.append("\n")
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(adf)
    return "".join(parts).strip() or None


def map_issue(jira_issue: dict) -> dict:
    fields = jira_issue["fields"]
    reporter = fields.get("reporter") or {}
    assignee = fields.get("assignee") or {}
    priority = fields.get("priority") or {}
    resolution = fields.get("resolution") or {}
    parent = fields.get("parent") or {}

    return {
        "jira_issue_id": jira_issue["id"],
        "jira_key": jira_issue["key"],
        "issue_type_jira_id": fields["issuetype"]["id"],
        "status_jira_id": fields["status"]["id"],
        "priority_jira_id": priority.get("id"),
        "summary": fields["summary"],
        "description": adf_to_text(fields.get("description")),
        "reporter_account_id": reporter.get("accountId"),
        "assignee_account_id": assignee.get("accountId"),
        "resolution": resolution.get("name"),
        "resolved_at": fields.get("resolutiondate"),
        "due_date": fields.get("duedate"),
        "labels": fields.get("labels") or [],
        "parent_jira_id": parent.get("id"),
        "changelog": jira_issue.get("changelog", {}).get("histories", []),
        "inline_comments": (fields.get("comment") or {}).get("comments", []),
        "inline_comment_total": (fields.get("comment") or {}).get("total", 0),
        "custom_fields": {
            key: value
            for key, value in fields.items()
            if key.startswith("customfield_") and value is not None
        },
    }
