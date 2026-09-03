from pydantic import BaseModel, ConfigDict

from app.models.status import StatusCategory


class StatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: StatusCategory
    description: str | None = None


class PriorityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    rank: int


class IssueTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    is_subtask: bool
    hierarchy_level: int


class IssueLinkTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    outward_name: str
    inward_name: str
    is_system: bool


class IssueLinkTypeCreate(BaseModel):
    name: str
    outward_name: str
    inward_name: str


class WorkflowTransitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    from_status_id: int | None = None
    to_status_id: int


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    initial_status_id: int


class ProjectRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    is_system: bool
