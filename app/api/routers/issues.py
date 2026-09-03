from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.comment import Comment
from app.models.issue import IssueHistory
from app.models.issue_link import IssueLink, IssueLinkType
from app.models.project import Project
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.schemas.issue import IssueCreate, IssueHistoryRead, IssueRead, IssueUpdate, TransitionRequest
from app.schemas.issue_link import IssueLinkCreate, IssueLinkRead
from app.schemas.metadata import WorkflowTransitionRead
from app.services import issue_service, workflow_service
from app.services.issue_service import IssueNotFoundError
from app.services.permission_service import require_permission

router = APIRouter(prefix="/issues", tags=["issues"])


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(
    payload: IssueCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    project = _project_for_key_or_404(db, payload.project_key)
    require_permission(db, user, project.id, "issue.create")
    try:
        issue = issue_service.create_issue(db, payload, user)
    except workflow_service.NoWorkflowSchemeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return issue_service.serialize_issue(issue)


@router.get("/me", response_model=list[IssueRead])
def list_my_issues(
    open_only: bool = False,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    issues = issue_service.list_issues_assigned_to(
        db, user.id, open_only=open_only, limit=limit, offset=offset
    )
    return [issue_service.serialize_issue(i) for i in issues]


@router.get("", response_model=list[IssueRead])
def list_issues(
    project: str | None = None,
    status_id: int | None = None,
    assignee_id: int | None = None,
    reporter_id: int | None = None,
    issue_type_id: int | None = None,
    q: str | None = None,
    open_only: bool = False,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    issues = issue_service.list_issues(
        db,
        project_key=project,
        status_id=status_id,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        issue_type_id=issue_type_id,
        q=q,
        open_only=open_only,
        limit=limit,
        offset=offset,
    )
    return [issue_service.serialize_issue(i) for i in issues]


def _get_issue_or_404(db: Session, key: str):
    try:
        return issue_service.get_issue_by_key(db, key)
    except (IssueNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _project_for_key_or_404(db: Session, project_key: str):
    project = db.query(Project).filter(Project.key == project_key).one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_key}' not found"
        )
    return project


@router.get("/{key}", response_model=IssueRead)
def get_issue(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    return issue_service.serialize_issue(issue)


@router.patch("/{key}", response_model=IssueRead)
def update_issue(
    key: str,
    payload: IssueUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    issue = _get_issue_or_404(db, key)
    require_permission(db, user, issue.project_id, "issue.edit")
    issue = issue_service.update_issue(db, issue, payload, user)
    return issue_service.serialize_issue(issue)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue(key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    require_permission(db, user, issue.project_id, "issue.delete")
    issue_service.delete_issue(db, issue)


@router.get("/{key}/transitions", response_model=list[WorkflowTransitionRead])
def get_transitions(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    return workflow_service.get_available_transitions(db, issue)


@router.post("/{key}/transitions", response_model=IssueRead)
def do_transition(
    key: str,
    payload: TransitionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    issue = _get_issue_or_404(db, key)
    require_permission(db, user, issue.project_id, "issue.transition")
    try:
        issue = workflow_service.apply_transition(db, issue, payload.transition_id, user)
    except workflow_service.InvalidTransitionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "valid_transitions": [
                    {"id": t.id, "name": t.name, "to_status_id": t.to_status_id}
                    for t in exc.valid_transitions
                ],
            },
        ) from exc
    db.commit()
    db.refresh(issue)
    return issue_service.serialize_issue(issue)


@router.get("/{key}/history", response_model=list[IssueHistoryRead])
def get_history(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    return (
        db.query(IssueHistory)
        .filter(IssueHistory.issue_id == issue.id)
        .order_by(IssueHistory.created_at)
        .all()
    )


# --- comments ---------------------------------------------------------------


@router.get("/{key}/comments", response_model=list[CommentRead])
def list_comments(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    return (
        db.query(Comment).filter(Comment.issue_id == issue.id).order_by(Comment.created_at).all()
    )


@router.post("/{key}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    key: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    issue = _get_issue_or_404(db, key)
    require_permission(db, user, issue.project_id, "comment.create")
    comment = Comment(issue_id=issue.id, author_id=user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.patch("/comments/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the comment author")
    comment.body = payload.body
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != user.id:
        require_permission(db, user, comment.issue.project_id, "comment.delete_any")
    db.delete(comment)
    db.commit()


# --- issue links --------------------------------------------------------------


def _link_label(link: IssueLink, from_issue_id: int) -> str:
    if link.source_issue_id == from_issue_id:
        return link.link_type.outward_name
    return link.link_type.inward_name


@router.get("/{key}/links", response_model=list[IssueLinkRead])
def list_links(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    issue = _get_issue_or_404(db, key)
    links = (
        db.query(IssueLink)
        .filter(
            (IssueLink.source_issue_id == issue.id) | (IssueLink.target_issue_id == issue.id)
        )
        .all()
    )
    return [
        IssueLinkRead(
            id=link.id,
            link_type_id=link.link_type_id,
            source_issue_id=link.source_issue_id,
            target_issue_id=link.target_issue_id,
            label=_link_label(link, issue.id),
        )
        for link in links
    ]


@router.post("/{key}/links", response_model=IssueLinkRead, status_code=status.HTTP_201_CREATED)
def create_link(
    key: str,
    payload: IssueLinkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    issue = _get_issue_or_404(db, key)
    require_permission(db, user, issue.project_id, "issue.link")

    target = _get_issue_or_404(db, payload.target_key)
    link_type = db.get(IssueLinkType, payload.link_type_id)
    if link_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link type not found")
    if target.id == issue.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot link an issue to itself"
        )

    if payload.direction == "inward":
        source_id, target_id = target.id, issue.id
    else:
        source_id, target_id = issue.id, target.id

    link = IssueLink(link_type_id=link_type.id, source_issue_id=source_id, target_issue_id=target_id)
    db.add(link)
    db.commit()
    db.refresh(link)
    return IssueLinkRead(
        id=link.id,
        link_type_id=link.link_type_id,
        source_issue_id=link.source_issue_id,
        target_issue_id=link.target_issue_id,
        label=_link_label(link, issue.id),
    )


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(link_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    link = db.get(IssueLink, link_id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    require_permission(db, user, link.source_issue.project_id, "issue.link")
    db.delete(link)
    db.commit()
