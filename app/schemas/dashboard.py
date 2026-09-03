from pydantic import BaseModel, ConfigDict

from app.models.status import StatusCategory


class DashboardCreate(BaseModel):
    name: str


class DashboardUpdate(BaseModel):
    name: str


class DashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_user_id: int
    name: str
    is_favorite: bool = False


class StatusCountRead(BaseModel):
    status_id: int
    status_name: str
    category: StatusCategory
    count: int
