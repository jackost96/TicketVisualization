from pydantic import BaseModel, ConfigDict


class FilterQuery(BaseModel):
    project: str | None = None
    status_id: int | None = None
    assignee_id: int | None = None
    reporter_id: int | None = None
    issue_type_id: int | None = None
    q: str | None = None


class SavedFilterCreate(BaseModel):
    name: str
    query: FilterQuery


class SavedFilterUpdate(BaseModel):
    name: str | None = None
    query: FilterQuery | None = None


class SavedFilterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_user_id: int
    name: str
    query: FilterQuery
