from pydantic import BaseModel

from app.models.status import StatusCategory


class BoardColumnRead(BaseModel):
    status_id: int
    name: str
    category: StatusCategory
    position: int


class BoardRead(BaseModel):
    id: int
    project_id: int
    name: str
    swimlane_strategy: str
    columns: list[BoardColumnRead]


class BoardSummary(BaseModel):
    id: int
    project_id: int
    name: str
    swimlane_strategy: str


class BoardCreate(BaseModel):
    name: str = "Kanban Board"
