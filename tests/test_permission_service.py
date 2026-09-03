from app.models.permission import ProjectRole


def _bug_issue_type_id(client, headers):
    resp = client.get("/api/v1/issue-types", headers=headers)
    types = {t["name"]: t["id"] for t in resp.json()}
    return types["Bug"]


def test_user_without_role_is_forbidden_then_allowed_after_grant(client, auth_client, db_session):
    admin_user, admin_headers = auth_client(email="admin@example.com")
    other_user, other_headers = auth_client(email="dev@example.com")

    project_resp = client.post(
        "/api/v1/projects", json={"key": "PERM", "name": "Permission Test"}, headers=admin_headers
    )
    assert project_resp.status_code == 201, project_resp.text

    bug_id = _bug_issue_type_id(client, admin_headers)

    forbidden_resp = client.post(
        "/api/v1/issues",
        json={"project_key": "PERM", "issue_type_id": bug_id, "summary": "Should be blocked"},
        headers=other_headers,
    )
    assert forbidden_resp.status_code == 403

    developer_role = db_session.query(ProjectRole).filter(ProjectRole.name == "Developer").one()
    grant_resp = client.post(
        f"/api/v1/projects/PERM/roles/{developer_role.id}/members",
        json={"user_id": other_user.id},
        headers=admin_headers,
    )
    assert grant_resp.status_code == 201, grant_resp.text

    allowed_resp = client.post(
        "/api/v1/issues",
        json={"project_key": "PERM", "issue_type_id": bug_id, "summary": "Should now work"},
        headers=other_headers,
    )
    assert allowed_resp.status_code == 201, allowed_resp.text


def test_admin_permission_required_to_grant_roles(client, auth_client):
    admin_user, admin_headers = auth_client(email="admin2@example.com")
    other_user, other_headers = auth_client(email="dev2@example.com")

    client.post(
        "/api/v1/projects", json={"key": "PERM2", "name": "Permission Test 2"}, headers=admin_headers
    )

    resp = client.patch(
        "/api/v1/projects/PERM2", json={"name": "Renamed"}, headers=other_headers
    )
    assert resp.status_code == 403
