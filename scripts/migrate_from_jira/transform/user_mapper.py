def map_user(jira_user: dict) -> dict:
    account_id = jira_user["accountId"]
    return {
        "jira_account_id": account_id,
        "email": jira_user.get("emailAddress") or f"{account_id}@unknown.invalid",
        "display_name": jira_user.get("displayName") or "Unknown User",
        "is_active": jira_user.get("active", True),
    }
