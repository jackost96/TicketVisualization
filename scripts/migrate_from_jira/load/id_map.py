from sqlalchemy.orm import Session

from app.models.jira_id_map import JiraIdMap


def get_local_id(db: Session, entity_type: str, jira_id: str | int | None) -> int | None:
    if jira_id is None:
        return None
    row = (
        db.query(JiraIdMap)
        .filter(JiraIdMap.entity_type == entity_type, JiraIdMap.jira_id == str(jira_id))
        .one_or_none()
    )
    return row.local_id if row else None


def record(db: Session, entity_type: str, jira_id: str | int, local_id: int) -> None:
    existing = (
        db.query(JiraIdMap)
        .filter(JiraIdMap.entity_type == entity_type, JiraIdMap.jira_id == str(jira_id))
        .one_or_none()
    )
    if existing is not None:
        existing.local_id = local_id
    else:
        db.add(JiraIdMap(entity_type=entity_type, jira_id=str(jira_id), local_id=local_id))
