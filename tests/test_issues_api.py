def _create_project(client, headers, key="ENG"):
    resp = client.post(
        "/api/v1/projects",
        json={"key": key, "name": "Engineering"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _bug_issue_type_id(client, headers):
    resp = client.get("/api/v1/issue-types", headers=headers)
    assert resp.status_code == 200
    types = {t["name"]: t["id"] for t in resp.json()}
    return types["Bug"]


def test_create_issue_assigns_sequential_key(client, auth_client):
    user, headers = auth_client()
    _create_project(client, headers)
    bug_id = _bug_issue_type_id(client, headers)

    resp1 = client.post(
        "/api/v1/issues",
        json={"project_key": "ENG", "issue_type_id": bug_id, "summary": "First bug"},
        headers=headers,
    )
    assert resp1.status_code == 201, resp1.text
    issue1 = resp1.json()
    assert issue1["key"] == "ENG-1"
    assert issue1["issue_number"] == 1

    resp2 = client.post(
        "/api/v1/issues",
        json={"project_key": "ENG", "issue_type_id": bug_id, "summary": "Second bug"},
        headers=headers,
    )
    assert resp2.status_code == 201, resp2.text
    assert resp2.json()["key"] == "ENG-2"


def test_get_issue_by_key(client, auth_client):
    user, headers = auth_client()
    _create_project(client, headers)
    bug_id = _bug_issue_type_id(client, headers)

    create_resp = client.post(
        "/api/v1/issues",
        json={"project_key": "ENG", "issue_type_id": bug_id, "summary": "Findable bug"},
        headers=headers,
    )
    key = create_resp.json()["key"]

    get_resp = client.get(f"/api/v1/issues/{key}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["summary"] == "Findable bug"


def test_update_issue_writes_history(client, auth_client):
    user, headers = auth_client()
    _create_project(client, headers)
    bug_id = _bug_issue_type_id(client, headers)

    create_resp = client.post(
        "/api/v1/issues",
        json={"project_key": "ENG", "issue_type_id": bug_id, "summary": "Original summary"},
        headers=headers,
    )
    key = create_resp.json()["key"]

    patch_resp = client.patch(
        f"/api/v1/issues/{key}", json={"summary": "Updated summary"}, headers=headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["summary"] == "Updated summary"

    history_resp = client.get(f"/api/v1/issues/{key}/history", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert any(h["field_name"] == "summary" and h["new_value"] == "Updated summary" for h in history)


def test_list_issues_assigned_to_me(client, auth_client):
    user, headers = auth_client()
    _create_project(client, headers)
    bug_id = _bug_issue_type_id(client, headers)

    client.post(
        "/api/v1/issues",
        json={
            "project_key": "ENG",
            "issue_type_id": bug_id,
            "summary": "Assigned to me",
            "assignee_id": user.id,
        },
        headers=headers,
    )

    resp = client.get("/api/v1/issues/me", headers=headers)
    assert resp.status_code == 200
    assert any(i["summary"] == "Assigned to me" for i in resp.json())
