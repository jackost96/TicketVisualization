import pytest

from app.models.issue_type import IssueType
from app.models.project import Project
from app.models.status import Status
from app.models.workflow import Workflow, WorkflowScheme, WorkflowTransition
from app.services import workflow_service


def _make_project(db_session, key="WF"):
    scheme = db_session.query(WorkflowScheme).filter(WorkflowScheme.name == "Default Scheme").one()
    project = Project(key=key, name="Workflow Test Project", default_workflow_scheme_id=scheme.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def _make_issue(db_session, project, make_user):
    user, _ = make_user()
    bug_type = db_session.query(IssueType).filter(IssueType.name == "Bug").one()
    workflow = workflow_service.resolve_workflow_for_issue_type(db_session, project, bug_type.id)

    from app.models.issue import Issue

    issue = Issue(
        project_id=project.id,
        issue_number=1,
        issue_type_id=bug_type.id,
        status_id=workflow.initial_status_id,
        workflow_id=workflow.id,
        summary="Workflow test issue",
        reporter_id=user.id,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)
    return issue, user


def test_resolve_workflow_uses_default_scheme_entry(db_session):
    project = _make_project(db_session)
    bug_type = db_session.query(IssueType).filter(IssueType.name == "Bug").one()

    workflow = workflow_service.resolve_workflow_for_issue_type(db_session, project, bug_type.id)

    assert workflow.name == "Default Workflow"
    open_status = db_session.query(Status).filter(Status.name == "Open").one()
    assert workflow.initial_status_id == open_status.id


def test_valid_transition_updates_status_and_history(db_session, make_user):
    project = _make_project(db_session)
    issue, user = _make_issue(db_session, project, make_user)

    in_progress = db_session.query(Status).filter(Status.name == "In Progress").one()
    start_progress = (
        db_session.query(WorkflowTransition)
        .filter(
            WorkflowTransition.workflow_id == issue.workflow_id,
            WorkflowTransition.to_status_id == in_progress.id,
            WorkflowTransition.name == "Start Progress",
        )
        .one()
    )

    workflow_service.apply_transition(db_session, issue, start_progress.id, user)
    db_session.commit()

    assert issue.status_id == in_progress.id

    from app.models.issue import IssueHistory

    history = (
        db_session.query(IssueHistory)
        .filter(IssueHistory.issue_id == issue.id, IssueHistory.field_name == "status")
        .all()
    )
    assert len(history) == 1
    assert history[0].new_value == str(in_progress.id)


def test_invalid_transition_raises(db_session, make_user):
    project = _make_project(db_session)
    issue, user = _make_issue(db_session, project, make_user)

    closed = db_session.query(Status).filter(Status.name == "Closed").one()
    close_transition = (
        db_session.query(WorkflowTransition)
        .filter(
            WorkflowTransition.workflow_id == issue.workflow_id,
            WorkflowTransition.to_status_id == closed.id,
            WorkflowTransition.name == "Close",
        )
        .one()
    )

    with pytest.raises(workflow_service.InvalidTransitionError) as exc_info:
        workflow_service.apply_transition(db_session, issue, close_transition.id, user)

    assert any(t.name == "Start Progress" for t in exc_info.value.valid_transitions)


def test_reaching_done_status_sets_resolved_at_and_reopen_clears_it(db_session, make_user):
    project = _make_project(db_session)
    issue, user = _make_issue(db_session, project, make_user)

    def transition_by_name(name: str):
        transitions = workflow_service.get_available_transitions(db_session, issue)
        transition = next(t for t in transitions if t.name == name)
        workflow_service.apply_transition(db_session, issue, transition.id, user)

    transition_by_name("Start Progress")
    transition_by_name("Investigate")
    transition_by_name("Move to QA")
    transition_by_name("Close")
    db_session.commit()

    assert issue.resolved_at is not None

    transition_by_name("Reopen")
    db_session.commit()

    assert issue.resolved_at is None
