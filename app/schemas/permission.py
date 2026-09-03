from pydantic import BaseModel


class EffectivePermissions(BaseModel):
    project_id: int
    permissions: list[str]
