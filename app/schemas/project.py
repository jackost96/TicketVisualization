from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    key: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z][A-Z0-9]*$")
    name: str
    description: str | None = None
    lead_user_id: int | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    lead_user_id: int | None = None
    is_archived: bool | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    description: str | None = None
    lead_user_id: int | None = None
    is_archived: bool


class ProjectRoleMemberCreate(BaseModel):
    user_id: int


class ProjectRoleMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    role_id: int
    user_id: int
